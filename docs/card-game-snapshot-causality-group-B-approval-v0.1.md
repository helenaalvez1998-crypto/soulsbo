# Aprovação do Grupo B — snapshot e causalidade v0.1

**Data:** 2026-11-27  
**Baseline aprovado:** `soulsbo-main-continuity-2026-11-27-rev8.zip`  
**Status:** `OWNER_APPROVED`  
**Origem:** resposta explícita do proprietário: “aprovo”, em resposta à pergunta sobre aprovação do Grupo B e remoção da amplificação por raridade (Alternativa A).  
**Runtime modificado:** não.

## Decisões aprovadas

| ID | Resultado | Regra aprovada |
|---|---|---|
| CI-005 | Aprovada | Manifesto imutável por partida com releases de catálogo, registry de efeitos, regras de balanceamento e ruleset; digest verificável; snapshot mecânico resolvido e digest por instância. `schema_version` permanece estrutural. |
| CI-011 | Aprovada | `operation_id` UUIDv4 identifica uma ação lógica; `event_id` UUIDv4 identifica cada evento. Eventos ordenados, append-only e ligados causalmente. Idempotência por fingerprint; resultado, estado, revisão e eventos persistidos atomicamente. |
| BUF-001 | Aprovada — Alternativa A | Raridade é classificação apenas. Não altera magnitude, limites, quantidade/seleção de alvos, duração nem qualquer parâmetro de execução. `RARITY_EFFECT_BUDGET` não será dependência do novo sistema. |
| BUF-002 | Aprovada | Efeitos reativos têm fonte própria e pai causal; nunca herdam raridade ou parâmetros de execução do efeito externo que os disparou. |
| BUF-012 | Aprovada | Apenas atribuições ativas e verificadas entram como capacidades no novo registry. Handlers órfãos e aliases inativos ficam em arquivo histórico/compatibilidade até reatribuição explícita. |
| RSRX-03 | Aprovada com dependência do Grupo F | Remoção/sacrifício bem-sucedido gera evento próprio. Vingança, se permitida pela causa aprovada no Grupo F, gera evento reativo separado. Bloqueio por escudo não é remoção e não dispara Vingança. |
| RSRX-05 | Aprovada quanto à separação causal | Vingança de Rykard e bônus direto do líder são outputs/eventos distintos, com fontes e ordem próprias. O +1 e +2 são observações do legado; o total +3 não fica congelado como valor de balanceamento. |

## Interpretação obrigatória de BUF-001

No novo sistema, a raridade não pode participar do cálculo nem da elegibilidade de efeitos. Isso inclui valores de bônus, penalidades, limiares de Execução/retorno, quantidade de alvos, seletores, duração e qualquer outro resultado mecânico. Os números necessários devem estar declarados em `effect_id`/`effect_params` ou em regras de jogo versionadas, não derivados de `rarity_id`.

O campo de raridade pode permanecer no snapshot para classificação, apresentação e regras de obtenção não mecânicas. Não deve ser fornecido como input ao resolvedor de efeitos. Cartas legadas que hoje dependem de limiares escalados por raridade precisam de parâmetros explícitos e revisão de texto antes de um release do novo catálogo.

## Limites do aceite

Esta aprovação não aprova EFP, fórmulas de custo, orçamento 32, `leader_load`, cortes numéricos de raridade ou todo o balance spec. Também não fecha a lista de causas de Vingança, que permanece no Grupo F; políticas de limpeza/duração permanecem no Grupo C; seletor/fallback/atomicidade no Grupo D; e persistência concorrente/migração real no Grupo E.

A aprovação fecha o desenho documental do Grupo B e autoriza a atualização do contrato candidato `CardInstance v0.3`. Não autoriza alterar o motor legado, publicar releases reais, executar migração, alterar o banco ou integrar o resolvedor.
