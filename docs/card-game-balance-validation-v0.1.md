# Validação exploratória do balanceamento v0.1

> **STATUS: RELATÓRIO EXPLORATÓRIO HISTÓRICO; PROPOSTA DE BALANCEAMENTO v0.1 NÃO APROVADA.** O relatório começou como diagnóstico do runtime anterior à política de combos. Uma atualização no final registra a regra de combos aprovada e implementada posteriormente. As métricas de custo/EFP permanecem exploratórias; não provam equilíbrio competitivo.

Data da revisão: 2026-11-27  
Baseline: ZIP-fonte `soulsbo-main(1).zip`, incluído no pacote mestre.  
Arquivos de evidência: `card-game-deck-cost-sampling-v0.2.json`, `card-game-combo-activation-v0.1.json`, `card-game-effect-runtime-smoke-v0.1.json` e `card-game-handler-coverage-v0.1.json`.

## 1. Conclusão executiva

A proposta quantitativa v0.1 **não deve ser aprovada nem aplicada ao jogo ainda**. Foram identificados três bloqueios:

1. A primeira amostragem de custo v0.1 atribuiu pontuação parcial de combo a uma carta sempre que ela possuía apenas uma das tags exigidas (`intersection`), mesmo quando o combo exigia todas as tags e eventualmente dois participantes. Também somou apenas as 12 cartas, embora a especificação dissesse que o orçamento incluiria relíquia e carga do líder.
2. A escala EFP tem pontuações agregadas subjetivas, sem memória de cálculo por efeito. Os testes de fumaça observam mudanças em estados controlados, mas não medem valor esperado em partidas, probabilidade real de condição, nem impacto em taxa de vitória.
3. A distribuição real de combos mostra frequência muito desigual, e a primeira simulação usa ordem aleatória e presume que todas as 10 cartas iniciais são jogadas na mesma rodada. Isso é útil para diagnosticar o código, mas não é comportamento competitivo.

A revisão v0.2 corrige a amostragem de custo: remove o crédito de combos por tag parcial e separa cenários com/sem relíquia equipada, acrescentando o custo experimental do líder. O teto 32 continua sem validação competitiva: aceita 68,8% dos decks aleatórios sem relíquia e 45,4% com relíquia equipada, sob as hipóteses descritas abaixo.

Na revisão exploratória original, nenhuma carta, habilidade, tabela, API, regra de partida, imagem ou arquivo funcional do runtime foi alterado. Posteriormente, a política de combos foi aprovada e aplicada; consulte a atualização final deste relatório.

## 2. Correção metodológica da amostragem de custo

### 2.1. Problemas da amostragem v0.1

O script histórico `scripts/sample-deck-cost-v0.1.py` calcula `combo_score` quando `tags.intersection(required_tags)` não está vazio. Isso concede EFP de combo a uma carta que pode ter somente parte das tags necessárias. O motor real, em `sistemas/gwent.py::_aplicar_combo_de_cartas()`, exige que **todas** as tags requeridas estejam no conjunto de tags do campo + carta atual e, quando definido, que o mínimo de participantes seja atingido.

Além disso, a amostragem v0.1 somava somente o custo das 12 cartas. A especificação dizia que o teto 32 incluiria também a relíquia equipada e `leader_load`. O endpoint atual mantém relíquia separada das 12 posições do deck; portanto, quando equipada, deve ser modelada como custo adicional, não como slot substituto. A escolha de `leader_load` é uma hipótese nova da proposta e ainda não é regra do backend.

Os resultados v0.1 (`média 32,08`, `mediana 32`, `56,3%` abaixo de 32) ficam preservados para histórico, mas **não devem mais ser usados para justificar o teto**.

### 2.2. Método revisto v0.2

Script: `scripts/sample-deck-cost-v0.2.py`. Saída: `card-game-deck-cost-sampling-v0.2.json`.

- 100.000 amostras por cenário, seed 42; resultado reproduzido exatamente em uma segunda execução.
- 12 modelos únicos por deck, entre 8 e 12 unidades e entre 0 e 4 especiais.
- 128 modelos com pontuação disponível: 101 unidades e 27 especiais. Nove unidades com IDs de habilidade sem pontuação/canonicalização foram excluídas.
- Combos não são incorporados ao custo individual da carta nesta versão. A frequência de combos passou a ser estimada em relatório separado; ainda falta converter frequência + valor de tabuleiro em uma contribuição EFP defensável.
- O custo da unidade usa `clamp(ceil((P + 2E) / 3.5), 1, 10)`; especial usa `P=0`.
- `leader_load` usa `clamp(ceil(E_leader / 2), 1, 5)`, hipótese não aprovada.
- Para o líder, o script escolhe uniformemente entre líderes da facção que empata ou tem maior número de unidades no deck. A escolha real do jogador e sua estratégia não são modeladas.
- Cenário com relíquia: seleciona uniformemente uma das seis relíquias e exclui essa mesma relíquia dos 12 slots do deck.

