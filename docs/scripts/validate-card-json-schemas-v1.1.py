#!/usr/bin/env python3
"""Validate both canonical card/effect JSON Schemas and their examples.

Optional developer tool: requires the `jsonschema` package. It is not a runtime
requirement of the bot.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("Dependência opcional ausente: instale jsonschema para validar Draft 2020-12.", file=sys.stderr)
    raise SystemExit(2)

PAIRS = (
    ("data/card_game/card-definition.schema.v1.json", "data/card_game/card-definition.example.v1.json"),
    ("data/card_game/effect-registry.schema.v1.json", "data/card_game/effect-registry.example.v1.json"),
)


def main() -> int:
    results = []
    for schema_relative, example_relative in PAIRS:
        schema = json.loads((ROOT / schema_relative).read_text(encoding="utf-8"))
        example = json.loads((ROOT / example_relative).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = sorted(Draft202012Validator(schema).iter_errors(example), key=lambda item: list(item.path))
        results.append({
            "schema": schema_relative,
            "example": example_relative,
            "schema_valid": True,
            "example_valid": not errors,
            "errors": [error.message for error in errors],
        })
    payload = {"draft": "2020-12", "checks": results, "all_passed": all(item["example_valid"] for item in results)}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
