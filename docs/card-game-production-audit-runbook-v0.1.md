# Runbook — auditoria de produção somente leitura (v0.1)

**Estado:** ferramentas preparadas e testadas localmente; nenhuma consulta ao banco real, ao Cloudflare R2 ou ao Discord de produção foi executada. Este documento descreve como obter evidência real no host, sem fornecer credenciais ao chat e sem alterar dados.

> **Contexto operacional:** o proprietário informou em 2026-11-27 que o jogo ainda não tem jogadores reais e que eventuais registros são dados de teste próprios. Portanto, este runbook não é um pré-requisito para continuar a reconstrução. Execute-o apenas quando houver necessidade de preservar/reutilizar artes aprovadas, submissões, anexos ou registros existentes. O fato de não haver jogadores reais não autoriza apagar automaticamente bucket R2, anexos do Discord ou arte aprovada. Para limpar somente dados de teste, prefira um procedimento separado de reset/reseed depois de identificar o banco correto e delimitar o escopo.

## 1. Objetivo e limites

Cruzar quatro origens de arte/cartas que o código mantém separadas:

1. `cartas_atelie_submissoes`: submissões completas do Ateliê. As submissões novas gravam `image_key` no SQLite e armazenam o arquivo original no R2; registros antigos podem continuar com `image_data` em BLOB.
2. `cartas_atelie_artes`: fluxo legado de pedidos do Ateliê/Coliseu. A tabela guarda `channel_id`, `message_id` e `attachment_id` do Discord, não `image_key` do R2. A existência do anexo precisa ser verificada no Discord, não no bucket.
3. `cartas_gwent_lideres_artes`: artes de líderes guardadas como BLOB no SQLite, com `mime_type` e `revision`.
4. `cartas_geradas` + `cartas_geradas_artes`: artes pessoais do Laboratório guardadas em `DATA_DIR/cartas_geradas/<owner_id>/<card_id>.png` e referenciadas pelo `storage_path`/`content_hash` da tabela de artes. O endpoint só publica a carta pessoal se `status='published'`, `art_status='validated'` e o hash do PNG local coincidir.

Além disso, o R2 pode conter `cards/<card_hash>/<etag>.<ext>`: são variantes imutáveis de cache/CDN, não as originais de submissão do Ateliê. Não classificar esse prefixo automaticamente como órfão.

O fluxo novo do Ateliê monta chaves neste formato:

`atelier/submissions/<user_id>/<sha256-card-id>/exemplar-<exemplar_id>/<sha256>-<nonce>.jpg`

O relatório exporta somente SHA-256 da chave + namespace, nunca o caminho bruto ou o ID do usuário.

## 2. Caminho provável do SQLite

A configuração fonte está em `config.py`:

- `DB_PATH` vence, se configurado.
- Caso contrário, o caminho é `DATA_DIR/colizeu.db`.
- `DATA_DIR` vem da variável de ambiente; se vazia, o código usa `/data` quando esse diretório existe; caso contrário usa `./data` relativo ao projeto.

**Não importe `config.py` nem instancie `Database.connect()` para uma auditoria read-only.** `Database.connect()` executa `SCHEMA`, `SCHEMA_CARTAS`, migrações, índices, triggers e atualizações de compatibilidade. Use os scripts abaixo, que dependem apenas da biblioteca padrão para o SQLite e abrem a origem com `mode=ro`/`query_only`.

## 3. Pré-requisitos no host

- Acesso ao terminal/console do mesmo host/volume que contém o SQLite e `DATA_DIR`.
- O processo/host deve ter acesso aos arquivos persistentes.
- Para R2, as variáveis `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` e `R2_BUCKET_NAME` devem estar no ambiente do processo de auditoria. `boto3` já consta em `requirements.txt`.
- Se o bucket público de cartas for separado, as variáveis opcionais `R2_PUBLIC_CARDS_BUCKET_NAME`, `R2_PUBLIC_CARDS_ACCOUNT_ID`, `R2_PUBLIC_CARDS_ACCESS_KEY_ID` e `R2_PUBLIC_CARDS_SECRET_ACCESS_KEY` devem seguir a mesma configuração da aplicação. Se não houver bucket separado, o inventariador lista uma vez o bucket primário.

