# Card Game — Handoff de continuidade

> Documento operacional vivo. Leia primeiro este arquivo e depois o inventário técnico em [`card-game-mapping-audit.md`](card-game-mapping-audit.md).

## Estado atual — potência da raridade e poder máximo (2026-11-28)

- **Poder máximo ≠ habilidade:** `PODER MÁXIMO` vem de `faixa_poder_exemplar()` (teto da faixa da raridade, ex.: Rara 4–6) e indica até onde o exemplar pode ser **aprimorado com almas**; não é bônus de efeito. Rótulo no site agora diz "(APRIMORAMENTO)".
- **Bug corrigido:** `bot.py` sobrescrevia `potencia_raridade` com `RARITY_EFFECT_BUDGET[raridade]` (Rara = 1) mesmo em carta sem efeito, mostrando "1/6" onde nada era amplificado. Agora vale o valor de `preparar_carta()` (0 sem habilidade/identidade/combo). Escala do site corrigida para `/ 3` (máximo real) e fallback por raridade removido.
- **Lore:** cartas geradas `jogo_*` e `patente_*` não carregam mais "Papel tático…/Sem habilidade…" na descrição; apenas lore.
- Testes: 8 suites 251/251; suíte de sincronia (lore sem mecânica inclui patentes) passa.

## Estado atual — efeitos não informados agora aparecem (2026-11-28)

- **Problema:** 19 cartas sem habilidade individual participam de combos mas diziam "Sem habilidade especial"; cartas com habilidade também não mencionavam seus combos (a ficha de coleção mostrava, mas imagem, partida e catálogo não).
- **Correção:** `preparar_carta()` acrescenta "Combo de deck: Nome (+N); ..." (até 3, por prioridade) ao `habilidade_texto`; cartas sem efeito próprio mostram "Sem habilidade individual. Combo de deck: ...". Como imagem, partida, coleção e catálogo usam esse texto, todos atualizam juntos. Limite do texto subiu de 420 para 520.
- **Site:** `/api/gwent/catalogo-cartas` devolve `combos` (nome+descrição) e `site/catalogo-cartas.html` os exibe; cache do app `20261128-r8`.
- **Teste:** `assert-deck-budget-purity-v0.1.py` verifica que toda carta com combo, habilidade, identidade ou hook tem o efeito no texto (0 omissões). 8 suites 251/251.

## Estado atual — correção da dessincronia texto/imagem/partida (2026-11-28)

Causas encontradas e corrigidas:
1. **Lore com mecânica falsa:** ~27 cartas (`luterano_*`, 8 V75 "sem habilidade", 8 V75 com identidade, `gwent_especial_requiem`) tinham `descricao` prometendo efeitos que o motor não executava (ex.: Sacerdote "cura", Irmão "ganha força ao vencer", Apóstolo "ambos ganham +1"). Agora `DESCRICOES_LORE` (cartas.py) deixa a descrição só como lore; o efeito vem só de `preparar_carta()`.
2. **Catálogo público (`site_hub.py`)** usava `HABILIDADES` genérico + `carta.descricao` como fallback e `Carta.custo`. Agora usa `preparar_carta()` (mesmo texto da imagem e da partida).
3. **Custo:** `Carta.custo` divergia da raridade em 19 cartas; agora é normalizado para `CUSTO_RARIDADE` no catálogo.
4. **Habilidade genérica morta:** 22 cartas têm identidade que substitui a genérica; o payload ainda expunha o ID genérico (aura/ícone errados). Agora `habilidade` vem vazia quando há identidade.
5. **Motor ≠ texto:** `devoto` exigia 2 aliados mas o texto diz "outro aliado" (corrigido para 1); `luterano_papa` ganhou identidade (`sinergia_faccao`).
6. **Imagem:** cartas sem efeito mostravam título "Habilidade"; agora "Sem habilidade", igual ao catálogo.

Teste: `docs/scripts/assert-deck-budget-purity-v0.1.py` agora também valida imagem==payload==catálogo para as 137 cartas, lore sem mecânica e comportamento das identidades legado/devoto/sinergia (26/26). 8 suites antigas 251/251; renders de amostra OK.

**Limitação conhecida:** arte oficial integral enviada por upload (no DB/R2, fora do ZIP) tem o texto embutido na imagem e NÃO é regenerada; se o efeito de uma carta mudou, a arte precisa ser reenviada/reaprovada. As artes geradas pelo renderer atualizam sozinhas (hash do payload).

## Estado atual — decisões delegadas e implementadas (2026-11-28)

**O usuário delegou todas as decisões pendentes** (jogo sem jogadores ativos; sem receio de mudar). Decisões tomadas e implementadas:

| Decisão | Implementação |
|---|---|
| Custo oficial = custo da raridade do **exemplar** (`CUSTO_RARIDADE`); fórmula EFP/(P+2E)/3,5 **não adotada** (EFP não calibrado) | `sistemas/gwent.py`: `custo_por_raridade()`, `custo_total_deck()`; `preparar_carta()` agora devolve `custo` (bug do payload corrigido) |
| Orçamento de deck = **36** (12 cartas + Relíquia equipada; líder grátis), validado no servidor | `bot.py::_api_gwent_deck_save` (400 com `custo`/`orcamento`); resposta de sucesso inclui custo; `site/app.js` mostra `custo X/36` e bloqueia mensagem; cache r7 |
| Pureza: "pura" = sem habilidade nem identidade individual (tags de combo são sinergia de deck). 52/137 (38%) cumprem; estrita sem tags: 15/110 unidades — **não** atinge 30% estrito, pois remover tags quebraria combos (cada tag tem só 2 provedores) | teste `assert-deck-budget-purity-v0.1.py` exige ≥30% pela definição adotada |
| Tags órfãs removidas (5) | `CARD_SYNERGY_TAGS` |
| 6 cartas `luterano_*` com `legado/devoto/sinergia_faccao` agora têm identidade ativa; metadados adicionados (`gloria`, `legado`, `devoto`, `sinergia_faccao`) | `CARD_IDENTITY_ABILITIES` (27→28 ativas, após filtro V18), `HABILIDADES` |
| Facções dos `luterano_*` mantidas como estão (campo é a autoridade do motor) | sem mudança |
| `sobrevivente` implementado (mantém a mais forte ao fim da rodada); `gloria` só mantém se venceu; mensagem de Glória só aparece se há carta Glória | `_resolve_round()` |

Validação: 8 suites anteriores 251/251 (teste de `sobrevivente` atualizado de "hook ausente" para "hook funciona"), nova suíte 21/21, `node --check`, `py_compile`. HTTP real continua não executado (sem `discord.py`/`aiosqlite`; sem rede).

**Ainda pendente:** execução HTTP real; poder-base 1–15 já satisfeito (verificado); refazer nomes/lore, remoção de ramos legados, schema canônico v1, raridade derivada e arte versionada não foram feitos (grande, exige arte/migração).

## Estado atual — mapa estático dos contratos HTTP Gwent v0.1 (2026-11-27)

**STATUS: mapa das 12 rotas Gwent produzido e reproduzido por AST; execução HTTP real continua pendente.** Esta é a revisão documental mais recente.

- Script: `docs/scripts/audit-gwent-http-contracts-v0.1.py`; relatórios: `docs/card-game-http-contract-map-v0.1.md` e `.json`.
- Foram identificadas 12 rotas: catálogo, imagem privada/pública, deck (GET/POST/reset), lista/criação de partidas, criação solo, resposta a convite, detalhe e ação.
- O mapa registra linha de registro, handler, linhas da função, sinais estáticos de autenticação/origem, campos de body, parâmetros de rota, chamadas de banco/motor e literais de consumo no `site/app.js`. O AST localiza `preparar_carta()`, `aplicar_jogada()`, `novo_estado()` e `executar_turno_ia()` nos handlers correspondentes.
- **Falha relevante para custo:** `POST /api/gwent/deck` valida 12 cartas-modelo únicas, pelo menos 8 unidades, no máximo 4 especiais, facção predominante, líder/facção, relíquia e propriedade de exemplares; não soma custos nem impõe orçamento.
- **Falha de payload:** `/api/gwent/cards` e `/api/gwent/deck` atribuem `payload['custo']` antes de chamar `preparar_carta()`, mas o dicionário de retorno explícito dessa função não inclui `custo`; portanto o campo é descartado no payload preparado.
- O frontend envia cartas como `{card_id, exemplar_id}` e configuração `{faction, leader_id, relic_id}`; ações de partida enviam `action`, `card_id`, `row`, `card_ids` e `target_id`. A ação retorna `{ok: true}` e o frontend refaz GET do detalhe.
- Convites guardam snapshots de deck/config como `pending`; aceite revalida relíquia, embaralha snapshots e chama `novo_estado()`. Solo espelha a configuração do jogador para NARA; a ação pode executar `executar_turno_ia()` no servidor, com fallback `pass` se a IA falhar.
- **Limite obrigatório:** isto é auditoria estática. `discord.py` e `aiosqlite` não estão instalados e a instalação por `pip` foi bloqueada por falha de DNS/rede. Não houve `aiohttp.TestClient`, import/dispatch real de `bot.py`, instância da classe `Database`, browser, convite, solo/IA ou produção. Não interpretar sinais AST como prova de status HTTP ou autorização em runtime.
- O restante do estado validado continua: 251/251 asserts em oito suites e 12/12 cenários stateful (contagens separadas). Política de combos aprovada continua sendo a única alteração funcional aprovada nesta trilha.

