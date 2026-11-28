# Validação — Grupo F v0.1

- **Resultado:** 29/29 verificações passaram; 0 falhas.
- **Script:** `docs/scripts/audit-card-game-removal-causes-group-F-v0.1.py`.
- **Resultado estruturado:** `docs/card-game-removal-causes-group-F-audit-v0.1.json`.
- **Baseline:** `soulsbo-main-continuity-2026-11-27-rev12.zip`.

## Regressões reexecutadas nesta revisão

| Suíte | Resultado |
|---|---:|
| CardInstance v0.5 | 28/28 |
| Grupo D — contratos | 13/13 |
| Grupo D — auditoria | 23/23 |
| Grupo A | 30/30 |
| Grupo B | 20/20 |
| Grupo C | 43/43 |
| Matriz cruzada | 272/272 |
| Seleção/fileiras | 15/15 |
| Paridade manual/UI | 12/12 |
| Resolver candidato remoção/ressurreição | 49/49 |

As suítes têm escopos independentes; não somar como cobertura integrada.
- **Status das regras:** recomendações do Grupo F continuam `PENDING_OWNER_APPROVAL`.

O harness combina leitura estática de `sistemas/gwent.py`/registry candidato e fixtures sintéticas em memória. Inclui chamada de handlers ativos para Devorar, Preço em Sangue e Rykard, além de casos de bloqueio por escudo, arquivamento e causas desconhecidas. Não testa DB real, HTTP, Discord, R2, concorrência multi-processo, replay persistido ou produção. Passar validação significa reproduzir evidência/comportamento, não aprovar as propostas.
