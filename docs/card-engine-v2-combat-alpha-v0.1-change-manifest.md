# Change manifest — combate por fileira alpha v0.1 / rev. 20

**Baseline:** `soulsbo-main-continuity-2026-11-27-rev19.zip`  
**Resultado:** `soulsbo-main-continuity-2026-11-28-rev20.zip`

## Arquivos novos

- `sistemas/card_engine_v2/combat.py`
- `data/card_game/card-engine-v2-alpha-ruleset.v0.2.json`
- `tests/card_engine_v2/test_combat.py`
- `docs/card-engine-v2-combat-alpha-v0.1.md`
- `docs/card-engine-v2-combat-alpha-v0.1-validation.json`
- `docs/card-engine-v2-combat-alpha-v0.1-change-manifest.md`

## Arquivos alterados

- `sistemas/card_engine_v2/alpha_catalog.py`: fixa release e valida o ruleset alpha v0.2.
- `sistemas/card_engine_v2/repository.py`: runtime mantém/valida vida por jogador; backfill de runtime antigo continua aceito.
- `sistemas/card_engine_v2/match.py`: inicializa vida, resolve dano por fileira no fechamento, persiste histórico/eventos com causalidade completa entre linhas resolvidas e placar e encerra a partida em letal.
- `tests/card_engine_v2/test_playable_match.py`: cobertura de vida inicial, dano por fileira, letal e empate simultâneo.
- `docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py`: inclui cobertura de combate no relatório e atualiza os limites para distinguir dano por fileira de regras físicas por unidade ainda não especificadas.
- `docs/card-engine-v2-playable-alpha-validation-v0.4.md/.json`: relatório regenerado com a suíte ampliada e escopo correto.
- `docs/card-game-handoff.md`: checkpoint atual rev. 20.
- `docs/PROJECT-OPERATING-CONTEXT.md`: contexto operacional atualizado.
- `docs/README-PACOTE-CONTINUIDADE.md`: checkpoint no topo; histórico rev. 19 preservado abaixo.
- `docs/PACOTE-MANIFESTO.md`: manifesto rev. 20 no topo; histórico preservado.
- `sistemas/card_engine_v2/README.md`: fluxo de combate e limites atualizados.
- `data/card_game/README.md`: ruleset v0.2 documentado.

## Arquivos legados protegidos

Os arquivos abaixo devem permanecer byte a byte idênticos ao baseline rev. 19:

- `sistemas/gwent.py`
- `sistemas/cartas.py`
- `bot.py`
- `database.py`
- `site/app.js`

## Resultado

117/117 testes; scripts de validação e simulações alpha aprovados. Nenhum banco publicado foi acessado. Nenhuma integração ou migração de produção foi executada.
