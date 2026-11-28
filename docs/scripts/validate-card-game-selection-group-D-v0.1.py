#!/usr/bin/env python3
"""Validate Group D candidate schemas/examples and decision register. Read-only docs test."""
from __future__ import annotations
import json
from pathlib import Path
import sys

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise SystemExit("jsonschema is required: python -m pip install jsonschema") from exc

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "docs" / "schemas"
EXAMPLES = ROOT / "docs" / "examples"

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    cases = 0
    schemas = {
      "request": load(SCHEMAS / "card-game-action-request.schema.v1.json"),
      "policy": load(SCHEMAS / "card-game-effect-target-policy.schema.v1.json"),
      "result": load(SCHEMAS / "card-game-action-result.schema.v1.json"),
      "offer": load(SCHEMAS / "card-game-target-offer.schema.v1.json"),
    }
    for name, schema in schemas.items():
      Draft202012Validator.check_schema(schema)
      print(f"PASS schema:{name}")
      cases += 1
    examples = [
      ("request", "card-game-action-request.example.v1.json"),
      ("policy", "card-game-effect-target-policy.example.v1.json"),
      ("result", "card-game-action-result.example.v1.json"),
      ("offer", "card-game-target-offer.example.v1.json"),
    ]
    for kind, filename in examples:
      Draft202012Validator(schemas[kind], format_checker=FormatChecker()).validate(load(EXAMPLES / filename))
      print(f"PASS example:{filename}")
      cases += 1
    register = load(ROOT / "docs" / "card-game-selection-group-D-decisions-v0.1.json")
    approval = load(ROOT / "docs" / "card-game-selection-group-D-approval-v0.1.json")
    assert register["status"] == "OWNER_APPROVED"
    assert len(register["decisions"]) == 12
    assert len({d["id"] for d in register["decisions"]}) == 12
    assert all(d["status"] == "OWNER_APPROVED" for d in register["decisions"])
    assert approval["status"] == "OWNER_APPROVED"
    assert set(approval["approved_decision_ids"]) == {d["id"] for d in register["decisions"]}
    print("PASS decision-register:12 approved, unique and matched to approval evidence")
    cases += 1
    # BUF-001 is already approved: no rarity input may be present in the target policy.
    policy = load(EXAMPLES / "card-game-effect-target-policy.example.v1.json")
    serialized = json.dumps(policy).casefold()
    assert "rarity" not in serialized and "potency_rarity" not in serialized
    print("PASS policy:no rarity dependency")
    cases += 1
    # Cross-check independent cost dimensions and gameplay outcomes.
    result = load(EXAMPLES / "card-game-action-result.example.v1.json")
    assert result["outcome"] == "partial"
    assert result["costs"]["turn_consumed"] is True
    assert result["costs"]["source_consumed"] is True
    assert len(result["target_results"]) == 2
    assert {x["outcome"] for x in result["target_results"]} == {"applied", "blocked"}
    print("PASS result:mixed per-target outcome and separate costs")
    cases += 1
    offer = load(EXAMPLES / "card-game-target-offer.example.v1.json")
    assert offer["state_revision"] == 17 and offer["metrics"]["eligibility_metric"] == "effective_power"
    assert offer["requires_confirmation"] is True and offer["secondary_targets_preview"] == []
    print("PASS offer:server metrics tied to revision and explicit preview")
    cases += 1
    try:
      Draft202012Validator(schemas["policy"], format_checker=FormatChecker()).validate({**policy, "rarity_id": "rare"})
    except Exception:
      print("PASS policy:additional rarity input rejected")
      cases += 1
    else:
      raise AssertionError("target policy accepted rarity input despite BUF-001")
    print(f"\nResultado: {cases}/{cases}; 0 falhas.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