### Próximo passo autorizado

Obter ambiente/wheels compatíveis com `requirements.txt` e executar `aiohttp.TestClient` contra as 12 rotas, cobrindo autenticação, origem, ownership, status, transações/rollback, convites, solo/IA, recompensas e refetch. Depois, corrigir o contrato de custo somente quando o schema/custo oficial for aprovado. Não modificar ainda poder, raridade, habilidade, DB, frontend ou imagens.



## Estado imediatamente anterior — integração stateful de partidas v0.1 (2026-11-27) — preservado como referência

**STATUS: 12/12 cenários stateful aprovados.** Esta é a etapa imediatamente anterior ao mapa HTTP estático; fica preservada como evidência de partidas/snapshots. Os oito conjuntos de testes anteriores continuam válidos em seus limites próprios (251/251 asserts); a nova suíte não soma seus 12 cenários aos 251 asserts como se fossem a mesma unidade de contagem.

- Novo script: `docs/scripts/assert-full-match-stateful-v0.1.py`; relatório: `docs/card-game-match-snapshot-integration-v0.1.json`; explicação e limitações: `docs/card-game-match-snapshot-integration-v0.1.md`.
- Quatro partidas completas de três rodadas foram conduzidas pelo motor em memória, cobrindo as quatro facções em pares cruzados, mulligan, turnos, jogadas, passes, encerramento de rodada, coroas e estado final. O estado foi serializado/desserializado por JSON durante os fluxos.
- `preparar_carta()` foi exercitada em todos os 137 modelos do catálogo. Um combo real foi ativado via jogadas normais. Também foram testados líder + carta especial climática + reset de rodada, relíquia de uso único, clima manual de uso único, snapshot legado e rejeição sem mutação do estado de entrada.
- O SQLite em memória executou as constantes `SCHEMA` e `SCHEMA_CARTAS` extraídas de `database.py` e testou insert/select/update da tabela `cartas_gwent_matches` com FK ativada. Isso não usa o wrapper `Database`/`aiosqlite` nem o DB de produção.
- Verificação estática do contrato `bot.py` ↔ `site/app.js` confirmou rotas e campos usados. `compileall` dos módulos-alvo e `node --check site/app.js` passaram.
- **Limite HTTP:** a camada HTTP não foi executada. `bot.py` não pôde ser importado porque `discord.py` não está instalado no ambiente de análise; `database.py` não pôde ser importado porque `aiosqlite` não está instalado. Ambos estão fixados em `requirements.txt`; tentei instalá-los com `pip`, mas a resolução DNS/rede do ambiente bloqueou o acesso ao índice. Não usei stubs. Portanto não houve `aiohttp.TestClient`, execução dos handlers reais, gateway Discord ou transação assíncrona do wrapper.
- As partidas completas usam 12 fixtures unitárias sintéticas por jogador para controlar poder/resultado; não são decks publicados validados pelo deck builder. O teste com cartas reais cobre o combo e a preparação de todos os modelos, não uma partida competitiva com decks reais.
- Runtime funcional não foi alterado nesta etapa. A alteração funcional aprovada permanece exclusivamente a política de combos em `sistemas/gwent.py`.

### Próximo passo autorizado naquela etapa (substituído pelo estado HTTP no início do handoff)

Continuar com integração HTTP real quando `discord.py` e `aiosqlite` estiverem disponíveis: testar criação/aceitação de convite, criação solo/IA, `GET /api/gwent/cards`, detalhe de partida, `POST /action`, autenticação, persistência transacional e recompensas. Em seguida validar no browser as respostas, imagens/R2 e só então avançar para testes de IA e simulação competitiva. Não recalibrar EFP/custo/raridade ainda.

## Estado anterior — política oficial de combos v0.1 (2026-11-27)

**STATUS: aprovada pelo usuário, implementada em runtime e coberta por regressões sintéticas.** Esta seção é a referência de estado mais recente; as seções intituladas v0.1/v0.2 abaixo preservam o histórico do baseline e devem ser lidas como registros históricos quando indicadas.

- Único arquivo funcional alterado nesta etapa: `sistemas/gwent.py` (`SYNERGY_COMBOS` e `_aplicar_combo_de_cartas()`).
- Regras: todos os 27 combos exigem duas instâncias distintas; a carta atual precisa contribuir com tag exigida; há no máximo um combo por jogada; `priority` único e explícito decide precedência (menor primeiro); combos pendentes só podem ser ativados por uma carta posterior que também contribua com tag exigida; o bônus individual vai para essa carta participante; `team_bonus` e reset de `synergy_used` foram preservados.
- Partidas persistidas antes do deploy mantêm bônus já concedidos no `state_json`; não há DB de produção no ZIP para uma migração/encerramento controlado. A política nova rege as jogadas resolvidas pelo processo atualizado.
- Os três combos anteriormente sem `minimum` (`cinzas_fornalha`, `vazio_astral`, `eco_convergente`) agora declaram `minimum: 2`.
- Validação: oito suites, **251/251 asserts**; auditoria pós-política em 4.422 pares e 287.430 trincas, zero ativações solo e todos os 2.582 eventos de combo posteriores examinados com carta que contribui com tag exigida.
- Documentos de autoridade: `card-game-combo-policy-v0.1.md`, `card-game-behavior-validation-v0.3.md/.json` e `card-game-combo-overlap-v0.2.md/.json`.
- Compatibilidade: sem migração de schema/DB; snapshots de partidas ativas mantêm bônus já concedidos pela política antiga. A nova regra se aplica às próximas jogadas resolvidas após atualizar o processo. O DB de produção não foi fornecido.
- EFP, custo, raridade, limite de deck e redistribuição das cartas continuam sem aprovação e sem implementação.

## Verificação dos quatro blocos obrigatórios da Regra 8 (revisão de continuidade)

Esta seção responde se o handoff, **isoladamente**, já satisfaz os quatro blocos pedidos. A resposta correta nesta revisão é: **há cobertura significativa, mas ainda não está 100% autossuficiente nem integralmente fechado**. O pacote completo complementa o handoff com a auditoria, matriz e proposta v0.1; o próximo chat deve ler os documentos na ordem definida em `README-PACOTE-CONTINUIDADE.md`.

| Bloco exigido | Estado | Onde está documentado | Pendências/defasagens conhecidas |
|---|---|---|---|
| 1. Mapa completo do sistema | **Parcialmente coberto no handoff; complementado pela auditoria** | `card-game-mapping-audit.md`, seções 2–3, 11–14 e 23 (contratos HTTP); handoff, seção “Problemas prioritários”. | O mapa lista módulos centrais/auxiliares, APIs principais, fluxo catálogo→DB/API→motor→frontend/imagem e alguns comandos/funções. Ainda não é um inventário de cada evento/handler de Discord, cada função chamada em todos os caminhos auxiliares, todos os comandos operacionais de execução/deploy nem um runbook testado. O DB de produção e configuração publicada não vieram no baseline; schema/runtime de produção não foi validado. |
| 2. Dados e regras oficiais | **Parcial; política de combos aprovada, novo balanceamento ainda proposto** | `card-game-combo-policy-v0.1.md` contém a regra oficial de combos implementada; `card-game-mapping-audit.md`, matriz e catálogo preservam o baseline; `card-game-balance-spec-v0.1.md` permanece proposta. | A política de combo é agora a única nova regra quantitativa aprovada e implementada nesta etapa. Não existe ainda catálogo completo novo nem schema v1. EFP, custo, teto 32, raridades, denominador/meta de cartas puras, `power_base=null` para especiais e `leader_load` permanecem propostas. Faltam decisões carta a carta `keep/merge/redesign/remove`, validação dos efeitos incompletos, identidades antigas/V75 e confirmação das facções `luterano_*`. `CARD_GAME_REDESIGN.md` continua defasado e não é autoridade. |
| 3. Histórico detalhado por arquivo/função/campo/motivo/impacto | **Parcial; as alterações desta continuidade estão registradas, histórico original do código não veio no ZIP** | Esta seção “Histórico de alterações desta continuidade”, seção final de implementação de combos, `PACOTE-MANIFESTO.md` e auditorias. | O histórico agora registra o runtime alterado em `sistemas/gwent.py`, a alteração exata em `SYNERGY_COMBOS`/`_aplicar_combo_de_cartas()`, o motivo, o impacto e as validações. O ZIP baseline não fornece histórico Git/commits; não há como reconstruir a história anterior do código. Para cada mudança futura, registrar caminho, função/campo/trecho, antes/depois, motivo, impacto em DB/API/frontend/arte, testes, migração e rollback. |
| 4. Estado exato, dependências e próximos passos | **Majoritariamente coberto; integração operacional pendente** | Este handoff; `card-game-behavior-validation-v0.3.md/.json`; `card-game-match-snapshot-integration-v0.1.md/.json`; `card-game-http-contract-map-v0.1.md/.json`; `card-game-combo-overlap-v0.2.md/.json`; README e manifesto. | Além dos 251/251 asserts em oito suites e da enumeração pós-política, a suíte stateful passou 12/12 cenários: quatro partidas de três rodadas em memória, JSON snapshots, payloads dos 137 modelos, combo por turno, líder/especial/clima, relíquia, legado e SQLite com DDL real extraído de `database.py`. O mapa estático agora cobre as 12 rotas Gwent e detecta o contrato de custo ausente. Faltam dispatch HTTP real, wrapper `Database`/aiosqlite, browser, IA/recompensas no fluxo real, DB/ambiente de produção, R2/artes e runbook de deploy reproduzido. |

