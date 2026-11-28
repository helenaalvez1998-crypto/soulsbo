# Metodologia de EFP v0.2 — decomposição antes da pontuação

> **STATUS: PROPOSTA METODOLÓGICA, NÃO APROVADA E NÃO IMPLEMENTADA.** Este documento substitui a ideia de tratar os valores EFP agregados de v0.1 como suficientemente fundamentados. Não altera cartas, custos, raridades ou regras do motor.

Data: 2026-11-27  
Baseline: `soulsbo-main(1).zip`  
Evidência primária: `card-game-effect-source-map-v0.1.json`, `card-game-handler-coverage-v0.1.json`, `card-game-effect-runtime-smoke-v0.1.json`, `card-game-effect-behavior-assertions-v0.1.json`, `card-game-combo-activation-v0.1.json`.

## 1. Decisão metodológica

**Não atribuir um único número EFP a partir da descrição textual ou de pesos fixos escolhidos manualmente.** Primeiro decompor cada efeito em operações mensuráveis no estado do jogo; depois estimar sua frequência e seu valor ao longo de partidas simuladas. Até essa etapa, manter EFP como `null` ou como intervalo provisório explicitamente não aprovado.

O catálogo atual v0.1 usa pesos fixos, por exemplo: +1 buff = 1,0; redução de bônus inimigo = 0,75; remoção por alvo elegível = 4,0; compra de carta = 2,0; escudo = 2,0. Esses valores são hipóteses de design, não resultados calibrados por partidas. Eles não capturam o valor do alvo, o número efetivo de alvos, a condição, o momento, os bloqueios nem o impacto futuro.

## 2. Cobertura ligada ao código atual

O mapa de evidências `card-game-effect-source-map-v0.1.json` foi gerado por AST sobre `sistemas/cartas.py` e `sistemas/gwent.py`. Para cada ID, registra ocorrências do literal, função envolvente, linha, condição de ramo quando identificável e trecho de código.

| Categoria | Quantidade | Resultado da ligação estática |
|---|---:|---|
| Habilidades genéricas declaradas | 59 | 56 ramos de jogada, 2 hooks de ciclo de vida, 1 sem handler (`sobrevivente`) |
| Hooks genéricos de ciclo de vida | 2 | `vinganca` em `_remover_unidade()`; `espolios` em `_resolve_round()` |
| Efeito de ciclo de vida oculto fora de `HABILIDADES` | 1 | `gloria` em `_resolve_round()`; não tem metadado correspondente no catálogo |
| Habilidades de identidade ativas | 22 | 22 têm referência de execução no resolvedor de identidade |
| Habilidades de líder | 10 | 10 têm referência de execução no fluxo de ativação do líder |
| Combos declarados | 27 | Configuração declarativa consumida por `_aplicar_combo_de_cartas()` |

A contagem de 56 ramos de jogada não significa 56 testes completos de todos os ramos condicionais. O teste de fumaça v0.1 executa a carta em um cenário controlado e confirma que a ação terminou sem erro; não prova todas as condições, caps e bloqueios.

O catálogo de tags possui 72 IDs de carta, 67 deles no catálogo atual, e 5 IDs órfãos. As 27 combinações possuem provedores de cada tag requerida no catálogo, mas isso não garante que todas as combinações sejam alcançáveis em deck válido ou que a ativação seja competitivamente saudável. A frequência medida sob ordem aleatória está em `card-game-combo-activation-v0.1.json`.

## 3. Registro mecânico obrigatório por efeito

Cada habilidade deve ter uma ficha estruturada com estes campos, todos derivados do handler e de testes:

