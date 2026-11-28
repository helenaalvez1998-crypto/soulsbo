#!/usr/bin/env python3
"""Run the full isolated Card Engine v2 alpha suite, including combos/factions/leaders."""
from __future__ import annotations
import json, sys, unittest
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TESTS = ROOT / "tests" / "card_engine_v2"
REPORT_JSON = ROOT / "docs" / "card-engine-v2-playable-alpha-validation-v0.4.json"
REPORT_MD = ROOT / "docs" / "card-engine-v2-playable-alpha-validation-v0.4.md"
def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(TESTS), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    failures = result.failures + result.errors
    passed = result.testsRun - len(failures) - len(result.skipped)
    report = {
        "metadata": {
            "document": "Soulsbo Card Engine v2 expanded playable alpha validation",
            "version": "0.4",
            "status": "PASS" if result.wasSuccessful() else "FAIL",
            "runtime_integration": "isolated_alpha_match_controller_only",
            "production_runtime_integration": False,
            "production_database_access": False,
            "catalog_release_id": "alpha-test-only.catalog.v0.3",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "summary": {"tests": result.testsRun, "passed": passed, "failed": len(failures), "skipped": len(result.skipped)},
        "coverage_groups": {
            "repository_and_persistence": "tests/card_engine_v2/test_repository.py",
            "generic_gameplay_resolver": "tests/card_engine_v2/test_gameplay_resolver.py",
            "playable_best_of_three_match": "tests/card_engine_v2/test_playable_match.py",
            "normal_sacrifice_turn_action": "tests/card_engine_v2/test_playable_match.py",
            "deck_fatigue_turn_start_runtime": "tests/card_engine_v2/test_deck_fatigue_runtime.py",
            "row_combat_and_player_life": "tests/test_combat.py and tests/test_playable_match.py",
            "schema_and_contract": "tests/card_engine_v2/test_schema.py",
            "expanded_entry_effects": "tests/card_engine_v2/test_expanded_entry_effects.py",
            "combos_faction_passives_leaders": "tests/card_engine_v2/test_combo_faction_leaders.py",
            "deck_fatigue_candidate_reference_only": "tests/card_engine_v2/test_deck_fatigue_candidate.py (historical candidate model)",
        },
        "content_scope": {
            "historical_models": 137,
            "alpha_allowlist_cards": 27,
            "blocked_historical_models": 110,
            "combo_definitions_registered": 27,
            "combos_reachable_with_current_allowlist_tags": 9,
            "combos_inert_until_missing_tag_sources_are_added": 18,
            "faction_passives": 4,
            "leader_handlers": 10,
            "entry_effect_families": 12,
        },
        "scope_limits": [
            "Tests use disposable local SQLite databases; no production database is accessed.",
            "No Discord, HTTP, frontend, aiosqlite or multi-host integration is exercised.",
            "The 27-card allowlist, 27 combo definitions, four faction passives and ten leaders are alpha-only fixtures, not a published catalog.",
            "Only nine registered combos have all required tags represented in the current 27-card allowlist; 18 remain inert until tag-source cards are added.",
            "Combo/passive/leader tests use isolated test matches; not every handler has been playtested through a human UI flow.",
            "The remaining 110 historical models are blocked; the full card catalog, per-unit attack/armor/hit-point rules, all special families and production adapter are incomplete.",
            "Normal sacrifice is exposed only as an internal alpha controller action; its current cost is turn consumption only, with no energy/resource economy or Discord/HTTP/frontend interaction.",
            "Deck fatigue is enabled only in the isolated alpha match controller; it is not integrated with Discord, HTTP, frontend or the production game runtime.",
            "The default alpha setup follows the redesign's four-card initial hand; deterministic legacy simulation fixtures may explicitly override the hand size.",
            "The alpha harness retains its existing draw of up to two cards at each new round; this draw schedule is a harness rule, not a complete production draw economy.",
            "Deck fatigue uses a provisional alpha balance policy: 1 damage on the first empty-deck turn, then +1 per later fatigue turn, no cap, per-player match counter, no reset and no discard reshuffle.",
            "Each player's first turn after the initial deal is fatigue-exempt; subsequent individual turns are checked before the player can act.",
        ],
        "failures": [str(err[1]) for err in failures],
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = (
        "# Card Engine v2 — expanded playable alpha validation v0.4\n\n"
        f"**Status:** {report['metadata']['status']}  \n"
        f"**Executado (UTC):** {report['metadata']['generated_at_utc']}  \n"
        f"**Resultado:** {passed}/{result.testsRun} testes aprovados; {report['summary']['failed']} falhas; {report['summary']['skipped']} ignorados.\n\n"
        "## Conteúdo validado\n\n"
        "- 27 cartas alpha explicitamente permitidas; 110 dos 137 modelos históricos continuam bloqueados.\n"
        "- 12 famílias de efeitos de entrada.\n"
        "- 27 definições de combo registradas; nove alcançáveis com as tags atuais.\n"
        "- Quatro passivas de facção e dez handlers de líderes.\n"
        "- Persistência SQLite, resolvedor de gameplay, partidas Bo3 e schemas.\n"
        "- Combate por fileira no fechamento da rodada, vida inicial de 20, dano letal e empate simultâneo (ruleset alpha v0.2).\n"
        "- Sacrifício como ação normal interna do `AlphaMatchController`: oferta server-side vinculada à revisão, confirmação transacional, custo de turno, bypass de Égide, contador separado, Vingança causal e replay idempotente.\n"
        "- Deck fatigue no controlador alpha: checagem no início de cada turno individual com pilha vazia; dano progressivo 1, 2, 3... antes da ação; contadores separados por jogador e finalização letal imediata (ruleset v0.3).\n"
        "- A política de fatigue é uma decisão provisória de balanceamento alpha, não uma regra final aprovada para publicação.\n\n"
        "## Limites\n\n" + "\n".join(f"- {item}" for item in report["scope_limits"]) + "\n"
    )
    REPORT_MD.write_text(md, encoding="utf-8")
    print(f"Card Engine v2 alpha: {passed}/{result.testsRun} passed; {len(failures)} failed")
    print(f"JSON: {REPORT_JSON.relative_to(ROOT)}")
    print(f"Markdown: {REPORT_MD.relative_to(ROOT)}")
    return 0 if result.wasSuccessful() else 1
if __name__ == "__main__":
    raise SystemExit(main())