### Interpretação obrigatória para um chat novo

- O **pacote ZIP completo** é a unidade de handoff; `card-game-handoff.md` é o índice operacional, não substitui a leitura da auditoria, matriz, especificação e manifesto.
- A existência de uma fórmula no documento v0.1 não significa aprovação. Apenas os requisitos listados em “Decisões já confirmadas pelo usuário” são requisitos confirmados; valores numéricos adicionais continuam como propostas.
- A auditoria descreve o baseline estático do ZIP de origem, não o estado do servidor/DB em produção.
- A política de combos v0.1 foi aprovada pelo usuário e aplicada em `sistemas/gwent.py`. O restante da reconstrução funcional (catálogo canônico, novas cartas, poderes, EFP/custo/raridade, migrações, imagens e limpeza geral) ainda não começou. O próximo chat deve preservar essa distinção.

## Matriz de rastreabilidade carta por carta (etapa concluída)

A matriz foi adicionada em três formatos, todos gerados a partir do catálogo runtime importado do ZIP baseline:

- [`card-game-card-traceability.md`](card-game-card-traceability.md): relatório legível com tabela de todas as 137 cartas e detalhe individual de cada definição.
- [`card-game-card-traceability.csv`](card-game-card-traceability.csv): uma linha por carta para filtragem e comparação.
- [`card-game-card-traceability.json`](card-game-card-traceability.json): dados estruturados para scripts e futuras migrações.

A matriz distingue habilidade genérica, identidade ativa, identidade histórica filtrada, tags/combos, pureza estrita, custo cadastrado, custo tabelado, texto efetivamente preparado e cobertura de aura/emblema.

**Correção técnica da auditoria:** quando uma carta tem `Carta.habilidade` preenchida e entrada ativa em `CARD_IDENTITY_ABILITIES`, `aplicar_jogada()` define `skill = ""` e suprime o efeito genérico antes da resolução. Só a identidade é executada. A inconsistência real está no payload de `preparar_carta()`: `habilidade` continua contendo o ID genérico, enquanto `habilidade_nome` e `habilidade_texto` apresentam a identidade. Não há dupla execução nesses 16 casos; há ambiguidade de contrato. A matriz JSON/CSV marca os 16 registros.

Achados quantitativos adicionais desta matriz:

- 16 cartas têm campo genérico preenchido e identidade ativa; o motor suprime o efeito genérico e executa somente a identidade. O payload ainda mantém o ID genérico em `habilidade`, enquanto nome/texto usam a identidade.
- 9 cartas carregam IDs ausentes de `HABILIDADES`: três `gloria`, executadas em `_resolve_round()` mas sem metadado/texto no catálogo; e seis `legado`, `devoto` ou `sinergia_faccao`, cujos valores no campo genérico não acionam os ramos homônimos porque esses ramos estão no resolvedor de identidade, sem associação ativa correspondente.
- 43 declarações literais de carta são modificadas pela transformação V18 durante o import: a habilidade é apagada e o poder pode aumentar em +1, limitado pelo teto da raridade. A matriz preserva os valores anteriores e runtime.
- 19 cartas divergem entre `Carta.custo` e `CUSTO_RARIDADE[raridade]`.
- A pureza estrita atual é 15/110 unidades (13,64%); 67 cartas têm tags de combo.
- Cinco IDs têm tags de sinergia sem carta correspondente no catálogo: `gwent_unidade_cruzado`, `gwent_unidade_evangelista`, `gwent_unidade_missionario`, `gwent_unidade_protetor`, `gwent_unidade_sacerdote`.

A geração da matriz não alterou código de jogo nem dados persistidos.


## Especificação de balanceamento — proposta v0.1

- [`card-game-balance-spec-v0.1.md`](card-game-balance-spec-v0.1.md): regras confirmadas separadas de propostas numéricas de EFP, poder, custo, budget de deck, raridade, pureza, distribuição e lore por facção. **Não implementar valores propostos antes de simulação e aprovação.**
- [`card-game-deck-cost-sampling-v0.1.json`](card-game-deck-cost-sampling-v0.1.json): resultado histórico/superado; método tinha crédito de combo parcial e não incluía relíquia/líder.
- [`card-game-deck-cost-sampling-v0.2.json`](card-game-deck-cost-sampling-v0.2.json): amostragem corrigida, separada em cenários com/sem relíquia equipada.
- [`scripts/sample-deck-cost-v0.1.py`](scripts/sample-deck-cost-v0.1.py): reprodução histórica/superada; não usar para recomendar teto.
- [`scripts/sample-deck-cost-v0.2.py`](scripts/sample-deck-cost-v0.2.py): script atual da amostragem de custo.
- [`card-game-effect-score-catalog.json`](card-game-effect-score-catalog.json): catálogo estruturado com os metadados atuais e estimativas provisórias para habilidades genéricas, identidades, combos e líderes. `null` indica definição não executável/incompleta, não carta pura.

A fórmula de custo proposta é `ceil((P + 2E)/3,5)` para unidades; raridade proposta `R = 2P + 3E + 0,5(10-C)`. O teto 32 foi uma hipótese preliminar, **não aprovado**. A amostragem v0.1 foi identificada como metodologicamente incompleta (crédito de combo por interseção parcial de tags e ausência de custo de líder/relíquia); consulte `card-game-balance-validation-v0.1.md` e a amostragem v0.2. Os dados revistos aceitam 68,8% dos decks sem relíquia e 45,4% com relíquia equipada no teto 32, sob premissas aleatórias. Isso não demonstra equilíbrio de partidas. Nenhum valor de custo, EFP, teto ou raridade foi implementado.

## Estado do repositório após política de combos — referência histórica (ver estado stateful no início e no fim do handoff)

- Data do baseline: 2026-11-27; pacote de continuidade recebido: `soulsbo-main-handoff.zip`.
- Código-base original: `soulsbo-main(1).zip`, SHA-256 documentado no manifesto anterior.
- **Uma alteração funcional foi aplicada:** `sistemas/gwent.py`, catálogo `SYNERGY_COMBOS` e `_aplicar_combo_de_cartas()`. Os demais endpoints, schema, frontend, arte e dados persistidos não foram modificados.
- Documentação adicionada/atualizada: regra oficial dos combos v0.1, suite de 32 regressões, auditoria pós-política v0.2, mapa AST pós-política v0.2 e relatório agregado v0.3.
- Validação daquela etapa: oito suites, 251/251 asserts; auditoria enumerativa pós-correção em 4.422 pares e 287.430 trincas. A validação stateful posterior está no bloco inicial e em ‘Estado exato ao encerrar esta entrega — integração stateful v0.1’.
- O DB de produção não veio no ZIP. O inventário não atesta dados de produção nem permite limpar bônus antigos de partidas ativas.

## Decisões já confirmadas pelo usuário

1. Fazer limpeza de versões antigas, mas somente depois de mapear o comportamento atual.
2. Poder-base futuro estritamente entre 1 e 15.
3. Distribuição de efeitos não aleatória.
4. Pelo menos 30% do jogo deve ser composto por cartas puras, sem habilidade/efeito.
5. Implementar custo como regra efetiva para limitar deck.
6. Raridade deve derivar do equilíbrio entre poder-base, efeito e custo, não de escolha arbitrária.
7. Refazer nomes e lore no universo Elden Ring / Dark Souls, mantendo coerência de facção.
8. Manter handoff autossuficiente com mapa técnico, regras, histórico e próximos passos.
9. Política de combos aprovada: duas instâncias distintas de unidade participantes; carta atual contribui com tag requerida; um combo por jogada; prioridade explícita (menor número primeiro); combo pendente só é ativado por participante posterior; bônus individual vai à carta participante que ativa, com bônus de equipe existente preservado.

## Evidências quantitativas do baseline

- 137 modelos: 110 unidades e 27 especiais.
- 59 definições em `HABILIDADES`.
- 22 identidades ativas; 40 antes do filtro (18 filtradas).
- 72 associações de tag; 5 IDs órfãos.
- 27 combos; 10 líderes; 6 relíquias.
- 15 unidades puras estritas (13,64% das unidades; 10,95% do catálogo total).
- 19 modelos com custo cadastrado diferente do custo tabelado pela raridade.
- Deck atual: 12 cartas diferentes, mínimo 8 unidades e máximo 4 especiais; sem orçamento de custo.

Os detalhes e listas completas são mantidos no inventário ligado acima. Não confiar em uma contagem resumida sem consultar as tabelas do inventário.

## Problemas prioritários ainda abertos

