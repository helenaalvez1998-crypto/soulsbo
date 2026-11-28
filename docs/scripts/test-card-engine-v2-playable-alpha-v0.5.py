#!/usr/bin/env python3
"""Run the full isolated Card Engine v2 alpha suite, including combos/factions/leaders."""
from __future__ import annotations
import json, sys, unittest
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TESTS = ROOT / "tests" / "card_engine_v2"
REPORT_JSON = ROOT / "docs" / "card-engine-v2-playable-alpha-validation-v0.5.json"
REPORT_MD = ROOT / "docs" / "card-engine-v2-playable-alpha-validation-v0.5.md"
COST_SCHEDULE = ROOT / "data" / "card_game" / "card-engine-v2-alpha-energy-cost-schedule.v0.1.json"
ABILITY_REGISTRY = ROOT / "data" / "card_game" / "card-engine-v2-alpha-activated-abilities.v0.1.json"
RULESET = ROOT / "data" / "card_game" / "card-engine-v2-alpha-ruleset.v0.5.json"
def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(TESTS), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    failures = result.failures + result.errors
    passed = result.testsRun - len(failures) - len(result.skipped)
    cost_schedule = json.loads(COST_SCHEDULE.read_text(encoding="utf-8"))
    ability_registry = json.loads(ABILITY_REGISTRY.read_text(encoding="utf-8"))
    ruleset = json.loads(RULESET.read_text(encoding="utf-8"))
    card_costs = [row["energy_cost"] for row in cost_schedule["card_energy_cost_by_card_id"].values()]
    leader_costs = [row["energy_cost"] for row in cost_schedule["leader_activation_energy_cost_by_leader_id"].values()]
    report = {
        "metadata": {
            "document": "Soulsbo Card Engine v2 expanded playable alpha validation",
            "version": "0.5",
            "status": "PASS" if result.wasSuccessful() else "FAIL",
            "runtime_integration": "isolated_alpha_match_controller_only",
            "production_runtime_integration": False,
            "production_database_access": False,
            "catalog_release_id": "alpha-test-only.catalog.v0.3",
            "ruleset_release_id": ruleset.get("release_id", "alpha-test-only.ruleset.v0.5"),
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
            "energy_economy_and_explicit_costs": "tests/card_engine_v2/test_energy_economy.py",
            "all_27_card_and_10_leader_price_checks": "tests/card_engine_v2/test_energy_economy.py::test_every_provisional_price_is_accepted_at_exact_balance_and_rejected_below_it",
            "generic_manual_ability_activation_framework": "tests/card_engine_v2/test_activated_abilities.py (synthetic test registry only)",
            "physical_exemplar_provenance_and_snapshot": "tests/card_engine_v2/test_deck_builder.py, test_deck_repository_application.py and test_schema.py (including Primordial display enum)",
            "global_exemplar_uniqueness_and_live_revalidation": "tests/card_engine_v2/test_deck_repository_application.py",
            "player_safe_match_projection": "tests/card_engine_v2/test_deck_repository_application.py::test_player_view_exposes_own_physical_cards_and_hides_opponent_hand",
            "server_controlled_shuffle_randomness": "tests/card_engine_v2/test_deck_repository_application.py::test_application_matchmaking_does_not_accept_client_shuffle_seeds",
            "legacy_collection_read_only_exemplar_adapter": "tests/card_engine_v2/test_deck_repository_application.py::test_legacy_collection_adapters_are_read_only_and_return_exact_ids",
        },
        "energy_cost_schedule": {
            "status": cost_schedule["status"],
            "cards_priced": len(card_costs),
            "leaders_priced": len(leader_costs),
            "card_cost_range": [min(card_costs), max(card_costs)] if card_costs else None,
            "leader_cost_range": [min(leader_costs), max(leader_costs)] if leader_costs else None,
            "manual_abilities_priced": len(cost_schedule["ability_activation_energy_cost_by_ability_id"]),
            "rarity_is_not_an_input": cost_schedule["design_basis"]["rarity_is_not_an_input"],
            "legacy_deck_cost_is_not_an_input": cost_schedule["design_basis"]["legacy_deck_cost_is_not_an_input"],
        },
        "activated_ability_registry": {
            "status": ability_registry["status"],
            "live_abilities_registered": len(ability_registry["abilities"]),
            "supported_action_types": ability_registry["supported_action_types"],
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
            "Competitive deck slots are bound to exact global cartas_exemplares.id values; current per-copy unit power is frozen into the match instance. Existing saved deck rows migrated from schema v1 have empty exemplar provenance and must be rebuilt from the live collection before matchmaking.",
            "The legacy collection bridge reads Database.coliseu_listar_exemplares only; database.py and the published/legacy engine are not modified or written. No Discord/HTTP authentication transport is connected yet.",
            "Player-safe match views hide the opponent's hand and physical exemplar IDs when the authenticated player ID is supplied. The transport must derive that ID from its session/Discord principal, never from client payload data; a privileged no-viewer projection remains for internal simulations.",
            "Synchronous and asynchronous application matchmaking APIs do not accept client-provided shuffle seeds; server system randomness is used. Deterministic seeds remain restricted to the low-level internal controller for reproducible tests/simulations.",
            "Primordial is supported as an additional display rarity classification. Rarity remains excluded from power, targeting and effect resolution.",
            "Energy gain is implemented in the isolated alpha runtime (+1 at each individual turn start, cap 5, carried across rounds); all 27 allowlisted card IDs and all ten leader IDs have explicit provisional per-ID costs in ruleset v0.5.",
            "The per-ID schedule is experimental and not approved for release or balance sign-off; its values have not been validated by human playtests or telemetry. Rarity and legacy deck-cost fields are not used as turn-energy prices.",
            "All play/leader/manual-ability actions without an explicit configured price are rejected; there are no free unpriced alpha actions. Sacrifice is a separate turn-consuming action and has no energy price in this alpha.",
            "No manual activated ability is declared for the live 27-card allowlist; the registry is intentionally empty. The generic server-registry activation API is tested with a synthetic fixture only; no on-play effect was converted into a repeatable manual ability.",
            "Reproducible gameplay simulations use a uniform-energy-cost=1 test fixture to isolate other mechanics; they do not validate the provisional per-ID balance schedule. Dedicated economy tests validate every 27 card and ten leader price entries.",
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
        "# Card Engine v2 — expanded playable alpha validation v0.5\n\n"
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
        "- Economia de energia: +1 no início de cada turno, limite 5, saldo persistente entre rodadas, guardrails de runtime e cobrança transacional.\n"
        f"- Agenda alpha provisória por ID: {len(card_costs)} cartas e {len(leader_costs)} líderes; custos de cartas {min(card_costs)}–{max(card_costs)} e líderes {min(leader_costs)}–{max(leader_costs)}. Não aprovada para release/playtest humano.\n"
        "- Raridade e custo legado de deck não determinam energia; ações sem custo explícito são rejeitadas. Sacrifício consome turno, sem custo energético.\n"
        f"- Ativação manual genérica: API server-side testada com fixture sintética; registry real vazio ({len(ability_registry['abilities'])} habilidades), pois nenhuma das 27 cartas declara habilidade manual. Efeitos de entrada não são reativáveis.\n"
        "- Simulações de gameplay usam fixture uniforme de custo 1 apenas para isolar mecânicas; testes de economia percorrem todos os preços da tabela real provisória.\n"
        "- Deck Builder competitivo vincula cada slot a um `cartas_exemplares.id` global único, revalida posse e modelo no matchmaking e congela o poder individual atual na instância da partida.\n"
        "- A ponte do inventário legado é somente leitura (`coliseu_listar_exemplares`); raridade Primordial é suportada como classificação, sem efeito mecânico.\n"
        "- A view destinada a jogador oculta a mão adversária e IDs físicos do oponente; autenticação Discord/HTTP ainda deve fornecer o ID do principal autenticado.\n"
        "- As APIs sync/async de aplicação não aceitam seed de embaralhamento do cliente; aleatoriedade do sistema é usada no matchmaking. Seeds determinísticas só existem no controlador interno para testes.\n"
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
