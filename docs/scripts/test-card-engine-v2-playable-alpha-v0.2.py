#!/usr/bin/env python3
"""Run the current playable Card Engine v2 alpha test suite."""
from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TESTS = ROOT / "tests" / "card_engine_v2"
REPORT_JSON = ROOT / "docs" / "card-engine-v2-playable-alpha-validation-v0.2.json"
REPORT_MD = ROOT / "docs" / "card-engine-v2-playable-alpha-validation-v0.2.md"


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(TESTS), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    failures = result.failures + result.errors
    passed = result.testsRun - len(failures) - len(result.skipped)
    report = {
        "metadata": {
            "document": "Soulsbo Card Engine v2 playable alpha validation",
            "version": "0.2",
            "status": "PASS" if result.wasSuccessful() else "FAIL",
            "runtime_integration": False,
            "production_database_access": False,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "summary": {
            "tests": result.testsRun,
            "passed": passed,
            "failed": len(failures),
            "skipped": len(result.skipped),
        },
        "coverage_groups": {
            "repository_and_persistence": "tests/test_repository.py",
            "generic_gameplay_resolver": "tests/test_gameplay_resolver.py",
            "playable_best_of_three_match": "tests/test_playable_match.py",
            "schema_and_contract": "tests/test_schema.py",
        },
        "scope_limits": [
            "Tests use disposable local SQLite databases and local independent connections.",
            "No production database, aiosqlite, Discord, HTTP, frontend or multi-host infrastructure was used.",
            "The match uses an explicit 10-card alpha allowlist, not the full production catalog.",
            "The controller does not yet implement all catalog effects, leaders, combos, damage or full turn/cost systems.",
        ],
        "failures": [str(err[1]) for err in failures],
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = (
        "# Card Engine v2 — playable alpha validation v0.2\n\n"
        f"**Status:** {report['metadata']['status']}  \n"
        f"**Executado (UTC):** {report['metadata']['generated_at_utc']}  \n"
        f"**Resultado:** {passed}/{result.testsRun} testes aprovados; "
        f"{report['summary']['failed']} falhas; {report['summary']['skipped']} ignorados.\n\n"
        "## Escopo\n\n"
        "- Repositório SQLite, CAS, ledger idempotente, journal e outbox.\n"
        "- Resolvedor genérico: alvos, remoção/sacrifício, proteção, bônus e Vingança.\n"
        "- Controlador de partida jogável melhor de três com allowlist de 10 cartas.\n"
        "- Schemas e contrato CardInstance v0.7.\n\n"
        "## Limites\n\n"
        + "\n".join(f"- {item}" for item in report["scope_limits"])
        + "\n"
    )
    REPORT_MD.write_text(md, encoding="utf-8")
    print(f"Card Engine v2 playable alpha: {passed}/{result.testsRun} passed; {len(failures)} failed")
    print(f"JSON: {REPORT_JSON.relative_to(ROOT)}")
    print(f"Markdown: {REPORT_MD.relative_to(ROOT)}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