1. Duas rotas fornecem descrição de habilidade diferente: `/api/gwent/cards` usa `preparar_carta()`; `/api/gwent/catalogo-cartas` usa `Carta.para_dict()` + `HABILIDADES`, sem consultar identidades ativas.
2. `sobrevivente` está no catálogo e na aura visual, mas não tem resolução no motor.
3. `legado`, `devoto`, `sinergia_faccao` e `escolha_ritmo` têm ramos nominais no resolver de identidade, mas não uma associação ativa por ID; cartas que possuem esses valores no campo genérico não disparam os ramos.
4. `espolios` está implementado no fechamento de rodada, mas não está atribuído a carta atual.
5. Identidades genéricas de cartas ativas são suprimidas por ID; o campo `habilidade` ainda contém um valor diferente que pode confundir consumidores.
6. Tags de combo incluem cinco card IDs ausentes do catálogo.
7. O campo de facção das seis cartas `luterano_*` da seção dos Esquecidos conflita com o comentário/grupo de tags; validar intenção antes de ajustar.
8. Custo não é aplicado como orçamento no deck. Há 19 divergências entre `Carta.custo` e `CUSTO_RARIDADE`; `preparar_carta()` não devolve `custo`.
9. A geração procedural usa `rng.random()`/`rng.choice()` para decidir se uma carta terá habilidade; monitoramento 50/50 só mede, não força uma regra de distribuição.
10. Arte oficial integral antiga não é reescrita; imagem é devolvida como composição completa sem texto dinâmico sobreposto.
11. A aura usa `card['habilidade']`, não o effect ID de identidade; cobertura visual parcial.
12. **RESOLVIDO:** o resolver de combos agora usa prioridades explícitas, exige contribuição da carta atual com tag do combo, exige duas instâncias participantes e bloqueia ativação solo. Ver `card-game-combo-policy-v0.1.md` e auditoria pós-correção `card-game-combo-overlap-v0.2.md`.
13. `docs/CARD_GAME_REDESIGN.md` descreve mecânicas que não são as do motor atual; deve ser reconciliado, não usado como autoridade sem revisão.

## Ordem recomendada para continuar

### Fase A — auditoria e matriz (concluída)

1. [x] Ler e mapear `card-game-mapping-audit.md`.
2. [x] Construir a matriz canônica de referência para os 137 modelos, com dados, habilidades, identidades, tags, combos, texto e arte.
3. [x] Documentar a definição proposta de carta pura: unidade sem habilidade individual, identidade, tag de combo ativo ou trigger próprio; passiva global de facção separada.
4. [x] Fixar como proposta o denominador de todos os modelos: 137 no baseline, exigindo 42 puras; confirmar/rever antes da implementação.
5. [x] Criar escala EFP e catálogo estruturado de habilidades, identidades, combos e líderes; estimativas ainda não validadas.

### Fase B — especificação quantitativa v0.1 (rascunho concluído; aprovação pendente)

6. [x] Propor poder 1–15 para unidades e `power_base=null` para especiais; confirmar a interpretação de especiais antes de migrar.
7. [x] Propor função de custo `ceil((P + 2E)/3,5)` para unidades e `ceil((2E)/3,5)` para especiais.
8. [x] Registrar teto experimental inicial de 32 com custo da relíquia e carga do líder como hipóteses; a validação v0.2 mostrou resultados distintos com/sem relíquia e não sustenta nem aprova esse teto.
9. [x] Propor raridade `R = 2P + 3E + 0,5(10-C)` com faixas Comum a Singular.
10. [x] Definir política proposta de distribuição por manifesto determinístico e meta mínima de 30% de cartas puras.

**Atenção:** `[x]` nesta fase significa que há uma proposta escrita, não que o usuário aprovou os números. Nenhum dos parâmetros de custo, EFP ou raridade foi implementado no motor.

### Fase C — reconstrução e migração

11. Consolidar schema canônico da carta e catálogo de regras em uma fonte única de verdade.
12. Refatorar motor para resolver por `effect_id` canônico; evitar lógica de identidade por ID separada de habilidade declarada. Se efeitos de assinatura forem mantidos, devem estar declarados na carta como efeito canônico explícito.
13. Corrigir facções, tags, combos e referências órfãs.
14. Unificar payload de carta para API de coleção, deck, catálogo público e arte.
15. Preparar migração compatível para exemplares e decks existentes; manter IDs estáveis ou produzir mapeamento antigo→novo.
16. Definir versão de schema/definição no snapshot de partida para que jogos já iniciados não mudem silenciosamente.
17. Definir política de imagem: invalidar cache, versionar arte oficial ou reaprová-la após alteração em nome/poder/raridade/efeito/lore.

### Fase D — validação e limpeza

18. Testar todas as habilidades individualmente com estados iniciais e resultados esperados.
19. Testar combos, passivas de facção, líderes, relíquias, clima, rodada, descarte e IA.
20. Testar invariantes: poder 1–15, percentual puro mínimo, custo total, raridade calculada, descrição = execução, arte = definição.
21. Só depois remover funções/atributos antigos e atualizar os docs antigos.
22. Registrar cada alteração por arquivo, linha/função/campo, antes/depois, motivo, impacto, testes e risco de migração.

## Validação exploratória do balanceamento v0.1 (concluída; sem aprovação)

A validação está consolidada em [`card-game-balance-validation-v0.1.md`](card-game-balance-validation-v0.1.md). A proposta v0.1 continua não aprovada e não implementada.

- A amostragem de custo v0.1 é histórica/superada: concedia EFP parcial se qualquer tag de combo coincidisse e não incluía líder nem relíquia. Não usar seus 56,3% de aceitação em 32 como justificativa.
- A amostragem v0.2 é reproduzível (100.000 decks por cenário, seed 42), sem combo parcial: 128 modelos pontuáveis, 9 excluídos. Teto 32 aceita 68,8% sem relíquia e 45,4% com relíquia; `leader_load` e inclusão de relíquia continuam sendo hipóteses de design.
- Simulação de combos: 100.000 decks, 57,19% com ao menos um combo, média de 0,956 combo ativado na mão de 10 assumida jogada na mesma rodada. Glória Divina atinge 15,87%; Eco das Pedras Cintilantes 9,31%. Frequência não equivale a valor de pontuação/partida.
- Auditoria de handlers: 59 habilidades genéricas; 56 referências diretas em `aplicar_jogada()`, dois hooks de ciclo de vida (`vinganca`, `espolios`) e `sobrevivente` sem handler encontrado. `gloria` é um hook oculto fora de `HABILIDADES`. Há 22 identidades ativas, todas com ramo, e 28 ramificações antigas sem mapeamento ativo.
- Testes de fumaça: 56 habilidades com ação direta concluída sem exceção; três IDs do catálogo com hooks de ciclo de vida testados separadamente (`vinganca`, `espolios`, `sobrevivente`); mais o hook oculto `gloria`; 22/22 identidades emitiram evento de ativação. Isso não equivale a cobertura de todos os ramos nem a teste competitivo.
- `CARD_SYNERGY_TAGS` mantém cinco IDs órfãos; todos os 27 combos têm provedor para cada tag exigida. A amostragem de ativação respeita a resolução real, mas assume ordem aleatória e todas as 10 cartas iniciais jogadas.

**Próximo passo autorizado após a política de combos:** ampliar os testes para sequências stateful de 12 cartas e pares sobrepostos adicionais; testar snapshots serializados e payload de `/api/gwent/cards`; decidir como tratar partidas ativas que conservam bônus legados; cobrir clima, transições, IA e interações cruzadas; revisar as 28 ramificações antigas e hooks `gloria`/`sobrevivente` sem removê-los antes de decisão. Depois construir simulador determinístico de partidas por facção. Não escolher nem implementar teto 32, pesos EFP ou raridade sem simulação e aprovação.

## Decomposição de efeitos e metodologia EFP v0.2 (proposta; sem aprovação)

A etapa seguinte à amostragem v0.1 produziu dois artefatos que ligam o catálogo à implementação real e retiram a pontuação agregada de uma posição de falsa precisão:

- `card-game-effect-source-map-v0.1.json` e `scripts/build-effect-source-map-v0.1.py`: mapa AST histórico congelado; o gerador v0.1 recusa sobrescrever o artefato no runtime atual. Para o código vigente, usar v0.2.
- [`card-game-effect-source-map-v0.2.json`](card-game-effect-source-map-v0.2.json) e [`scripts/build-effect-source-map-v0.2.py`](scripts/build-effect-source-map-v0.2.py): mapa AST regenerado a partir do runtime pós-política.
- [`card-game-efp-methodology-v0.2.md`](card-game-efp-methodology-v0.2.md): metodologia proposta para registrar componentes imediatos/atrasados, alvos, caps, precondições, bloqueios, duração, testes e valor esperado em partidas.

**Cobertura por referência no baseline:** 59 habilidades genéricas: 56 handlers de jogada, dois hooks de ciclo de vida (`vinganca`, `espolios`) e uma sem handler identificado (`sobrevivente`). `gloria` é um hook oculto em `_resolve_round()`, fora do catálogo `HABILIDADES`. As 22 identidades ativas e dez líderes possuem referências de execução. Os 27 combos são declarativos e compartilham `_aplicar_combo_de_cartas()`.

O mapa AST prova apenas onde o código menciona os IDs; não prova alcançabilidade em produção nem correção funcional. O smoke test v0.1 também não cobre todas as condições/branches. EFP v0.1 continua não aprovado: valores fixos para buff, remoção, compra, escudo etc. não estão calibrados por estado e frequência real. A metodologia v0.2 propõe medir um vetor de consequências e valor esperado por política/facção; até testes e simulações serem concluídos, manter `null`/intervalos não aprovados e não recalcular custo ou raridade em produção.

