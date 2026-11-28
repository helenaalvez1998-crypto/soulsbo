# Modelo canônico de carta v1 — contrato de dados

**Estado:** estrutura técnica inicial implementada e testada; catálogo novo ainda não publicado no runtime. Este documento fixa o contrato estrutural, não aprova fórmulas de custo/raridade nem escolhe quais efeitos antigos serão mantidos.

## 1. Objetivo

O sistema antigo espalha a definição mecânica entre `Carta.habilidade`, `CARD_IDENTITY_ABILITIES`, tags em `CARD_SYNERGY_TAGS`, metadados de `HABILIDADES`, modificadores de raridade e descrições próprias de APIs/renderizadores. O modelo novo elimina esse arranjo por meio de uma definição autoral por `card_id`, um registry central de efeitos e uma camada de compilação de balanceamento.

O fluxo alvo é:

```text
card_id
  -> definição canônica (faction, kind, row, power_base, effect_id, params, tags, lore)
  -> registry de efeitos + parâmetros tipados
  -> compilador de balanceamento (custo e raridade derivados)
  -> definição compilada/runtime
  -> motor / deck builder / API / site / imagem
```

O runtime legado continua sendo a fonte ativa até uma migração posterior. `sistemas/card_contract.py` não é importado por `cartas.py`, `gwent.py` ou `bot.py` nesta etapa.

## 2. Contrato canônico por carta

A estrutura JSON Schema está em `data/card_game/card-definition.schema.v1.json`; exemplo ilustrativo em `data/card_game/card-definition.example.v1.json`. O registry possui schema próprio em `data/card_game/effect-registry.schema.v1.json` e exemplo em `data/card_game/effect-registry.example.v1.json`.

| Campo | Tipo | Regra |
|---|---|---|
| `schema_version` | integer | Sempre `1`. |
| `card_id` | string | ID estável em snake_case ASCII; não muda quando nome/lore mudarem. |
| `name` | string | Nome canônico exibido, entre 1 e 100 caracteres. |
| `title` | string/null | Epíteto opcional de até 80 caracteres. |
| `kind` | enum | `unit`, `special` ou `relic`. |
| `faction_id` | enum | `golden_order`, `crimson_veil`, `dark_moon` ou `the_forgotten`. |
| `row` | enum/null | Unidade: `melee`, `ranged` ou `siege`; especial/relíquia: `null`. |
| `power_base` | integer/null | Unidade: inteiro estrito de 1 a 15; especial/relíquia: `null`, pois não são corpos de combate. Nunca usar 0 como poder-base. |
| `effect_id` | string/null | No máximo um efeito individual canônico; `null` representa ausência de habilidade individual. Especial/relíquia requer efeito. |
| `effect_params` | object | Parâmetros explícitos e tipados para aquele `effect_id`; deve ser `{}` quando `effect_id=null`. |
| `combo_tags` | string[] | Tags declarativas para combos; sem duplicatas. Tag de combo é efeito indireto e desqualifica a unidade como pura. |
| `lore` | string | Narrativa independente da regra, entre 1 e 600 caracteres. |
| `art_version` | integer | Versão da arte compatível com a versão dos dados visuais/mecânicos. Incrementar quando alteração exigir regeneração. |
| `origin_id` | string/null | Referência opcional a personagem, fonte ou origem autoral. |
| `source_game` | string/null | `Elden Ring`, `Dark Souls`, `Original` ou outra origem autorizada. |

### 2.1. Tipos e slots não são a mesma coisa

- `unit`: ocupa uma das 12 posições do deck, tem fileira e poder-base.
- `special`: ocupa uma das 12 posições do deck, não tem fileira nem poder-base; executa uma ação/efeito.
- `relic`: ocupa o slot separado de relíquia, não uma das 12 posições; não tem fileira nem poder-base.
- Líderes não são cartas de deck e ficam num registry próprio de líderes.

O baseline de 137 modelos se divide em 110 unidades, 21 especiais táticas e 6 relíquias. A classificação antiga agrupava especiais e relíquias sob `categoria=Especial`; o modelo novo separa os tipos para impedir que a regra de 12 cartas trate a relíquia como carta normal.

### 2.2. Efeito individual único

A habilidade que antes vinha de `CARD_IDENTITY_ABILITIES` deve ser migrada para o mesmo `effect_id` usado por qualquer outra carta. O `card_id` não pode, por si só, ativar uma segunda habilidade oculta. O registry contém a implementação e metadados; a carta aponta para exatamente um efeito individual ou `null`.

Combos permanecem separados e declarativos. Uma carta pode ter um efeito individual e tags de combo, mas suas regras devem ser exibidas explicitamente. Não haverá efeito executável ligado apenas por um mapa secreto de IDs.

### 2.3. Separação de lore e regra

- `lore`: origem, conflito/motivação e relação com a facção. Nunca serve como fallback mecânico.
- `effect_id` + `effect_params`: verdade mecânica.
- Texto da habilidade: gerado a partir do template do registry e dos parâmetros validados.
- Texto de combo: gerado a partir do registry de combos e das condições de ativação.
- Não escrever números de efeito manualmente na lore.

