#!/usr/bin/env python3
"""Run the isolated Card Engine v2 alpha suite and write a JSON report."""
from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TESTS = ROOT / "tests" / "card_engine_v2"
OUT = ROOT / "docs" / "card-engine-v2-alpha-validation-v0.1.json"


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(TESTS), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    report = {
        "metadata": {
            "document": "Soulsbo Card Engine v2 isolated alpha validation",
            "version": "0.1",
            "status": "PASS" if result.wasSuccessful() else "FAIL",
            "runtime_integration": False,
            "production_database_access": False,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "summary": {
            "tests": result.testsRun,
            "passed": passed,
            "failed": len(result.failures) + len(result.errors),
            "skipped": len(result.skipped),
        },
        "limitations": [
            "SQLite tests use temporary dedicated files and independent local connections.",
            "No aiosqlite, Discord, HTTP, frontend, production database or multi-host environment was exercised.",
            "The domain handler is a pure callback; the real card/effect catalog is not integrated.",
            "The schema validation tests are skipped when the optional jsonschema package is unavailable.",
        ],
        "failures": [str(err[1]) for err in result.failures + result.errors],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Card Engine v2 alpha: {passed}/{result.testsRun} passed; {report['summary']['failed']} failed")
    print(f"Report: {OUT.relative_to(ROOT)}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
