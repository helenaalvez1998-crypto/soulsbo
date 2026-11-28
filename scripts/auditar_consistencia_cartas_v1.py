#!/usr/bin/env python3
"""Auditoria reproduzível de consistência entre catálogo, runtime e payload do site.

O relatório valida campos mecânicos publicados contra preparar_carta(), que é a
mesma preparação usada pelo motor de combate. Também valida cobertura declarativa
 das habilidades, custo por raridade e o limite físico do texto na placa da carta.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from sistemas.cartas import CARTAS_POR_ID, CARTAS_PACOTE, CARTAS_EXPANSAO_V75, CARTAS_EXPANSAO_V77, CUSTO_RARIDADE, HABILIDADES
from sistemas.gwent import (
    CARD_IDENTITY_ABILITIES,
    HABILIDADES_ESPECIAIS_IMPLEMENTADAS,
    HABILIDADES_UNIDADE_IMPLEMENTADAS,
    preparar_carta,
    SPECIAL_EFFECT_ALIASES,
)
from sistemas.arte_cartas import _layout_texto_lore, _layout_painel_lore_template
from sistemas.templates_cartas import carregar_layout


def construir_auditoria() -> dict[str, Any]:
    draw = ImageDraw.Draw(Image.new("RGB", (840, 1240)))
    rows: list[dict[str, Any]] = []
    checks = {
        "ids_unicos": True,
        "custo_por_raridade": True,
        "habilidade_nao_vazia": True,
        "lore_separada": True,
        "habilidade_implementada": True,
        "lore_cabe_na_carta": True,
        "lore_cabe_no_template": True,
        "fileira_valida": True,
    }

    for model in CARTAS_POR_ID.values():
        prepared = preparar_carta(model.para_dict())
        card_id = prepared["id"]
        skill = str(prepared.get("habilidade") or "")
        special = bool(prepared.get("especial"))
        ability_text = str(prepared.get("habilidade_texto") or "")
        lore = str(prepared.get("descricao") or "")
        rarity = str(prepared.get("raridade") or "")
        row = str(prepared.get("fileira") or "")

        if special:
            effective_skill = SPECIAL_EFFECT_ALIASES.get(skill, skill)
            ability_implemented = (not skill) or (skill in HABILIDADES and effective_skill in HABILIDADES_ESPECIAIS_IMPLEMENTADAS) or card_id in CARD_IDENTITY_ABILITIES
            row_valid = str(prepared.get("row_label") or "") == "Carta especial"
        else:
            ability_implemented = (not skill) or skill in HABILIDADES_UNIDADE_IMPLEMENTADAS or card_id in CARD_IDENTITY_ABILITIES
            row_valid = row in {"melee", "ranged", "siege"}

        cost_ok = prepared["custo"] == CUSTO_RARIDADE.get(rarity)
        has_mechanical_effect = bool(
            skill or card_id in CARD_IDENTITY_ABILITIES
            or prepared.get("sinergias") or prepared.get("combos_compativeis")
        )
        ability_ok = bool(ability_text.strip()) if has_mechanical_effect else not ability_text.strip()
        lore_separate = ability_text.strip() != lore.strip()

        # A arte física imprime somente a lore; regras de combate ficam no site.
        try:
            if lore.strip():
                _font, lore_lines, _step = _layout_texto_lore(draw, lore, 342, 94)
                fits = " ".join(" ".join(lore_lines).split()) == " ".join(lore.split())
            else:
                fits = True
        except Exception:
            lore_lines = []
            fits = False
        try:
            if lore.strip():
                _font_template, template_lines, _step, _margin, _y = _layout_painel_lore_template(
                    draw, lore, tuple(carregar_layout(rarity)["habilidade"])
                )
                template_fits = " ".join(" ".join(template_lines).split()) == " ".join(lore.split())
            else:
                template_fits = True
        except Exception:
            template_fits = False

        checks["custo_por_raridade"] &= cost_ok
        checks["habilidade_nao_vazia"] &= ability_ok
        checks["lore_separada"] &= lore_separate
        checks["habilidade_implementada"] &= ability_implemented
        checks["lore_cabe_na_carta"] &= fits
        checks["lore_cabe_no_template"] &= template_fits
        checks["fileira_valida"] &= row_valid

        rows.append({
            "id": card_id,
            "nome": prepared["nome"],
            "categoria": prepared["categoria"],
            "faccao": prepared["faccao"],
            "fileira": prepared["row_label"],
            "raridade": rarity,
            "poder": int(prepared["poder"]),
            "custo": int(prepared["custo"]),
            "habilidade_id": skill,
            "habilidade": prepared["habilidade_nome"],
            "habilidade_texto": ability_text,
            "lore": lore,
            "identidade": bool(prepared.get("habilidade_identidade")),
            "checks": {
                "custo_por_raridade": cost_ok,
                "habilidade_nao_vazia": ability_ok,
                "lore_separada": lore_separate,
                "habilidade_implementada": ability_implemented,
                "lore_cabe_na_carta": fits,
                "lore_cabe_no_template": template_fits,
                "fileira_valida": row_valid,
            },
        })

    ids = [item["id"] for item in rows]
    checks["ids_unicos"] = len(ids) == len(set(ids))
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "versao": "2.0",
        "total_cartas": len(rows),
        "total_unicas": len(set(ids)),
        "total_pacote": len(CARTAS_PACOTE),
        "total_expansao_v75": len(CARTAS_EXPANSAO_V75),
        "total_expansao_v77": len(CARTAS_EXPANSAO_V77),
        "checks": checks,
        "falhas": failed,
        "cartas": sorted(rows, key=lambda item: item["nome"].casefold()),
        "escopo": [
            "Verifica consistência dos dados publicados com preparar_carta(), fonte de preparação compartilhada pelo motor e pelo site.",
            "Verifica que cada habilidade declarada está registrada como implementada ou é uma habilidade de identidade exclusiva.",
            "Verifica custo por raridade, separação entre regra e lore, fileira e encaixe integral da lore no painel físico (o efeito não é impresso na imagem).",
            "Não substitui testes de integração de todas as combinações possíveis de combate, efeitos cruzados, banco de dados, Discord ou produção.",
        ],
    }


def escrever_relatorios(root: Path | None = None) -> dict[str, Path]:
    root = root or Path(__file__).resolve().parents[1]
    report = construir_auditoria()
    out_json = root / "docs" / "auditoria-consistencia-cartas-v1.0.json"
    out_md = root / "docs" / "auditoria-consistencia-cartas-v1.0.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Auditoria de consistência das cartas — v1.0",
        "",
        f"**Resultado:** {'APROVADO' if not report['falhas'] else 'FALHAS'} — {report['total_unicas']}/{report['total_cartas']} IDs únicos.",
        "",
        "## Verificações globais",
        "",
    ]
    lines.extend(f"- [{'x' if ok else ' '}] `{name}`" for name, ok in report["checks"].items())
    lines += ["", "## Escopo e limite da auditoria", ""]
    lines.extend(f"- {item}" for item in report["escopo"])
    lines += [
        "",
        "## Catálogo completo",
        "",
        "A regra abaixo é o texto preparado pelo mesmo contrato usado pelo motor e pela API do site. A lore fica em campo separado.",
        "",
    ]
    for card in report["cartas"]:
        lines += [
            f"### {card['nome']}",
            f"`{card['id']}` · {card['categoria']} · {card['faccao']} · {card['fileira']} · {card['raridade']} · Poder {card['poder']} · Custo {card['custo']}",
            "",
            f"**{card['habilidade']}** (`{card['habilidade_id'] or 'sem habilidade'}`)",
            card["habilidade_texto"],
            "",
            f"*Lore:* {card['lore'] or 'Sem lore cadastrada.'}",
            "",
        ]
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return {"json": out_json, "markdown": out_md}


if __name__ == "__main__":
    outputs = escrever_relatorios()
    result = construir_auditoria()
    for label, path in outputs.items():
        print(f"{label}: {path}")
    print(f"Resultado: {'APROVADO' if not result['falhas'] else 'FALHAS'}; {result['total_cartas']} cartas; falhas={result['falhas']}")
    raise SystemExit(0 if not result["falhas"] else 1)