### 2.3. Resultados v0.2

| Métrica | Sem relíquia equipada | Com relíquia equipada |
|---|---:|---:|
| Média de custo total | 31,14 | 32,96 |
| Mediana | 31 | 33 |
| Mínimo–máximo | 21–46 | 23–47 |
| P10 | 27 | 29 |
| P25 | 29 | 31 |
| P75 | 33 | 35 |
| P90 | 35 | 37 |
| P95 | 36 | 38 |
| Decks que cabem em 32 | **68,8%** | **45,4%** |
| Decks que cabem em 34 | 86,8% | 70,7% |
| Decks que cabem em 36 | 95,8% | 87,9% |
| Decks que cabem em 38 | 99,0% | 96,2% |

**Interpretação:** com o conjunto de hipóteses atual, teto 32 produz taxas de aceitação materialmente diferentes conforme o jogador equipe ou não uma relíquia. Isso impede tratar 32 como um valor neutro. Antes de aprová-lo, é necessário definir a taxa de aceitação desejada, se relíquia entra no orçamento, se líder realmente recebe carga adicional e se esses pesos EFP/custo refletem valor de jogo.

### 2.4. Cobertura incompleta e viés de facção

Os nove modelos excluídos são:

`luterano_cruzado`, `luterano_bispo`, `luterano_anjo`, `luterano_papa`, `luterano_pastor`, `luterano_mistico`, `luterano_profeta`, `luterano_vigia`, `luterano_anjo2`.

A distribuição das 101 unidades pontuáveis da amostra é: Ordem Áurea 36, Lua Negra 34, Véu Carmesim 27 e Os Esquecidos 4. No catálogo completo há 110 unidades; os seis possíveis erros de facção da expansão dos Esquecidos ainda não foram corrigidos. A amostra não representa a composição final pretendida das facções.

## 3. Frequência de ativação dos 27 combos

Script: `scripts/simulate-combo-activation-v0.1.py`. Saída: `card-game-combo-activation-v0.1.json`.

Método: 100.000 decks aleatórios, seed 42, 12 modelos únicos, 8–12 unidades, 0–4 especiais; mão inicial de 10; todas as dez cartas são assumidas jogadas na mesma rodada em ordem aleatória. O script chama o resolvedor real `sistemas.gwent._aplicar_combo_de_cartas()`, respeitando a regra de um combo por jogada e o uso de cada combo uma vez por jogador/rodada.

### 3.1. Resultado no nível do deck

- 57,19% dos decks amostrados ativaram pelo menos um combo.
- Média de combos potencialmente disponíveis por mão inicial: 1,052.
- Média de combos efetivamente ativados na ordem aleatória: 0,956.
- Número efetivo por deck: mediana 1; P90 2; P95 3; máximo observado 6.
- A diferença entre combo potencial e ativado decorre principalmente da prioridade do primeiro combo elegível e da regra de um único combo ativado por jogada.

### 3.2. Resultado por combo