Não copie o `.env` preenchido para o repositório ou para o chat. Os scripts não leem `.env` automaticamente: recebem credenciais somente do ambiente do processo. Não execute `env`, `printenv`, `set` nem comandos que imprimam os segredos no log.

## 4. Execução recomendada

Execute no host de produção, a partir da raiz do checkout implantado. Ajuste o nome da pasta temporária se a política operacional do host exigir outro local seguro.

```bash
umask 077
AUDIT_DIR="/tmp/card-game-production-audit"
mkdir -m 700 -p "$AUDIT_DIR"
chmod 700 "$AUDIT_DIR"

if [ -n "${DB_PATH:-}" ]; then
  DB_FILE="$DB_PATH"
elif [ -n "${DATA_DIR:-}" ]; then
  DB_FILE="$DATA_DIR/colizeu.db"
elif [ -d /data ]; then
  DB_FILE="/data/colizeu.db"
else
  DB_FILE="./data/colizeu.db"
fi

if [ -n "${DATA_DIR:-}" ]; then
  DATA_ROOT="$DATA_DIR"
elif [ -d /data ]; then
  DATA_ROOT="/data"
else
  DATA_ROOT="./data"
fi

python docs/scripts/snapshot-sqlite-readonly-v0.1.py \
  --source "$DB_FILE" \
  --output "$AUDIT_DIR/colizeu-production-snapshot.sqlite3"

python docs/scripts/audit-production-card-db-v0.1.py \
  --db "$AUDIT_DIR/colizeu-production-snapshot.sqlite3" \
  --output "$AUDIT_DIR/card-game-production-db-audit.json" \
  --verify-local-generated-art \
  --data-dir "$DATA_ROOT"

python docs/scripts/inventory-r2-readonly-v0.1.py \
  --output "$AUDIT_DIR/cloudflare-r2-object-inventory.json"

python docs/scripts/reconcile-production-card-assets-v0.1.py \
  --db-audit "$AUDIT_DIR/card-game-production-db-audit.json" \
  --r2-inventory "$AUDIT_DIR/cloudflare-r2-object-inventory.json" \
  --output "$AUDIT_DIR/card-game-production-assets-reconciliation.json"
```

### 4.1. O que cada comando faz

- `snapshot-sqlite-readonly-v0.1.py`: abre o arquivo origem com URI `mode=ro`, ativa `query_only`, valida `quick_check` e usa a API oficial `sqlite3.Connection.backup` para produzir snapshot consistente (inclusive considerando o mecanismo WAL). A origem não é aberta para escrita. O destino é criado com permissão `0600` e nunca sobrescrito.
- `audit-production-card-db-v0.1.py`: lê apenas tabelas relacionadas ao jogo de cartas; agrega coleção, exemplares, decks, status de partidas e arte. Não exporta valores de `user_id`/`reviewer_id`, prompts, razões de rejeição, BLOBs, imagem ou conteúdo de `state_json`. `image_key` vira SHA-256.
- `inventory-r2-readonly-v0.1.py`: chama apenas `ListObjectsV2` no(s) bucket(s) configurado(s). Não chama `GetObject`, `HeadObject`, `PutObject`, `DeleteObject`, `CopyObject` ou operações de ACL. Lista metadados (tamanho/data/ETag/storage class) e SHA-256 da chave, sem a chave bruta. Saída também fica com permissão `0600`.
- `reconcile-production-card-assets-v0.1.py`: cruza hashes SQLite/R2, diferencia referências aprovadas ausentes e objetos `atelier/submissions` sem referência. Recusa inventário truncado. Não remove nem altera nada.

O snapshot SQLite contém dados completos de produção, inclusive dados pessoais e possivelmente BLOBs legados. **Mantenha-o somente no host/volume seguro; não envie, não comite e não inclua esse arquivo em `soulsbo-main-handoff.zip`.** Os JSONs locais também são material operacional; o reconciliador é a saída preferida para compartilhar um resumo, pois não contém caminhos brutos nem credenciais.

