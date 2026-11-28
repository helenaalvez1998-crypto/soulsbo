# Card Engine v2 — implementação isolada alpha v0.1

**Status:** núcleo de persistência e primeira fatia de gameplay funcional em ambiente isolado.  
**Base contratual:** `CardInstance v0.7` e decisões aprovadas dos Grupos A–F.  
**Integração com legado:** nenhuma.  
**Runtime anterior modificado:** não.

## O que está funcionando

### Persistência e identidade

1. Banco SQLite dedicado com marker de engine e migration ledger com checksum.
2. Snapshot v7 com revisão monotônica e watermark de eventos.
3. Invariantes de UUIDv4, ownership, exemplar e partição exclusiva das quatro zonas.
4. Transição de zona e movimento entre fileiras por `instance_id`, sem limpeza implícita de grants.
5. `BEGIN IMMEDIATE` + compare-and-swap por `expected_revision`.
6. Idempotência durável: replay igual retorna resultado armazenado; fingerprint diferente para a mesma chave falha.
7. Resposta stale/rejected persistida sem avançar revisão.
8. Snapshot, ledger, eventos, recompensas e outbox no mesmo commit.
9. Journal append-only e sequência estrita por partida.
10. Outbox com claim/lease/retry/dead-letter/ack; ainda sem consumidor externo.
11. Backup por SQLite Backup API com checks de integridade, hash SHA-256 e contagens.
12. Arquivamento bruto de snapshot legado e mapping de ocorrências persistido uma vez.

### Gameplay implementado

13. `GameplayResolver` com registry confiável de ações, policies de alvo e profiles de proteção.
14. Target Offers server-side vinculados à revisão, com métricas disponíveis, ordenação determinística, cardinalidade e preview de alvos secundários.
15. `unit.remove` e `unit.sacrifice`, incluindo causas distintas, seleção por causa, escudos, cargas, counters, eventos diretos e Vingança reativa.
16. Remoções multi-alvo finalizam todos os resultados diretos antes de distribuir Vingança aos sobreviventes.
17. `unit.move` para instância própria no campo, limitado às fileiras liberadas pelo registry.
18. `unit.grant_bonus` e `unit.grant_protection` com valores/parâmetros definidos pelo servidor.
19. Requests rejeitam tentativa de sobrescrever pelo cliente magnitude/duração do bônus e perfil/cargas/duração da proteção.
20. Outcomes `applied`, `partial`, `blocked`, `consumed_no_effect` e `rejected`, com custos reportados e commits atômicos.

## Tabelas da base dedicada

- `cartas_gwent_matches`
- `cartas_gwent_match_operations`
- `cartas_gwent_match_events`
- `cartas_gwent_match_rewards`
- `cartas_gwent_outbox`
- `card_game_schema_migrations`
- `card_engine_v2_legacy_archive`
- `card_engine_v2_database_marker`

A migration está em `sistemas/card_engine_v2/repository.py`; referência SQL exportada em `docs/schemas/card-engine-v2-persistence-schema-v0.1.sql`.

## Interface interna

- `SQLiteMatchRepository(database_path)` — cria a base dedicada e aplica migration checksummed.
- `create_match(state_v7)` — valida e persiste match inicial em revisão zero.
- `execute_operation(match_id, request, handler)` — executa callback puro sob transação, CAS, idempotência e commit atômico.
- `GameplayResolver.target_offer_for_action(...)` — constrói oferta com policy associada à ação/causa configurada no servidor.
- `GameplayResolver.execute(repository, match_id, request)` — executa o handler de gameplay por meio do repositório transacional.
- `claim_outbox()` / `mark_outbox_delivered()` / `fail_outbox()` — controla entrega pós-commit.
- `create_verified_backup(path)` — backup sem sobrescrever destino existente.
- `archive_legacy_snapshot(...)` — preserva origem e mapping UUIDv4 estável para a mesma origem.
- `transition_instance_zone(...)` / `move_instance_row(...)` — transições físicas exatas.

Handlers devem ser puros: sem HTTP, Discord, R2, envio de mensagem ou outra operação externa dentro da transação. Agende qualquer efeito externo via `outbox`.

## Resultados dos testes alpha

- 62/62 testes locais aprovados.
- Cobertura combinada de repository/domínio, gameplay resolver, concorrência/transações e schemas/contratos.
- Relatório atual: `docs/card-engine-v2-alpha-validation-v0.1.json` e `.md`.
- Runner: `docs/scripts/test-card-engine-v2-alpha-v0.1.py`.
- Smoke command dedicado: `python -m sistemas.card_engine_v2 <novo-caminho.sqlite3>`.

Os testes são locais/sintéticos. Não demonstram integração no ambiente assíncrono do bot nem comportamento do banco de produção.

## Limites e trabalho seguinte

- O catálogo verdadeiro e os registries de ações/policies/proteção ainda não foram conectados.
- O cálculo canônico de poder efetivo com clima e estados ainda não foi portado; policies `effective_power` precisam de `metric_resolver` confiável e vinculado ao release.
- `bonus_clamp_policy_id` é registrado, mas o algoritmo de clamp ainda não foi implementado.
- `turn_consumed`, `activation_consumed` e custos genéricos são campos normalizados, mas o state machine de turnos/ativações ainda não existe. Atualmente são aplicados consumo de fonte configurado (somente fonte na mão, ações de remoção/sacrifício) e cargas de proteção.
- Ainda não há combate/dano completo, combos, líderes, clima, round-close global ou execução geral do registry de efeitos.
- Falta adapter assíncrono/worker para o event loop real; o repositório é `sqlite3` síncrono.
- O arquivamento legado não é um migrador completo, não leu banco de produção e não autoriza cutover.

## Guardrail

A implementação nova fica isolada em `sistemas/card_engine_v2/` e `tests/card_engine_v2/`. Não altera `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`, catálogo ativo, registries ativos ou banco publicado. O repositório v2 recusa arquivo SQLite não vazio sem seu próprio marker.
