# Contrato `CardInstance` v0.6 — Grupos A/B/C/D/F aprovados; Grupo E aberto

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev13.zip`  
**Status:** `DRAFT_AFTER_GROUP_A_B_C_D_F_APPROVAL_NOT_FROZEN`  
**Integração:** nenhuma. Runtime, DB, catálogo ativo, API, bot e frontend permanecem inalterados.

## 1. Escopo

A v0.6 incorpora os Grupos A, B, C, D e F aprovados. O Grupo E permanece aberto e bloqueia persistência do novo contrato, replay durável, migração e cutover. Esta revisão é uma especificação candidata, não um schema de produção.

Artefatos normativos do draft:

- `docs/schemas/card-game-card-instance-match.schema.v6.json` — envelope v6;
- `docs/examples/card-instance-match.example.v6.json` — fixture com remoção e Vingança canônicas;
- `docs/schemas/card-game-removal-cause.schema.v1.json` — enum fechado de causas;
- schemas de request/offer/policy/result aprovados no Grupo D;
- aprovações formais dos Grupos A, B, C, D e F.

`schema_version=6` é a versão estrutural do envelope. Não muda os quatro release IDs do `DefinitionManifest` nem congela números de balanceamento.

## 2. Grupo F — semântica aprovada

### 2.1 Causas de remoção

O enum fechado contém somente:

- `normal_removal`;
- `execution`;
- `sacrifice`.

Aliases legados (`remocao`, default, `execucao`, `sacrificio`) podem existir exclusivamente no adaptador de leitura/migração. Causa desconhecida falha antes de mutação. `round_archive` é evento separado de transição de zona; não é causa de remoção e não ativa Vingança.

### 2.2 Vingança

Vingança dispara uma vez após remoção bem-sucedida por qualquer uma das três causas canônicas. Não dispara quando escudo bloqueia remoção/execução, nem em arquivamento, movimento, recuperação ou ressurreição. O escopo do efeito é aliados remanescentes na mesma fileira.

O ID canônico é `effect.vengeance_on_removal`. `habilidade == "vinganca"` permanece apenas um alias legado.

### 2.3 Contadores derivados

- `board_removal_count` = remoções normais bem-sucedidas + execuções bem-sucedidas;
- `sacrifice_count` = sacrifícios bem-sucedidos;
- `legacy_baixas` = projeção de compatibilidade `board_removal_count + sacrifice_count`, nunca semântica de mortes;
- `round_archive`, bloqueios e movimentos não incrementam esses contadores.

As contagens têm como fonte os eventos causais bem-sucedidos. Campos de contador no snapshot são projeções verificáveis, não a autoridade histórica.

### 2.4 Rykard e causalidade

Vingança (`effect.vengeance_on_removal`) e Rykard (`leader.rykard_devour`) geram outputs distintos. Podem somar no mesmo sobrevivente, mas não são deduplicados como se fossem um único grant. Os valores +1 e +2 observados no legado não ficam congelados; são parâmetros versionados por release.

### 2.5 Eventos v2

O evento `unit_removed` precisa carregar `cause_id`, `from_zone=board`, `to_zone=discard` e `affected_player_id`. `unit_removal_blocked` só admite `normal_removal` ou `execution`. `unit_archived` usa `transition_id=round_archive`, sem `cause_id`. `vengeance_bonus_applied` exige `source_effect_id=effect.vengeance_on_removal`.

O fixture v6 corrige o ID histórico divergente `unit.vengeance_on_removal` para o ID canônico em novos documentos; o fixture antigo v4/v5 permanece imutável como evidência histórica.

## 3. Decisões aprovadas herdadas

- **A:** identidade por ocorrência UUIDv4; `card_id` pode repetir; `exemplar_id` preserva proveniência; alvo por `instance_id`.
- **B:** manifesto de definições imutável; raridade apenas classificatória; eventos causais com fontes distintas.
- **C:** grants de bônus/proteção/status/resistência climática com origem e expiração; `round_close` global; políticas explícitas de transição.
- **D:** offers autoritativas do servidor; políticas declarativas de alvo; outcomes e custos separados; operação com `operation_id` e `expected_revision`.
- **F:** causas fechadas; Vingança após sucesso; contadores separados; Rykard/Vingança aditivos e causalmente independentes.

## 4. Grupo E — bloqueio de integração

A auditoria do Grupo E (`docs/card-game-persistence-group-E-audit-v0.1.md`) confirmou que o legado já usa `BEGIN IMMEDIATE`, WAL, `busy_timeout` e transações que agrupam o snapshot e recompensas. Entretanto, o banco ainda não tem coluna `state_revision`, ledger durável de operações de gameplay, tabela de eventos de domínio, outbox ou ledger versionado de migrações. O request HTTP legado não recebe `operation_id` nem `expected_revision`.

Portanto, v0.6 ainda não pode ser persistido no banco atual. As propostas E-001..E-010 precisam ser aprovadas, desenhadas e testadas em cópia antes de qualquer migração.

## 5. Guardrails

- Não alterar `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`, schema SQLite de produção, catálogo ativo ou resolvedores.
- Não executar migrador, atribuir `instance_id` a partidas reais nem converter snapshots persistidos.
- Não ativar rotas de Action Request/Offer/Result.
- Não tratar resultados SQLite em fixture como teste HTTP/aiosqlite ou prova sobre o banco publicado.
- Manter o runtime legado como executor das partidas existentes até que a política de compatibilidade do Grupo E seja aprovada.

## 6. Próximo gate

Aprovar/ajustar as dez propostas E-001..E-010. Depois, especificar a migração com backup, dry-run, verificação de integridade, transação atômica e plano de rollback. Mesmo após aprovação, a migração só pode ser executada em ambiente controlado e com cópia verificada do banco real.