| Combo | Potencial na mão | Ativação em ordem aleatória | Ativação dado potencial | Bônus da carta | Bônus de equipe |
|---|---:|---:|---:|---:|---:|
| Aliança da Árvore Áurea (`cinzas_fornalha`) | 2.84% | 2.84% | 100.00% | +2 | +0 |
| Caçada da Faca Negra (`veu_sombrio`) | 2.90% | 2.90% | 100.00% | +2 | +0 |
| Alinhamento Astral (`vazio_astral`) | 2.35% | 2.35% | 100.00% | +2 | +0 |
| Maré Abissal (`mare_abissal`) | 0.46% | 0.46% | 100.00% | +2 | +0 |
| Juramento de Leyndell (`juramento_estandarte`) | 0.50% | 0.49% | 97.60% | +1 | +1 |
| Dança da Lua Negra (`passos_duas_luas`) | 3.01% | 2.98% | 98.94% | +2 | +0 |
| Eco das Pedras Cintilantes (`eco_convergente`) | 9.41% | 9.31% | 98.94% | +2 | +0 |
| Chamas do Monte Gelmir (`chama_dupla`) | 0.51% | 0.51% | 100.00% | +2 | +0 |
| Defesa de Leyndell (`muralha_inabalavel`) | 1.58% | 1.58% | 100.00% | +2 | +1 |
| Banquete de Sangue (`banquete_guerra`) | 0.53% | 0.53% | 100.00% | +3 | +0 |
| Procissão dos que Vivem na Morte (`procissao_fantasma`) | 1.53% | 1.52% | 99.93% | +2 | +1 |
| Saque da Cidade Eterna (`caravana_saqueadora`) | 0.56% | 0.56% | 100.00% | +2 | +0 |
| Ritual das Runas (`ritual_runico`) | 1.48% | 1.48% | 99.93% | +2 | +1 |
| Eclipse Sanguíneo (`eclipse_voraz`) | 0.56% | 0.56% | 100.00% | +3 | +0 |
| Caminho do Maculado (`rota_peregrina`) | 0.55% | 0.55% | 100.00% | +1 | +0 |
| Juramento da Árvore Áurea (`juramento_erdtree`) | 6.56% | 5.88% | 89.71% | +2 | +1 |
| Convergência da Lua Negra (`convergencia_lunar`) | 4.64% | 4.07% | 87.61% | +2 | +0 |
| Ritual do Véu Carmesim (`ritual_dinastia`) | 2.91% | 2.70% | 92.91% | +2 | +1 |
| Juramento do Crisol e da Graça (`v75_juramento_dois_crisol`) | 1.94% | 1.93% | 99.79% | +2 | +0 |
| Banquete da Hemorragia (`v75_banquete_hemorragia`) | 2.03% | 2.02% | 99.65% | +2 | +0 |
| Convergência da Geada Lunar (`v75_convergencia_gelida`) | 1.88% | 1.88% | 99.84% | +2 | +0 |
| Glória Divina (`fe_gloria`) | 15.91% | 15.87% | 99.72% | +2 | +0 |
| Devoção (`fe_devocao`) | 8.98% | 8.12% | 90.50% | +2 | +0 |
| Evangelho (`fe_evangelho`) | 8.95% | 7.68% | 85.79% | +2 | +0 |
| Irmandade Esquecida (`fe_irmandade`) | 9.02% | 7.16% | 79.43% | +2 | +0 |
| Soberania Divina (`fe_soberania`) | 8.92% | 6.45% | 72.27% | +2 | +0 |
| Sacerdócio (`fe_sacerdos`) | 4.65% | 3.19% | 68.56% | +2 | +0 |

### 3.3. Leituras e limites

- Maior ativação observada: **Glória Divina (`fe_gloria`) 15,87%**; em seguida **Eco das Pedras Cintilantes (`eco_convergente`) 9,31%**. Esses números são frequências de ativação sob a amostra, não taxa de vitória nem evidência isolada de sobrepotência.
- Os seis combos da família `fe_*` dos Esquecidos ativam entre 3,19% e 8,12%. Todos compartilham a tag `fe`, presente em 14 cartas do catálogo. Como uma jogada só ativa o primeiro combo elegível, esses combos competem entre si; por exemplo, `fe_sacerdos` tem potencial de 4,65%, mas ativa em 3,19% dos decks e ativa em 68,56% dos casos em que estava potencialmente disponível.
- A carta `gwent_unidade_eco` aparece como principal carta concluidora de combo, com 7.610 ativações acumuladas nas 100.000 amostras. Isso é sinal para revisar sua densidade de tags e não deve ser convertido automaticamente em custo individual sem examinar quais combos e bônus foram realmente concedidos.
- Todos os 27 combos têm ao menos um provedor de cada tag obrigatória no catálogo atual; portanto, nenhum é estruturalmente impossível por ausência de provedor. A regra de participantes mínimos continua necessária quando definida.
- `CARD_SYNERGY_TAGS` contém 72 IDs de carta; 67 pertencem ao catálogo atual e cinco são referências órfãs: `gwent_unidade_cruzado`, `gwent_unidade_evangelista`, `gwent_unidade_missionario`, `gwent_unidade_protetor`, `gwent_unidade_sacerdote`. A estrutura tem 108 associações individuais carta-tag.

