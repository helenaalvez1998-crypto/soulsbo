#!/usr/bin/env python3
"""Validate an authored v1 card catalogue against its effect/combo registries.

Example:
  python docs/scripts/validate-card-catalog-v1.py \\
    --catalog path/to/catalog-v1.json \\
    --registry path/to/effect-registry-v1.json

The command does not compile cost/rarity: the numeric balance rules are still
pending approval. It validates structure, references, IDs and the 30% purity
quota only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas.card_contract import validate_catalog, validate_effect_registry  # noqa: E402


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"não foi possível ler {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido em {path}:{exc.lineno}:{exc.colno}: {exc.msg}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, type=Path, help="JSON do catálogo autoral v1")
    parser.add_argument("--registry", required=True, type=Path, help="JSON dos efeitos e combos")
    parser.add_argument("--pure-ratio", type=float, default=0.30, help="quota pura; padrão 0.30")
    args = parser.parse_args()

    try:
        catalog = read_json(args.catalog)
        registry = read_json(args.registry)
    except ValueError as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2

    registry_result = validate_effect_registry(registry)
    if not registry_result.valid:
        print(json.dumps({"valid": False, "stage": "registry", "errors": list(registry_result.errors)}, ensure_ascii=False, indent=2))
        return 2

    effects = registry["effects"]
    combos = registry["combos"]
    effect_registry = {item["effect_id"]: item for item in effects}
    effect_ids = set(effect_registry)
    combo_tags = {tag for item in combos for tag in item["required_tags"]}
    result = validate_catalog(
        catalog,
        known_effect_ids=effect_ids,
        known_combo_tags=combo_tags,
        effect_registry=effect_registry,
        pure_ratio=args.pure_ratio,
    )
    payload = {
        "valid": result.valid,
        "card_count": len(catalog.get("cards", [])) if isinstance(catalog, dict) and isinstance(catalog.get("cards"), list) else 0,
        "known_effect_count": len(effect_ids),
        "known_combo_tag_count": len(combo_tags),
        "effect_parameter_validation": True,
        "combo_minimum_and_priority_validation": True,
        "pure_ratio_required": args.pure_ratio,
        "errors": list(result.errors),
        "warnings": list(result.warnings),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