| Campo | O que registrar |
|---|---|
| `effect_id` / `card_id` | Identificador canônico e cartas que o utilizam. |
| `handler` | Arquivo, função, linhas e ramo efetivo. |
| `trigger` | Jogada, líder, relíquia, remoção, fim de rodada, início/fim de partida ou combo. |
| `preconditions` | Condições exatas de ativação; declarar se são obrigatórias ou alternativas. |
| `targets` / `target_cap` | Lado, fileira, critério de seleção, ordenação e limite de alvos. |
| `immediate_components` | Buff, redução, alteração de poder-base, remoção, movimento, compra, invocação, escudo ou purificação executados imediatamente. |
| `delayed_components` | Sangramento, Geada, Podridão, Loucura, escudo consumível, compra condicionada, retenção de rodada e demais consequências futuras. |
| `duration` | Instantâneo, até fim da rodada, persistente, até consumir ou até evento de limpeza. |
| `blockers` | Escudo, limite de bônus, ausência de alvo, carta indisponível, imunidade, condição climática e demais bloqueios. |
| `rarity_interaction` | Se `RARITY_EFFECT_BUDGET` afeta o efeito e quais alterações incrementais realmente são elegíveis. |
| `tests` | Casos positivo, negativo, limite, alvo ausente, alvo protegido e interação de estado. |
| `measurements` | Vetor antes/depois observado e distribuição dos resultados em simulação. |
| `confidence` | `unverified`, `mechanics_tested`, `simulation_estimated` ou `approved`. |

Não preencher campos por inferência baseada no nome ou na lore. Quando não houver handler ou teste, registrar `unknown`/`null` e abrir uma decisão explícita.

## 4. Modelo de medição proposto

### 4.1. Primeiro nível: vetor de consequência

Para cada cenário `s`, registrar antes e depois da ativação:

- `own_board_effective_power_delta`;
- `enemy_board_effective_power_delta`;
- `own_base_power_delta` e `enemy_base_power_delta`;
- `units_removed_by_side` e poder efetivo dos alvos removidos;
- `cards_drawn`, `cards_returned`, `cards_revived` e poder/raridade das cartas envolvidas;
- `shields_added`, `shields_consumed` e remoções bloqueadas;
- `status_added`, `status_removed`, marcas aplicadas e marcas que efetivamente causaram consequência;
- `units_moved`, fileiras de origem/destino e alteração climática/tática resultante;
- `round_end_retention`, vencedor da rodada e mudança na pontuação final.

O delta imediato de placar deve ser calculado como diferença de pontuação dos dois lados, mas não substitui recursos e consequências futuras. Compra, ressurreição, escudo, marcas, movimento e retenção exigem medir eventos posteriores.

### 4.2. Segundo nível: valor condicionado ao estado

Para cada efeito, criar cenários estratificados. A amostra deve incluir estados em que a habilidade é ativada, estados em que quase pode ativar e estados em que não deve ativar. Exemplos:

- placar próprio vencendo, perdendo e empatado;
- primeira/segunda/terceira rodada;
- fileira vazia, com um alvo e com vários alvos;
- alvo forte/fraco, com bônus positivo/negativo e com escudo;
- com/sem clima e com resistências;
- descarte vazio/cheio, mão curta/cheia e reserva disponível/indisponível;
- uma ou mais marcas de estado, antes e depois do limite de ativação;
- aliados na mesma fileira, em outras fileiras e em facções diferentes;
- condição de combo potencial e concorrência com outro combo elegível.

A probabilidade de cada cenário não deve ser um multiplicador manual do tipo 0,7 ou 0,85. Ela deve ser estimada com partidas reproduzíveis sob políticas de jogo documentadas, separando facção, força do deck, ordem de turno e estratégia. Quando a amostra for insuficiente, registrar intervalo e baixa confiança.

### 4.3. Terceiro nível: valor esperado em partidas

Para um efeito `e`, usar uma estimativa sobre estados observados `S`:

`EV(e) = soma_s [frequencia(s) × delta_valor_do_estado(e, s)]`.

`delta_valor_do_estado` precisa incluir efeitos persistentes e recursos. Não assumir que um ponto de bônus equivale sempre a um ponto de valor: por exemplo, bônus limitado em alvo prestes a ser removido pode valer menos; compra depende da qualidade média da reserva; escudo vale conforme probabilidade de remoção bloqueada; purificação só vale quando remove um estado prejudicial que teria consequência; movimento depende de clima e regras da fileira.

