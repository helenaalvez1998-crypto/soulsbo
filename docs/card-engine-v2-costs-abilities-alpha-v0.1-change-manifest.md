# Manifesto de alterações — custos e habilidades manuais alpha v0.1 (rev. 25)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev24.zip`  
**Resultado:** `soulsbo-main-continuity-2026-11-28-rev25.zip`  
**Status:** validação aprovada; custos experimentais, não aprovados para release.

## Novos artefatos

- `data/card_game/card-engine-v2-alpha-activated-abilities.v0.1.json`
- `data/card_game/card-engine-v2-alpha-energy-cost-schedule.v0.1.json`
- `data/card_game/card-engine-v2-alpha-ruleset.v0.5.json`
- `docs/card-engine-v2-alpha-activated-abilities-v0.1.md`
- `docs/card-engine-v2-alpha-energy-cost-schedule-v0.1.md`
- `docs/card-engine-v2-costs-abilities-alpha-v0.1-change-manifest.md`
- `docs/card-engine-v2-costs-abilities-alpha-v0.1-validation.json`
- `docs/card-engine-v2-energy-economy-alpha-v0.2.md`
- `tests/card_engine_v2/support.py`
- `tests/card_engine_v2/test_activated_abilities.py`

## Arquivos existentes modificados

- `data/card_game/README.md`
- `docs/PACOTE-MANIFESTO.md`
- `docs/card-engine-v2-combo-faction-leader-alpha-run.v0.1.json`
- `docs/card-engine-v2-playable-alpha-validation-v0.5.json`
- `docs/card-engine-v2-playable-alpha-validation-v0.5.md`
- `docs/card-engine-v2-playable-match-alpha-run.v0.3.json`
- `docs/card-game-handoff.md`
- `docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py`
- `docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py`
- `docs/scripts/test-card-engine-v2-playable-alpha-v0.5.py`
- `sistemas/card_engine_v2/README.md`
- `sistemas/card_engine_v2/alpha_catalog.py`
- `sistemas/card_engine_v2/gameplay.py`
- `sistemas/card_engine_v2/match.py`
- `sistemas/card_engine_v2/repository.py`
- `tests/card_engine_v2/test_combo_faction_leaders.py`
- `tests/card_engine_v2/test_deck_fatigue_runtime.py`
- `tests/card_engine_v2/test_energy_economy.py`
- `tests/card_engine_v2/test_expanded_entry_effects.py`
- `tests/card_engine_v2/test_playable_match.py`

## Regras que permanecem

- +1 energia no início de cada turno individual, teto 5, saldo entre rodadas.
- Raridade e `deck_cost_legacy` não definem energia (BUF-001 preservado).
- Ação de carta, líder ou habilidade sem preço explícito é rejeitada; não existe gratuidade implícita.
- Sacrifício consome turno e não tem custo energético nesta alpha.
- Efeitos `unit_on_play` não viram habilidades repetíveis.
- Nenhuma carta bloqueada foi liberada; allowlist segue 27/137 e 110 bloqueadas.

## Validação e preservação

A suíte registrou 150/150 testes; staging 137/27/110; simulação Bo3 Player A 2–1 Player B (97 eventos); demonstração de combos/passiva/líder Player A 20–10 (49 eventos); ambas as bases temporárias SQLite passaram `integrity_check` e `quick_check`. O ZIP foi extraído em diretório limpo, validado com `unzip -t`, e a cópia extraída passou novamente em 150/150 testes e no carregamento do catálogo.

Cinco arquivos centrais do motor legado foram comparados por SHA-256 com a rev. 24 e permanecem byte a byte idênticos: `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js`. Nenhum arquivo foi removido nesta revisão.

Não há integração Discord/HTTP/frontend, banco publicado, adapter assíncrono, telemetria, playtest humano ou cutover de produção.
