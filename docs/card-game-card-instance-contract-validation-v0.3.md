# Validação CardInstance v0.3 e aprovação do Grupo B

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev8.zip`  
**Resultado:** **42/42 verificações aprovadas; 0 falhas**  
**Runtime modificado:** não.  
**DB de produção utilizado:** não.

## Escopo verificado

- Meta-validação Draft 2020-12 dos schemas de partida, manifesto e evento.
- Validação integral do exemplo v3 contra o schema de partida.
- Recomputação dos digests do manifesto e das definições mecânicas de cada instância na fixture restrita.
- Distinção entre `schema_version` estrutural e release IDs.
- Igualdade de releases fixados no manifesto e em cada instância.
- UUIDv4, cópias de `card_id`, unicidade/ownership/totalidade de zonas.
- Identidade de `operation_id`, fingerprint, revisão esperada e namespace distinto de `event_id`.
- Referências operação/evento, lista de eventos emitidos, sequência única e ordenada, pais causais existentes e anteriores.
- Separação de remoção e Vingança em eventos direct/reactive, com fonte própria da reação.
- Ausência de parâmetros de execução derivados de raridade nos payloads e parâmetros de efeito da fixture.
- Registro aprovado das decisões BUF-001/A, BUF-002, BUF-012, RSRX-03 e RSRX-05.
- Verificações lógicas sintéticas de retry idempotente, conflito por fingerprint e rejeição de revisão obsoleta.
- Verificações de regra aprovadas: shield-block não é remoção/Vingança; outputs reativo e direto de Rykard são eventos distintos.

## Resultado das regressões reexecutadas

| Suíte | Resultado |
|---|---:|
| Grupo B — auditoria de snapshot/causalidade | 20/20 |
| Grupo A — identidade física | 30/30 |
| CardInstance v0.2 | 30/30 |
| Matriz cruzada CI/BUF/RSRX | 272/272 |
| CardInstance v0.3 + registro de aprovação B | 42/42 |

As suítes têm unidades e escopos diferentes; não somar esses números como cobertura única.

## Limitações

- O exemplo usa release IDs `example-only.*` e digests sintéticos; nenhum release operacional de catálogo, efeitos, balanceamento ou ruleset foi publicado/verificado.
- O cálculo do digest na fixture usa apenas o subconjunto JSON seguro utilizado pelo exemplo (chaves ASCII, valores inteiros/string/null). A implementação de produção deve usar uma implementação completa de JCS/RFC 8785.
- Não foi executado um runtime novo, DB de produção, concorrência real, transação SQLite concorrente, CAS, HTTP, Discord, browser ou replay de partida persistida.
- Os grupos C, D, F e E permanecem abertos. A lista final de causas de Vingança não foi definida.
- EFP, custo, orçamento 32, `leader_load` e cortes numéricos de raridade não foram aprovados.

**Comando:** `python docs/scripts/validate-card-game-card-instance-v0.3.py` (requer `jsonschema`).
