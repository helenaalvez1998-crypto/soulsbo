# Card Engine v2 — change manifest rev. 17

**Baseline:** `soulsbo-main-continuity-2026-11-27-rev16.zip`  
**New package:** `soulsbo-main-continuity-2026-11-27-rev17.zip`

## Summary

This revision adds a playable, isolated two-player best-of-three match controller on top of the v2 transactional repository and generic gameplay resolver. The demo executes in a disposable SQLite database and uses a strict ten-card alpha allowlist sourced from the historical catalog snapshot plus explicitly marked alpha effect/balance/ruleset files.

## Files added

- `data/card_game/card-engine-v2-alpha-balance.v0.1.json`
- `data/card_game/card-engine-v2-alpha-effects.v0.1.json`
- `data/card_game/card-engine-v2-alpha-ruleset.v0.1.json`
- `sistemas/card_engine_v2/alpha_catalog.py`
- `sistemas/card_engine_v2/match.py`
- `sistemas/card_engine_v2/power.py`
- `tests/card_engine_v2/test_playable_match.py`
- `docs/card-engine-v2-playable-alpha-validation-v0.2.json/.md`
- `docs/card-engine-v2-playable-match-alpha-v0.1.md`
- `docs/card-engine-v2-playable-match-alpha-run.v0.1.json`
- `docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.1.py`
- `docs/scripts/test-card-engine-v2-playable-alpha-v0.2.py`

## Existing files changed

- `sistemas/card_engine_v2/repository.py`: additive match-runtime sidecar/migration; snapshot and runtime revision are coupled under the same transaction/CAS.
- `sistemas/card_engine_v2/__init__.py`: exports alpha catalog, match controller and power projections.
- `sistemas/card_engine_v2/README.md`: usage, playable alpha scope and limitations.
- `docs/README-PACOTE-CONTINUIDADE.md`: latest continuity state.
- `docs/card-game-handoff.md`: latest handoff and next work block.

## Validation

- Full suite: **78/78 passed**.
- Demonstration: **16 operations / 48 domain events**; final state `finished`; Player A wins 2–1 (rounds: A 9–4, B 0–6, A 6–0).
- SQLite: `quick_check=ok`, `integrity_check=ok`, zero foreign-key, revision or event-sequence violations.
- Dedicated tests verify that a targeted special requires the `expected_revision` from the latest server target offer and that an obsolete offer is rejected without consuming the source card.

The test suite uses local temporary SQLite databases. It does not exercise production, aiosqlite, Discord, HTTP, frontend or multi-host systems.

## Integrity boundary

No files were removed. No change was made to the five legacy application files:

- `sistemas/gwent.py`
- `sistemas/cartas.py`
- `bot.py`
- `database.py`
- `site/app.js`

No production database migration, runtime integration or cutover was performed. The new engine remains an isolated alpha.