**Estado atualizado pós-política e pós-snapshot:** a validação de comportamento isolado continua em `card-game-behavior-validation-v0.3.md/.json`, com oito suites e 251/251 asserts; a validação stateful atual está em `card-game-match-snapshot-integration-v0.1.md/.json`, com 12/12 cenários. A auditoria atual de combos é `card-game-combo-overlap-v0.2.md/.json`: 4.422 pares, 287.430 trincas, zero ativações solo e 2.582/2.582 eventos posteriores com contribuição de tag exigida. A política foi aprovada e implementada; a seção abaixo com 219 asserts e a auditoria v0.1 são registros históricos pré-patch. Ainda faltam dispatch HTTP real, `Database`/aiosqlite, browser, IA e recompensas de partida, produção, R2/artes e decisão operacional sobre partidas ativas.

## Registro histórico pré-política: validação comportamental v0.2 — 219/219 asserts

> **Histórico pré-patch:** esta seção descreve a etapa anterior à aprovação e implementação da política de combos. O resultado atual é oito suites/251 asserts em `card-game-behavior-validation-v0.3.md`.

A expansão de testes desta etapa está consolidada em [`card-game-behavior-validation-v0.2.md`](card-game-behavior-validation-v0.2.md) e [`card-game-behavior-validation-v0.2.json`](card-game-behavior-validation-v0.2.json). O runner `scripts/summarize-card-game-behavior-v0.2.py` verifica os sete relatórios individuais e agrega suas contagens. Resultado repetido nesta revisão: **219 asserts, 219 aprovados, zero falhas**.

As sete suites são: 13 efeitos representativos iniciais; 33 cenários de identidade (22 positivos para as identidades ativas + 11 negativos/limite); 39 cenários de habilidades genéricas de unidade; sete de ciclo de vida; 18 de especiais/relíquias; 22 de líderes (dez handlers positivos + 12 negativos/limite); e 87 de combos/passiva (27 ativações positivas, 27 requisitos incompletos, 27 bloqueios de repetição do mesmo combo, um teste sem tags, quatro passivas de facção e um especial que não consome a passiva). As contagens são asserções e cenários, não 219 efeitos diferentes.

Os dez líderes verificados são Godfrey, Morgott, Radagon, Mohg, Rykard, Esgar, Papa Esquecido, Rennala, Astel e Loretta. Os testes chamam o `aplicar_jogada()` real com `action="leader"`, mas usam estados sintéticos em memória. Não validam integração HTTP, DB, frontend, Discord, R2, estados persistidos ou força competitiva.

A classificação de código legado foi detalhada em `card-game-stale-identity-disposition-v0.1.md/.json`: 28 ramos sem associação ativa = 18 identidades filtradas pelo V18 + quatro efeitos legados em campos sem dispatch ativo (`devoto`, `legado`, `escolha_ritmo`, `sinergia_faccao`) + seis ramos V75 antigos. A contagem não inclui os problemas separados de `gloria` (hook oculto em `_resolve_round()`, presente em três cartas) e `sobrevivente` (declarado sem handler localizado). **Nenhum ramo foi removido**; ainda falta decidir o destino de cada identidade/efeito legado e revisar as tags associadas especificamente a essas cartas antigas, sem confundir isso com a política de combos já aprovada.

A validação sintética não aprova EFP, custo, raridade, teto 32 ou distribuição. Naquele ponto histórico, a auditoria de sobreposição havia enumerado pares e trincas de IDs distintos, mas não simulava partidas completas. A decisão sobre participação/mínimos/precedência foi aprovada e implementada posteriormente; a sequência autorizada atual está no bloco “Estado exato ao encerrar esta entrega” e inclui testes stateful, snapshots, integração e simulação por facção.

## Histórico pré-patch: auditoria de sobreposição, precedência e participação dos combos

> **Histórico do defeito anterior à política aprovada.** Use `card-game-combo-overlap-v0.2.md` para o estado atual.

Documentos: [`card-game-combo-overlap-v0.1.md`](card-game-combo-overlap-v0.1.md) e JSON congelado. O script `scripts/audit-combo-overlap-v0.1.py` é arquivado: só reproduz o baseline em checkout pré-política e recusa execução no código atual. Para runtime vigente, use v0.2.

O script examina o resolvedor real `sistemas/gwent.py::_aplicar_combo_de_cartas()` com 67 unidades do catálogo que possuem tags, excluindo cinco IDs órfãos. Enumera 4.422 ordens de dois modelos distintos e 287.430 sequências ordenadas de três modelos distintos. Não valida um deck completo de 12 cartas, posse, partida, API ou vitória.

Achados objetivos:

- 154/4.422 ordens de pares (3,4826%) têm mais de um combo elegível ao mesmo tempo; correspondem a 77 pares não ordenados e envolvem 15 dos 27 combos. O resolvedor aplica o primeiro na ordem do dicionário e retorna; os demais ficam adiados.
- 11.780/287.430 trincas (4,0984%) ativam pelo menos dois combos diferentes em jogadas sucessivas; 1.088 dessas trincas pertencem à mesma facção.
- Em 8.096 de 11.784 eventos de combo posterior (68,7033%), a carta que recebeu o bônus não contribuiu com nenhuma tag exigida por aquele combo. A causa é que o resolvedor só testa se a carta atual tem qualquer tag não vazia; a condição do combo pode já estar completa no tabuleiro.
- Três combos não têm `minimum`: `cinzas_fornalha`, `vazio_astral` e `eco_convergente`. No catálogo atual, `gwent_unidade_eco` (`Erudito das Pedras Cintilantes`, tags `astral` + `eco`) ativa `eco_convergente` sozinho, embora a descrição cite o Erudito e outra unidade Astral.

Exemplo: `chefe_guardiao_cinzas` + `gwent_unidade_baluarte` completam tanto `cinzas_fornalha` quanto `juramento_erdtree`; o primeiro dispara por precedência. Em seguida `covenant_irmandade_ferro`, que só possui a tag `estandarte`, aciona o `juramento_erdtree` pendente e recebe o bônus individual apesar de não contribuir com `ordem_dourada`.

**Decisão posteriormente aprovada e implementada:** a carta atual precisa contribuir com tag exigida; os 27 combos exigem duas instâncias distintas; `priority` crescente decide a precedência; apenas um combo ativa por jogada; a carta participante atual recebe o bônus individual; `team_bonus` permanece. Consulte `card-game-combo-policy-v0.1.md` e a seção de estado atual no início deste handoff.

A auditoria é reproduzível e não altera o motor. Os detalhes, linhas, método, limitações e decisões estão no relatório completo.

## Regra permanente de pacote de continuidade

O usuário determinou que **toda entrega futura deste trabalho deve atualizar um único arquivo `.zip`** contendo os materiais necessários para outro chat/agente assumir sem depender do histórico da conversa. Esta é uma exigência recorrente, não uma ação opcional.

Em cada nova etapa que produza ou altere documentação, código, dados, testes ou decisões:

1. Atualizar este handoff e os documentos técnicos afetados.
2. Incluir no mesmo pacote o projeto-fonte disponível e todos os documentos de continuidade/auditoria, mantendo caminhos relativos.
3. Incluir um índice de leitura e um manifesto com o estado da entrega, arquivos adicionados/alterados, validações e limitações conhecidas.
4. Recriar o ZIP completo; não entregar documentos avulsos como substitutos do pacote.
5. Verificar a integridade do ZIP, a presença de todos os documentos e a ausência de segredos, arquivos temporários e artefatos locais desnecessários antes de fornecer o link.
6. Informar claramente se algum arquivo necessário não estava disponível para inclusão.

O arquivo ZIP mais recente deve ser tratado como o pacote de continuidade de referência da etapa atual. O handoff dentro do próprio pacote deve indicar o estado exato e a ordem de leitura.

## Regras de operação para a próxima IA

- Comece lendo este arquivo e `card-game-mapping-audit.md`.
- Não assumir que o código executável corresponde aos textos de descrição.
- Não apagar IDs de carta já persistidos sem migração/alias; verificar `cartas_colecao`, `cartas_exemplares`, `cartas_gwent_decks`, `cartas_gwent_matches`, Ateliê e artes pessoais.
- Não confiar em `HABILIDADES_UNIDADE_IMPLEMENTADAS` como prova suficiente de execução; conferir o caminho de chamada e simular partida.
- Não usar a lore como texto mecânico. A descrição mecânica deve derivar do mesmo `effect_id` que o motor executa.
- Não editar arte oficial integral como se fosse um layer; o renderer devolve o arquivo completo sem overlays.
- Não usar a tabela de raridade antiga como a fórmula nova; preservar os valores históricos até existir migração aprovada.
- Não tratar `docs/CARD_GAME_REDESIGN.md` como fonte de verdade sem conciliar com o motor real.
- Nunca atualizar apenas frontend para uma regra de deck/custo: validação autoritativa fica no servidor.

## Histórico de alterações desta continuidade

