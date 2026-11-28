# Especificação quantitativa de balanceamento — proposta v0.1

> **STATUS: PROPOSTA, NÃO APROVADA E NÃO IMPLEMENTADA.** Requisitos confirmados pelo usuário são separados das escolhas numéricas sugeridas. Todos os EFP são estimativas de triagem; não foram validados por simulações ou telemetria de produção.

> **NOTA DE REVISÃO (2026-11-27):** os resultados de `card-game-deck-cost-sampling-v0.1.json` são históricos e foram superados. O script v0.1 atribuía EFP parcial quando uma carta tinha apenas uma das tags de um combo (`intersection`) e não incluía carga do líder nem relíquia equipada. A revisão v0.2 remove esse crédito parcial e mede cenários com/sem relíquia; ver `card-game-balance-validation-v0.1.md` e `card-game-deck-cost-sampling-v0.2.json`. Portanto, o teto 32 **não está sustentado nem aprovado** pelos resultados v0.1. A ativação de combos foi medida em relatório separado, mas ainda não fornece valor esperado de pontuação nem EFP por participante.

## 1. Requisitos confirmados

- Poder-base futuro estritamente entre 1 e 15.
- Distribuição de efeitos deliberada e determinística, sem sorteio para definir a mecânica da carta.
- Pelo menos 30% dos modelos oficiais do jogo devem ser puros, sem efeito/habilidade individual.
- Cada carta deve ter custo usado como limite real na montagem do deck.
- Raridade calculada a partir de poder-base, força do efeito e custo; poder/efeito maiores e custo menor devem elevar a raridade.
- Nome, título, lore e identidade de cada carta devem ser coerentes com a facção e com Elden Ring / Dark Souls.

## 2. Definições propostas

| Item | Regra proposta | Estado |
|---|---|---|
| Unidade | `power_base` inteiro de 1 a 15, inclusive | Proposta técnica |
| Especial | `power_base = null`; especial não é unidade e não entra na soma de fileira | Requer confirmar que 1–15 se aplica às unidades |
| Pura | Unidade sem `effect_id`, identidade, hook individual ou tag ligada a combo ativo | Proposta |
| Passiva global de facção | Não retira pureza: é um modificador global do deck, não efeito individual da carta | Proposta |
| Denominador 30% | Todos os IDs únicos de modelos jogáveis: unidades + especiais; não contar exemplares/cópias | Proposta |
| Quota mínima | `ceil(0,30 × N_modelos)`; baseline de 137 modelos = **42 cartas puras** | Proposta |
| Meta operacional | Mirar 35% em expansões para evitar ficar abaixo de 30% após novas cartas | Proposta |
| Efeito individual | No máximo um `effect_id` individual canônico por carta; combos e passivas continuam explicitamente separados | Proposta |
| Efeito por raridade | Raridade não aumenta secretamente magnitude, alvos ou duração | Proposta |
| Custo | Inteiro de 1 a 10 por modelo jogável, incluindo especiais e relíquias | Proposta |

### 2.1. Baseline de cartas puras

No catálogo runtime do baseline há 137 modelos (110 unidades + 27 especiais). A auditoria estrita encontrou 15 unidades puras (13,64% das unidades e 10,95% do catálogo completo). Como especiais são ações e não podem ser puras nesta proposta, o alvo mínimo literal é `ceil(0,30 × 137) = 42` unidades puras. A quota por facção só deve ser calculada depois de corrigir as seis atribuições suspeitas das cartas `luterano_*`; depois disso, aplicar método dos maiores restos proporcional ao número de unidades por facção.

Critérios automatizáveis de pureza: `effect_id` nulo; não estar em `CARD_IDENTITY_ABILITIES`; não ter hook individual; nenhuma tag que o conecte a combo ativo. A passiva global de facção fica fora da contagem.

## 3. Métrica EFP — pontos estimados de força do efeito

EFP aproxima o swing de poder e recursos produzido pela habilidade num cenário padronizado. Não é o poder-base da carta nem garantia do valor em todo estado de partida. A tabela completa com os 59 metadados genéricos, 22 identidades e estimativas está em `card-game-effect-score-catalog.json`.

