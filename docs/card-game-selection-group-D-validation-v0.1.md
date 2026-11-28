# Validação — Grupo D v0.1

**Data:** 2026-11-27  
**Status:** `PASS`; decisões DSEL-DEC-001..012 estão `OWNER_APPROVED` com evidência em `card-game-selection-group-D-approval-v0.1.md/.json`.

| Suite | Passaram | Falhas |
|---|---:|---:|
| Auditoria Grupo D | 23 | 0 |
| Schemas e exemplos candidatos do Grupo D | 13 | 0 |
| Escopo de seleção/fileira | 15 | 0 |
| Paridade manual/UI | 12 | 0 |
| CardInstance v0.5 | 28 | 0 |
| Grupo A | 30 | 0 |
| Grupo B | 20 | 0 |
| Grupo F | 29 | 0 |
| Grupo C | 43 | 0 |
| Matriz cruzada histórica | 272 | 0 |

## O que os testes verificam

- Os 23 casos do Grupo D executam fixtures contra funções reais do motor legado e verificações estáticas pontuais da API, frontend e comportamento legado.
- Os 13 checks de contrato validam quatro schemas Draft 2020-12, quatro exemplos, as 12 decisões aprovadas e conferidas contra o registro formal de aceite, a ausência de dependência de raridade e a separação entre resultado por alvo e custos.
- As suítes de regressão A/B/C, Grupo F e CardInstance foram reexecutadas sem falhas.

## Limites

As suítes possuem escopos independentes e não representam cobertura integrada. Não houve teste de browser real, rede, concorrência entre processos, retry/replay persistido, migração, integração do CardInstance com o runtime nem teste de produção. `expected_revision` e idempotência estão definidos apenas em schema candidato e continuam dependentes do Grupo E.

**Runtime modificado:** não. Todo artefato novo desta etapa permanece em `docs/`.

Reprodução: `python docs/scripts/audit-card-game-selection-group-D-v0.1.py` e `python docs/scripts/validate-card-game-selection-group-D-v0.1.py`.