**Limitações relevantes:** a amostra não filtra posse, líder escolhido, nível/raridade dos exemplares, estratégia, passagem antecipada, remoções, clima ou estados. Pressupõe que todas as 10 cartas iniciais sejam jogadas na mesma rodada. A ordem aleatória afeta o primeiro combo elegível; uma política estratégica pode mudar as taxas. Também não mede a variação total de pontuação nem o efeito do combo no resultado da partida.

## 4. Auditoria estática de ligação de handlers

Script: `scripts/audit-effect-handler-coverage-v0.1.py`. Saída: `card-game-handler-coverage-v0.1.json`.

| Camada | Catálogo/mapeamento | Referências no motor | Conclusão |
|---|---:|---:|---|
| Habilidades genéricas | 59 | 56 tratadas diretamente em `aplicar_jogada()` + 2 hooks de ciclo de vida | 58/59 têm referência de resolução; `sobrevivente` não tem handler encontrado. |
| Identidades por carta | 22 ativas | 50 valores/ramificações `effect` no resolvedor | 22/22 identidades ativas têm ramo; 28 ramos permanecem sem mapeamento ativo. |
| Combos | 27 | 27 definições verificadas | Todas as tags obrigatórias têm provedor atual; cinco IDs de tag são órfãos. |
| Líderes | 10 | Ações específicas do motor | Catálogo presente; ainda não foi validado por simulação competitiva. |

As 56 habilidades de execução direta incluem `instinto` e `fome_abismo`, que compartilham uma condição em `skill in {"instinto", "fome_abismo"}`. Os dois hooks de ciclo de vida são:

- `vinganca`: dispara em `_remover_unidade()` quando a unidade cai.
- `espolios`: dispara em `_resolve_round()` quando a unidade está em campo e seu jogador vence a rodada.

`gloria` não é um dos 59 IDs de `HABILIDADES`, mas existe como hook oculto em `_resolve_round()` e mantém a unidade mais forte com essa habilidade em campo após vitória. `sobrevivente` está descrita no catálogo e tem aura visual, mas não foi encontrado hook equivalente: o teste mostrou que é enviada ao descarte.

Os 28 valores antigos no resolvedor de identidade sem associação na tabela ativa são:

`astral_thread`, `conductive_spark`, `counterflame`, `covering_shot`, `devoto`, `echo_orb`, `ember_kin`, `escolha_ritmo`, `faceless_hunt`, `forge_rhythm`, `furnace_charge`, `grey_watch`, `last_oath`, `legado`, `mist_trail`, `pilgrim_duel`, `shadow_paths`, `shared_sentinel`, `sinergia_faccao`, `tide_resonance`, `v75_blood_feast`, `v75_blood_pursuit`, `v75_crucible_guard`, `v75_golden_standard`, `v75_lunar_cartography`, `v75_moon_ward`, `veil_shift`, `wandering_ember`.

A auditoria AST é estática: encontrar uma comparação/literal não garante que todo caminho condicional seja alcançável. Ela deve ser lida junto com os testes de fumaça.

## 5. Testes de fumaça no motor real

Script: `scripts/validate-card-effect-smoke-v0.1.py`. Saída: `card-game-effect-runtime-smoke-v0.1.json`.

O script constrói estados sintéticos e chama funções reais de `sistemas.gwent`: `aplicar_jogada()`, `_remover_unidade()` e `_resolve_round()`. Após revisão dos fixtures, foram corrigidas duas condições de teste: `encadeamento` agora é jogada na mesma fileira de `last_row`, e `sangue_frio` compara pontuações pré-jogada iguais (11 × 11). Ambos produziram +2 no cenário correspondente.

| Verificação | Resultado |
|---|---:|
| Habilidades no catálogo | 59 |
| Ações de jogada aceitas nos fixtures diretos (sem erro) | 56 |
| IDs do catálogo testados como hooks de ciclo de vida | 3 |
| Erros nos 59 testes de habilidade | 0 |
| Identidades ativas testadas | 22/22 sem exceção e com evento de ativação |

Casos de ciclo de vida observados:

- `vinganca`: removida a unidade, duas aliadas da mesma fileira receberam +1.
- `espolios`: a unidade permaneceu em campo até o encerramento e o jogador vencedor comprou uma carta.
- `gloria`: caso adicional de hook oculto; a unidade foi mantida em campo após vencer a rodada, apesar de não constar em `HABILIDADES`.
- `sobrevivente`: a unidade foi enviada ao descarte; ausência de handler correspondente confirmada no cenário testado.

