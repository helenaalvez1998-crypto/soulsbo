#!/usr/bin/env python3
"""Structural validation for the Soulsbo CI/BUF/RSRX cross-decision review.

This checks review-document integrity only. It does not validate game rules,
approve recommendations, exercise the legacy runtime, or test persistence.
Run from the repository root:
    python docs/scripts/validate-card-game-cross-decision-review-v0.1.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
REPORT = DOCS / "card-game-cross-decision-review-ci-buf-rsrx-v0.1.json"


def main() -> int:
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    errors: list[str] = []
    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)

    check(data.get("metadata", {}).get("version") == "0.1", "review version must be 0.1")
    check(data.get("metadata", {}).get("runtime_integration") is False, "runtime_integration must be false")
    check(data.get("metadata", {}).get("owner_approval_inferred") is False, "owner approval must not be inferred")

    decisions = data.get("decisions", {})
    expected = {
        "CI": [f"CI-{i:03d}" for i in range(1, 15)],
        "BUF": [f"BUF-{i:03d}" for i in range(1, 15)],
        "RSRX": [f"RSRX-{i:02d}" for i in range(1, 11)],
    }
    all_ids: set[str] = set()
    for group, ids in expected.items():
        rows = decisions.get(group, [])
        actual = [row.get("id") for row in rows]
        check(len(rows) == len(ids), f"{group}: expected {len(ids)} rows, got {len(rows)}")
        check(actual == ids, f"{group}: IDs missing, duplicated, or out of order: {actual}")
        for row in rows:
            rid = row.get("id", "")
            check(rid not in all_ids, f"duplicate decision ID across groups: {rid}")
            all_ids.add(rid)
            check(row.get("status") == "OPEN_NOT_APPROVED", f"{rid}: status must remain OPEN_NOT_APPROVED")
            check(bool(row.get("recommendation", "").strip()), f"{rid}: recommendation is blank")
            check(isinstance(row.get("dependencies"), list), f"{rid}: dependencies must be a list")

    counts = data.get("counts", {})
    check(counts.get("CI") == 14, "counts.CI must equal 14")
    check(counts.get("BUF") == 14, "counts.BUF must equal 14")
    check(counts.get("RSRX_review_local") == 10, "counts.RSRX_review_local must equal 10")

    for group in data.get("cross_decision_groups", []):
        check(bool(group.get("id")), "cross-decision group has no id")
        check(bool(group.get("decisions")), f"{group.get('id')}: no linked decisions")
        for ref in group.get("decisions", []):
            check(ref in all_ids, f"{group.get('id')}: unknown decision reference {ref}")

    for gap in data.get("schema_gaps", []):
        check(bool(gap.get("recommended_change")), f"{gap.get('id')}: missing recommended change")
        for ref in gap.get("requires", []):
            check(ref in all_ids, f"{gap.get('id')}: unknown dependency {ref}")

    for key, value in data.get("guardrails", {}).items():
        check(value is False, f"guardrail {key} must remain false in this review")

    required_sources = [
        "card-game-card-instance-contract-v0.1.md",
        "card-game-buffs-decision-register-v0.1.md",
        "card-game-removal-sacrifice-resurrection-review-v0.1.md",
        "card-game-removal-resurrection-interaction-matrix-v0.1.md",
        "card-game-buffs-cross-interactions-v0.1.md",
        "card-game-manual-target-ui-parity-audit-v0.1.md",
        "card-game-target-selection-row-scope-audit-v0.1.md",
        "card-game-sequence-power-state-audit-v0.1.md",
    ]
    for source in required_sources:
        check((DOCS / source).is_file(), f"required source document missing: {source}")

    if errors:
        print(f"Cross-decision review: {checks - len(errors)}/{checks} passed; {len(errors)} failed")
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print(f"Cross-decision review: {checks}/{checks} passed; 0 failed")
    print("CI=14, BUF=14, RSRX-local=10; recommendations remain unapproved; runtime guardrails intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
