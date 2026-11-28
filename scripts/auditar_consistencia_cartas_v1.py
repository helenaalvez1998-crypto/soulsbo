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

from sistemas.cartas import CARTAS_POR_ID, CARTAS_PACOTE, CARTAS_EXPANSAO_V75, CUSTO_RARIDADE
from sistemas.gwent import (
    CARD_IDENTITY_ABILITIES,
    HABILIDADES_ESPECIAIS_IMPLEMENTADAS,
    HABILIDADES_UNIDADE_IMPLEMENTADAS,
    preparar_carta,
)
from sistemas.arte_cartas import _ajustar_texto, _wrap
from sistemas.templates_cartas import carregar_layout


def construir_auditoria() -> dict[str, Any]:
    layout = carregar_layout()
    hx1, hy1, hx2, hy2 = layout["habilidade"]
    width = (hx2 - hx1) - 48
    draw = ImageDraw.Draw(Image.new("RGB", (840, 1240)))
    rows: list[dict[str, Any]] = []
    checks = {
        "ids_unicos": True,
        "custo_por_raridade": True,
        "habilidade_nao_vazia": True,
        "lore_separada": True,
        "habilidade_implementada": True,
        "texto_cabe_na_carta": True,
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
            ability_implemented = (not skill) or skill in HABILIDADES_ESPECIAIS_IMPLEMENTADAS or card_id in CARD_IDENTITY_ABILITIES
            row_valid = str(prepared.get("row_label") or "") == "Carta especial"
        else:
            ability_implemented = (not skill) or skill in HABILIDADES_UNIDADE_IMPLEMENTADAS or card_id in CARD_IDENTITY_ABILITIES
            row_valid = row in {"melee", "ranged", "siege"}

        cost_ok = prepared["custo"] == CUSTO_RARIDADE.get(rarity)
        ability_ok = bool(ability_text.strip())
        lore_separate = ability_text.strip() != lore.strip()

        title = str(prepared.get("habilidade_nome") or "")
        _, _, title_height = _ajustar_texto(
            draw, title.upper(), width, 27,
            maximo=23, minimo=15, negrito=True, max_linhas=1, espaco=1.0,
        )
        y_body = hy1 + 9 + max(25, title_height) + 1
        available_height = hy2 - 9 - y_body
        body_font, lines, _ = _ajustar_texto(
            draw, ability_text, width, available_height,
            maximo=19, minimo=12, max_linhas=3, espaco=1.05,
        )
        # O renderer acrescenta reticências quando precisa cortar o fim da regra.
        actual_lines = _wrap(draw, ability_text, body_font, width)
        fits = len(actual_lines) <= 3 and not (lines and lines[-1].endswith("…"))

        checks["custo_por_raridade"] &= cost_ok
        checks["habilidade_nao_vazia"] &= ability_ok
        checks["lore_separada"] &= lore_separate
        checks["habilidade_implementada"] &= ability_implemented
        checks["texto_cabe_na_carta"] &= fits
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
                "texto_cabe_na_carta": fits,
                "fileira_valida": row_valid,
            },
        })

    ids = [item["id"] for item in rows]
    checks["ids_unicos"] = len(ids) == len(set(ids))
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "versao": "1.0",
        "total_cartas": len(rows),
        "total_unicas": len(set(ids)),
        "total_pacote": len(CARTAS_PACOTE),
        "total_expansao_v75": len(CARTAS_EXPANSAO_V75),
        "checks": checks,
        "falhas": failed,
        "cartas": sorted(rows, key=lambda item: item["nome"].casefold()),
        "escopo": [
            "Verifica consistência dos dados publicados com preparar_carta(), fonte de preparação compartilhada pelo motor e pelo site.",
            "Verifica que cada habilidade declarada está registrada como implementada ou é uma habilidade de identidade exclusiva.",
            "Verifica custo por raridade, separação entre regra e lore, fileira e ajuste do texto no slot gráfico.",
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