**Limite do teste:** os 56 casos diretos comprovam que `aplicar_jogada()` aceitou a carta e concluiu a ação em cada fixture, não que todos os ramos condicionais foram acionados nem que todos os alvos possíveis foram testados. `immediate_field_swing_delta_excluding_base_power` é uma observação do estado sintético, não EFP calibrado. Efeitos de compra, escudo, marca, remoção bloqueada, duração e ressurreição exigem asserts específicos por resultado.

## 6. Por que EFP ainda não pode ser aprovado

O catálogo atual contém 59 habilidades genéricas (58 com score numérico e uma `null`), 22 identidades (22 com score), 27 combos (27 `null`) e 10 líderes (10 scores). As regras de componente padronizam valores de buffs, redução de poder, remoção, compra, ressurreição, escudo, purificação, movimento, condições e duração; porém o catálogo armazena um total agregado por efeito, sem decompor cada valor em:

- componente mecânico exato e magnitude;
- quantidade de alvos esperada e máxima;
- limite/cap aplicado pelo handler;
- chance de condição ser satisfeita;
- duração e probabilidade de o efeito sobreviver até pontuar;
- chance de bloqueio por escudo/limite/ausência de alvo;
- valor esperado da carta comprada/ressuscitada/removida;
- dependência de fileira, rodada, descarte, mão e composição da equipe.

O componente de remoção, por exemplo, usa peso fixo por alvo elegível, mas o valor real depende do poder do alvo, do escudo e da posição no tabuleiro. O peso de compra não considera qualidade da carta comprada. Um efeito que marca estados pode ter valor postergado, e o teste de delta imediato não captura isso. Portanto, os números EFP atuais são úteis apenas para ordenar hipóteses para revisão, não para definir custos/raridades automaticamente.

### Recomendação para EFP v0.2

Criar memória de cálculo por efeito, com estrutura semelhante a:

`effect_id → componentes → magnitudes/caps → alvos → condição → duração → probabilidade observada → valor esperado → intervalo/confiança → EFP aprovado`.

> **Nota histórica pré-política:** este parágrafo antecede a decisão do usuário. A semântica agora está fixada e implementada em `card-game-combo-policy-v0.1.md`. Para EFP continua válido medir o valor esperado do combo no nível do deck (frequência × variação de pontuação), ajustado por participantes, condições e concorrência de prioridade; o método de atribuição desse valor ao custo individual/compartilhado ainda não foi aprovado.

## 7. Decisões de balanceamento ainda abertas

1. O orçamento inclui relíquia equipada? A relíquia fica fora dos 12 slots no backend atual, mas incluir seu custo é uma regra de design nova.
2. O orçamento inclui `leader_load`? Líder não ocupa um dos 12 slots e seu efeito é ativado como ação de partida; o custo adicional é proposta nova.
3. Qual taxa de aceitação de decks aleatórios é desejável em 32 pontos? A amostra demonstra a distribuição, não define a taxa correta.
4. Como o poder-base de modelo (1–15) se relaciona ao poder do exemplar, que pode variar por raridade/instância no estado atual?
5. Especiais devem ter `power_base=null` ou um número visual independente? Ainda é proposta.
6. Como a quota de 30% será contada após expansão, cartas pessoais/geradas, e eventual separação de modelos jogáveis e especiais?
7. Qual o destino de `sobrevivente`, `gloria`, os 28 ramos de identidade antigos e os cinco IDs órfãos de tags?
8. As seis cartas suspeitas da expansão dos Esquecidos terão facção corrigida? Nenhuma correção foi aplicada.

## 8. Próximos passos na ordem correta

1. Revisar cada um dos 28 ramos de identidade sem mapeamento e decidir `keep`, `merge`, `redesign` ou `remove`; decidir também `sobrevivente` e `gloria`.
2. Criar asserts individuais para efeitos de compra, remoção, ressurreição, marcas, escudo, clima, movimento, purificação, sacrifício e duração; converter os testes de fumaça em testes de comportamento com precondição e resultado esperado.
3. Criar memória de cálculo EFP por efeito, sem preencher `null` por suposição.
4. Simular partidas completas em matrizes de confrontos entre facções, incluindo decks de baixo/médio/alto custo e políticas de jogo documentadas; medir taxa de vitória, pontos por rodada, duração, uso de habilidade, taxa de ativação de combo e efeito médio no placar.
5. Recalibrar custo, teto, EFP e raridade com resultados das partidas e definir se líder/relíquia entram no orçamento.
6. Só então apresentar v1 de balanceamento para aprovação. Não implementar antes da decisão do usuário.