## 3. Regra de carta pura

Uma unidade é pura somente quando:

```text
effect_id == null
AND effect_params == {}
AND combo_tags == []
```

A passiva global de facção não conta como habilidade individual e não retira a pureza. Uma unidade com tag de combo não é pura, mesmo que não tenha `effect_id` individual.

Quota mínima confirmada: `ceil(0,30 × N_modelos_oficiais)`. Para 137 modelos, o mínimo aritmético é **42 unidades puras**. Especiais e relíquias não são puras. Uma meta interna de 35% apareceu na proposta v0.1, mas não foi aprovada e não é exigência nesta fase.

## 4. Dados derivados: custo e raridade

Custo e raridade não serão escolhidos manualmente na definição autoral. Um compilador de balanceamento os produzirá com base em poder-base e efeito avaliado, conforme regras aprovadas/versionadas.

**Não estão congelados nesta versão:** fórmula EFP, pesos de compra/remoção/escudo, fórmula de custo, teto de deck, `leader_load`, faixas numéricas de raridade ou pesos de obtenção. A proposta em `card-game-balance-spec-v0.1.md` permanece não aprovada. O modelo fonte não grava valores fictícios para preencher essas lacunas.

Depois de aprovada, a compilação fornecerá no mínimo `deck_cost`, `rarity_score`, `rarity_id` e `balance_rules_version`. O runtime, deck builder e renderer devem consumir o mesmo objeto compilado.

## 5. Catálogo de efeitos

O registry futuro deve declarar, no mínimo:

- `effect_id` estável;
- nome e descrição/template;
- timing (`on_play`, `on_round_end`, `on_match_start`, `activated_action`, etc.);
- parâmetros, tipos, limites, lista de obrigatórios e política de parâmetros extras;
- alvo e seleção determinística;
- duração, stack e condições;
- identificador do handler único;
- ID(s) de teste comportamental;
- componentes EFP mensuráveis (após calibração).

`data/card_game/effect-registry.example.v1.json` é apenas exemplo estrutural. O inventário fiel de IDs e textos antigos está em `data/card_game/catalog-legacy-baseline-v0.1.json`, sob `effect_registry_legacy`; não o importar em runtime novo sem revisão.

## 6. Facções

| `faction_id` | Nome atual | Direção temática |
|---|---|---|
| `golden_order` | Ordem Áurea | Erdtree, Leyndell, Crisol, lei, proteção, ouro e dever. |
| `crimson_veil` | Véu Carmesim | Dinastia Mohgwyn, sangue, hemorragia, recusantes, sacrifício e chama profana. |
| `dark_moon` | Lua Negra | Caria, Raya Lucaria, Sellia, Nox, estrelas, gravidade, geada e feitiçaria. |
| `the_forgotten` | Os Esquecidos | Facção autoral: fé marginal, peregrinação, memória, irmandade, ruínas, cinzas e sobrevivência; ecos de Dark Souls quando coerentes. |

O manifesto antigo contém seis cartas `luterano_*` com facção divergente da identidade indicada pelo próprio grupo. Elas ficam marcadas para revisão no snapshot; não foram corrigidas nesta etapa porque nomes, lore e facção serão refeitos em conjunto.

## 7. IDs, versões e artes

- `card_id` não é nome exibido e não deve ser derivado novamente após lançamento.
- Nome, título, lore, poder, efeito, parâmetros, tags, facção ou estrutura visual que mude a composição da imagem exige revisão de `art_version`.
- Uma imagem aprovada só pode ser considerada atual se seu fingerprint/versão corresponder à definição compilada.
- Não apagar artes existentes automaticamente. O snapshot documental não copia imagens nem acessa R2.

## 8. Validação automática

Implementação independente de dependências externas: `sistemas/card_contract.py`.

Valida:

- campos obrigatórios e desconhecidos;
- ID estável e formato;
- tipo, facção e fileira;
- poder de unidade em 1–15 e `null` para special/relic;
- efeito único, referência ao registry e parâmetros contra tipos/limites/required definidos no registry;
- integridade do registry: IDs únicos, handler/timing, parâmetros declarados, mínimo de dois participantes e prioridades de combo únicas;
- tags únicas e registradas;
- lore e versão de arte;
- IDs duplicados no catálogo;
- quota mínima de 30% de cartas puras.

Testes: `docs/scripts/test-card-contract-v1.py`. O CLI `docs/scripts/validate-card-catalog-v1.py` valida primeiro o registry e depois o catálogo, incluindo os parâmetros efetivos de cada carta.

## 9. Estado e limites

Concluído nesta etapa: contrato, schemas JSON da carta e do registry, exemplos, validação dos parâmetros do efeito, CLI, snapshot reproduzível do baseline e 35 testes do contrato. O novo catálogo ainda não substitui `CARTAS_POR_ID`; `cartas.py`, `gwent.py`, `bot.py`, `database.py`, `site/app.js` e renderizadores permanecem no runtime legado.

Não interpretar o snapshot como catálogo aprovado. IDs e valores são cópia do estado antigo; nomes/lore/facções/efeitos/custos/raridades serão revisados antes da publicação do catálogo novo.
