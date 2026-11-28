# Auditoria de sequência e estado `last_row` — v0.1

**Data:** 2026-11-27  
**Status:** `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`  
**Escopo:** família candidata `effect.sequence_power`; três habilidades genéricas atualmente ativas (`encadeamento`, `adaptacao`, `quebra_ritmo`) e ciclo de vida do campo `player.last_row`.

> Esta auditoria registra o comportamento do motor legado. Não aprova o comportamento como regra definitiva e não altera o runtime.

## 1. Resultado

**Resultado: 10/10 verificações aprovadas; zero falhas.**

A evidência confirma que `last_row` não representa a posição atual de uma unidade nem a fileira para a qual uma unidade foi movida. É um estado histórico por jogador: a fileira da última unidade jogada com sucesso naquela rodada.

- `encadeamento`: concede +2 quando a unidade atual é jogada na mesma fileira de `player.last_row`.
- `adaptacao`: concede +1 quando já existe uma fileira anterior registrada e a nova unidade é jogada em outra fileira.
- `quebra_ritmo`: concede +1 quando a fileira da unidade atual coincide com `other.last_row`.
- Após resolver uma jogada de unidade com sucesso, o motor atualiza `player.last_row` para a fileira da unidade que acabou de entrar.
- Jogar uma carta especial em outra fileira não altera `last_row`.
- `gwent_passo` pode mover a última unidade jogada sem alterar `last_row`.
- Remover a última unidade jogada não apaga `last_row`.
- Na transição para a rodada seguinte, `_resolve_round()` redefine `last_row` para `None` nos dois jogadores.

## 2. Evidência reproduzível

| ID | Cenário | Resultado observado |
|---|---|---|
| SEQ-01 | `encadeamento`, fileira anterior igual | +2 |
| SEQ-02 | `encadeamento`, fileira anterior diferente | 0 |
| SEQ-03 | `adaptacao`, fileira anterior diferente | +1 |
| SEQ-04 | `adaptacao`, sem jogada de unidade anterior | 0 |
| SEQ-05 | `quebra_ritmo`, última fileira do adversário igual | +1 |
| SEQ-06 | `quebra_ritmo`, última fileira do adversário diferente | 0 |
| SEQ-07 | mover a última unidade jogada e então usar `adaptacao` | a unidade foi de Corpo a Corpo para Longa Distância; `last_row` continuou Corpo a Corpo; `adaptacao` jogada em Longa Distância recebeu +1 |
| SEQ-08 | jogar uma especial em fileira diferente | `last_row` não mudou |
| SEQ-09 | remover a última unidade jogada | `last_row` permaneceu registrado |
| SEQ-10 | iniciar rodada seguinte | ambos os `last_row` foram redefinidos para `None` |

O caso SEQ-07 é a interação mais importante: o movimento altera `unit.row`, mas a habilidade de sequência consulta o histórico de jogada do jogador, não a posição atual daquela unidade. Portanto, o resultado pode parecer contraintuitivo se o campo for entendido como “última fileira ocupada”.

## 3. Implementação legada observada

Referências em `sistemas/gwent.py`:

- `aplicar_jogada()`, linhas 1825–1845: captura `player.last_row` e `other.last_row` antes de resolver as habilidades e aplica as três condições.
- `aplicar_jogada()`, linha 1925: após a unidade ser adicionada ao tabuleiro, grava `player.last_row = row`.
- `gwent_passo`, linhas 1780–1798: altera `unit.row`; não atualiza `player.last_row`.
- `_remover_unidade()`: não altera o histórico `last_row` do jogador.
- `_resolve_round()`, linha 1199: limpa `last_row` ao iniciar a rodada seguinte.

O snapshot de `last_row` é lido antes da resolução da unidade atual. A nova fileira passa a ser o histórico do jogador somente depois que a jogada de unidade foi concluída e anexada ao tabuleiro.

## 4. Variações da família e atribuições

A família candidata `effect.sequence_power` agrupa condições que compartilham o mecanismo histórico, mas não são intercambiáveis:

| Alias ativo | Referência | Relação de fileira | Bônus legado |
|---|---|---|---:|
| `encadeamento` | próprio jogador | igual | +2 |
| `adaptacao` | próprio jogador | diferente, exigindo valor anterior | +1 |
| `quebra_ritmo` | adversário | igual | +1 |

O mapa semântico também registra `veil_shift`, `pilgrim_duel` e `mist_trail` como branches/aliases históricos filtrados ou inativos. Não devem ser tratados como atribuições ativas nem reativados automaticamente na reconstrução. Ver `card-game-effect-semantic-audit-v0.1.md` e `card-game-stale-identity-disposition-v0.1.md`.

## 5. Requisitos candidatos para o modelo novo

Sem aprovar ainda nomes de schema, a modelagem deve separar explicitamente:

1. `current_row` da unidade — posição atual em campo, alterável por movimento.
2. Fileira-base da unidade — referência de sua carta/catalogação, se continuar necessária.
3. Histórico de jogada do jogador — fileira da última unidade jogada com sucesso na rodada.
4. Histórico de movimento — eventos de reposicionamento, caso outras regras precisem consultar movimentos.

A condição de sequência deve declarar `reference_side`, `row_relation`, `requires_previous_play` e `bonus`. `last_row` deve ser renomeado ou documentado como estado de histórico de jogada, não de posição. Movimentação, cartas especiais e remoção não devem sobrescrevê-lo por acidente.

**Recomendação candidata:** representar o histórico como estado por jogador, por exemplo `last_unit_play_row`, com atualização após uma jogada de unidade bem-sucedida e reset na transição de rodada. Separar histórico de movimento em eventos próprios; não inferir histórico a partir das unidades que permanecem no tabuleiro.

## 6. Decisões que continuam abertas

- Se a nova regra deve preservar literalmente os gatilhos históricos ou se deve reagir a eventos de movimento além de jogadas de unidade.
- Se efeitos que consultam a última fileira do adversário devem considerar apenas jogadas de unidade, como no legado, ou qualquer ação que escolha uma fileira.
- Se o histórico deve ser limpo em algum evento além da transição de rodada (por exemplo, reinício de estado), explicitamente definido no ciclo de vida novo.
- Se aliases históricos filtrados (`veil_shift`, `pilgrim_duel`, `mist_trail`) serão removidos, arquivados ou reassociados futuramente. Esta auditoria não reativa nenhum deles.

## 7. Validação e limites

- Script: `docs/scripts/audit-sequence-power-state-v0.1.py`
- Resultado: `docs/card-game-sequence-power-state-audit-v0.1.json`
- Resultado: **10/10 assertions aprovadas; zero falhas**.
- Fixtures sintéticas em memória; chamadas reais a `aplicar_jogada()`, `_remover_unidade()` e `_resolve_round()`.
- Não valida partidas completas de 12 cartas, comportamento de UI, persistência/serialização de snapshots, produção, equilíbrio ou frequência de condições.
- Não altera `sistemas/gwent.py`, catálogo, banco, API ou frontend.

**Próximo passo:** integrar estes requisitos ao mapa de decisões BUF-008/BUF-013 e depois revisar as famílias restantes de alta prioridade que dependem de estado temporal/seleção. As propostas continuam não aprovadas; o motor antigo permanece como baseline de evidência.