Somente depois da estimativa de `EV`, do intervalo de confiança, da cobertura de testes e da validação em partidas é que se poderá normalizar para a escala EFP 0–10. Até lá, manter vetor e intervalo, não um número único aprovado.

## 5. Combos: valorar como externalidade do deck, não como bônus automático por tag

O motor exige o conjunto de tags completo e pode limitar ativações por combo/rodada e pela ordem de jogada. Os seis combos `fe_*` compartilham a tag `fe` e competem pelo primeiro combo elegível. Portanto:

1. Não atribuir EFP a uma carta só porque ela carrega uma tag isolada.
2. Calcular probabilidade de ativação por composição de deck, mão, ordem de jogada, estado e concorrência.
3. Medir o delta real do combo quando conclui, inclusive bônus da carta e bônus distribuído à equipe.
4. Calcular o valor esperado no nível do deck.
5. Decidir separadamente se o custo será compartilhado entre participantes, contabilizado como custo de sinergia do deck ou representado por outro mecanismo. Não duplicar o mesmo valor em todas as cartas.

A amostragem atual de combos presume que todas as dez cartas iniciais são jogadas na mesma rodada em ordem aleatória. Isso é apenas diagnóstico de frequência potencial e competição; precisa ser substituído por simulação com políticas e restrições reais de turno. A auditoria de precedência `card-game-combo-overlap-v0.1.md/.json` também identificou que o resolver pode conceder um combo pendente a uma carta que não fornece tag exigida e que `eco_convergente` ativa solo. Portanto, não atribuir EFP final a combos enquanto a política de participação, mínimo, precedência e alvo do bônus não estiver aprovada e corrigida/testada.

## 6. Critério mínimo para promover um EFP

Um efeito só pode sair de `unverified` quando:

1. o `effect_id` está ligado a um handler ativo e único;
2. todas as condições e os caps do ramo estão descritos;
3. existem asserts positivos e negativos, inclusive limites e bloqueios relevantes;
4. os deltas imediatos e atrasados foram conferidos;
5. a frequência da condição foi estimada em partidas simuladas;
6. o intervalo de confiança e os vieses conhecidos estão documentados.

Só pode receber estado `approved` depois de avaliação em matriz de confrontos entre facções e aprovação explícita do balanceamento. A aprovação do EFP não aprova automaticamente custo, raridade ou orçamento de deck.

## 7. Implicações para custo e raridade

Enquanto não houver EFP validado, não usar a fórmula v0.1 para atribuir custo/raridade em produção. A fórmula atual pode permanecer no documento como cenário de sensibilidade, mas nenhum deck, carta ou exemplar deve ser migrado por causa dela.

A raridade deve ser consequência de um modelo calibrado; não deve multiplicar silenciosamente o efeito funcional. A regra atual do motor `RARITY_EFFECT_BUDGET` precisa ser analisada separadamente, pois acrescenta pontos a alterações numéricas produzidas por algumas habilidades e pode alterar o resultado sem fazer parte da habilidade nominal.

## 8. Próxima execução técnica

1. Revisar o mapa de evidências para os 59 genéricos, 22 identidades, 10 líderes e 27 combos; decidir `keep`, `merge`, `redesign` ou `remove` para ramos antigos/incompletos.
2. Após a expansão sintética v0.2 (219/219 asserts em sete suites), expandir pares alternativos de combos, precedência de tags sobrepostas, clima, transições ampliadas, IA e interações cruzadas; o número de asserts não equivale a cobertura total.
3. Preencher as fichas de decomposição mecânica por família (buff/debuff, remoção, compra/ressurreição, estados, escudo, clima/movimento, combo, líder/relíquia).
4. Construir simulador de partidas por facção com política determinística e seed fixa; medir pontos por rodada, taxa de vitória, duração, ativação e valor pós-ativação.
5. Calibrar EFP, depois testar custo, raridade e orçamento; apresentar proposta v1 para aprovação.