| Data | Arquivo | Trecho/campo | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|---|
| 2026-11-27 | `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PACOTE-MANIFESTO.md` | Quadro de completude da Regra 8 e aviso de entrada para chat novo | Tornada explícita a finalidade de handoff do pacote, adicionada mensagem inicial sugerida e avaliada a cobertura dos quatro blocos com pendências/defasagens. | Evitar que um novo chat trate o pacote como 100% completo ou confunda propostas com regras aprovadas. | Sem impacto no runtime; clarifica limites e ordem de leitura. | Conteúdo comparado com auditoria, spec v0.1, matriz e inventário do ZIP; revisão documental. |
| 2026-11-27 | `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md` | Regra permanente de entrega | Registrada a exigência do usuário de manter todo o contexto necessário em um único ZIP atualizado a cada nova etapa, com índice, manifesto e verificação de integridade. | Garantir continuidade entre chats sem depender do histórico da conversa. | Nenhum impacto funcional; altera somente o processo documental/de entrega. | Regra incorporada ao handoff e incluída no pacote de continuidade. |
| 2026-11-27 | `docs/card-game-mapping-audit.md` | Novo documento | Criado inventário estático completo, incluindo catálogo de habilidades, identidades, combos, líderes, relíquias, dados, APIs e falhas encontradas. | Registrar o estado anterior antes de qualquer remoção. | Nenhum impacto funcional; referência técnica para a reconstrução. | Catálogos importados e contagens conferidas; sem teste de partida real. |
| 2026-11-27 | `docs/card-game-handoff.md` | Novo documento | Criado handoff operacional com regras confirmadas, estado, prioridades e próximos passos. | Permitir continuidade entre chats/agentes. | Nenhum impacto funcional. | Revisão estática do conteúdo e links relativos. |
| 2026-11-27 | `docs/card-game-card-traceability.md`, `.csv`, `.json` | Novos documentos | Criada matriz individual do catálogo runtime, incluindo efeitos, identidade, tags, custo, texto preparado e cobertura visual. | Permitir decidir carta por carta o que preservar, corrigir ou remover. | Nenhum impacto funcional; artefatos de auditoria para a reconstrução. | Import do catálogo e do motor; comparação estática de campos e mapeamentos; sem partidas reais/DB de produção. |
| 2026-11-27 | `docs/card-game-mapping-audit.md` | Seção 12 — Matriz de rastreabilidade individual | Adicionadas referências aos três formatos da matriz e os achados atualizados da auditoria carta por carta. | Manter o baseline técnico conectado à evidência individual. | Nenhum impacto funcional. | Conferência das 137 cartas e referências relativas. |
| 2026-11-27 | `docs/card-game-handoff.md` | Seção Matriz e Estado exato | Atualizados o ponto de continuidade, achados quantitativos, dependências e estado da implementação. | Garantir handoff atualizado após a nova etapa. | Nenhum impacto funcional. | Revisão dos links e cruzamento com a matriz JSON/CSV/Markdown. |

| 2026-11-27 | `docs/scripts/build-effect-source-map-v0.1.py`, `docs/card-game-effect-source-map-v0.1.json` | Novo índice AST de efeitos | Ligados 59 IDs genéricos, 22 identidades, 10 líderes e 27 combos às funções/linhas/condições do código. | Evitar inferir mecânica apenas de nome/descrição; localizar o handler exato. | Somente diagnóstico documental; nenhum módulo de runtime alterado. | Geração repetida; 56 handlers diretos, 2 hooks, `sobrevivente` sem handler, 22 identidades e 10 líderes com referências. |
| 2026-11-27 | `docs/card-game-efp-methodology-v0.2.md` | Novo método de avaliação | Substituída a recomendação de pontuação fixa por decomposição de vetor mecânico, cenários estratificados e valor esperado em simulações. | Pesos da v0.1 não têm calibração empírica. | Sem alteração funcional; metodologia permanece proposta não aprovada. | Revisão cruzada com resolver, handlers, smoke e frequência de combos. |
| 2026-11-27 | `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PACOTE-MANIFESTO.md`, `docs/card-game-balance-validation-v0.1.md` | Estado, ordem e próximos passos | Incluídos mapa de fonte, método EFP v0.2 e pendências de asserts/simulação. | Manter novo chat no estágio correto e evitar adoção prematura de pontuações. | Apenas documentação. | Conferência dos links relativos, contagens e saídas geradas. |

| 2026-11-27 | `docs/scripts/assert-card-effect-behavior-v0.1.py`, `docs/card-game-effect-behavior-assertions-v0.1.json` | Primeira bateria de comportamento | Adicionadas 13 asserções explícitas para buffs, debuffs, compra, escudo, ressurreição, movimento, invocação, remoção, clima/estado e identidade. | Verificar resultado esperado, não apenas ausência de exceção. | Ferramenta diagnóstica apenas; nenhuma alteração de runtime. | 13/13 passaram com raridade Comum e fixtures sintéticos. |
| 2026-11-27 | `docs/scripts/assert-leader-effects-v0.1.py`, `docs/card-game-leader-assertions-v0.1.json` | Novo harness; `state_for()`, `activate()`, dez handlers e condições de falha | Adicionadas 22 asserções: dez positivas (todos os líderes) e doze negativas/limite. | Completar a cobertura controlada da ação de líder que não estava nos testes anteriores. | Diagnóstico apenas; nenhum impacto no runtime. | 22/22 aprovadas por `aplicar_jogada(action="leader")` em fixtures sintéticos. |
| 2026-11-27 | `docs/scripts/summarize-card-game-behavior-v0.2.py`, `docs/card-game-behavior-validation-v0.2.json`, `.md` | Agregador e relatório de seis suites | Consolidadas 132 asserts, resultados, limitações, mapa dos 28 ramos antigos e próximos passos. | Criar um ponto único e reprodutível de leitura para o próximo chat. | Apenas documentação e ferramentas de diagnóstico. | Nove scripts executados novamente; 132/132 aprovados; agregador verifica presença/contagem/status. |
| 2026-11-27 | `docs/scripts/assert-combo-and-faction-passive-v0.1.py`, `docs/card-game-combo-faction-assertions-v0.1.json` | Novo teste de `_aplicar_combo_de_cartas()`, `aplicar_jogada()` e `_resolve_round()` | Incluídos 87 cenários: todos os 27 combos com um par ativador, requisito incompleto e bloqueio de repetição; quatro passivas de facção; carta sem tags; exclusão de especial. | Completar a validação controlada dos combos e passivas antes da simulação competitiva. | Apenas ferramenta/JSON diagnóstico; nenhum impacto no runtime. | 87/87 passaram. Cada combo testado com um par ativador concreto; outras combinações e precedências sobrepostas ainda não exaustivas. |
| 2026-11-27 | `docs/scripts/summarize-card-game-behavior-v0.2.py`, `docs/card-game-behavior-validation-v0.2.md/.json` | Agregador ampliado de seis para sete suites | Total atualizado de 132 para 219 cenários; novo bloco detalha combos e passivas. | Evitar handoff defasado após nova bateria. | Apenas documentação e ferramentas. | Sete relatórios JSON validados; 219/219 aprovados, zero falhas. |
| 2026-11-27 | `docs/card-game-stale-identity-disposition-v0.1.md`, `.json`, `docs/scripts/audit-stale-identity-branches-v0.1.py` | Classificação de 28 ramos sem associação ativa | Separados 18 ramos filtrados pelo V18, quatro campos legados e seis ramos V75; separados também `gloria`/`sobrevivente`. | Não classificar código como morto sem identificar carta, tag e dependência; evitar exclusão prematura. | Nenhuma remoção nem alteração funcional. | Auditoria AST/runtime: 28 = 18+4+6; três cartas com `gloria`; `sobrevivente` sem handler. |
| 2026-11-27 | `docs/card-game-handoff.md`, `README-PACOTE-CONTINUIDADE.md`, `PACOTE-MANIFESTO.md`, `card-game-mapping-audit.md`, `card-game-balance-validation-v0.1.md`, `card-game-efp-methodology-v0.2.md` | Estado, ordem de leitura, completude e próximos passos | Atualizada a fase de 13 asserts para seis suites/132 asserts; incluídos testes de líder e disposição dos ramos antigos. | Não deixar o próximo chat repetir trabalho concluído nem interpretar asserts como prova de balanceamento. | Apenas documentação. | Links e contagens cruzados com relatórios individuais e agregador. |

## Estado exato ao encerrar esta entrega — integração stateful v0.1

