#!/usr/bin/env python3
"""Validate the current 137-card staging artifact against alpha catalog v0.3."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog
BASELINE = ROOT / "data/card_game/catalog-legacy-baseline-v0.1.json"
ALLOWLIST = ROOT / "data/card_game/card-engine-v2-alpha-catalog.v0.3.json"
STAGING = ROOT / "data/card_game/card-engine-v2-legacy-catalog-staging.v0.2.json"
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
def main() -> int:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    allowlist = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    active_ids = set(AlphaCatalog().allowed_card_ids())
    records = staging["cards"]
    record_ids = [item["card_id"] for item in records]
    statuses = {item["card_id"]: item["runtime_status"] for item in records}
    assert staging["status"] == "review_only_not_a_runtime_catalog"
    assert len(record_ids) == len(set(record_ids)) == 137
    assert set(record_ids) == {item["card_id"] for item in baseline["cards"]}
    assert active_ids == set(allowlist["card_ids"])
    assert len(active_ids) == 27
    assert {card_id for card_id, status in statuses.items() if status == "alpha_test_only"} == active_ids
    blocked = {card_id for card_id, status in statuses.items() if status == "blocked_staging_only"}
    assert len(blocked) == 110 and not blocked.intersection(active_ids)
    assert all(item["runtime_blockers"] for item in records if item["runtime_status"] == "blocked_staging_only")
    assert staging["source"]["baseline_sha256"] == sha256(BASELINE)
    assert staging["source"]["allowlist_sha256"] == sha256(ALLOWLIST)
    expected_summary = {
        "historical_model_count": 137,
        "alpha_test_only_count": 27,
        "blocked_staging_only_count": 110,
        "not_rebuilt_count": 137,
        "faction_unreviewed_count": 137,
        "legacy_cost_mismatch_count": 19,
    }
    assert staging["summary"] == expected_summary

    report = {
        "status": "PASS",
        "artifact": "card-engine-v2-legacy-catalog-staging.v0.2.json",
        "checks": {
            "review_only_status": True,
            "all_137_historical_ids_present_once": True,
            "allowlist_matches_alpha_catalog": True,
            "27_alpha_models_only": True,
            "110_models_blocked": True,
            "blocked_models_have_blockers": True,
            "source_hashes_match": True,
            "staging_summary_matches_expected": True,
        },
        "summary": expected_summary,
        "source_sha256": {
            "catalog-legacy-baseline-v0.1.json": sha256(BASELINE),
            "card-engine-v2-alpha-catalog.v0.3.json": sha256(ALLOWLIST),
            "card-engine-v2-legacy-catalog-staging.v0.2.json": sha256(STAGING),
        },
        "runtime_integration": False,
        "production_database_access": False,
    }
    json_path = ROOT / "docs/card-engine-v2-legacy-catalog-staging-validation-v0.2.json"
    md_path = ROOT / "docs/card-engine-v2-legacy-catalog-staging-validation-v0.2.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(
        "# Validação do staging histórico Card Engine v2 v0.2\n\n"
        "**Status:** PASS  \n"
        "**Modelos históricos:** 137  \n"
        "**Alpha-only:** 27  \n"
        "**Bloqueados:** 110\n\n"
        "Foram verificados IDs únicos, igualdade com o snapshot histórico, partição exata da allowlist, bloqueadores presentes nos registros bloqueados, resumo e SHA-256 das três fontes. Este staging é review-only e não é carregado como catálogo de runtime.\n\n"
        "O script `docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py` regenera este relatório.\n",
        encoding="utf-8",
    )
    print("Card Engine v2 legacy staging v0.2: PASS")
    print("137 historical models | 27 alpha-only | 110 blocked")
    print("Source hashes and allowlist/staging partition: PASS")
    print(f"Reports written: {json_path.relative_to(ROOT)}, {md_path.relative_to(ROOT)}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