| Componente | Valor inicial | Contagem |
|---|---:|---|
| +1 poder/bônus próprio ou de aliado | 1,00 | Por ponto aplicado |
| -1 poder efetivo de inimigo | 1,00 | Por alvo/ponto |
| -1 bônus positivo de inimigo | 0,75 | Apenas bônus removível |
| -1 poder-base de inimigo | 1,50 | Por ponto persistente |
| Remover unidade inimiga | 4,00 | Por alvo elegível; ×0,75 se escudo normalmente pode bloquear |
| Comprar uma carta | 2,00 | Ajustar por condição tardia |
| Retornar unidade à mão | 1,50 | Por unidade |
| Ressuscitar no campo | `2,50 + 0,25 × min(power_base, 10)` | Não duplicar bônus/corpo |
| Invocar token | `0,75 × poder-base do token` | Por token |
| Escudo contra remoção | 2,00 | Por unidade protegida |
| Purificar um estado | 0,75 | Por estado removido; bônus é adicional |
| Mover unidade | 0,75 | Por unidade movida |
| Resistência climática | 0,50 | Por ponto de penalidade evitado |
| Sacrificar aliado | `-1,00 × poder-base esperado` | Custo negativo; ganho recebido pontua em separado |

Padronização de alvos: alvo único = 1; fileira = 2; campo inteiro = 3. Fator de condição: incondicional 1,00; estado comum de tabuleiro 0,85; condição tática específica 0,70; estado raro/de rodada 0,55; dois ou mais pré-requisitos 0,40. Duração: persistente 1,00; até fim da rodada 0,75; expira por evento 0,60. `E_individual = min(10, soma(componentes × fatores))`.

Combos não tornam a carta pura. Parcela preliminar por participante: `E_combo = min(2, 0,5 × (bonus + 2 × team_bonus) / participantes_minimos)`. Somar combos e limitar a parcela total a 2 EFP por carta. O fator 0,5 é hipótese inicial e precisa ser substituído por frequência real de ativação medida em simulação.

`E_total = min(10, E_individual + E_combo)`. `E=0` significa ausência intencional de efeito individual; `E=null` significa regra declarada que ainda não está ligada/validada. Nunca transformar automaticamente `null` em `0`.

## 4. Catálogo preliminar de estimativas

`card-game-effect-score-catalog.json` deriva nomes, IDs e textos dos dicionários importados do baseline. Inclui as 59 entradas de `HABILIDADES`, 22 identidades ativas, 27 combos e 10 líderes. Os scores numéricos são hipóteses de balanceamento, não valores atuais do motor. `sobrevivente` recebe `null` porque há definição sem handler de partida. Efeitos sem atribuição atual são marcados como tal. Os 18 mapeamentos de identidade filtrados não são tratados como ativos.

## 5. Custo proposto

Unidades: `C = clamp(ceil((P + 2 × E) / 3,5), 1, 10)`.

Especiais: `C = clamp(ceil((2 × E) / 3,5), 1, 10)`. O termo de poder é matematicamente zero, mas `power_base` persistido permanece `null` para especial. O peso 2 do efeito reflete seu impacto não limitado a um corpo de unidade. A fórmula é monotônica: aumentar P ou E não reduz C.

### 5.1. Orçamento do deck

Proposta inicial revisada: teto **32 pontos**, calculado como `soma(custo das 12 cartas) + custo da relíquia equipada + leader_load`. Manter temporariamente as restrições existentes: 12 cartas únicas, pelo menos 8 unidades, no máximo 4 especiais.

O ramo `action == "relic"` no motor mostra que a relíquia é ação tática separada das 12 cartas. Por isso precisa entrar no orçamento para não contornar o teto. Líder também altera a partida fora das 12 posições; sugestão `leader_load = clamp(ceil(E_lider / 2), 1, 5)`. O teto 32 e o valor de `leader_load` são hipóteses que devem ser calibradas por simulação.

Validação autoritativa deve ocorrer no backend (`bot.py`, `_api_gwent_deck_save`); `site/app.js` apenas apresenta e antecipa a soma. Persistir custo total e versão das regras no deck. Recalcular o custo no servidor, nunca confiar em valor enviado pelo browser.

### 5.2. Simulação exploratória do teto (não é simulação de partidas)

Aplicando os EFP provisórios do catálogo às cartas do baseline, 128 modelos puderam ser pontuados (101 unidades + 27 especiais); nove cartas com IDs `gloria`, `legado`, `devoto` ou `sinergia_faccao` foram excluídas por não terem resolução canônica confirmada. Foram sorteados 100.000 baralhos de 12 modelos únicos, com 8–12 unidades e 0–4 especiais, seed 42. Não foram modelados propriedade, facção, líder, relíquia nem taxa real de ativação de combos. O custo total teve média 32,08, mediana 32 e percentis 10/25/50/75/90/95 = 28/30/32/34/36/37. Fração dos decks amostrados abaixo do teto: 30 pontos = 31,8%; 32 = 56,3%; 34 = 77,9%; 36 = 91,6%; 38 = 97,7%; 40 = 99,5%.