- **Concluído anteriormente:** política de combos aprovada e implementada em `sistemas/gwent.py`; 27 combos com `minimum: 2` e `priority` único; bônus individual limitado à carta participante; `team_bonus` preservado. Oito suites anteriores: 251/251 asserts; auditoria de 4.422 pares e 287.430 trincas, zero ativações solo e 2.582/2.582 eventos posteriores com carta participante.
- **Concluído nesta etapa:** 12/12 cenários stateful; quatro partidas em memória de três rodadas cobrindo as quatro facções; round-trip JSON em ações/resoluções; 137/137 modelos preparados com contrato de payload; combo real por jogadas; líder + especial climático + reset; relíquia de uso único; clima manual de uso único; defaults de snapshot legado; imutabilidade da entrada em ação rejeitada; `SCHEMA` + `SCHEMA_CARTAS` reais executados em SQLite `:memory:` e persistência `state_json` verificada; contrato bot/site inspecionado estaticamente; `compileall` e `node --check` aprovados.
- **Não confundir com integração de produção:** os quatro jogos stateful usam unidades sintéticas para controlar resultado; o teste SQLite usa DDL real mas conexão `:memory:` e não o wrapper `Database`. O HTTP foi analisado estaticamente, não despachado. `discord.py` e `aiosqlite` não estão instalados no ambiente de análise, impedindo import real do bot/wrapper nesta etapa.
- **Runtime funcional:** nenhuma mudança nesta etapa. A última mudança funcional continua em `sistemas/gwent.py` na implementação da política de combos. Nenhum schema, endpoint, frontend ou imagem foi alterado.
- **Pendente imediato:** obter ambiente com `discord.py==2.7.1` e `aiosqlite==0.22.1` (ou wheels locais; tentativa de instalação via pip bloqueada por DNS nesta sessão); executar testes reais de handlers HTTP; fluxo de convite e aceitação; criação solo/IA e fallback; persistência via classe `Database`; autenticação e respostas API; browser para catálogo, detalhes e jogadas; arte/R2.
- **Pendente de reconstrução:** destino de habilidades/identidades antigas, corrigir tags e facções apontadas, novo catálogo, lore, poder 1–15, pelo menos 30% de cartas puras, distribuição determinística, EFP/custo/raridade e orçamento de deck. Valores de `card-game-balance-spec-v0.1.md` continuam propostas não aprovadas e fora do runtime.
- **Dependências ausentes:** DB de produção, credenciais/configuração publicada, `discord.py` e `aiosqlite` neste ambiente de análise, estado R2 e artes aprovadas publicadas.
- **Referência de continuidade:** ler `README-PACOTE-CONTINUIDADE.md`, depois este handoff, `card-game-match-snapshot-integration-v0.1.md`, `card-game-behavior-validation-v0.3.md` e a política de combos. O ZIP mestre é atualizado a cada etapa.

## Histórico de alterações — etapa de especificação v0.1 (2026-11-27)

| Arquivo | Trecho/campo | Alteração | Motivo | Impacto/validação |
|---|---|---|---|---|
| `docs/card-game-card-traceability.json` | 16 registros; `status_resolucao`, `efeitos_efetivos_listados`, `divergencia_exibicao_vs_execucao`, novo `habilidade_generica_suprimida_por_identidade` | Corrigido para indicar supressão do genérico e execução única da identidade. | O resolver define `skill=""` quando há identidade ativa. | Somente documentação/dados de auditoria; origem conferida em `sistemas/gwent.py:1472` e chamada de identidade em `:1863`. |
| `docs/card-game-card-traceability.csv` | Todas as linhas/colunas | Regenerado do JSON corrigido. | Manter formatos tabular e JSON idênticos. | CSV conferido por contagem de 137 linhas de dados. |
| `docs/card-game-card-traceability.md` | Convenções, inconsistências e 16 fichas | Removida a alegação de dupla execução e documentada ambiguidade do payload. | Corrigir conclusão técnica anterior. | Comparação estática com o resolver e `preparar_carta()`. |
| `docs/card-game-mapping-audit.md` | Nova seção de retificação | Adicionada explicação de `skill=""` e do payload com ID genérico + texto de identidade. | Preservar o histórico sem ocultar a correção. | Nenhum impacto funcional. |
| `docs/card-game-balance-spec-v0.1.md` | Novo documento integral | Formalizada proposta de EFP, pureza, custo, orçamento (inicialmente 60, depois revisado para 32 por amostragem), raridade, distribuição determinística, schema e facções. | Estabelecer critérios mensuráveis antes da reconstrução. | Proposta não aprovada; pesos e limiares não testados em simulação. |
| `docs/card-game-effect-score-catalog.json` | Novo catálogo estruturado | Adicionados 59 metadados de habilidade, 22 identidades, 27 combos e 10 líderes, com scores estimados/estados. | Permitir revisão efeito a efeito sem confundir metadados com regras já implementadas. | EFP é hipótese; `null` marca definição sem handler/associação validada. |
| `docs/card-game-handoff.md` | Estado, links, achados e histórico | Corrigida conclusão de identidade e adicionada proposta v0.1/ordem de continuidade. | Próxima IA precisa receber contexto correto e status explícito. | Nenhum impacto funcional. |
| `docs/card-game-balance-spec-v0.1.md`, `docs/card-game-deck-cost-sampling-v0.1.json` | Seção 5 e teto experimental | Teto 60 rejeitado como permissivo; proposta passou a 32 após amostra reproduzível de 100.000 decks. | 100% dos decks amostrados ficaram ≤60 e só 56,3% ≤32. | Amostragem aleatória, não simulação de resultados de partida; orçamento permanece não aprovado. |

### Próximo passo autorizado na etapa v0.1 (histórico; concluído pela validação exploratória)

A instrução anterior para validar a proposta foi cumprida parcialmente sem alterar o runtime. Os achados e correções metodológicas estão em `card-game-balance-validation-v0.1.md`. A próxima etapa agora é construir EFP com memória de cálculo e testes por efeito; simulação competitiva ainda falta.


### Resultado histórico da amostragem de custo v0.1 (superado; não usar para aprovar orçamento)

- 128 modelos pontuáveis: 101 unidades e 27 especiais; 9 unidades com habilidade não resolvida foram excluídas da amostra.
- 100.000 decks aleatórios, 12 cartas únicas, 8–12 unidades, 0–4 especiais, seed 42.
- Média/mediana de custo: 32,08 / 32; p90 = 36.
- Teto 32: 56,3% dos decks amostrados caberiam; teto 36: 91,6%; teto 60: 100%.
- Raridade calculada nos 128 modelos pontuáveis: 8 Comuns, 36 Raras, 45 Épicas, 32 Lendárias, 7 Míticas, 0 Primordiais e 0 Singulares. Resultado estimado pelo score v0.1, sem distribuição de drop.
- O teto 32 substitui 60 como hipótese experimental. Amostra não simula jogabilidade, posse, facção, líder ou relíquia e não comprova equilíbrio.



## Histórico de alterações — validação exploratória v0.1 (2026-11-27)

| Arquivo | Trecho/função/campo | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/card-game-balance-validation-v0.1.md` | Novo relatório | Registradas as falhas de método v0.1, amostragem de custo v0.2, frequência de 27 combos, auditoria de handlers, testes de fumaça, limites de EFP e próximos passos. | Criar evidência para não aprovar parâmetros não sustentados. | Somente documentação. | Cruzado com scripts/JSON gerados e código estático; nenhuma regra do jogo alterada. |
| `docs/scripts/validate-card-effect-smoke-v0.1.py` | `fixture()`, `run_skill()` e agregações | Carta reserva evita auto-pass; condições de `encadeamento` e `sangue_frio` corrigidas; status não declara cobertura completa de ramo. | Corrigir fixtures e precisão do diagnóstico. | Ferramenta em `docs/scripts/`, sem chamada pelo runtime. | 59 ações sem exceção; `encadeamento` +2, `sangue_frio` +2; hooks verificados separadamente; 22/22 identidades com evento. |
| `docs/card-game-effect-runtime-smoke-v0.1.json` | Resultado regenerado | Atualizadas contagens e detalhes dos fixtures. | Refletir teste corrigido. | Evidência documental. | Script executado com sucesso. |
| `docs/scripts/audit-effect-handler-coverage-v0.1.py` | Novo script AST | Cruzamento estático de `HABILIDADES`, handlers genéricos, hooks, identidade e tags. | Encontrar ramos antigos e ligações ausentes. | Ferramenta diagnóstica, não altera runtime. | 59 genéricas, 58 com referência (1 sem), 22 identidades ativas (22 com ramo), 28 ramos antigos, 27 combos sem tag impossível. |
| `docs/card-game-handler-coverage-v0.1.json` | Novo relatório | Saída estruturada da auditoria estática. | Facilitar continuação automatizada. | Somente docs. | Reproduzido pelo script AST. |
| `docs/scripts/sample-deck-cost-v0.2.py` / `docs/card-game-deck-cost-sampling-v0.2.json` | Cálculo e hipóteses | Removida pontuação parcial de combo; adicionados cenários com/sem relíquia e `leader_load`; limitações atualizadas para reconhecer medição de combo separada. | Corrigir método da amostragem v0.1. | Estimativa analítica, não custo em produção. | Reexecução com seed 42 idêntica: 68,8% aceitação em 32 sem relíquia; 45,4% com relíquia. |
| `docs/scripts/sample-deck-cost-v0.1.py` | Docstring | Marcado como histórico/superado, preservando cálculo antigo para auditabilidade. | Evitar uso equivocado da fórmula antiga. | Nenhum impacto no runtime. | Inspeção estática. |
| `docs/scripts/simulate-combo-activation-v0.1.py` / `docs/card-game-combo-activation-v0.1.json` | Novo diagnóstico | Medida de ativação potencial/real dos 27 combos chamando o resolvedor atual. | Não imputar EFP por tag parcial; obter frequência preliminar realista. | Não altera jogo e não atribui EFP aos combos. | Segunda execução com seed 42 idêntica; 57,19% de decks com ao menos um combo. |
| `docs/card-game-balance-spec-v0.1.md` | Nota de revisão | Marcada a amostragem v0.1 como superada e teto 32 como sem sustentação/aprovação. | Evitar confundir dado antigo com decisão. | Apenas documentação. | Conferido com relatório v0.2. |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem e histórico | Atualizados para próxima fase EFP/testes/simulação e incluídos novos materiais. | Permitir que novo chat continue sem consultar esta conversa. | Apenas docs. | Links relativos, contagens e hashes revisados. |


## Histórico de alterações — implementação da política oficial de combos (2026-11-27)

| Arquivo | Trecho/função/campo | Antes | Depois | Motivo | Impacto | Validação |
|---|---|---|---|---|---|---|
| `sistemas/gwent.py` | `SYNERGY_COMBOS` | 27 definições; três sem mínimo explícito; nenhuma prioridade própria | Todos os 27 têm `minimum: 2` e `priority` inteiro único de 10 a 270, em intervalos de dez | Formalizar duas unidades distintas e precedência determinística aprovada | Corrige combos solo e remove dependência da ordem do dicionário | Teste de contrato: 27 mínimos e 27 prioridades únicos |
| `sistemas/gwent.py` | `_aplicar_combo_de_cartas()` | Uma carta com qualquer tag podia receber combo já elegível; mínimo era opcional; primeira entrada do dict vencia | Exige tag atual intersectando tags do combo; conta instâncias distintas; ordena por priority ascendente; aplica um combo por chamada | Garantir participação efetiva e prioridade estável | Muda resolução de jogadas futuras; mantém `synergy_used`, `bonus`, `team_bonus` e reset de rodada | 32/32 regressões; 87/87 combo/facção; auditoria pós-patch |
| `sistemas/gwent.py` | Descrições em `SYNERGY_COMBOS` | Algumas diziam “carta que completa”; três descrições não deixavam o mínimo explícito | Texto diz “carta participante que ativa” e explicita cartas distintas nos três casos | Alinhar texto ao alvo real do bônus e mínimo | Texto de combo retornado pelo motor é atualizado; imagens integrais aprovadas não são regeneradas | Revisão estática das 27 definições e teste do contrato |
| `docs/scripts/assert-combo-policy-v0.1.py`, `docs/card-game-combo-policy-assertions-v0.1.json`, `docs/card-game-combo-policy-v0.1.md` | Nova suite e especificação oficial | Inexistentes | Adicionados contrato, prioridades, exemplos, impacto e 32 asserts, incluindo caminho público `aplicar_jogada(action="play")` | Tornar a política aprovada reproduzível | Diagnóstico/documentação, não chamado no runtime | 32/32 passaram |
| `docs/scripts/audit-combo-overlap-v0.2.py`, `docs/card-game-combo-overlap-v0.2.json/.md` | Nova auditoria pós-política | Relatório antigo era baseline pré-patch | Enumerados pares/trincas no resolver atualizado | Medir regressões e estado após correção | Diagnóstico apenas; sem mudança adicional no motor | 4.422 pares, 287.430 trincas; 0 solo; 2.582 eventos posteriores todos participantes |
| `docs/scripts/summarize-card-game-behavior-v0.3.py`, `docs/card-game-behavior-validation-v0.3.json/.md` | Novo agregador e relatório | v0.2 totalizava 219 asserts em sete suites antes da nova política | v0.3 inclui oitava suite e total de 251 asserts | Um resultado único pós-patch | Handoff tem contagem reprodutível | 8 suites, 251/251 aprovados |
| `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md`, `docs/card-game-mapping-audit.md`, `docs/card-game-balance-validation-v0.1.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem de leitura, pendências e histórico | Diziam que decisão de combo era pendente e nenhuma alteração funcional existia | Registram decisão aprovada, patch, compatibilidade e próximos passos atuais | Evitar handoff incorreto ao chat novo | Documentação de continuidade | Links/contagens conferidos com scripts e JSONs |

