# Change manifest — deck fatigue alpha v0.2

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev22.zip`  
**Release:** `alpha-test-only.ruleset.v0.3`  
**Scope:** isolated Card Engine v2 alpha only.

## Added

- `data/card_game/card-engine-v2-alpha-ruleset.v0.3.json` — new hash-pinned ruleset with four-card initial hand and explicit fatigue policy.
- `docs/card-engine-v2-deck-fatigue-alpha-v0.2.md` — implementation contract, decision rationale and limits.
- `docs/card-engine-v2-deck-fatigue-alpha-v0.2-change-manifest.md` — this manifest.
- `tests/card_engine_v2/test_deck_fatigue_runtime.py` — controller-level fatigue tests.

## Modified

- `sistemas/card_engine_v2/alpha_catalog.py` — loads and validates ruleset v0.3 and its fatigue values.
- `sistemas/card_engine_v2/match.py` — per-player turn-start fatigue, lethal termination, persisted counters and read-only view fields.
- `sistemas/card_engine_v2/repository.py` — runtime validation for fatigue counters and initial-turn exemptions.
- `tests/card_engine_v2/test_playable_match.py` — adapts deterministic six-card fixtures and verifies the additional turn-start fatigue event in its round-close scenario.
- `docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py` — keeps the six-card scenario explicit as a fixture.
- `docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py` — records runtime integration and the updated coverage.
- `docs/card-engine-v2-playable-alpha-validation-v0.4.md/.json` — regenerated from the full suite.
- `docs/card-engine-v2-playable-match-alpha-run.v0.3.json` — regenerated Bo3 proof with fatigue events.
- `docs/card-engine-v2-legacy-catalog-staging-validation-v0.2.md/.json` — regenerated staging validation.
- `docs/card-game-handoff.md`, `docs/PACOTE-MANIFESTO.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `data/card_game/README.md`, `sistemas/card_engine_v2/README.md` — continuity and usage notes.
- `data/card_game/card-engine-v2-deck-fatigue-policy-candidate.v0.1.json` — marked as superseded historical candidate, not the runtime source.
- `tests/card_engine_v2/test_deck_fatigue_candidate.py` — assertion updated to preserve and identify the candidate as historical.
- `docs/card-engine-v2-deck-fatigue-contract-v0.1.md` — marked as superseded historical candidate.

## Preserved

- CardInstance schema v7 and SQL migrations.
- Alpha card allowlist (27 enabled, 110 blocked).
- Combo, faction passive and leader registries.
- Approved removal, sacrifice, protection and Vingança semantics.
- Five central legacy files remain byte-identical to the baseline: `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`.
- No production database, bot, Discord, HTTP, frontend, migration or cutover was accessed or modified.