## 9. Histórico de alterações deste relatório

| Arquivo | Trecho/função/campo | Alteração | Motivo | Impacto no restante do projeto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/validate-card-effect-smoke-v0.1.py` | `fixture()`, `run_skill()`, status e métricas | Adicionada carta-reserva para evitar auto-pass; corrigidos os cenários de `encadeamento` e `sangue_frio`; renomeado status para declarar que play aceita não é cobertura completa de ramo. | Evitar falso zero e evitar afirmar execução de todos os ramos apenas porque a jogada terminou. | Apenas ferramenta de diagnóstico; nenhuma chamada no runtime de produção. | 59 ações sem erro; 56 testes diretos; `encadeamento` +2; `sangue_frio` +2; hooks separados testados. |
| `docs/card-game-effect-runtime-smoke-v0.1.json` | `generic_skill_counts`, `generic_skill_smoke`, `lifecycle_cases` | Regenerado com resultados corrigidos e ressalvas. | Preservar saída reproduzível da ferramenta. | Somente evidência documental. | Executado novamente; 22/22 identidades reconhecidas; `sobrevivente` sem handler no caso testado. |
| `docs/scripts/audit-effect-handler-coverage-v0.1.py` | Novo script AST/runtime de catálogo | Criada auditoria estática entre HABILIDADES, referências do resolver de unidade, hooks de ciclo de vida, identidade e tags de combo. | Separar definições ativas de ramos antigos/desconectados. | Somente diagnóstico; não modifica os módulos analisados. | Resultado reproduzível: 59 genéricas, 58 com referência, 1 ausente; 22 identidades ativas, 28 ramos antigos; 27 combos sem tag impossível. |
| `docs/card-game-handler-coverage-v0.1.json` | Novo relatório estruturado | Registradas contagens, listas órfãs/antigas e cobertura de tags. | Permitir checagem automatizada em continuidade futura. | Somente documentação/dados de auditoria. | Gerado pelo script AST. |
| `docs/scripts/sample-deck-cost-v0.2.py` e `docs/card-game-deck-cost-sampling-v0.2.json` | Modelo de amostragem e limites | Separados cenários com/sem relíquia, acrescentado `leader_load` e removido o crédito de combo por tag parcial. | Corrigir duas falhas de método na amostragem v0.1. | Modelo analítico, não afeta cálculo de custo no backend. | Duas execuções com seed 42 produziram JSON idêntico; 100.000 amostras por cenário. |
| `docs/scripts/simulate-combo-activation-v0.1.py` e `docs/card-game-combo-activation-v0.1.json` | Novo diagnóstico de `_aplicar_combo_de_cartas()` | Medida a frequência de combo potencial/real sob 100.000 decks e ordem aleatória. | Evitar atribuir EFP parcial a uma carta por possuir apenas uma tag; observar competição/prioridade do combo real. | Nenhum impacto funcional; não incorpora valor de combo ao custo v0.2. | Reexecução idêntica com seed 42; 57,19% dos decks com ao menos um combo. |
| `docs/card-game-balance-validation-v0.1.md` | Documento novo | Consolidados método, resultados, limitações e próximos passos. | Criar evidência autossuficiente antes de decidir parâmetros. | Nenhum impacto funcional. | Conferido contra os quatro JSON e scripts incluídos. |
| `docs/card-game-balance-spec-v0.1.md`, `docs/card-game-handoff.md`, `docs/card-game-mapping-audit.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PACOTE-MANIFESTO.md` | Estado, avisos, leitura e histórico | Atualizadas as pendências e a referência à validação; marcada v0.1 como não aprovada e amostragem v0.1 como histórica/superada. | Impedir que outro chat use os valores antigos como decisão final. | Apenas documentação de continuidade. | Links relativos, contagens, status e hashes do runtime conferidos. |


## 11. Mapa de fonte por efeito e metodologia EFP v0.2

Foram acrescentados `card-game-effect-source-map-v0.1.json` e `scripts/build-effect-source-map-v0.1.py`. O gerador analisa por AST `sistemas/cartas.py` e `sistemas/gwent.py`, registra função, linha, condição de ramo e excerto associado a cada ID genérico, identidade, líder e combo. Resultado: 59 habilidades genéricas (56 handlers diretos em `aplicar_jogada()`, dois hooks de ciclo de vida e `sobrevivente` sem handler), 22 identidades ativas com referências, 10 líderes com referências e 27 combos declarativos ligados ao resolver comum. `gloria` continua como hook de rodada oculto e fora de `HABILIDADES`. O script v0.1 e seu JSON são registros históricos do baseline; o gerador agora recusa execução no runtime pós-política para não sobrescrever o mapa congelado. Para a fonte atual, usar `card-game-effect-source-map-v0.2.json` e `scripts/build-effect-source-map-v0.2.py`.

O mapa é evidência de localização no código, não prova de alcançabilidade de cada caminho nem correção do efeito. A nova proposta metodológica está em `card-game-efp-methodology-v0.2.md`: decompor cada habilidade em precondições, alvos/caps, operações imediatas e atrasadas, duração, bloqueios, interação de raridade, testes e vetor antes/depois; depois estimar frequência e valor esperado em partidas simuladas. Isso substitui a confiança indevida em pesos fixos da v0.1, mas ainda não fornece números EFP aprovados.

**Próxima tarefa:** acrescentar asserts explícitos por habilidade e casos limite; depois construir simulações completas por facção/política. Nenhuma regra funcional foi alterada.


## 12. Primeira bateria de asserts comportamentais

Script: `scripts/assert-card-effect-behavior-v0.1.py`. Saída: `card-game-effect-behavior-assertions-v0.1.json`.

A bateria executa `sistemas.gwent.aplicar_jogada()` em fixtures sintéticos e verifica resultados explícitos para 13 casos: `primeira_luz` (+1 na rodada 1), `drenagem` (-1 de bônus por inimigo, respeitado o piso), `gwent_batedor` (compra uma carta em raridade Comum), `gwent_egide` (um escudo), `gwent_requiem` (ressuscita a unidade elegível mais forte), `gwent_passo` (move uma unidade), `gwent_invocacao` (invoca token de poder 3), `gwent_queima` (remove uma unidade mais forte de cada lado), `gwent_purificar` (zera clima), `gwent_sangramento` (aplica uma marca na fileira escolhida), `gwent_execucao` (remove alvo elegível), `gwent_chifre` (+2 aos aliados da fileira) e `arma_grande_sino` (identidade concede +2 quando está perdendo). Resultado: **13 passaram, 0 falharam**.

Limites: é uma bateria representativa, não cobertura completa. Todos os casos usam raridade Comum para isolar handlers de `RARITY_EFFECT_BUDGET`; não prova efeitos em outras raridades, todos os ramos/condições, bloqueios, eventos atrasados, líderes, relíquias ou equilíbrio. A próxima execução deve ampliar casos positivos/negativos e limites para as demais famílias.

| Arquivo | Trecho/função/campo | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/assert-card-effect-behavior-v0.1.py` | Novo script; `play()`, `test_*()` e `check()` | Adicionadas 13 asserções que verificam mudanças explícitas no estado após chamadas ao motor real. | Distinguir “a jogada terminou sem exceção” de “o efeito teve o resultado esperado”. | Apenas ferramenta de diagnóstico em `docs/scripts/`; nenhuma chamada no runtime de produção. | 13/13 cenários aprovados. |
| `docs/card-game-effect-behavior-assertions-v0.1.json` | Novo relatório | Registra resultados, expectativas e limites dos 13 casos. | Preservar evidência estruturada e reproduzível para o próximo chat. | Somente documentação. | JSON gerado pelo script. |