## 5. Permissões mínimas e segurança R2

O token de auditoria precisa apenas da permissão de listagem equivalente a `s3:ListBucket` nos buckets configurados. Não conceda permissões de escrita, exclusão, leitura de objeto ou administração para esta etapa. A auditoria falha de modo explícito se a listagem não estiver autorizada; não deve ser contornada com token de escrita mais amplo.

O script não imprime nem persiste `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` ou `R2_ACCOUNT_ID`. O inventário contém nomes de bucket, namespace, hashes de chaves, tamanhos, datas, ETags e classe de armazenamento. Não contém URLs públicas nem imagem.

## 6. Como interpretar a reconciliação

- `approved_r2_refs_missing_and_without_legacy_blob > 0`: provável arte oficial aprovada sem objeto R2 acessível no bucket inventariado. Antes de concluir perda, confirme que o snapshot DB e o inventário listaram todos os buckets certos e foram capturados em janelas próximas.
- `db_key_hashes_missing_from_r2_by_status.pending`: submissões pendentes com referência que não apareceu no inventário completo; investigar sincronização/expiração, sem apagar linha.
- `unlinked_atelier_r2_objects_candidate_count > 0`: objetos no prefixo `atelier/submissions` sem referência na cópia DB. São **candidatos** a órfão, não lixo comprovado: o upload pode ter ocorrido antes de commit, o banco pode ter snapshot mais antigo ou histórico DB pode ter sido removido.
- Namespace `cards`: cache/CDN pública. Pode conter várias variantes por carta, `etag` e formato; não deve ser comparado um-para-um com submissões aprovadas.
- `cartas_atelie_artes`: requer verificação de `message_id`/`attachment_id` no canal privado do Discord. Este runbook não baixa anexos nem usa o token do bot.
- `cartas_gwent_lideres_artes`: conferir bytes e MIME no relatório DB; os arquivos vivem no BLOB SQLite.
- `cartas_geradas_artes`: com `--verify-local-generated-art`, conferir `exists` e `actual_sha256_matches_db`. A saída não revela os caminhos locais.

Nenhuma categoria ou métrica autoriza limpeza automática. A próxima ação, diante de divergência, é inspeção individual e backup validado.

## 7. Testes locais feitos nesta revisão

`python docs/scripts/test-production-audit-tooling-v0.1.py`

Sete testes passaram usando SQLite temporário e um cliente S3 simulado: snapshot read-only, leitura de linha ainda presente no WAL sem alterar o WAL, sanitização do relatório DB, verificação de arte local sem revelar paths, chamada apenas de `ListObjectsV2`, detecção de referência ausente/objeto não vinculado e rejeição de inventário truncado. **Isso não é evidência de acesso ao banco, R2 ou Discord de produção.**

## 8. Evidências que devem voltar ao projeto/chat

Depois da execução, compartilhe somente:

- `card-game-production-assets-reconciliation.json`;
- e, se necessário, `card-game-production-db-audit.json` após confirmar que está sanitizado.

Não compartilhe: snapshot `.sqlite3`, `.env`, tokens, access keys, arquivos de imagem, prompts particulares, mensagens de Discord ou inventário de chaves brutas. Os scripts não devem ser modificados para imprimir esses dados.

## 9. Limitações abertas

- Não temos o banco de produção, o R2, o volume `/data`, o canal privado do Discord nem o ambiente de hospedagem desta sessão.
- A verificação de anexos Discord ainda exige uma etapa no próprio host com sessão/bot autorizado e só leitura.
- As artes de líder são validadas por presença de BLOB neste inventário, não por decodificação completa da imagem.
- As imagens de `cards/` são cache/CDN; determinar cache expirado exige comparar ETag e cache local, não somente uma listagem de objetos.
- O exportador DB suporta ausência de tabelas/colunas em bancos mais antigos por inspeção de schema, mas uma versão de schema desconhecida deve ser revisada antes de qualquer migração.
