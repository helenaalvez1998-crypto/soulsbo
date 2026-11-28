# CardInstance v0.7 — contrato consolidado dos Grupos A/B/C/D/E/F

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev14.zip`  
**Status:** `DRAFT_IMPLEMENTED_ALPHA_NOT_FROZEN`  
**Grupos aprovados:** A, B, C, D, E e F.  
**Integração com legado:** nenhuma. O alpha em `sistemas/card_engine_v2/` é isolado.

## 1. O que a v0.7 consolida

A v0.7 consolida os contratos aprovados anteriores e incorpora o Grupo E. A versão estrutural do envelope passa a ser `schema_version=7`; isso não cria nem altera release IDs de catálogo, registry de efeitos, balanceamento ou ruleset.

A v0.7 é um draft implementado em um núcleo isolado. Não é contrato congelado, não é o novo jogo completo e não autoriza migração de produção ou cutover.

## 2. Envelope de partida

O snapshot contém:

- `schema_version=7`;
- `match_id`;
- `state_revision` monotônica;
- `event_watermark` (última sequência de evento comprometida);
- `status`;
- `players` com as quatro zonas e projeções de contadores;
- `instances` indexadas por `instance_id` UUIDv4;
- `definition_manifest` imutável.

`operations` e `events` deixam de ser arrays canônicos dentro de `state_json`. Operações e eventos passam a residir em ledgers duráveis. O snapshot mantém `state_revision` e `event_watermark` como checkpoints que são verificados contra as tabelas persistentes.

O JSON Schema Draft 2020-12 está em `docs/schemas/card-game-card-instance-match.schema.v7.json`; o fixture persistido está em `docs/examples/card-instance-match.example.v7.json`.

## 3. Identidade e zonas (Grupo A)

- `card_id` identifica o modelo e pode se repetir na mesma partida.
- `exemplar_id` preserva o ID global do exemplar quando conhecido; não é inferido.
- `instance_id` UUIDv4 identifica uma ocorrência física/virtual específica.
- Cada instância deve aparecer em exatamente uma das zonas `hand`, `draw_pile`, `board` ou `discard` de seu proprietário.
- Alvos e transições recebem o `instance_id` exato.
- `current_row` é `null` fora do campo; `last_board_row` preserva a última fileira válida.
- Transições genéricas de zona não limpam bônus, escudos, estados ou resistência implicitamente. O chamador deve aplicar a policy aprovada para o efeito/transição.

## 4. Manifesto e causalidade (Grupo B)

O `DefinitionManifest` congela os quatro release IDs e os hashes SHA-256 dos artefatos publicados. Cada instância preserva o snapshot mecânico e `definition_digest`. O manifesto e os snapshots não mudam durante uma partida.

Eventos carregam `event_id` próprio, `operation_id`, sequência, `caused_by_event_ids`, escopo e fonte do efeito. Efeito reativo usa a própria fonte; não herda raridade ou parâmetros da ação que causou o trigger. Raridade é somente classificatória no novo sistema.

O digest do manifesto continua sendo calculado pelo publicador de definições conforme RFC 8785/JCS. O runtime alpha valida a presença/formato do digest, mas ainda não implementa o publicador nem recalcula JCS.

## 5. Estado, duração e proteção (Grupo C)

- `bonus_grants[]`, `protection_grants[]`, `status_applications[]` e `weather_resistance_modifiers[]` preservam origem, evento de aplicação e expiração.
- Resistência climática intrínseca pertence ao `definition_snapshot`; modificadores temporários pertencem ao runtime state.
- `round_close` ocorre após congelar a pontuação e expira somente os grants/aplicações com essa policy em todas as zonas, inclusive na rodada terminal.
- Selo de Vigília expira em `board_exit`.
- Escudo não é imunidade universal; sacrifício ignora escudos conforme as decisões aprovadas.
- Ressurgir/Réquiem zeram bônus, Esgar acrescenta +1 ao bônus anterior, Lágrima Sagrada recupera para a mão; normalização não é inferida genericamente.

## 6. Seleção, outcomes e custos (Grupo D)

O servidor calcula ofertas autoritativas de alvo e métricas exibidas. Policies definem métrica, filtros, cardinalidade, fallback e desempate. Alvos secundários precisam estar na prévia antes da confirmação.

Outcomes válidos: `applied`, `partial`, `blocked`, `consumed_no_effect` e `rejected`. Seleção inválida/rejeição não consome custos; bloqueio ou efeito parcial pode consumir custos conforme a policy. O handler deve refletir custos consumidos no snapshot/eventos/recompensas/outbox da mesma transação.

O request interno normalizado v1 está em `docs/schemas/card-engine-v2-operation-request.schema.v1.json`. Ele é chamado depois da autenticação/autorização; não é um endpoint público.

## 7. Remoção, sacrifício e Vingança (Grupo F)

Causas fechadas: `normal_removal`, `execution` e `sacrifice`. Causa desconhecida é rejeitada antes da mutação. `round_archive` é transição de zona separada, não uma causa de remoção.

Vingança (`effect.vengeance_on_removal`) dispara após remoção bem-sucedida por qualquer uma das três causas. Escudo bloqueia remoção comum/execução; sacrifício ignora escudo. `board_removal_count` e `sacrifice_count` são separados; `legacy_baixas` é apenas projeção de compatibilidade. Vingança e Rykard (`leader.rykard_devour`) produzem grants/eventos distintos e aditivos; valores são parâmetros versionados, não números congelados pelo observado no legado.

## 8. Persistência, concorrência, idempotência e migração (Grupo E)

### 8.1 Revisão e CAS

- `state_revision` existe na linha da partida e no envelope.
- Cada request interno traz `expected_revision`.
- A transação inicia com `BEGIN IMMEDIATE` e o snapshot é atualizado com `WHERE match_id=? AND state_revision=?`.
- Uma operação aceita que altera estado/recompensa/evento/outbox avança a revisão uma vez. Rejeições persistidas não avançam revisão.

### 8.2 Ledger de operações

Chave única: `(match_id, operation_id)`. O fingerprint SHA-256 inclui match, ator, revisão esperada, ação, payload e `ruleset_release_id`.

- mesmo ID + mesmo fingerprint: retorna o resultado persistido sem reaplicar;
- mesmo ID + fingerprint diferente: `IdempotencyConflict`;
- revisão obsoleta: resultado `rejected/revision_conflict` persistido, sem mutação de jogo;
- exceção antes do commit: rollback integral e `operation_id` não fica reservado.

No alpha, os fingerprints usam `soulsbo-json-int-v1`: JSON UTF-8 com chaves ordenadas, separadores compactos e números inteiros apenas. Payloads de request com float são rejeitados até existir uma implementação canônica interoperável para esse caso. Isso é separado do digest RFC 8785 do DefinitionManifest.

### 8.3 Commit atômico e journal

Snapshot, `state_revision`, operação, eventos, recompensas, projeções no snapshot e outbox são gravados na mesma transação. O journal de eventos é append-only por triggers, com `UNIQUE(event_id)` e `UNIQUE(match_id, sequence)`. `event_watermark` é conferido contra a sequência persistida.

### 8.4 Outbox

A outbox grava a mensagem na transação do jogo. O alpha fornece claim com lease, tentativa, retry, dead-letter e conclusão. Entrega externa é at-least-once; o consumidor final ainda deve deduplicar pela `idempotency_key`. Nenhuma notificação real é enviada pelo alpha.

### 8.5 Migrations e backup

`card_game_schema_migrations` registra ID, checksum, data e versão da aplicação. Mesmo ID com checksum divergente é erro fatal. O alpha cria uma base dedicada identificada por marker e recusa arquivo SQLite não vazio sem esse marker.

`create_verified_backup()` usa SQLite Backup API, executa `quick_check`/`integrity_check`, retorna SHA-256, contagens por tabela e partidas por status; não sobrescreve backup existente.

### 8.6 Snapshots legados e cutover

- partidas ativas/pending permanecem no motor legado até conclusão/expiração;
- concluídas ficam como arquivo histórico somente leitura;
- novas partidas v2 só após o gate integrado;
- provenance ausente não é inventada.

O alpha oferece `archive_legacy_snapshot()`: arquiva JSON bruto/hash e persiste uma mapping `legacy_locator -> instance_id` UUIDv4 uma vez, reutilizando-a para a mesma origem. Isso não é um migrador completo nem lê o banco real; o adaptador que extrai ocorrências do formato legado e o dry-run em clone continuam pendentes.

## 9. Implementação alpha disponível

Pacote Python isolado: `sistemas/card_engine_v2/`.

- `SQLiteMatchRepository`: migration ledger, match store, CAS, idempotency ledger, event journal, rewards, outbox, backup e arquivo de snapshot legado.
- `make_card_instance()` / `new_instance_id()`: identidade UUIDv4 de instância.
- `transition_instance_zone()` / `move_instance_row()`: transições por identidade exata, sem limpeza implícita.
- `validate_match_state()`: invariantes de zona, proprietário, UUID, exemplar e fileira.

Teste: `python -m unittest discover -s tests/card_engine_v2 -v` na raiz do projeto.

## 10. Limites explícitos do alpha

- Nenhum handler de cartas/efeitos/combos real está conectado; o handler ainda é callback de domínio.
- Não há integração com `bot.py`, HTTP, Discord, `database.py`, `sistemas/gwent.py`, catálogo ativo ou frontend.
- O repository é síncrono (`sqlite3`); não deve ser chamado diretamente no event loop Discord/HTTP antes de um adapter assíncrono/worker adequado.
- Não houve teste com `aiosqlite`, requests HTTP, Discord, banco de produção ou multi-host.
- O arquivo SQLite deve ficar em filesystem local/single-host quando usar WAL.
- Não executar migration de partidas reais. O database marker existe para evitar que o alpha seja apontado acidentalmente para um arquivo antigo não marcado.

## 11. Próximo marco

Construir o resolvedor mínimo vertical sobre este repository: validação de Action Request/Target Offer, uma operação de jogo end-to-end sem catálogo ativo, eventos diretos/reativos e policies de custo. Depois criar adapter assíncrono e testes integrados em staging. Só então preparar o migrador completo a partir de clone do banco real.
