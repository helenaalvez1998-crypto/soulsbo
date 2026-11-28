#!/usr/bin/env python3
"""Consolidate the current synthetic behavior-assertion reports (v0.2)."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SUITES = [
    ("generic_initial", "card-game-effect-behavior-assertions-v0.1.json", "Initial representative effect cases"),
    ("active_identities", "card-game-identity-behavior-assertions-v0.1.json", "22 active identity effects plus negative/limit cases"),
    ("generic_units", "card-game-generic-unit-assertions-v0.1.json", "Generic unit effects, selected positive and negative cases"),
    ("lifecycle", "card-game-lifecycle-assertions-v0.1.json", "Removal and round-end lifecycle effects"),
    ("specials_relics", "card-game-special-relic-assertions-v0.1.json", "Selected special effects and all six relic handlers"),
    ("leaders", "card-game-leader-assertions-v0.1.json", "All ten leader handlers plus negative/limit cases"),
    ("combos_faction_passive", "card-game-combo-faction-assertions-v0.1.json", "All 27 combos plus four faction passives and special exclusion"),
]
reports = []
for suite_id, filename, label in SUITES:
    path = DOCS / filename
    if not path.exists():
        raise SystemExit(f"Missing suite report: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    counts = data.get("counts", {})
    total = counts.get("assertions", counts.get("total_assertions"))
    passed = counts.get("passed")
    failed = counts.get("failed")
    if not isinstance(total, int) or not isinstance(passed, int) or not isinstance(failed, int):
        raise SystemExit(f"Unsupported count schema in {filename}: {counts}")
    case_statuses = [x.get("status") for x in data.get("cases", [])]
    if case_statuses and (len(case_statuses) != total or any(x not in {"passed", "failed"} for x in case_statuses)):
        raise SystemExit(f"Case list/count mismatch in {filename}")
    if passed + failed != total:
        raise SystemExit(f"Count arithmetic mismatch in {filename}")
    reports.append({
        "suite": suite_id,
        "label": label,
        "source": f"docs/{filename}",
        "assertions": total,
        "passed": passed,
        "failed": failed,
        "metadata_status": data.get("metadata", {}).get("status"),
        "limitations": data.get("limitations", []),
    })

coverage = json.loads((DOCS / "card-game-handler-coverage-v0.1.json").read_text(encoding="utf-8"))
stale = json.loads((DOCS / "card-game-stale-identity-disposition-v0.1.json").read_text(encoding="utf-8"))
assertions = sum(x["assertions"] for x in reports)
passed = sum(x["passed"] for x in reports)
failed = sum(x["failed"] for x in reports)
summary = {
    "metadata": {
        "document": "Card game behavioral validation aggregate v0.2",
        "status": "DIAGNOSTIC ONLY; SYNTHETIC CONTROLLED STATES; NOT BALANCE OR PRODUCTION INTEGRATION",
        "baseline": "soulsbo-main(1).zip",
        "date": "2026-11-27",
        "runtime_modified": False,
        "runner": "docs/scripts/summarize-card-game-behavior-v0.2.py",
    },
    "counts": {"suites": len(reports), "assertions": assertions, "passed": passed, "failed": failed},
    "suites": reports,
    "static_handler_coverage": {
        "generic_catalog_ids": coverage["generic_skills"]["catalog_count"],
        "generic_direct_handler_values": coverage["generic_skills"]["direct_handler_literal_values_count"],
        "generic_lifecycle_hooks": coverage["generic_skills"]["lifecycle_hook_ids_found_in_runtime"],
        "generic_declared_ids_without_handler": coverage["generic_skills"]["declared_ids_without_matching_handler_reference"],
        "hidden_lifecycle_hooks_not_in_catalog": coverage["generic_skills"]["additional_hidden_lifecycle_hooks_not_in_catalog"],
        "active_identities": coverage["identity_effects"]["active_identity_card_count"],
        "inactive_identity_branches": coverage["identity_effects"]["stale_or_unmapped_identity_handler_effect_ids"],
        "combos": coverage["synergies"]["combo_count"],
        "orphan_tag_card_ids": coverage["synergies"]["orphan_tag_card_ids"],
    },
    "stale_identity_disposition": {
        "inactive_branches": stale["counts"]["stale_branches"],
        "v18_filtered_identity_cards": stale["counts"]["v18_filtered_identity_cards"],
        "unmapped_legacy_field_effects": stale["counts"]["unmapped_legacy_field_effects"],
        "stale_v75_effects": stale["counts"]["stale_v75_effects"],
        "hidden_gloria_cards": stale["counts"]["hidden_gloria_cards"],
    },
    "limitations": [
        "The assertions are distributed across seven suites and are not distinct abilities; some functional areas are intentionally exercised by more than one suite. The current total is 219 scenarios.",
        "All tests invoke the current in-memory engine with synthetic fixtures. They do not validate the production database, HTTP APIs, browser frontend, Discord command handlers, Cloudflare R2 or published image assets.",
        "The suites cover selected positive, negative and limit cases; they do not enumerate every branch combination, rarity modifier, state interaction or AI decision.",
        "Each of the 27 combos is tested with one concrete activating pair discovered from the current tag map. Alternate card combinations, overlapping-combo precedence and all tag permutations are not exhaustive.",
        "Faction passives are tested for each of the four factions with foreign/first/second unit and round-reset scenarios; faction-specific card identities and all rarity modifiers are not exhausted.",
        "Passing assertions do not measure effect value, deck strength, win rate, faction parity or competitive balance.",
        "The `sobrevivente` ability remains without a corresponding lifecycle handler in the current source audit; `gloria` remains a hidden round-end hook outside HABILIDADES.",
        "The 28 inactive identity branches are inventoried but not deleted; all require an explicit keep/merge/redesign/remove decision and tag/combo review.",
        "EFP v0.2 and balance spec v0.1 remain proposals, not approved rules; no cost, rarity, deck budget or card distribution has been implemented.",
    ],
    "next_steps": [
        "Use the combo/faction suite as a baseline, then cover alternate tag-provider combinations, overlapping-combo precedence, climate interactions, round transitions, AI actions and cross-effect interactions with positive and negative assertions.",
        "Create explicit behavior contracts for uncovered generic/special/identity interactions and remaining branches." ,
        "Review and decide the disposition of all 28 inactive identity branches and the separate `gloria`/`sobrevivente` lifecycle issues before deleting or reactivating code.",
        "Build a deterministic full-match simulator with documented policies and matchup coverage across all four factions.",
        "Only then calibrate EFP and propose costs, rarities and the deck budget for user approval.",
    ],
}
(DOCS / "card-game-behavior-validation-v0.2.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary["counts"], ensure_ascii=False))
print(f"wrote {DOCS / 'card-game-behavior-validation-v0.2.json'}")
if failed:
    raise SystemExit(1)
