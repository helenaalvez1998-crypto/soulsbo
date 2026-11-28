# Change manifest — Card Engine v2 alpha rev. 16

**Baseline:** rev. 15 (2026-11-27).  
**Status:** persistence foundation + first gameplay resolver vertical; no legacy integration.

## New gameplay implementation files

- `sistemas/card_engine_v2/gameplay.py`: trusted action registry, target-offer integration, remove/execute/sacrifice, shields, reactive Vingança, movement, bonus grants and protection grants.
- `sistemas/card_engine_v2/targeting.py`: revision-bound server offers, target predicates/metrics, deterministic sorting and `manual_primary_auto_fill` secondary-target preview.
- `tests/card_engine_v2/test_gameplay_resolver.py`: action, target, protection, reactivity, source-consumption and schema tests.
- `docs/card-engine-v2-gameplay-resolver-alpha-v0.1.md`: behavior, usage, validation and limitations.

## Existing files updated

- `sistemas/card_engine_v2/repository.py`: normalized Action Result costs and validates protection-grant events.
- `sistemas/card_engine_v2/__init__.py`: exports gameplay/targeting alpha public types.
- `sistemas/card_engine_v2/README.md`: new gameplay quickstart, server-trust boundary and limitations.
- `docs/schemas/card-game-target-offer.schema.v1.json`: adds `secondary_primary_instance_id` for the server-generated secondary-target preview.
- `docs/card-engine-v2-alpha-validation-v0.1.json` / `.md`: refreshed 62/62 test report and scope.
- `docs/card-engine-v2-implementation-alpha-v0.1.md`: current implementation inventory and open limits.
- `docs/card-engine-v2-alpha-change-manifest-v0.1.md`: this revision manifest.

## Functional scope added

The resolver currently handles five action types: `unit.remove`, `unit.sacrifice`, `unit.move`, `unit.grant_bonus` and `unit.grant_protection`. The same transaction commits snapshot changes, idempotency ledger, direct/reactive events and configured source/protection costs. Target offers are server-generated and revalidated at execution.

## Preserved boundaries

The following pre-existing runtime files remain byte-identical to rev. 15: `database.py`, `bot.py`, `sistemas/gwent.py`, `sistemas/cartas.py` and `site/app.js`. No existing legacy runtime entry point was modified.

No production database was opened or migrated. No API, Discord, frontend, catalog release or live rules registry was connected. The new engine uses a dedicated SQLite file and a synchronous repository; do not call it directly from an async event loop without an adapter/worker.
