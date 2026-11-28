# Agenda experimental de custos de energia — Card Engine v2 alpha v0.1

**Status:** provisória para playtest controlado; não aprovada para release nem para balanceamento final.  
**Ruleset consumidor:** `alpha-test-only.ruleset.v0.5`.  
**Fonte estruturada:** `data/card_game/card-engine-v2-alpha-energy-cost-schedule.v0.1.json`.

## Princípios

- A economia concede +1 energia no início de cada turno individual, com máximo de 5 e saldo persistente entre rodadas.
- O preço é explícito por `card_id` para cartas e por `leader_id` para líderes.
- Raridade e `deck_cost_legacy` não entram no preço de energia; isso preserva a decisão BUF-001 de raridade classificatória.
- A proposta considera poder-base, magnitude e alcance do efeito implementado, condicionalidade, limite de uso e oportunidade de ação consumida.
- Valores não foram validados por telemetria nem por playtests humanos. A tabela existe para tornar o custo real e testável na alpha, não para declarar equilíbrio.

## Cartas permitidas

| ID (`card_id`) | Tipo | Poder-base | Energia | Justificativa resumida |
|---|---|---:|---:|---|
| `arma_cajado_marulho` | unit | 6 | **3** | Unidade de poder-base 6 sem efeito individual ativo; custo médio para corpo puro. |
| `arma_duas_luas` | unit | 7 | **4** | Poder-base 7 com bônus condicional de presença em outra fileira. |
| `arma_grande_sino` | unit | 8 | **5** | Poder-base 8 e bônus condicional de recuperação de +2 quando atrás. |
| `arma_lanca_fornalha` | unit | 5 | **2** | Poder-base 5 sem efeito individual; custo de entrada intermediário. |
| `arma_martelo_fornalha` | unit | 6 | **3** | Poder-base 6 sem efeito individual. |
| `chefe_dama_vazio` | unit | 6 | **4** | Poder-base 6 com redução relevante de bônus do inimigo mais forte. |
| `chefe_maliketh_morte_destinada` | unit | 8 | **5** | Poder-base 8 combinado com redução de bônus em alvo inimigo. |
| `chefe_oraculo_ruina` | unit | 7 | **4** | Poder-base 7 com enfraquecimento de inimigo e bônus situacional de recuperação. |
| `chefe_rei_afogado` | unit | 7 | **4** | Poder-base 7 com bônus de entrada de até +2 condicionado ao descarte/estado do oponente. |
| `chefe_vigia_cinzento` | unit | 5 | **2** | Poder-base 5 sem efeito individual. |
| `elden_especial_geada` | special | — | **3** | Especial que aplica Geada a inimigos na fileira escolhida; impacto potencial em múltiplos alvos. |
| `gwent_especial_egide` | special | — | **2** | Especial defensivo que concede uma carga de proteção a um aliado. |
| `gwent_especial_execucao` | special | — | **4** | Remoção de uma unidade inimiga elegível até poder efetivo 6; alto impacto de troca. |
| `gwent_especial_tempestade` | special | — | **3** | Aplica penalidade climática à fileira escolhida durante a rodada. |
| `gwent_singular_primeiro` | unit | 10 | **5** | Poder-base 10 e bônus condicional adicional quando está sozinho na fileira. |
| `gwent_unidade_herdeiro_portao` | unit | 6 | **3** | Poder-base 6 com Vingança reativa após remoção elegível. |
| `gwent_unidade_veterano_cercos` | unit | 6 | **3** | Poder-base 6 sem efeito individual; tags podem contribuir para combos. |
| `gwent_v75_ordem_veterano_juramento` | unit | 4 | **3** | Poder-base 4, mas concede bônus de entrada à própria unidade e a um aliado. |
| `luterano_anjo` | unit | 3 | **1** | Poder-base 3; efeito individual não está habilitado no runtime alpha. |
| `luterano_papa` | unit | 7 | **3** | Poder-base 7 sem efeito individual habilitado; tags ficam disponíveis para sinergias. |
| `magia_nevoa_antiga` | unit | 7 | **4** | Poder-base 7 com bônus condicional de +2 quando a condição climática está ativa. |
| `magia_selo_vigilia` | unit | 5 | **3** | Poder-base 5 com suporte de resistência climática e bônus a aliado. |
| `magia_sol_negro` | unit | 8 | **5** | Poder-base 8 com bônus condicional de +2 contra campo inimigo com bônus positivo. |
| `magia_trovao_oco` | unit | 6 | **4** | Poder-base 6 com redução de bônus em múltiplos inimigos na mesma fileira. |
| `patente_1` | unit | 3 | **2** | Poder-base 3 com bônus condicional de +1; barato, mas não é corpo puro. |
| `patente_10` | unit | 6 | **3** | Poder-base 6 com bônus condicional de +1 conforme a ação anterior do oponente. |
| `patente_9` | unit | 8 | **4** | Poder-base 8 com bônus condicional de +1 quando está à frente. |

## Líderes

| ID (`leader_id`) | Energia | Usos | Consome turno | Justificativa |
|---|---:|---:|---|---|
| `arquimaga_eclipse` | **2** | 1 | Sim | Rennala: purificação situacional e bônus condicionado aos aliados purificados em Cerco. |
| `bastiao_ancestral` | **3** | 1 | Sim | Morgott: até dois escudos e bônus de +1 em aliados prioritários. |
| `comandante_fornalha` | **3** | 1 | Sim | Godfrey: +2 em todas as unidades aliadas de Corpo a Corpo. |
| `juiz_cerco` | **3** | 1 | Sim | Radagon: purifica múltiplos estados e concede +1 por unidade purificada. |
| `lider_papa_esquecido` | **2** | 1 | Sim | Papa Esquecido: +1 a aliados de sua facção na fileira escolhida. |
| `mestre_eclipse` | **3** | 1 | Sim | Astel: aplica Geada em até três inimigos na fileira escolhida. |
| `mestre_veu` | **3** | 1 | Sim | Mohg: aplica marcas a dois inimigos e pode gerar penalidade de -2. |
| `oraculo_tempestade` | **3** | 1 | Sim | Loretta: concede +2 às duas unidades aliadas mais fortes de Longa Distância. |
| `sombra_caminhante` | **3** | 1 | Sim | Rykard: sacrifica o aliado mais fraco e concede +2 aos sobreviventes da fileira. |
| `voz_caidos` | **3** | 1 | Sim | Esgar: ressuscita a unidade elegível mais forte com bônus adicional. |

## Habilidades manuais

A tabela `ability_activation_energy_cost_by_ability_id` está vazia porque o registry ativo não declara habilidades manuais individuais. Efeitos `unit_on_play` são efeitos de entrada e não podem ser repetidos por uma ativação manual.

## Guardrails do runtime

- `play_unit` e `play_special` exigem preço explícito para o `card_id` usado.
- `activate_leader` exige preço explícito para o `leader_id` selecionado.
- `activate_card_ability` exige uma habilidade registrada no servidor e preço explícito por `ability_id`.
- Preço ausente ou saldo insuficiente rejeita a ação sem consumir a carta, o turno, a ativação ou a energia.
- Sacrifício consome a ação/turno alpha, mas não possui custo energético nesta revisão.
- Pagamento e efeito aprovado são persistidos na mesma transação; o evento `player_energy_spent` registra o débito.

## Como interpretar a tabela

Use estes números como ponto de partida para partidas controladas. Depois de playtests, revise a razão custo/impacto e a frequência real de uso. Não promova estes valores a regras oficiais sem nova validação de design e balanceamento.
