# Card Engine v2 — combate por fileira alpha v0.1

**Status:** `ISOLATED_ALPHA_IMPLEMENTATION_NOT_PRODUCTION_READY`  
**Pacote-base:** `soulsbo-main-continuity-2026-11-27-rev19.zip`  
**Pacote resultante:** revisão rev. 20 (2026-11-28)  
**Contrato CardInstance:** v0.7 / schema 7, draft implementado e não congelado  
**Ruleset:** `alpha-test-only.ruleset.v0.2`

## Objetivo desta fatia

Conectar o cálculo de poder efetivo já existente ao fechamento normal de uma rodada, calcular dano por fileira, persistir a vida dos jogadores e encerrar a partida quando a vida chega a zero.

A fonte de regra do projeto é `docs/CARD_GAME_REDESIGN.md`, seção **10. REGRAS OFICIAIS**:

- Cada jogador começa com 20 de vida.
- O poder é totalizado por fileira.
- O dano corresponde à diferença entre o poder inimigo e o aliado.
- A vida é reduzida pelo dano total.
- Vida zero encerra a partida.
- Se ambos chegarem a zero na mesma resolução, o resultado é empate.

## Resolução implementada

`sistemas/card_engine_v2/combat.py` fornece duas funções puras:

- `resolve_row_combat(state, player_ids, weather_by_row)`: totaliza o poder efetivo de cada jogador em `melee`, `ranged` e `siege`; em cada fileira, a maior potência causa somente a diferença positiva como dano ao oponente. Empate na fileira causa zero.
- `apply_life_damage(life_by_player, damage_by_player)`: aplica dano simultaneamente, limita a vida mínima a zero e identifica os jogadores derrotados.

O controlador chama o resolvedor em `AlphaMatchController._close_round`, antes do arquivamento das unidades. O cálculo usa `effective_power`, portanto já incorpora bônus, clima, resistência climática e estados de controle da release alpha.

O runtime da partida persiste `life_by_player`, com 20 pontos por jogador no setup. A vida é exposta em `AlphaMatchController.view`.

## Eventos de domínio

Cada fechamento registra:

- `combat_row_resolved`: potência de cada jogador, dano por jogador e vencedor da fileira.
- `player_damage_applied`: vida anterior, dano tomado e vida restante; seus pais causais são os eventos das fileiras que produziram o dano.
- `player_defeated`: emitido quando a vida chega a zero.
- `round_score_frozen`: agora contém potência por fileira, dano total e vida após o combate.
- `match_finished`: inclui `finish_reason`, vida final e vencedor; `simultaneous_lethal` identifica empate por eliminação simultânea.

A série melhor de três permanece como fallback do harness alpha quando nenhum jogador chega a zero até o limite configurado de rodadas. Essa condição está explicitada no ruleset alpha v0.2; não representa uma decisão final de release.

## Limites deliberados

- O contrato e as regras atuais não definem atributos individuais de ataque, armadura, defesa física ou pontos de vida por unidade. Não foram adicionados.
- A resistência existente é **resistência climática**, usada para calcular poder efetivo sob clima; não equivale a armadura ou mitigação de dano físico.
- O combate por fileira causa dano à vida do jogador; não destrói automaticamente unidades.
- Remoção, Execução, sacrifício, proteção e Vingança continuam no `GameplayResolver`. A ação normal de sacrifício ainda não foi integrada ao `AlphaMatchController` nesta fatia.
- Dano crescente por esgotamento do deck, descrito na visão geral do redesign, ainda não foi implementado.
- Custos de energia, limite de ativações e economia de turno além da regra alpha de uma ação por turno continuam pendentes.
- A regra continua alpha/teste, sem aprovação para publicação, integração Discord/API/frontend ou migração do motor legado.

## Testes adicionados

`tests/card_engine_v2/test_combat.py`:

1. Diferença positiva de poder causa dano somente ao lado inferior.
2. Resistência climática reduz a penalidade de clima antes do cálculo de dano.
3. Dano não reduz vida abaixo de zero e identifica derrota.
4. Eliminação simultânea identifica ambos os jogadores.
5. Dados inválidos são rejeitados.

`tests/card_engine_v2/test_playable_match.py`:

- Dano em fileiras diferentes atinge os dois jogadores na mesma resolução.
- Dano letal termina a partida antes do limite Bo3.
- Dano letal simultâneo termina em empate.
- Setup inicia ambos os jogadores com 20 de vida e vincula o manifesto ao ruleset v0.2.

## Validação desta revisão

- Suíte Card Engine v2: **117/117 testes aprovados** (baseline anterior: 109/109).
- `py_compile` em módulos, scripts e testes: aprovado.
- Teste alpha v0.4: aprovado.
- Validação do staging histórico: aprovada; 137 modelos, 27 alpha-only e 110 bloqueados.
- Simulação de partida Bo3: Player A vence 2–1, 16 operações, 60 eventos; integridade e foreign keys SQLite aprovadas.
- Demonstração combo/passiva/líder: aprovada, 25 eventos; integridade SQLite aprovada.
- Banco publicado, Discord, HTTP, frontend e runtime legado: não acessados.