## Histórico de alterações — auditoria de combos sobrepostos (2026-11-27)

| Arquivo | Função/campo/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/audit-combo-overlap-v0.1.py` | Script arquivado de baseline pré-política | Rodava contra o resolvedor original antes da aprovação; agora o runtime mudou | Guardado com fail-fast no checkout pós-política; só pode ser reproduzido em checkout pré-política | Evitar sobrescrever ou confundir o relatório histórico | Ferramenta documental apenas; não é importada pelo runtime | JSON/Markdown v0.1 congelados; auditoria atual é v0.2 |
| `docs/scripts/build-effect-source-map-v0.1.py` | Gerador arquivado do mapa AST pré-política | Gerava o índice histórico a partir do runtime daquele baseline | Guardado com fail-fast no checkout pós-política; mapa atual é v0.2 | Evitar sobrescrever as referências históricas e misturar linhas/branches de versões distintas | Ferramenta documental apenas | JSON v0.1 congelado; script/JSON v0.2 são a fonte atual |
| `docs/card-game-combo-overlap-v0.1.json`, `.md` | Novos relatórios | Documentados combos simultaneamente elegíveis, ativações diferidas, 8.096/11.784 eventos sem contribuição da carta atual, `eco_convergente` solo e decisões de design pendentes. | Tornar explícito o comportamento escondido do resolver antes de qualquer alteração. | Apenas evidência e documentação; nenhuma regra de partida alterada. | JSON regenerado pelo script; exemplos conferidos com o catálogo e o resolver em `sistemas/gwent.py:916–946`. |
| `docs/card-game-handoff.md`, `README-PACOTE-CONTINUIDADE.md`, `PACOTE-MANIFESTO.md`, `card-game-mapping-audit.md`, `card-game-balance-validation-v0.1.md`, `card-game-behavior-validation-v0.2.md`, `card-game-efp-methodology-v0.2.md` | Estado, ordem de leitura, riscos e próximos passos | Atualizadas referências e pendências para exigir decisão explícita sobre participação, mínimo, precedência e alvo dos combos. | Evitar simular EFP/custo com semântica de combo ambígua. | Documentação/handoff somente. | Links, métricas e limitações cruzados com o JSON de auditoria. |


## Histórico de alterações — mapa estático de contratos HTTP v0.1 (2026-11-27)

| Arquivo | Função/campo/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/audit-gwent-http-contracts-v0.1.py` | AST de registros de rota, funções handler, `preparar_carta()` e literais de `site/app.js` | Criado/ajustado gerador para inventariar as 12 rotas Gwent, os campos de requisição, sinais de autenticação/origem, chamadas DB/motor e sinais frontend; corrigido o acesso AST para reconhecer funções referenciadas por nome. | Fechar a lacuna entre mapa geral do sistema e contratos concretos entre bot, UI, motor e banco, sem fingir execução HTTP. | Apenas ferramenta documental; não é importada pelo runtime. | Script reproduz 12 rotas; identifica ausência de orçamento e ausência de `custo` no retorno preparado. |
| `docs/card-game-http-contract-map-v0.1.md/.json` | Novo relatório de contratos | Registradas as 12 rotas, linhas/handlers, campos do frontend, validações de deck, fluxo de convite/solo/ação e limites da análise estática. | Documentar as conexões exatas e a pendência real de integração. | Handoff/diagnóstico; sem impacto em APIs ou partidas. | Gerado pelo script e revisado contra `bot.py`, `site/app.js` e `sistemas/gwent.py`. |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem de leitura, mapa e histórico | Incluída a revisão HTTP estática como estado mais recente; etapa stateful preservada como referência anterior; registrada a perda do campo `custo` em `preparar_carta()` e falta de enforcement do orçamento no deck save. | Impedir que próximo chat confunda análise estática com integração executada e antecipar o contrato a corrigir quando as regras de custo forem aprovadas. | Apenas documentação e scripts em `docs/`; runtime intocado. | 12 rotas reproduzidas; testes comportamentais/stateful reexecutados separadamente. |

## Histórico de alterações — validação stateful v0.1 (2026-11-27)

| Arquivo | Trecho/função/campo | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/assert-full-match-stateful-v0.1.py` | Nova suíte: `novo_estado()`, `aplicar_jogada()`, `_resolve_round()`, `preparar_carta()`, snapshot JSON e DDL SQLite | Criados 12 cenários stateful para quatro jogos de três rodadas, catálogo 137 modelos, combo normal, líder/especial/clima, relíquia, clima manual, snapshot legado, ação rejeitada, SQLite e contrato estático bot/site. | A suíte anterior testava principalmente funções/condições isoladas; era necessário validar transições, serialização e o fluxo em várias rodadas. | Somente ferramenta de teste; nenhum import/call no runtime. | 12/12 cenários; relatório JSON associado. |
| `docs/card-game-match-snapshot-integration-v0.1.md/.json` | Novo relatório | Registrados escopo, evidências, comandos de reprodução e limitações, incluindo ausência de `discord.py`/`aiosqlite` no ambiente. | Evitar afirmar integração HTTP/produção que não foi executada. | Handoff e diagnóstico. | JSON gerado pelo runner; 12/12. |
| `docs/card-game-handoff.md` | Estado atual, tabela da Regra 8, estado exato e histórico | Atualizado de testes sintéticos isolados para 251 asserts + 12 cenários stateful separados; próximos passos HTTP explicitados. | Impedir que novo chat repita validação ou trate análise estática como integração executada. | Somente documentação. | Links e resultados cruzados com relatório. |
| `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PACOTE-MANIFESTO.md`, `docs/card-game-mapping-audit.md` | Ordem de leitura, estado, mapa e manifesto | Incluídos testes stateful, resultados, tentativa de instalação de dependências e bloqueio de DNS/produção. | Manter pacote autossuficiente e atual. | Somente documentação. | Referências, contagens e validações conferidas. |
