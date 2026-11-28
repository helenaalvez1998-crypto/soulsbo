# Validação `CardInstance` v0.4 — Grupos A/B/C

**Data:** 2026-11-27  
**Resultado:** `PASS — 72/72`  
**Status do contrato:** draft, não congelado.  
**Runtime/DB/API/frontend:** não alterados.

## Escopo executado

O script `docs/scripts/validate-card-game-card-instance-v0.4.py` executa:

- meta-validação do JSON Schema Draft 2020-12;
- validação integral do exemplo v4;
- invariantes entre registros de instância, zonas, proprietário e posição atual;
- validação de grants/aplicações e referências a eventos de origem;
- simulações pequenas em memória para movimento, saída do campo, bloqueio, sacrifício, `round_close`, purificação, recuperação à mão e regras de retorno;
- conferência do escopo de aprovação do Grupo C e dos limites ainda abertos.

## Resultado

| Área | Casos | Resultado |
|---|---:|---:|
| Schema e envelope | 7 | PASS |
| Identidade, zonas e fileiras | 11 | PASS |
| Grants, aplicações e causalidade | 12 | PASS |
| Movimento e saída do campo | 11 | PASS |
| `round_close`, clima e purificação | 10 | PASS |
| Retorno, proteção e guardrails A/B/C | 21 | PASS |
| **Total** | **72** | **72/72** |

Os nomes e detalhes individuais estão em `card-game-card-instance-contract-validation-v0.4.json`.

## Regressões reexecutadas

| Suíte | Resultado |
|---|---:|
| Grupo A — identidade | 30/30 |
| Grupo B — snapshot/causalidade | 20/20 |
| Matriz histórica CI/BUF/RSRX | 272/272 |
| Auditoria do Grupo C — fonte legada/proposta | 43/43 |
| CardInstance v0.3 + Grupo B | 42/42 |
| CardInstance v0.4 — novo contrato | 72/72 |

As suítes têm escopos diferentes. A matriz CI/BUF/RSRX é um artefato histórico de recomendações e não substitui os registros posteriores de aprovação dos Grupos A/B/C.

## Limitações

Os 72 casos validam schema, exemplo e semântica isolada em memória. Não executam o novo contrato contra o motor, banco SQLite real, transações concorrentes, CAS/locks, HTTP, Discord, frontend, navegador, migração de snapshots ou partidas de produção. A aprovação dos Grupos A/B/C autoriza consolidar este draft, não congelá-lo nem integrá-lo.
