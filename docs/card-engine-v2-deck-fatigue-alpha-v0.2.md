# Card Engine v2 — deck fatigue no controlador alpha (documentação v0.2 / ruleset v0.3)

**Status:** implementado e testado somente no `AlphaMatchController`; política de dano provisória de alpha, não aprovada para publicação.  
**Ruleset:** `alpha-test-only.ruleset.v0.3`.  
**Baseline de entrada:** revisão 22.  
**Sem alteração:** CardInstance schema 7, SQL, catálogo allowlist, API/Discord/frontend e motor legado.

## 1. Regra-fonte

`docs/CARD_GAME_REDESIGN.md`, seção `10. REGRAS OFICIAIS`, define:

- Cada jogador começa com 20 de vida.
- A mão inicial é de quatro cartas.
- Deck vazio causa dano crescente por turno.
- Vida zero encerra a partida.
- Letal simultâneo gera empate.

A fonte não define dano inicial, incremento, teto, regra de reshuffle ou cadência detalhada de compra. Esta revisão fixa escolhas de implementação para a alpha, sem tratá-las como balanceamento final.

## 2. Decisões adotadas nesta alpha

| Decisão | Comportamento |
|---|---|
| Gatilho | Início de cada turno individual, quando `draw_pile` está vazia |
| Primeiro dano | 1 ponto de vida |
| Progressão | +1 em cada aplicação posterior do mesmo jogador: 1, 2, 3, 4... |
| Teto | Nenhum teto implícito |
| Contador | Independente por jogador e por partida |
| Reset | Não reinicia durante a partida, mesmo se uma carta voltar ao deck no futuro |
| Setup | Cada jogador tem seu primeiro turno após a distribuição inicial isento de fatigue |
| Momento letal | Dano é aplicado antes de o jogador poder realizar uma ação |
| Descarte | Não é embaralhado de volta ao deck automaticamente |
| Resolução entre jogadores | Não é uma fase simultânea; cada jogador recebe fatigue quando seu próprio turno começa |

Fórmula usada para a n-ésima aplicação de fatigue daquele jogador:

```text
damage(n) = initial_damage + (n - 1) * damage_increment
initial_damage = 1
damage_increment = 1
maximum_damage = null  # sem teto
```

O contador mede o total de aplicações de fatigue na partida, e não uma sequência temporária. Se um efeito futuro devolver cartas à pilha de compra, o dano deixa de ocorrer enquanto ela não estiver vazia; o contador histórico permanece.

## 3. Relação com a compra alpha existente

- A mão inicial padrão passou a quatro cartas, conforme o redesign.
- O harness alpha continua comprando até duas cartas no início de cada nova rodada. Essa compra por rodada é comportamento do harness existente; a fonte normativa não define todo o ciclo de compra por turno.
- A fatigue é verificada depois da compra de início de rodada e antes da ação do jogador que começa a rodada.
- Se a compra de duas cartas encontrar apenas uma carta disponível, essa carta é entregue; a fatigue é aplicada uma única vez no início do turno se a pilha estiver vazia.
- Não foi inventada uma compra automática em todo turno. A cadência geral de compra continua sendo uma decisão de regras separada.

Com um deck de 30 cartas, mão inicial de quatro e apenas duas compras por nova rodada no harness atual, a pilha normalmente não se esgota em uma partida de três rodadas. A regra está ativa e pronta para quando a pilha acabar — seja por compras adicionais, efeitos futuros ou cenários de teste — mas a cadência completa de compra do jogo ainda precisa ser definida antes da publicação.

## 4. Pontos de integração

A checagem de início de turno ocorre após:

- Jogar uma unidade.
- Jogar uma carta especial.
- Sacrificar uma unidade.
- Ativar o líder.
- Passar, quando o turno passa ao outro jogador.
- Iniciar a próxima rodada, depois de distribuir as cartas daquela transição.

A verificação não ocorre no meio da ação do jogador, nem a cada carta faltante da compra. Uma vez iniciado o turno, o jogador não recebe aplicações adicionais de fatigue até o próximo início de turno.

## 5. Eventos e persistência

A contagem fica no sidecar de runtime, por jogador:

- `deck_fatigue_count_by_player`
- `initial_turn_exemption_pending_by_player`

A vida é atualizada em `life_by_player`. Não há migração SQL nem mudança do snapshot `CardInstance`.

Quando a pilha está vazia, a cadeia de eventos é:

1. `deck_fatigue_applied` — registra jogador, rodada/turno, contador, dano e vida antes/depois.
2. `player_damage_applied` — registra a alteração de vida, causado pelo evento de fatigue.
3. Se letal, `player_defeated` — motivo `deck_fatigue`.
4. `match_finished` — vencedor é o outro jogador e motivo `deck_fatigue`.

Tudo é persistido na mesma operação transacional que concluiu a ação anterior ou a passagem de turno. A vida chega a zero antes de qualquer ação do jogador afetado.

Como o gatilho é por turno individual, a fatigue sozinha não causa letal simultâneo: a partida termina no primeiro turno que reduz um jogador a zero. O empate por letal simultâneo continua pertencendo à resolução simultânea de combate por fileira.

## 6. Interface de leitura

`AlphaMatchController.view()` agora expõe por jogador:

- `deck_fatigue_count` — total de aplicações.
- `deck_fatigue_next_damage` — próximo dano previsto quando a pilha está vazia e a isenção inicial já foi consumida; `null` quando a pilha não está vazia ou a isenção está pendente.

A view é somente leitura; o cliente não escolhe ou calcula o dano.

## 7. Testes

`tests/card_engine_v2/test_deck_fatigue_runtime.py` cobre:

- Mão inicial padrão de quatro cartas e release `v0.3`.
- Isenção do primeiro turno de cada jogador.
- Dano 1, depois 2, em turnos individuais sucessivos.
- Contadores e vida independentes por jogador.
- Ausência de dano quando existe carta na pilha.
- Compra parcial na transição de rodada e uma única aplicação antes da ação.
- Derrota letal imediata, sem permitir ação posterior.
- Causalidade entre fatigue, dano, derrota e fim de partida.

A suíte geral de testes, staging do catálogo e as simulações Bo3 e de combos/passivas/líderes continuam sendo executadas como regressão.

## 8. Limites

- Os parâmetros 1/+1/sem teto são uma decisão provisória de alpha; exigem playtest e balanceamento.
- A implementação não adiciona compra automática a cada turno.
- O efeito não está integrado com Discord, HTTP, frontend nem com o motor ou banco publicados.
- Não altera a allowlist de 27 cartas nem libera os 110 modelos históricos bloqueados.
- Não adiciona HP por unidade nem transforma o combate por fileira em ataque físico individual.