## 12. Registro histórico pré-política: validação comportamental expandida v0.2 — 219/219

> Esta seção descreve sete suites executadas antes da política de combos ser aprovada/implementada. O agregado vigente é v0.3: oito suites, 251/251 asserts.

A etapa posterior expandiu a bateria inicial de 13 cenários para sete suites. Resultado consolidado em `card-game-behavior-validation-v0.2.md/.json`: 219 asserts, 219 aprovados, zero falhas. A soma é de cenários/asserts distribuídos em suites, não de 219 efeitos distintos. A suite mais recente adiciona 87 cenários: um par ativador por cada um dos 27 combos, ausência de parceiro, bloqueio de repetição do mesmo combo, uma carta sem tags, passivas das quatro facções e exclusão de especiais da passiva de unidades.

| Família | Resultado |
|---|---:|
| Efeitos representativos iniciais | 13/13 |
| Identidades ativas | 33/33 |
| Habilidades genéricas de unidade | 39/39 |
| Hooks de ciclo de vida | 7/7 |
| Especiais e relíquias | 18/18 |
| Líderes | 22/22 |

Os dez handlers de líder foram chamados diretamente por `aplicar_jogada(action="leader")`; as 22 asserções incluem dez cenários positivos e 12 de rejeição/limite. A auditoria de 28 ramos antigos também foi detalhada: 18 V18 filtrados, quatro IDs legados sem dispatch ativo e seis ramos V75; `gloria` e `sobrevivente` são problemas de ciclo de vida separados. Nenhum ramo foi apagado.

