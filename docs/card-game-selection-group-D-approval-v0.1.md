# Aprovação do Grupo D — seleção, fallback, resultados e custos v0.1

**Status:** `OWNER_APPROVED`  
**Baseline auditado:** `soulsbo-main-continuity-2026-11-27-rev11.zip`  
**Pacote que contém o aceite e a consolidação:** revisão rev. 13  
**Evidência do aceite:** o proprietário respondeu “ok, continua” imediatamente após a pergunta explícita de aprovação de DSEL-DEC-001 a DSEL-DEC-012.  
**Runtime/API/DB/frontend alterados:** não.

## 1. Escopo aprovado

O aceite cobre integralmente as doze resoluções do registro `docs/card-game-selection-group-D-decisions-v0.1.json`, respeitando os limites de cada item:

1. **DSEL-DEC-001 — Identidades e escolhas separadas:** `source_instance_id`, `target_instance_id(s)`, `choice_id` e `target_row` não compartilham o significado legado de `target_id`.
2. **DSEL-DEC-002 — Oferta autoritativa:** o servidor calcula e revalida ofertas, elegibilidade, métricas, revisão, zona, fileira e cardinalidade; o cliente apenas apresenta opções.
3. **DSEL-DEC-003 — Política declarativa por efeito:** lado, zona, fileira, predicates versionados, métricas, sort, cardinalidade, fallback, parcialidade, desempate, proteção e custos são declarados por binding/release.
4. **DSEL-DEC-004 — Cardinalidade independente de raridade:** `exact`, `up_to` e `all_matching` têm mínimo/máximo explícitos; raridade não altera número de alvos. `up_to 2` com mínimo 1 e apenas um elegível é `applied`, não `partial` por falta do máximo.
5. **DSEL-DEC-005 — Alvos múltiplos visíveis:** preferir `manual_set`; qualquer `manual_primary_auto_fill` precisa mostrar a prévia completa dos secundários antes da confirmação.
6. **DSEL-DEC-006 — Fallback por efeito:** não há fallback global. `on_no_target` é `reject`, `consume_no_effect` ou `fallback` nomeado.
7. **DSEL-DEC-007 — Outcomes distintos:** `applied`, `partial`, `blocked`, `consumed_no_effect` e `rejected`; estados por alvo `applied`, `blocked` e `skipped`. Conflitos de revisão/idempotência pertencem ao transporte/persistência do Grupo E.
8. **DSEL-DEC-008 — Custos separados:** turno, fonte, ativação, carga de proteção e outros consumíveis são campos independentes; rejeição não consome; bloqueio/no-op só consome custos declarados.
9. **DSEL-DEC-009 — Desempate de proteção:** grants compatíveis e ativos são escolhidos por menor `applied_event.sequence`, depois `grant_id` lexicográfico. Políticas especiais podem declarar prioridade em release versionado.
10. **DSEL-DEC-010 — Resolução lógica atômica:** planejar sem mutação, validar, resolver em working copy, verificar invariantes e fazer um commit único; falha inesperada descarta a working copy.
11. **DSEL-DEC-011 — Request com revisão:** `operation_id` UUIDv4 e `expected_revision` integram o request e o registro lógico. Enforcement persistente/CAS real continua no Grupo E.
12. **DSEL-DEC-012 — Métricas de UI do servidor:** ofertas entregam as métricas usadas para elegibilidade, exibição e ordenação; o cliente não recalcula ranking ou elegibilidade.

## 2. Restrições herdadas e fronteiras

- BUF-001 aprovado continua impedindo qualquer dependência mecânica de `rarity_id`, inclusive quantidade de alvos.
- BUF-013 aprovado continua exigindo ordem/desempate estáveis e persistidos.
- CI-014 **não** fica encerrado: concorrência e enforcement real de `expected_revision` pertencem ao Grupo E.
- Não há autorização para migrar endpoints, alterar schemas de produção, integrar request/offer/result ao bot/site ou substituir o motor legado.
- Os valores finais de quantidade, predicates, fallback e custos carta-a-carta continuam vinculados aos releases/registries que ainda serão aprovados.

## 3. Consequência documental

O Grupo D pode ser incorporado ao draft `CardInstance v0.5`. O v0.5 continua `DRAFT_NOT_FROZEN`: o Grupo F (causas de remoção/Vingança) e o Grupo E (persistência, concorrência, replay e migração) permanecem abertos. A validação estrutural não equivale a integração ou teste de produção.
