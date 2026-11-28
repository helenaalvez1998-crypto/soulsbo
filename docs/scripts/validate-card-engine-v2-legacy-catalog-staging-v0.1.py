#!/usr/bin/env python3
"""Validate the review-only 137-card staging artifact and its runtime boundary."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog  # noqa: E402

BASELINE = ROOT / "data/card_game/catalog-legacy-baseline-v0.1.json"
ALLOWLIST = ROOT / "data/card_game/card-engine-v2-alpha-catalog.v0.2.json"
STAGING = ROOT / "data/card_game/card-engine-v2-legacy-catalog-staging.v0.1.json"
REPORT_JSON = ROOT / "docs/card-engine-v2-legacy-catalog-staging-validation-v0.1.json"
REPORT_MD = ROOT / "docs/card-engine-v2-legacy-catalog-staging-validation-v0.1.md"


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
    assert len(active_ids) == 24
    assert {card_id for card_id, status in statuses.items() if status == "alpha_test_only"} == active_ids
    blocked = {card_id for card_id, status in statuses.items() if status == "blocked_staging_only"}
    assert len(blocked) == 113 and not blocked.intersection(active_ids)
    assert all(item["runtime_blockers"] for item in records if item["runtime_status"] == "blocked_staging_only")
    assert staging["source"]["baseline_sha256"] == sha256(BASELINE)
    assert staging["source"]["allowlist_sha256"] == sha256(ALLOWLIST)
    expected_summary = {
        "historical_model_count": 137,
        "alpha_test_only_count": 24,
        "blocked_staging_only_count": 113,
        "not_rebuilt_count": 137,
        "faction_unreviewed_count": 137,
        "legacy_cost_mismatch_count": 19,
    }
    assert staging["summary"] == expected_summary
    report = {
        "status": "PASS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "review_only_status": True,
            "all_137_historical_ids_present_once": True,
            "allowlist_matches_alpha_catalog": True,
            "24_alpha_models_only": True,
            "113_models_blocked": True,
            "blocked_models_have_blockers": True,
            "source_hashes_match": True,
            "staging_summary_matches_expected": True,
        },
        "summary": expected_summary,
        "source_sha256": {
            BASELINE.name: sha256(BASELINE),
            ALLOWLIST.name: sha256(ALLOWLIST),
            STAGING.name: sha256(STAGING),
        },
        "runtime_integration": False,
        "production_database_access": False,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(
        "# Card Engine v2 — validação do staging histórico v0.1\n\n"
        "**Status:** PASS\n\n"
        "| Verificação | Resultado |\n|---|---|\n"
        + "\n".join(f"| `{name}` | PASS |" for name in report["checks"])
        + "\n\n**Resumo:** 137 registros históricos; 24 permitidos somente para testes alpha; 113 bloqueados. Todos os 137 ainda constam como não reconstruídos e sem revisão de facção no snapshot de origem; 19 têm divergência histórica de custo.\n\n"
        "Este resultado valida a integridade e a fronteira do artefato staging. Não aprova cartas, efeitos, custos, facções ou publicação.\n",
        encoding="utf-8",
    )
    print("Card Engine v2 legacy staging: PASS")
    print("137 historical models | 24 alpha-only | 113 blocked")
    print("Source hashes: PASS | Runtime boundary: PASS")
    print(f"JSON: {REPORT_JSON.relative_to(ROOT)}")
    print(f"Markdown: {REPORT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