**Limitações das sete suites históricas pré-política:** são fixtures sintéticos em memória. Cada combo foi testado com um único par ativador concreto; os 219 asserts, isoladamente, não cobrem todos os pares alternativos nem a precedência. Uma auditoria enumerativa posterior e separada examinou todos os pares e trincas de IDs de unidades atuais com tags; veja `card-game-combo-overlap-v0.1.md/.json`. Essa varredura não equivale a partidas completas de 12 cartas. As suites não cobrem banco de produção, APIs, frontend, Discord, R2, artes publicadas, todos os estados/raridades, IA ou métricas de vitória. Portanto, 219/219 demonstra apenas que os resultados esperados nos cenários selecionados foram observados. Não aprova EFP, custo, raridade, teto 32 nem a nova distribuição de cartas.

Próxima fase após a política de combos aprovada: expandir testes para sequências stateful de 12 cartas, snapshots serializados e integração de API/site; cobrir clima, transições de rodada, IA e interações cruzadas; deliberar sobre os 28 ramos de identidade antigos e construir simulador determinístico de partidas por facção/política; somente depois calibrar EFP, custos e raridades.


## 13. Auditoria de semântica e sobreposição de combos (2026-11-27)

A auditoria complementar `card-game-combo-overlap-v0.1.md/.json` foi produzida pelo script `scripts/audit-combo-overlap-v0.1.py` no checkout original pré-política. Ela enumerou o comportamento do resolvedor baseline com 67 unidades que possuem tags, 4.422 pares ordenados e 287.430 trincas de IDs distintos. O script v0.1 agora está arquivado e recusa execução no runtime atual; a auditoria pós-política vigente é v0.2. Nenhuma dessas enumerações é simulação competitiva nem calibra EFP por si só.

Os resultados confirmam que 154 pares (3,4826%) deixam mais de um combo elegível; 11.780 trincas (4,0984%) ativam pelo menos dois combos; 1.088 dessas trincas são monofacção. Em 8.096/11.784 eventos de combo posterior (68,7033%), a carta que recebe o efeito não contribui com nenhuma das tags exigidas pelo combo. Isso decorre do resolvedor aceitar qualquer tag não vazia na carta atual e encontrar a condição completa no tabuleiro. Além disso, três combos não têm `minimum`, e `gwent_unidade_eco` ativa `eco_convergente` sozinho, apesar de a descrição mencionar dois participantes.

> **Texto histórico anterior à aprovação.** A participação obrigatória, mínimo 2, prioridade explícita e destinatário do bônus já foram aprovados e implementados. Para EFP, o trabalho pendente é medir o valor de pontuação dos combos sob essa semântica em partidas completas e decidir como a externalidade afeta custo individual/compartilhado; não reabrir a regra de participação sem solicitação explícita.


## Atualização posterior — política de combos aprovada e implementada

> Esta atualização é posterior ao diagnóstico exploratório originalmente descrito neste relatório. As seções que dizem “resolvedor atual” e reproduzem frequências/comportamentos de combos referem-se ao baseline pré-política; não devem ser tomadas como a regra vigente.

O usuário aprovou e o runtime recebeu a política formal em `card-game-combo-policy-v0.1.md`: dois participantes distintos para todos os 27 combos; carta atual com contribuição de tag requerida; prioridade explícita crescente; um combo por jogada; ativação pendente apenas por participante posterior; bônus individual para a carta participante atual; preservação de `team_bonus` e de uso por combo/rodada.

A auditoria atualizada está em `card-game-combo-overlap-v0.2.md/.json`, e as regressões em `card-game-combo-policy-assertions-v0.1.json`. O agregado atual é `card-game-behavior-validation-v0.3.md/.json` (251/251 em oito suites). Os resultados de amostragem de custo e frequência de combos documentados acima continuam análises exploratórias, não foram recalibrados para medir partidas completas sob a política nova e não aprovam EFP, custo, raridade ou teto de deck.
