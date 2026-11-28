#!/usr/bin/env python3
"""Static cross-check between the current card/effect catalogs and engine handlers.

This is a source inspection aid. It does not execute games and is not proof of full
branch coverage; pair it with validate-card-effect-smoke-v0.1.py.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas import cartas, gwent  # noqa: E402

OUT = ROOT / "docs" / "card-game-handler-coverage-v0.1.json"


def _string_literals(node: ast.AST) -> set[str]:
    values: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            values.add(child.value)
    return values


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise KeyError(f"Function not found: {name}")


def _compared_values(fn: ast.FunctionDef, variable: str) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(fn):
        if not isinstance(node, ast.Compare):
            continue
        left_names = {item.id for item in ast.walk(node.left) if isinstance(item, ast.Name)}
        if variable not in left_names:
            continue
        for comparator in node.comparators:
            result.update(_string_literals(comparator))
    return result


def _lifecycle_hability_values(fn: ast.FunctionDef) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(fn):
        if not isinstance(node, ast.Compare):
            continue
        has_habilidade_get = any(
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr == "get"
            and item.args
            and isinstance(item.args[0], ast.Constant)
            and item.args[0].value == "habilidade"
            for item in ast.walk(node.left)
        )
        if has_habilidade_get:
            for comparator in node.comparators:
                result.update(_string_literals(comparator))
    return result


def main() -> None:
    source_path = ROOT / "sistemas" / "gwent.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    apply_fn = _function(tree, "aplicar_jogada")
    identity_fn = _function(tree, "_aplicar_habilidade_identidade")
    removal_fn = _function(tree, "_remover_unidade")
    round_fn = _function(tree, "_resolve_round")

    catalog_skills = set(cartas.HABILIDADES)
    direct_skill_values = _compared_values(apply_fn, "skill")
    # `skill in {"instinto", "fome_abismo"}` is captured by AST set literals above.
    lifecycle_removal = _lifecycle_hability_values(removal_fn)
    lifecycle_round = _lifecycle_hability_values(round_fn)
    lifecycle_catalog_hooks = (lifecycle_removal | lifecycle_round) & catalog_skills
    declared_covered = (direct_skill_values | lifecycle_catalog_hooks) & catalog_skills
    missing_declared = sorted(catalog_skills - declared_covered)

    identity_handler_values = _compared_values(identity_fn, "effect")
    active_identity_effects = {entry["effect"] for entry in gwent.CARD_IDENTITY_ABILITIES.values()}
    stale_identity_handler_values = sorted(identity_handler_values - active_identity_effects)
    active_without_handler = sorted(active_identity_effects - identity_handler_values)

    current_card_ids = set(cartas.CARTAS_POR_ID)
    tagged_map_ids = set(gwent.CARD_SYNERGY_TAGS)
    orphan_tag_ids = sorted(tagged_map_ids - current_card_ids)
    tag_providers = {
        tag: sorted(
            card_id for card_id in current_card_ids
            if tag in gwent.CARD_SYNERGY_TAGS.get(card_id, set())
        )
        for combo in gwent.SYNERGY_COMBOS.values()
        for tag in combo["tags"]
    }
    combo_coverage = []
    for combo_id, combo in gwent.SYNERGY_COMBOS.items():
        providers = {tag: tag_providers[tag] for tag in sorted(combo["tags"])}
        missing_tags = [tag for tag, ids in providers.items() if not ids]
        combo_coverage.append({
            "id": combo_id,
            "name": combo["name"],
            "required_tags": sorted(combo["tags"]),
            "minimum_participants": combo.get("minimum"),
            "provider_counts": {tag: len(ids) for tag, ids in providers.items()},
            "impossible_due_to_missing_tag_provider": bool(missing_tags),
            "missing_tags": missing_tags,
        })

    report = {
        "metadata": {
            "document": "Effect handler coverage audit v0.1",
            "status": "STATIC SOURCE AUDIT; PAIR WITH RUNTIME SMOKE TESTS",
            "source": "sistemas/cartas.py and sistemas/gwent.py from supplied baseline ZIP",
        },
        "generic_skills": {
            "catalog_count": len(catalog_skills),
            "direct_handler_literal_values_count": len(direct_skill_values & catalog_skills),
            "lifecycle_hook_ids_found_in_runtime": sorted(lifecycle_catalog_hooks),
            "declared_ids_covered_by_direct_or_lifecycle_hook": len(declared_covered),
            "declared_ids_without_matching_handler_reference": missing_declared,
            "additional_hidden_lifecycle_hooks_not_in_catalog": sorted((lifecycle_removal | lifecycle_round) - catalog_skills),
        },
        "identity_effects": {
            "active_identity_card_count": len(gwent.CARD_IDENTITY_ABILITIES),
            "active_effect_ids": sorted(active_identity_effects),
            "identity_resolver_effect_branches_count": len(identity_handler_values),
            "stale_or_unmapped_identity_handler_effect_ids": stale_identity_handler_values,
            "active_effect_ids_without_resolver_branch": active_without_handler,
        },
        "synergies": {
            "tag_map_card_ids_including_orphans": len(tagged_map_ids),
            "current_catalog_card_ids_with_tags": len(tagged_map_ids & current_card_ids),
            "orphan_tag_card_ids": orphan_tag_ids,
            "total_tag_associations": sum(len(tags) for tags in gwent.CARD_SYNERGY_TAGS.values()),
            "combo_count": len(gwent.SYNERGY_COMBOS),
            "combo_required_tag_coverage": combo_coverage,
        },
        "other_catalog_counts": {
            "leader_count": len(gwent.LEADERS),
            "relic_ids": sorted(card_id for card_id in current_card_ids if card_id.startswith("reliquia_")),
        },
        "limitations": [
            "AST literal matching detects source references, not full control-flow reachability.",
            "A skill may have a handler reference but still fail under some card states or target conditions.",
            "Combo tag coverage proves at least one provider exists for each required tag, not that every deck can activate the combo.",
            "Use the runtime smoke report and controlled branch tests for behavior; this static report does not replace them.",
        ],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "generic": report["generic_skills"],
        "identity": {
            "active": len(active_identity_effects),
            "branches": len(identity_handler_values),
            "stale": len(stale_identity_handler_values),
            "active_without_handler": active_without_handler,
        },
        "synergy": {
            "combos": len(gwent.SYNERGY_COMBOS),
            "orphan_ids": orphan_tag_ids,
            "impossible_combos": [x["id"] for x in combo_coverage if x["impossible_due_to_missing_tag_provider"]],
        },
        "output": str(OUT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
