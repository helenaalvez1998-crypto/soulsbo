# Card Engine v2 — validação do staging histórico v0.1

**Status:** PASS

| Verificação | Resultado |
|---|---|
| `review_only_status` | PASS |
| `all_137_historical_ids_present_once` | PASS |
| `allowlist_matches_alpha_catalog` | PASS |
| `24_alpha_models_only` | PASS |
| `113_models_blocked` | PASS |
| `blocked_models_have_blockers` | PASS |
| `source_hashes_match` | PASS |
| `staging_summary_matches_expected` | PASS |

**Resumo:** 137 registros históricos; 24 permitidos somente para testes alpha; 113 bloqueados. Todos os 137 ainda constam como não reconstruídos e sem revisão de facção no snapshot de origem; 19 têm divergência histórica de custo.

Este resultado valida a integridade e a fronteira do artefato staging. Não aprova cartas, efeitos, custos, facções ou publicação.
