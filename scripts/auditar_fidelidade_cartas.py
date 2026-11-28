#!/usr/bin/env python3
"""Gera docs/AUDITORIA-FIDELIDADE-CARTAS.md para o catálogo completo."""
from pathlib import Path
import json

from sistemas.auditoria_efeitos import (
    gerar_relatorio_fidelidade_cartas,
    gerar_markdown_fidelidade_cartas,
)

ROOT = Path(__file__).resolve().parents[1]
report = gerar_relatorio_fidelidade_cartas()
output = ROOT / "docs" / "AUDITORIA-FIDELIDADE-CARTAS.md"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(gerar_markdown_fidelidade_cartas(report), encoding="utf-8")
json_output = ROOT / "docs" / "AUDITORIA-FIDELIDADE-CARTAS.json"
json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Status: {report['status']}")
print(f"Cartas: {report['total_cartas']} | Site: {report['total_publicadas_site']}")
print(f"Divergências: {report['total_erros']}")
if report["erros"]:
    for error in report["erros"]:
        print(f"- {error}")
    raise SystemExit(1)
print(f"Relatório: {output}")
print(f"Dados estruturados: {json_output}")