**Conclusão provisória:** 60 era claramente permissivo demais e foi substituído por 32 como teto experimental inicial. 32 rejeita aproximadamente 43,7% dos decks aleatórios nesse conjunto de premissas. Isso não prova equilíbrio; o teto deve ser reavaliado depois de simular partidas, facções e sinergias com a nova distribuição de poder/efeitos. O relatório estruturado completo está em `card-game-deck-cost-sampling-v0.1.json`.

## 6. Raridade derivada

Score proposto: `R = 2 × P + 3 × E + 0,5 × (10 − C)`. Para especial, usar `P=0` somente na fórmula; `power_base` continua `null`.

| Raridade | Intervalo de R proposto |
|---|---:|
| Comum | R < 10 |
| Rara | 10 ≤ R < 15 |
| Épica | 15 ≤ R < 20 |
| Lendária | 20 ≤ R < 26 |
| Mítica | 26 ≤ R < 32 |
| Primordial | 32 ≤ R < 39 |
| Singular | R ≥ 39 |

A fórmula foi escolhida para que +1 P aumente R em no mínimo 1,5 mesmo quando C sobe um ponto; +1 E eleva R em no mínimo 2,5 quando C também sobe; reduzir custo aumenta R em 0,5 por ponto. Isso satisfaz a direção definida pelo usuário. Exemplo: unidade P5/E0/C2 → R14 (Rara); P10/E0/C3 → R23,5 (Lendária); P8/E3/C4 → R28 (Mítica); especial E5/C3 → R18,5 (Épica). Esses exemplos são demonstrações matemáticas, não cartas aprovadas.

Raridade é classificação, não multiplicador de habilidade. Remover a dependência de `RARITY_EFFECT_BUDGET`: o mesmo `effect_id` e parâmetros executam os mesmos números em qualquer raridade. Probabilidades de obtenção podem existir à parte, mas não determinam raridade da carta.

## 7. Distribuição determinística

A definição de efeito, poder, facção, custo e raridade deve vir de um manifesto estático/versionado por `card_id`. Eliminar sorteios e hash condicional para mecânica (`rng.random`, `rng.choice`, hash pseudoestável). Se geração procedural continuar, ela escolhe templates de uma tabela de regras explícita, sujeita a quotas e validações; RNG pode variar apenas cosméticos sem efeito no balanceamento. Teste de build garante `ceil(0,30 × N)` puras e rejeita qualquer geração que viole quota.

## 8. Diretriz de facção, nome e lore

| Facção | Eixos temáticos coerentes | Vocabulário/títulos preferenciais | Evitar |
|---|---|---|---|
| Ordem Áurea | Erdtree, Leyndell, Crisol, lei, proteção, ouro, dever e conflito com a Vontade Maior | sentinela, juramentado, inquisidor, cavaleiro, confessor, guardião | atribuir sangue Mohgwyn ou culto lunar sem ponte narrativa |
| Véu Carmesim | Mohgwyn, sangue, hemorragia, recusantes, Volcano Manor, sacrifício, chama profana | acólito, carrasco, devoto do sangue, recusante, ritualista, herético | narrar como braço da Ordem Áurea sem explicação |
| Lua Negra | Caria, Raya Lucaria, Sellia, Nokron/Nox, estrelas, gravidade, geada e feitiçaria | astrólogo, astrólogo cariano, oráculo, graviturgo, feiticeiro, exilado lunar | eixo central de culto sanguíneo ou dogma dourado sem vínculo |
| Os Esquecidos | facção autoral do projeto: fé marginal, peregrinação, memória, ruínas, irmandade, cinzas e sobrevivência; ecos de Dark Souls quando coerentes | peregrino, guardião das cinzas, sacerdote, irmão juramentado, vigia das ruínas | identidade luterana genérica ou atribuição de facção contraditória |

A lore deve ficar separada da descrição mecânica. Uma lore concisa traz origem → conflito/motivação → vínculo com a facção. Personagens canônicos não devem receber biografias inventadas que contradigam os jogos; personagens autorais devem parecer originais do projeto e não canon oficial.


> **REVISÃO METODOLÓGICA EFP v0.2 (2026-11-27):** a estimativa agregada em `card-game-effect-score-catalog.json` não possui memória de cálculo suficiente nem calibração em partidas. Consultar `card-game-effect-source-map-v0.1.json` para referências exatas dos handlers e `card-game-efp-methodology-v0.2.md` para a metodologia proposta de decomposição em componentes e valor esperado. Não aprovar nem aplicar os scores numéricos atuais como pesos definitivos.

## 9. Schema canônico proposto

