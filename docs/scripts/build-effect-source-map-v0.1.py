#!/usr/bin/env python3
"""ARCHIVED pre-policy source map generator.

The v0.1 JSON is a frozen baseline index. This script imports source from its
checkout and refuses to overwrite the historical output on a post-policy tree;
use build-effect-source-map-v0.2.py for current source references.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas import cartas, gwent

# Keep the historical v0.1 source-map artifact frozen on the current tree.
if any("priority" in combo for combo in gwent.SYNERGY_COMBOS.values()):
    raise SystemExit(
        "ARCHIVED v0.1 source map: current runtime includes the approved combo policy. "
        "Do not overwrite the baseline index; use docs/scripts/build-effect-source-map-v0.2.py."
    )

OUT = ROOT / "docs" / "card-game-effect-source-map-v0.1.json"


def load_source(relative: str) -> tuple[str, list[str], ast.AST, dict[int, list[ast.AST]]]:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tree = ast.parse(text, filename=relative)
    parents: dict[int, list[ast.AST]] = {}
    stack: list[ast.AST] = [tree]
    while stack:
        node = stack.pop()
        for child in ast.iter_child_nodes(node):
            parents.setdefault(id(child), []).append(node)
            stack.append(child)
    return text, lines, tree, parents


SOURCES = {
    "sistemas/gwent.py": load_source("sistemas/gwent.py"),
    "sistemas/cartas.py": load_source("sistemas/cartas.py"),
}


def names_in(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def strings_in(node: ast.AST) -> set[str]:
    return {n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def nearest_function(node: ast.AST, parents: dict[int, list[ast.AST]]) -> str:
    current = node
    while parents.get(id(current)):
        current = parents[id(current)][0]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
    return "<module>"


def source_refs(identifier: str, *, only_engine: bool = False) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    candidates = ["sistemas/gwent.py"] if only_engine else list(SOURCES)
    for relative in candidates:
        text, lines, tree, parents = SOURCES[relative]
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and node.value == identifier and isinstance(node.value, str)):
                continue
            # Only include executable AST nodes; comments/docstrings are not parsed
            # here as references to behavior.
            chain: list[ast.AST] = []
            current = node
            while parents.get(id(current)):
                current = parents[id(current)][0]
                chain.append(current)
            fn = next((n.name for n in chain if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))), "<module>")
            nearest_if = next((n for n in chain if isinstance(n, ast.If) and identifier in strings_in(n.test)), None)
            line = getattr(node, "lineno", 1)
            context_start = max(1, line - 2)
            context_end = min(len(lines), line + 2)
            ref: dict[str, Any] = {
                "file": relative,
                "function": fn,
                "literal_line": line,
                "context": "\n".join(f"{i}: {lines[i-1]}" for i in range(context_start, context_end + 1)),
            }
            if nearest_if is not None:
                test_text = ast.get_source_segment(text, nearest_if.test) or ""
                body_nodes = list(nearest_if.body)
                body_end = max((getattr(child, "end_lineno", child.lineno) for child in body_nodes), default=nearest_if.lineno)
                ref["branch"] = {
                    "test": test_text,
                    "line_start": nearest_if.lineno,
                    "body_line_start": min((child.lineno for child in body_nodes), default=nearest_if.lineno),
                    "body_line_end": body_end,
                    "body_size_lines": body_end - nearest_if.lineno + 1,
                    "body_excerpt": "\n".join(
                        f"{i}: {lines[i-1]}"
                        for i in range(nearest_if.lineno, min(body_end, nearest_if.lineno + 24) + 1)
                    ),
                }
            refs.append(ref)
    # Remove duplicates by file/function/literal line.
    unique: dict[tuple[str, str, int], dict[str, Any]] = {}
    for ref in refs:
        key = (ref["file"], ref["function"], ref["literal_line"])
        unique[key] = ref
    return sorted(unique.values(), key=lambda x: (x["file"], x["literal_line"]))


def function_ref(relative: str, function_name: str) -> dict[str, Any] | None:
    text, lines, tree, _ = SOURCES[relative]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return {
                "file": relative,
                "function": function_name,
                "line_start": node.lineno,
                "line_end": getattr(node, "end_lineno", node.lineno),
                "source_excerpt": "\n".join(
                    f"{i}: {lines[i-1]}"
                    for i in range(node.lineno, min(getattr(node, "end_lineno", node.lineno), node.lineno + 30) + 1)
                ),
            }
    return None


generic = []
for skill_id, metadata in cartas.HABILIDADES.items():
    refs = source_refs(skill_id, only_engine=True)
    functions = {ref["function"] for ref in refs}
    if "aplicar_jogada" in functions:
        execution_class = "direct_play_handler"
    elif functions.intersection({"_remover_unidade", "_resolve_round"}):
        execution_class = "lifecycle_hook"
    else:
        execution_class = "no_matching_engine_handler"
    generic.append({
        "id": skill_id,
        "name": metadata.get("nome", ""),
        "description": metadata.get("texto", ""),
        "execution_class": execution_class,
        "engine_references": refs,
        "catalog_references": source_refs(skill_id),
    })

identities = []
for card_id, data in gwent.CARD_IDENTITY_ABILITIES.items():
    effect_id = str(data.get("effect", ""))
    identities.append({
        "card_id": card_id,
        "effect_id": effect_id,
        "name": data.get("name", ""),
        "description": data.get("text", ""),
        "engine_references": source_refs(effect_id, only_engine=True),
    })

leaders = []
for leader_id, data in gwent.LEADERS.items():
    effect_id = str(data.get("effect", ""))
    leaders.append({
        "leader_id": leader_id,
        "name": data.get("name", ""),
        "faction": data.get("faction", ""),
        "effect_id": effect_id,
        "description": data.get("description", ""),
        "engine_references": source_refs(effect_id, only_engine=True),
    })

combos = []
combo_resolver = function_ref("sistemas/gwent.py", "_aplicar_combo_de_cartas")
for combo_id, data in gwent.SYNERGY_COMBOS.items():
    combos.append({
        "id": combo_id,
        "name": data.get("name", ""),
        "required_tags": sorted(data.get("required_tags", [])),
        "minimum": data.get("minimum"),
        "bonus": data.get("bonus", 0),
        "team_bonus": data.get("team_bonus", 0),
        "description": data.get("description", ""),
        "resolver": combo_resolver,
        "note": "Combo declarativo; os dados definem tags/participantes/bônus e o resolver comum aplica as condições.",
    })

hooks = {
    name: function_ref("sistemas/gwent.py", name)
    for name in ("_remover_unidade", "_resolve_round", "aplicar_jogada", "_aplicar_habilidade_identidade", "_aplicar_potencia_raridade")
}

report = {
    "metadata": {
        "document": "Mapa de evidências de código por efeito v0.1",
        "generated_at": "2026-11-27",
        "baseline": "soulsbo-main(1).zip",
        "status": "SOURCE MAP ONLY; DOES NOT APPROVE EFP OR CHANGE RUNTIME",
        "method": "Python AST over sistemas/cartas.py and sistemas/gwent.py; exact string literals linked to enclosing functions and nearest matching if branch where available.",
        "warning": "A ocorrência de um literal não prova que o ramo seja alcançável em produção nem que a descrição corresponda ao efeito completo. Conferir o ramo e executar testes comportamentais.",
    },
    "counts": {
        "generic_skills": len(generic),
        "generic_direct_play_handlers": sum(x["execution_class"] == "direct_play_handler" for x in generic),
        "generic_lifecycle_hooks": sum(x["execution_class"] == "lifecycle_hook" for x in generic),
        "generic_without_matching_handler": [x["id"] for x in generic if x["execution_class"] == "no_matching_engine_handler"],
        "identity_effects": len(identities),
        "identity_without_engine_literal_refs": [x["effect_id"] for x in identities if not x["engine_references"]],
        "leaders": len(leaders),
        "leaders_without_engine_literal_refs": [x["effect_id"] for x in leaders if not x["engine_references"]],
        "combos": len(combos),
    },
    "generic_skills": generic,
    "identity_effects": identities,
    "leaders": leaders,
    "combos": combos,
    "shared_lifecycle_and_engine_hooks": hooks,
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report["counts"], ensure_ascii=False))
print(f"wrote {OUT}")
