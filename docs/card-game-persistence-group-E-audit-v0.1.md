# Grupo E — Auditoria de persistência, concorrência, idempotência e migração v0.1

**Baseline:** `soulsbo-main-continuity-2026-11-27-rev13.zip`  
**Status:** `AUDITED_READ_ONLY; DECISIONS_PENDING_OWNER_APPROVAL`  
**Resultado:** 24/24 verificações passaram; zero falhas.  
**Runtime/DB/API/frontend alterados:** não.

## 1. Conclusão executiva

O legado tem uma base transacional útil: partidas são alteradas dentro de `Database.transaction()`, que usa `BEGIN IMMEDIATE`; o arquivo SQLite usa WAL e `busy_timeout=10000`. Um teste com duas conexões independentes confirmou que um segundo `BEGIN IMMEDIATE` espera o primeiro commit e então lê o estado atualizado. Isso evita lost update no caminho atual quando todos os escritores usam a mesma transação.

A proteção não equivale a idempotência de ação nem a um protocolo explícito de revisão. A tabela de partidas armazena `state_json` sem `state_revision`; a rota de ação não recebe `operation_id`/`expected_revision`; não há ledger durável de operações, event journal de domínio, outbox ou migration ledger.

## 2. Evidências do código

| Fonte | Evidência observada | Consequência |
|---|---|---|
| `database.py:619-630` | `cartas_gwent_matches` contém `id`, participantes, `status`, `state_json` e timestamps; não há coluna de revisão | O envelope v0.6 ainda não cabe no esquema atual sem migração |
| `database.py:1015-1045` | Locks de escrita por instância; WAL e `busy_timeout=10000` para arquivo | Boa base SQLite, mas lock Python não coordena processos diferentes |
| `database.py:1153-1198` | Transações de escrita executam `BEGIN IMMEDIATE` antes do SELECT/UPDATE | Serialização entre conexões SQLite no mesmo arquivo; teste isolado confirmado |
| `database.py:1044-1112` | `connect()` executa DDL/ALTERs incrementais e commit, sem `schema_migrations`/`user_version` | Migrações não têm ID/checksum auditável |
| `bot.py:1838-1900` | Ação lê estado e escreve snapshot dentro da transação; request aceita action/card_id/row/card_ids/target_id | Sem `operation_id`, `expected_revision` ou update CAS explícito |
| `sistemas/gwent.py:874-912` | `novo_estado` não cria envelope v6; `event_log` é histórico textual limitado a 20 entradas | Não serve como journal append-only nem como ledger de replay |
| `database.py:640-652` | `cartas_gwent_rewards` tem PK `(match_id,user_id)` | Recompensa de conclusão tem deduplicação por participante/partida |
| `database.py:705-718` | `cartas_recompensas.event_key` é PK | Drops com chave estável são deduplicados |
| `bot.py:1907-1995` | Ranking/economia/rewards ficam na transação; alerta de turno é `create_task` antes do commit; sync de patentes ocorre depois e só registra falha | Efeitos externos precisam de outbox para entrega/retry confiável |
| `docs/scripts/snapshot-sqlite-readonly-v0.1.py` | Origem `mode=ro`, `query_only`, SQLite Backup API e `quick_check` | Ferramenta existente de backup seguro; não executada contra banco real ausente |

## 3. O que foi comprovado com SQLite isolado

- DDL real extraído de `SCHEMA` e `SCHEMA_CARTAS` de `database.py` executou em banco temporário.
- Rollback reverteu em conjunto a alteração de `state_json` e a inserção de recompensa.
- As chaves primárias de `cartas_gwent_rewards` e `cartas_recompensas.event_key` rejeitaram duplicatas.
- Duas conexões independentes: B ficou bloqueada enquanto A mantinha `BEGIN IMMEDIATE`; após commit de A, B leu o novo estado e só então atualizou. Resultado final esperado, sem lost update.
- SQLite Backup API criou snapshot consistente e `quick_check` retornou `ok`.

## 4. Decisões propostas E-001 a E-010

As recomendações detalhadas estão em `docs/card-game-persistence-group-E-decisions-v0.1.json`. Nenhuma está aprovada.

## 5. Limites da auditoria

- O ZIP não contém banco de produção, credenciais nem linhas de partidas reais; não foi possível inventariar partidas ativas/pending/finished, JSONs inválidos ou estado real dos usuários.
- `aiosqlite` e `discord.py` não estão disponíveis no ambiente; a classe `Database` e os handlers HTTP não foram instanciados. O wrapper foi lido estaticamente; as experiências de lock/rollback foram executadas pelo `sqlite3` da biblioteca padrão, com DDL real extraído do código.
- Nenhuma migração, alteração de schema, request HTTP, replay da API, notificação Discord, sync de patente ou acesso ao banco publicado foi executado.
- O teste multi-conexão valida semântica SQLite em arquivo local, não topologia multi-host nem filesystem de rede. WAL/SQLite deve permanecer em armazenamento local suportado; distribuição multi-host exige arquitetura diferente.

## 6. Próximo gate

Aprovar ou ajustar E-001..E-010. Em seguida, desenhar a migration SQL e o plano operacional em clone do banco, com backup verificado, dry-run, contagem pré/pós, hash dos snapshots, transação/rollback, integridade e janela de cutover. Não migrar partidas ativas até aprovar a política de compatibilidade legado/novo runtime.