## 8.1. Primeira bateria de asserts comportamentais

Foi criada inicialmente `scripts/assert-card-effect-behavior-v0.1.py`, com saída `card-game-effect-behavior-assertions-v0.1.json`. Essa bateria histórica chama `aplicar_jogada()` real em fixtures controlados e verificou 13 resultados esperados: buff de primeira rodada, redução de bônus inimigo, compra, escudo, ressurreição, movimento, invocação, remoção dos mais fortes dos dois lados, limpeza de clima, marcas de Sangramento, execução de alvo elegível, buff de fileira e a identidade `arma_grande_sino`. Resultado desta execução: **13/13 passaram**.

Isto comprova apenas os cenários selecionados, com raridade Comum, e não cobre todas as 59 habilidades, identidades, líderes, relíquias, estados persistentes ou condições negativas. O roteiro segue sendo expandir asserts por família, condição, limite e bloqueio.

## 9. Histórico desta etapa

| Arquivo | Função/campo | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/build-effect-source-map-v0.1.py` | Script novo; AST dos módulos de cartas e motor | Gera índice por ID com linhas, funções, testes de ramo e excertos de código para genéricos, identidades, líderes e combos. | Ligar o catálogo à implementação real, sem inferir mecânica pelo texto. | Apenas diagnóstico documental; não é importado pelo runtime. | Geração repetida; 59 genéricos (56 diretos, 2 hooks, 1 sem handler), 22 identidades e 10 líderes com referências, 27 combos. |
| `docs/card-game-effect-source-map-v0.1.json` | Relatório novo | Armazena o mapa de evidências por efeito e hooks compartilhados. | Permitir que outro chat localize cada ramo exato no código-base. | Apenas evidência; sem alteração funcional. | JSON gerado pelo script e conferido com auditoria AST anterior. |
| `docs/card-game-efp-methodology-v0.2.md` | Documento novo | Define decomposição em vetor de efeitos, frequência de condição, valor esperado, teste mínimo e regras para combos; inclui a primeira bateria de asserts. | Evitar pontuações EFP arbitrárias e custos/raridades não sustentados. | Atualiza o roteiro de validação; não muda fórmulas executadas no jogo. | Revisão cruzada com handlers, smoke e 13 asserts comportamentais. |

## 10. Limitações remanescentes

- Não foram simuladas partidas completas nem calculadas taxas de vitória.
- O relatório de smoke atual não é cobertura completa de branches.
- `sobrevivente` continua declarado sem handler identificado; `gloria` continua como efeito oculto de ciclo de vida fora do catálogo.
- Não há ainda distribuição real de estados de jogo, qualidade de compra, probabilidade de escudo ser consumido ou frequência de efeitos atrasados.
- Nenhum número EFP, custo, raridade ou teto de deck está aprovado.
- Nenhum arquivo funcional do motor, catálogo, banco, API, frontend ou imagem foi alterado.


## Validação sintética expandida — v0.2

A etapa inicial de 13 asserts foi expandida para sete suites e consolidada em `card-game-behavior-validation-v0.2.md/.json`: 219 asserts, 219 aprovados, zero falhas. As suites cobrem identidades, habilidades genéricas, ciclo de vida, especiais, relíquias, os dez handlers de líder e os 27 combos com um par ativador concreto por combo; também testam as passivas das quatro facções. Pares alternativos, precedência de combos sobrepostos, clima, IA e interações cruzadas ainda não foram exauridos. O agregador reproduzível é `scripts/summarize-card-game-behavior-v0.2.py`.

Esses resultados são testes de estado sintético em memória. Ainda não estimam frequência em partidas completas, valor esperado, win rate, equilíbrio de facções ou efeito combinado de todos os modificadores. A EFP v0.2 permanece uma metodologia proposta, sem pontuação aprovada. O próximo passo é testar combos/passivas/clima/transições/IA e interações cruzadas; depois construir simulador determinístico de partidas antes de calibrar EFP, custo ou raridade.
