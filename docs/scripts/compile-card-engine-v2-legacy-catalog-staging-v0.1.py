#!/usr/bin/env python3
"""Compile the 137-model historical baseline into a review-only staging artifact.

This does not publish or activate any card. Runtime eligibility is limited to
AlphaCatalog's explicit allowlist, which is itself marked alpha-only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog  # noqa: E402

BASELINE = ROOT / "data/card_game/catalog-legacy-baseline-v0.1.json"
ALIASES = ROOT / "data/card_game/legacy-effect-aliases-v0.1.json"
ALLOWLIST = ROOT / "data/card_game/card-engine-v2-alpha-catalog.v0.2.json"
OUTPUT = ROOT / "data/card_game/card-engine-v2-legacy-catalog-staging.v0.1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> dict:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    aliases = json.loads(ALIASES.read_text(encoding="utf-8"))
    allowlist = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    alpha_card_allowlist = frozenset(AlphaCatalog().allowed_card_ids())
    if set(allowlist.get("card_ids", [])) != set(alpha_card_allowlist):
        raise RuntimeError("compiled allowlist differs from the AlphaCatalog-validated artifact")
    generic = {item["legacy_id"]: item for item in aliases.get("generic_and_special_aliases", [])}
    identities = {item["card_id"]: item for item in aliases.get("active_identity_card_overrides", [])}

    cards = []
    for raw in baseline.get("cards", []):
        card_id = raw["card_id"]
        skill_id = raw.get("declared_generic_skill_id")
        identity = identities.get(card_id)
        alias = generic.get(skill_id)
        if identity:
            candidate_effect_id = identity.get("canonical_effect_id")
            resolution_source = "active_identity_candidate"
            candidate_params = identity.get("default_effect_params", {})
        elif alias:
            candidate_effect_id = alias.get("canonical_effect_id")
            resolution_source = "generic_alias_candidate"
            candidate_params = alias.get("default_effect_params", {})
        else:
            candidate_effect_id = raw.get("effective_legacy_effect_id")
            resolution_source = raw.get("legacy_resolution_source", "unmapped")
            candidate_params = {}

        blockers = []
        if card_id not in alpha_card_allowlist:
            blockers.append("not_in_card_engine_v2_alpha_allowlist")
        if raw.get("faction_review_status") != "reviewed":
            blockers.append("faction_not_reviewed")
        if raw.get("legacy_cost_mismatch"):
            blockers.append("legacy_cost_mismatch_requires_cost_rebuild")
        if raw.get("migration_status") != "rebuilt":
            blockers.append("card_definition_not_rebuilt")
        if candidate_effect_id and card_id not in alpha_card_allowlist:
            blockers.append("effect_not_connected_to_alpha_runtime")

        cards.append(
            {
                "card_id": card_id,
                "display_name_legacy": raw.get("name_legacy"),
                "kind_legacy": raw.get("legacy_kind"),
                "slot_legacy": raw.get("legacy_slot"),
                "faction_legacy": raw.get("faction_legacy"),
                "faction_id_candidate": raw.get("faction_id_candidate"),
                "faction_review_status": raw.get("faction_review_status"),
                "row_legacy": raw.get("row_legacy"),
                "power_base_legacy": raw.get("power_base_legacy"),
                "rarity_legacy": raw.get("rarity_legacy"),
                "legacy_deck_cost": raw.get("deck_cost_legacy"),
                "legacy_cost_mismatch": bool(raw.get("legacy_cost_mismatch")),
                "generic_skill_id_legacy": skill_id,
                "candidate_effect_id": candidate_effect_id,
                "candidate_effect_params": candidate_params,
                "effect_resolution_source": resolution_source,
                "combo_tags_legacy": list(raw.get("legacy_combo_tags") or []),
                "migration_status": raw.get("migration_status"),
                "runtime_status": "alpha_test_only" if card_id in alpha_card_allowlist else "blocked_staging_only",
                "runtime_blockers": blockers,
                "source_class": raw.get("source_class"),
                "source_status": raw.get("legacy_resolution_status_from_audit"),
            }
        )

    counts = Counter(card["runtime_status"] for card in cards)
    artifact = {
        "artifact_type": "soulsbo_card_engine_v2_legacy_catalog_staging",
        "version": "0.1",
        "status": "review_only_not_a_runtime_catalog",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "baseline_file": BASELINE.name,
            "baseline_sha256": sha256(BASELINE),
            "aliases_file": ALIASES.name,
            "aliases_sha256": sha256(ALIASES),
            "allowlist_file": ALLOWLIST.name,
            "allowlist_sha256": sha256(ALLOWLIST),
            "source_snapshot_status": baseline.get("status"),
        },
        "summary": {
            "historical_model_count": len(cards),
            "alpha_test_only_count": counts.get("alpha_test_only", 0),
            "blocked_staging_only_count": counts.get("blocked_staging_only", 0),
            "not_rebuilt_count": sum(card["migration_status"] != "rebuilt" for card in cards),
            "faction_unreviewed_count": sum(card["faction_review_status"] != "reviewed" for card in cards),
            "legacy_cost_mismatch_count": sum(card["legacy_cost_mismatch"] for card in cards),
        },
        "policy": [
            "This file contains all historical model records for traceability, not approved new definitions.",
            "Only the 24 IDs in the explicit, hash-pinned AlphaCatalog allowlist are executable in the isolated v2 alpha.",
            "The remaining 113 historical models stay blocked, regardless of whether their legacy effect appears simple.",
            "Faction, cost, effect parameters and card text still require authorial review before publication.",
            "No rarity-based mechanical amplification is introduced by this staging compiler.",
        ],
        "cards": sorted(cards, key=lambda item: item["card_id"]),
    }
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(artifact["summary"], ensure_ascii=False, indent=2))
    print(f"OUTPUT: {OUTPUT.relative_to(ROOT)}")
    return artifact


if __name__ == "__main__":
    main()