```json
{
  "schema_version": 1,
  "card_id": "stable_id",
  "name": "Nome canônico",
  "title": "Epíteto opcional",
  "category": "unit",
  "faction_id": "golden_order",
  "row": "melee",
  "power_base": 8,
  "effect_id": "effect.example",
  "effect_params": {},
  "effect_points": 2.5,
  "combo_tags": [],
  "deck_cost": 4,
  "rarity_score": 28.0,
  "rarity": "Mítica",
  "lore": "Origem, conflito e vínculo com a facção.",
  "description_mechanical": "Texto gerado do mesmo effect_id e parâmetros.",
  "art_version": 1
}
```

Para especial: `row=null`, `power_base=null`, mas `effect_id` obrigatório. Unidade pura: `effect_id=null`, parâmetros vazios, `effect_points=0`, tags vazias e descrição mecânica explícita de ausência de habilidade.

## 10. Critérios de aceite antes de implementação

1. Toda unidade tem `1 <= power_base <= 15`; especiais têm `null`.
2. Pelo menos `ceil(0,30 × N_modelos)` IDs únicos são puros.
3. Pura não tem efeito individual, identidade, hook ou tag de combo ativo.
4. Cada `effect_id` tem um handler único, parâmetros tipados, texto gerado da mesma definição e testes de resultado.
5. Mesmo input produz EFP, custo e raridade iguais; nenhuma seleção mecânica depende de RNG/hash.
6. Aumentar P ou E nunca reduz raridade; para P/E iguais, custo menor nunca reduz raridade.
7. Deck de 12 cartas, mínimo 8 unidades, máximo 4 especiais, custo total ≤32 incluindo relíquia e carga do líder (se orçamento aprovado).
8. A raridade não modifica magnitude, alvos nem duração de efeito.
9. Descrição cobre todos os parâmetros reais do handler; testes com estado inicial e final confirmam o texto.
10. Mudança mecânica ou de texto invalida/atualiza arte aprovada; versão de imagem deve corresponder à versão do modelo.

## 11. Pontos abertos — não implementar sem decisão

- Confirmar se 1–15 se aplica às unidades (proposta) ou se especiais precisam de outra escala visual.
- Validar teto 32, fator de custo e cortes de raridade com partidas simuladas.
- Corrigir facções das seis cartas `luterano_*` antes de distribuir quota por facção ou escrever lore.
- Decidir destino de 18 identidades filtradas, seis handlers V75 desconectados e habilidades sem metadado/handler; não atribuir EFP positivo a lógica não executável.
- Incluir cartas pessoais/geradas no mesmo schema; migrar exemplares e snapshots sem sobrescrever partidas em andamento.
- Aprovar ou rejeitar `leader_load`; líder não é carta do deck, mas modifica o jogo fora das 12 posições.

## 12. Sequência recomendada

1. Simular decks de referência por facção e custo, recolhendo taxa de vitória, duração média, cartas/efeitos mais frequentes e ativação de combo.
2. Calibrar EFP, fórmula de custo, teto e faixas de raridade.
3. Aprovar formalmente a v1 do balanceamento.
4. Decidir cada habilidade antiga: `keep`, `merge`, `redesign` ou `remove`, com alias de IDs.
5. Escrever catálogo canônico v1; depois refatorar banco, motor, APIs, frontend e arte em migração versionada.

## Histórico

| Data | Versão | Alteração | Situação |
|---|---|---|---|
| 2026-11-27 | 0.1 | Primeira proposta de EFP, custo, teto, raridade, pureza, geração determinística e diretriz de facções/lore. | Proposta não aprovada; sem alteração funcional. |


> **ATUALIZAÇÃO 2026-11-27 — contrato estrutural separado:** o modelo estrutural novo foi documentado em `card-game-canonical-model-v1.md` e implementado como validador em `sistemas/card_contract.py`. Isso não aprova as fórmulas numéricas desta especificação. EFP, custo, raridade, orçamento 32, leader_load e cortes de raridade seguem não aprovados e não entram no runtime. A interpretação estrutural atual separa unidades, especiais e relíquias; unidades têm poder 1–15 e special/relic usam `power_base=null`.


## Adendo de aprovação — raridade classificatória (2026-11-27)

O proprietário aprovou BUF-001, Alternativa A, no Grupo B. Para o novo sistema, a raridade é classificação apenas e não altera magnitude, elegibilidade/limiares, quantidade ou seleção de alvos, duração ou qualquer saída mecânica. `RARITY_EFFECT_BUDGET` não será dependência do novo resolvedor. Valores mecânicos devem ser parâmetros explícitos de efeito ou regras versionadas.

**Escopo limitado:** esta aprovação não aprova as fórmulas numéricas de EFP, custo, orçamento 32, `leader_load`, cortes de raridade, scores ou distribuição apresentados neste documento. Todos esses itens permanecem propostas até simulação e aprovação específicas. O motor legado permanece inalterado e pode continuar demonstrando o comportamento histórico até a migração autorizada.
