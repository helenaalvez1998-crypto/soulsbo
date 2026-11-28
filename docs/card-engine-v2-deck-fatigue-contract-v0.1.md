> **Status histórico:** este contrato candidato foi substituído pela implementação alpha v0.2 em `docs/card-engine-v2-deck-fatigue-alpha-v0.2.md` e pelo ruleset `alpha-test-only.ruleset.v0.3`. Os valores e a cadência deixaram de estar pendentes no controlador isolado; continuam provisórios e não aprovados para publicação.

# Card Engine v2 — contrato candidato de deck fatigue v0.1

**Status:** `CANDIDATE_NOT_APPROVED_NOT_WIRED`  
**Baseline:** `soulsbo-main-continuity-2026-11-28-rev21.zip`  
**Artifact:** `data/card_game/card-engine-v2-deck-fatigue-policy-candidate.v0.1.json`  
**Runtime:** sem alteração; `AlphaMatchController` não importa o módulo candidato.

## 1. Regra comprovada pela fonte

`docs/CARD_GAME_REDESIGN.md`, seção **10. REGRAS OFICIAIS / Fim de Jogo**, registra:

- Deck vazio: dano crescente por turno.
- Vida 0: derrota.
- Ambos chegam a 0 no mesmo turno: empate.

A fonte não informa a quantidade inicial de dano, a progressão numérica, um teto, nem define precisamente o momento em que a compra ocorre. O mesmo redesign indica mão inicial de quatro cartas; a alpha atual distribui seis, outro ponto que deve ser alinhado em uma futura revisão de ruleset.

## 2. Incompatibilidade com a alpha atual

O `AlphaMatchController` distribui seis cartas na mão inicial e mantém o restante em `draw_pile`. Depois, em `_close_round`, a próxima rodada compra até duas cartas por jogador (`draw_per_round=2`). Quando a pilha acaba, o loop simplesmente para; não existe contador de fatigue nem dano por esgotamento.

A regra do redesign fala em dano por **turno**, mas a alpha atual compra na transição de **rodada**. Esses ciclos não são equivalentes. Alterar a cadência de compra ou aplicar fatigue na transição de rodada sem decisão explícita mudaria o ritmo e o consumo do deck.

## 3. Referência matemática isolada

O módulo `sistemas/card_engine_v2/deck_fatigue_candidate.py` oferece funções puras para testar a hipótese de progressão aritmética e uma política candidata de draw parcial:

```text
n = falhas anteriores de compra do jogador + 1
dano_n = dano_inicial + (n - 1) * incremento
dano_aplicado = min(dano_n, teto)  # somente se um teto for definido
```

`initial_damage`, `damage_increment` e `maximum_damage` são argumentos obrigatórios/explicitamente opcionais da função. Nenhum valor de balanceamento é definido no runtime nem defaultado pela referência. Os números `1, 3, 5, 7` usados nos testes são apenas fixtures matemáticas, não proposta de balanceamento.

O contador é modelado como independente por jogador e por partida. A referência de fase candidata aplica uma única etapa quando a fase não consegue satisfazer todos os draws solicitados, mesmo se faltarem várias cartas; este comportamento de draw parcial ainda requer aceite. As funções não alteram vida, zonas, eventos, turno, snapshot ou banco; não decidem a cadência real de compra nem quando o controlador deve chamá-las.

## 4. Matriz de contrato candidata

| Caso | Comportamento candidato | Estado |
|---|---|---|
| Compra satisfeita | Não incrementa fatigue | Regra de teste |
| Fase de compra com pilha vazia e compra pendente | Incrementa uma vez naquela fase | Regra de teste |
| Duas compras pendentes e pilha vazia | No máximo uma aplicação por fase | Pendente de aceite |
| Jogadores diferentes | Contadores independentes | Regra de teste |
| Dano subsequente | Progressão aritmética parametrizada | Pendente de aceite |
| Teto | Só existe se definido explicitamente e deve permitir dano acima do valor inicial | Pendente de aceite |
| Vida chega a zero | Reutilizar finalização por vida esgotada | Regra-fonte; timing pendente |
| Ambos chegam a zero no mesmo turno | Empate | Regra-fonte |
| Descarte embaralhado de volta | Não presumir reshuffle | Não definido pela fonte |

## 5. Decisões necessárias antes da integração

1. **Cadência:** compra/fatigue em cada turno de jogador ou uma fase por nova rodada?
2. **Progressão:** qual o dano inicial e o incremento por falha consecutiva? Existe teto?
3. **Compra parcial:** se a fase pede duas cartas e resta uma, aplica fatigue na mesma fase após comprar a última ou somente na próxima?
4. **Reinício:** se um efeito futuro devolver cartas ao deck, o contador de fatigue zera, pausa ou permanece acumulado?
5. **Lethal timing:** dano é aplicado imediatamente na fase de compra, impedindo qualquer ação do jogador em 0 de vida?
6. **Resolução conjunta:** se os dois jogadores tiverem fase de compra no mesmo limite temporal, o dano é aplicado simultaneamente?

Sem essas decisões, qualquer implementação no `match.py` teria comportamento inventado.

## 6. Limite deliberado desta entrega

- Não altera `AlphaMatchController`, `combat.py`, repository, schema v7, SQL, catálogo alpha ou ruleset v0.2.
- Não altera os cinco arquivos centrais do motor legado.
- Não cria atributos de HP por unidade nem morte de unidade por dano de combate: o combate atual causa dano à vida dos jogadores.
- O módulo candidate é uma referência matemática testável, não um handler ativo.

## 7. Validação

Comando:

```bash
python -m unittest tests.card_engine_v2.test_deck_fatigue_candidate -v
```

Os testes cobrem progressão parametrizada, contadores independentes, teto explícito, ausência de teto implícito, draw completo sem fatigue, draw parcial com uma única aplicação, fase sem cartas e rejeição de valores inválidos. Também verificam que os parâmetros não aprovados permaneçam nulos e desligados no manifesto candidato.
