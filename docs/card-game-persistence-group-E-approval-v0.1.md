# Aprovação formal — Grupo E (E-001 a E-010)

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev14.zip`  
**Status:** `OWNER_APPROVED; ISOLATED_IMPLEMENTATION_AUTHORIZED; PRODUCTION_MIGRATION_NOT_AUTHORIZED`

O proprietário respondeu **“ok, faça”** após a recomendação explícita de aprovar em bloco as dez decisões E-001 a E-010, consolidar `CardInstance v0.7` e iniciar a implementação isolada do novo núcleo. O aceite cobre as dez recomendações nos termos do registro estruturado `docs/card-game-persistence-group-E-decisions-v0.1.json`.

## Escopo aprovado

1. **E-001:** `state_revision` monotônica por partida, espelhada no snapshot e no registro persistido.
2. **E-002:** `BEGIN IMMEDIATE` com compare-and-swap (`UPDATE ... WHERE state_revision=?`) na mesma transação.
3. **E-003:** ledger durável por `(match_id, operation_id)` e fingerprint SHA-256 do contexto canônico; replay idêntico retorna resultado persistido e reutilização conflitante falha.
4. **E-004:** snapshot, revisão, ledger, eventos, contadores/projeções, recompensas e outbox no mesmo commit.
5. **E-005:** journal append-only com sequência estrita por partida; `event_log` textual não é fonte de verdade.
6. **E-006:** transactional outbox, entrega at-least-once, lease/retry/dead-letter e chave idempotente de consumidor.
7. **E-007:** migration ledger com ID, checksum, data e versão de aplicação; checksum divergente é falha fatal.
8. **E-008:** backup SQLite pela Backup API, `quick_check`, `integrity_check`, SHA-256 e preservação imutável do snapshot de origem.
9. **E-009:** partidas ativas/pending permanecem no motor legado até conclusão/expiração; concluídas ficam somente leitura; novas partidas v2 apenas após gates integrados. Não inventar provenance ausente.
10. **E-010:** dry-run e classificação de snapshots, UUIDv4 criado uma vez por ocorrência e mapping persistido atomicamente; preservar `exemplar_id` quando presente, caso contrário usar origem desconhecida; validar partição/conservação/ownership/integridade e rollback.

## Limites que permanecem

- A aprovação autoriza implementação isolada em `sistemas/card_engine_v2` e testes em arquivos SQLite temporários/dedicados.
- Não autoriza alterar `database.py`, `bot.py`, `sistemas/gwent.py`, `sistemas/cartas.py`, `site/app.js`, o banco publicado, o catálogo ativo ou os resolvedores legados.
- Não autoriza migrar partidas reais, iniciar cutover, converter partidas ativas ou conectar o novo engine ao Discord/HTTP.
- O ambiente não contém banco de produção. A ferramenta de arquivamento/mapeamento implementada no alpha não substitui o migrador de snapshots completo; este exige o banco real em clone, adaptador de leitura conhecido e validação de invariantes.
- SQLite WAL permanece limitado a arquivo local/single-host; não é autorização para deployment multi-host ou filesystem de rede.

## Resultado

Grupos A, B, C, D, E e F estão aprovados dentro dos escopos de seus registros. `CardInstance v0.7` é um draft consolidado. A primeira implementação do núcleo v2 é alpha isolado, sem integração ou migração de produção.
