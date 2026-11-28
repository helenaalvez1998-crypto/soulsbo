#!/usr/bin/env python3
"""Read-only audit of removal causes and Vengeance in the legacy Soulsbo engine.

Uses synthetic in-memory match states and static source/catalog cross-checks.
Does not patch or write to runtime, database, API, bot, catalogue, or frontend.
"""
from __future__ import annotations
import copy
import importlib.util
import inspect
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sistemas import gwent  # noqa: E402
from sistemas.cartas import CARTAS_POR_ID  # noqa: E402

SOURCE_PATH = ROOT / "sistemas/gwent.py"
REGISTRY_PATH = ROOT / "data/card_game/removal-resurrection-registry-candidate.v1.json"
SMOKE_HELPER_PATH = ROOT / "docs/scripts/validate-card-effect-smoke-v0.1.py"
REPORT_PATH = ROOT / "docs/card-game-removal-causes-group-F-audit-v0.1.json"
_spec = importlib.util.spec_from_file_location("group_f_smoke_helpers", SMOKE_HELPER_PATH)
smoke = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(smoke)
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def unit(name: str, *, row: str = "melee", skill: str = "", power: int = 3,
         bonus: int = 0, shield: int = 0) -> dict:
    return smoke.unit(name, row=row, skill=skill, power=power, bonus=bonus, escudo=shield)


def side_with(victim: dict, *survivors: dict) -> dict:
    return {"board": [victim, *survivors], "discard": [], "baixas": 0}


class GroupFRemovalCauseAudit(unittest.TestCase):
    def test_01_default_normal_removal_triggers_vengeance_after_success(self):
        victim = unit("victim", skill="vinganca")
        ally = unit("ally", bonus=0)
        side = side_with(victim, ally)
        gwent._remover_unidade(side, victim)
        self.assertEqual(1, ally["bonus"])
        self.assertEqual([victim], side["discard"])

    def test_02_execution_cause_triggers_vengeance_after_success(self):
        victim = unit("victim", skill="vinganca")
        ally = unit("ally", bonus=0)
        side = side_with(victim, ally)
        gwent._remover_unidade(side, victim, "execucao")
        self.assertEqual(1, ally["bonus"])

    def test_03_sacrifice_cause_triggers_vengeance_in_legacy(self):
        victim = unit("victim", skill="vinganca", shield=1)
        ally = unit("ally", bonus=0)
        side = side_with(victim, ally)
        gwent._remover_unidade(side, victim, "sacrificio")
        self.assertEqual(1, ally["bonus"])
        self.assertEqual(1, side["baixas"])

    def test_04_shield_blocks_normal_removal_without_vengeance(self):
        victim = unit("victim", skill="vinganca", shield=1)
        ally = unit("ally", bonus=0)
        side = side_with(victim, ally)
        gwent._remover_unidade(side, victim, "remocao")
        self.assertEqual(0, ally["bonus"])
        self.assertEqual([victim, ally], side["board"])
        self.assertEqual([], side["discard"])
        self.assertEqual(0, side["baixas"])

    def test_05_shield_blocks_execution_without_vengeance(self):
        victim = unit("victim", skill="vinganca", shield=1)
        ally = unit("ally", bonus=0)
        side = side_with(victim, ally)
        gwent._remover_unidade(side, victim, "execucao")
        self.assertEqual(0, ally["bonus"])
        self.assertEqual(0, side["baixas"])
        self.assertEqual(0, victim["escudo"])

    def test_06_sacrifice_bypasses_shield_and_triggers_vengeance(self):
        victim = unit("victim", skill="vinganca", shield=2)
        ally = unit("ally", bonus=0)
        side = side_with(victim, ally)
        gwent._remover_unidade(side, victim, "sacrificio")
        self.assertEqual(1, ally["bonus"])
        self.assertNotIn("escudo", victim)
        self.assertEqual([victim], side["discard"])

    def test_07_non_board_target_does_not_trigger_or_increment(self):
        victim = unit("victim", skill="vinganca")
        ally = unit("ally", bonus=0)
        side = {"board": [ally], "discard": [], "baixas": 0}
        gwent._remover_unidade(side, victim, "sacrificio")
        self.assertEqual(0, ally["bonus"])
        self.assertEqual(0, side["baixas"])
        self.assertEqual([], side["discard"])

    def test_08_vengeance_only_affects_remaining_allies_in_same_row(self):
        victim = unit("victim", skill="vinganca", row="ranged")
        same_row = unit("same", row="ranged", bonus=2)
        other_row = unit("other", row="siege", bonus=2)
        side = side_with(victim, same_row, other_row)
        gwent._remover_unidade(side, victim, "execucao")
        self.assertEqual(3, same_row["bonus"])
        self.assertEqual(2, other_row["bonus"])

    def test_09_non_vengeance_unit_does_not_trigger(self):
        victim = unit("victim", skill="devorar")
        ally = unit("ally")
        side = side_with(victim, ally)
        gwent._remover_unidade(side, victim, "remocao")
        self.assertEqual(0, ally["bonus"])

    def test_10_one_successful_removal_triggers_once(self):
        victim = unit("victim", skill="vinganca")
        ally = unit("ally")
        side = side_with(victim, ally)
        gwent._remover_unidade(side, victim, "remocao")
        gwent._remover_unidade(side, victim, "remocao")
        self.assertEqual(1, ally["bonus"])
        self.assertEqual(1, side["baixas"])

    def test_11_two_distinct_vengeance_victims_trigger_independently(self):
        first = unit("first", skill="vinganca")
        second = unit("second", skill="vinganca")
        survivor = unit("survivor")
        side = side_with(first, second, survivor)
        gwent._remover_unidade(side, first, "sacrificio")
        gwent._remover_unidade(side, second, "execucao")
        self.assertEqual(2, survivor["bonus"])
        self.assertEqual(2, side["baixas"])

    def test_12_legacy_counter_counts_successful_effect_removal(self):
        victim = unit("victim")
        side = side_with(victim)
        gwent._remover_unidade(side, victim, "remocao")
        self.assertEqual(1, side["baixas"])

    def test_13_legacy_counter_counts_successful_execution(self):
        victim = unit("victim")
        side = side_with(victim)
        gwent._remover_unidade(side, victim, "execucao")
        self.assertEqual(1, side["baixas"])

    def test_14_legacy_counter_counts_successful_sacrifice(self):
        victim = unit("victim")
        side = side_with(victim)
        gwent._remover_unidade(side, victim, "sacrificio")
        self.assertEqual(1, side["baixas"])

    def test_15_only_three_removal_causes_are_declared_in_candidate_registry(self):
        causes = {x["cause_id"] for x in REGISTRY["removal_policy"]["causes"]}
        self.assertEqual({"normal_removal", "execution", "sacrifice"}, causes)

    def test_16_active_black_flame_and_execution_catalog_bindings_exist(self):
        self.assertEqual("gwent_queima", CARTAS_POR_ID["gwent_especial_queima"].habilidade)
        self.assertEqual("gwent_execucao", CARTAS_POR_ID["gwent_especial_execucao"].habilidade)
        self.assertIn("_remover_unidade(side, strongest)", SOURCE)
        self.assertIn('_remover_unidade(other, victim, "execucao")', SOURCE)

    def test_17_active_devour_and_blood_price_bindings_exist(self):
        self.assertEqual("devorar", CARTAS_POR_ID["gwent_unidade_carniceiro_forja"].habilidade)
        self.assertIn("gwent_v75_veu_carrasco_preco", gwent.CARD_IDENTITY_ABILITIES)
        self.assertIn('_remover_unidade(player, presa, "sacrificio")', SOURCE)
        self.assertIn('_remover_unidade(player, victim, "sacrificio")', SOURCE)

    def test_18_rykard_is_active_leader_and_routes_through_sacrifice(self):
        self.assertEqual("rykard_devour", gwent.LEADERS["sombra_caminhante"]["effect"])
        self.assertIn('_remover_unidade(player, victim, "sacrificio")', SOURCE)

    def test_19_devour_real_handler_triggers_vengeance_then_gain(self):
        card = smoke.unit("devourer-veng", skill="devorar", power=4)
        state = smoke.fixture(card, "melee")
        player = state["players"]["1"]
        victim = smoke.unit("vengeance-victim", skill="vinganca", row="melee", power=2)
        survivor = smoke.unit("survivor", row="melee", power=5, bonus=0)
        player["board"] = [victim, survivor]
        player["hand"] = [card, smoke.unit("devourer-reserve")]
        result = gwent.aplicar_jogada(state, 1, card_id="devourer-veng", action="play", row="melee")
        self.assertNotIn("error", result)
        after = result["state"]["players"]["1"]
        played = next(item for item in after["board"] if item["id"] == "devourer-veng")
        remaining = next(item for item in after["board"] if item["id"] == "survivor")
        self.assertEqual(2, played["bonus"])
        self.assertEqual(1, remaining["bonus"])

    def test_20_blood_price_real_identity_handler_triggers_vengeance(self):
        card = smoke.unit("gwent_v75_veu_carrasco_preco", power=5, skill="")
        state = smoke.fixture(card, "melee")
        player = state["players"]["1"]
        victim = smoke.unit("price-victim", skill="vinganca", row="melee", power=2)
        survivor = smoke.unit("price-survivor", row="melee", power=5)
        player["board"] = [victim, survivor]
        player["hand"] = [card, smoke.unit("price-reserve")]
        result = gwent.aplicar_jogada(state, 1, card_id="gwent_v75_veu_carrasco_preco", action="play", row="melee")
        self.assertNotIn("error", result)
        after = result["state"]["players"]["1"]
        self.assertEqual(1, next(item for item in after["board"] if item["id"] == "price-survivor")["bonus"])
        self.assertTrue(any(item["id"] == "price-victim" for item in after["discard"]))

    def test_21_rykard_real_handler_stacks_vengeance_then_direct_bonus(self):
        base = smoke.unit("rykard_fixture")
        state = smoke.fixture(base, "melee")
        player = state["players"]["1"]
        player["faction"] = "Véu Carmesim"
        player["leader_id"] = "sombra_caminhante"
        player["leader_used"] = False
        victim = smoke.unit("rykard_victim", skill="vinganca", row="melee", power=1)
        ally_a = smoke.unit("rykard_ally_a", row="melee", power=3, bonus=0)
        ally_b = smoke.unit("rykard_ally_b", row="melee", power=4, bonus=0)
        player["board"] = [victim, ally_a, ally_b]
        player["hand"] = [smoke.unit("rykard_reserve")]
        result = gwent.aplicar_jogada(state, 1, action="leader", row="melee")
        self.assertNotIn("error", result)
        after = result["state"]["players"]["1"]
        self.assertEqual(3, next(item for item in after["board"] if item["id"] == "rykard_ally_a")["bonus"])
        self.assertEqual(3, next(item for item in after["board"] if item["id"] == "rykard_ally_b")["bonus"])

    def test_22_round_archive_does_not_call_removal_or_increment_baixas(self):
        base = smoke.unit("round_fixture")
        state = smoke.fixture(base, "melee")
        player = state["players"]["1"]
        victim = smoke.unit("round_victim", skill="vinganca", row="melee", bonus=0)
        survivor = smoke.unit("round_survivor", row="melee", bonus=0)
        player["board"] = [victim, survivor]
        player["discard"] = []
        player["baixas"] = 0
        gwent._resolve_round(state)
        self.assertEqual(0, player["baixas"])
        self.assertEqual([], player["board"])
        self.assertEqual({"round_victim", "round_survivor"}, {x["id"] for x in player["discard"]})
        source = inspect.getsource(gwent._resolve_round)
        self.assertNotIn("_remover_unidade", source)

    def test_23_terminal_round_returns_without_board_removal_or_vengeance(self):
        base = smoke.unit("terminal_fixture")
        state = smoke.fixture(base, "melee")
        player = state["players"]["1"]
        victim = smoke.unit("terminal_victim", skill="vinganca")
        player["board"] = [victim]
        player["baixas"] = 0
        state["round"] = 3
        gwent._resolve_round(state)
        self.assertEqual("finished", state["status"])
        self.assertEqual([victim], player["board"])
        self.assertEqual(0, player["baixas"])

    def test_24_relic_flame_is_power_and_bonus_reduction_not_removal(self):
        start = SOURCE.index('elif skill == "reliquia_noite_chama":')
        end = SOURCE.index('elif skill == "reliquia_lamina_negra":', start)
        block = SOURCE[start:end]
        self.assertNotIn("_remover_unidade", block)
        self.assertIn('alvo["poder"]', block)
        self.assertIn('alvo["bonus"]', block)

    def test_25_black_blade_is_bonus_reduction_not_removal(self):
        start = SOURCE.index('elif skill == "reliquia_lamina_negra":')
        end = SOURCE.index('elif skill == "reliquia_algemas":', start)
        block = SOURCE[start:end]
        self.assertNotIn("_remover_unidade", block)
        self.assertIn('alvo["bonus"]', block)

    def test_26_unknown_legacy_cause_is_not_rejected(self):
        victim = unit("victim")
        side = side_with(victim)
        gwent._remover_unidade(side, victim, "round_close_archive")
        self.assertEqual([victim], side["discard"])
        self.assertEqual(1, side["baixas"])

    def test_27_legacy_vengeance_check_uses_habilidade_string(self):
        source = inspect.getsource(gwent._remover_unidade)
        self.assertIn('unit.get("habilidade") == "vinganca"', source)
        self.assertNotIn('definition_snapshot.effect_id', source)

    def test_28_candidate_and_example_use_different_vengeance_effect_ids(self):
        registry_effect = REGISTRY["removal_policy"]["on_remove_effects"][0]["effect_id"]
        example_path = ROOT / "docs/examples/card-instance-match.example.v4.json"
        example = json.loads(example_path.read_text(encoding="utf-8"))
        example_ids = {e.get("source_effect_id") for e in example["events"] if e.get("kind") == "vengeance_bonus_applied"}
        self.assertEqual("effect.vengeance_on_removal", registry_effect)
        self.assertEqual({"unit.vengeance_on_removal"}, example_ids)

    def test_29_legacy_baixas_is_not_a_death_only_counter(self):
        source = inspect.getsource(gwent._remover_unidade)
        self.assertIn('side["baixas"] = int(side.get("baixas", 0)) + 1', source)
        # Sacrifice is explicitly routed through the same incrementing function.
        self.assertIn('_remover_unidade(player, victim, "sacrificio")', SOURCE)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GroupFRemovalCauseAudit)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    failed_methods = {
        getattr(test, "_testMethodName", "")
        for test, _ in (result.failures + result.errors)
    }
    report = {
        "audit": "card_game_removal_causes_group_F",
        "version": "0.1",
        "date": "2026-11-27",
        "status": "READ_ONLY_LEGACY_AUDIT; RESOLUTIONS_CANDIDATE_NOT_APPROVED",
        "baseline": "soulsbo-main-continuity-2026-11-27-rev12.zip",
        "total": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failed": len(result.failures) + len(result.errors),
        "runtime_modified": False,
        "groups_D_status": "OWNER_APPROVED",
        "cases": [
            {"id": f"F-{i:03d}", "title": title, "test_method": method,
             "status": "FAIL" if method in failed_methods else "PASS"}
            for i, (title, method) in enumerate(zip([
                "normal removal triggers Vengeance after success", "execution triggers Vengeance after success",
                "sacrifice triggers Vengeance in legacy", "shield-blocked normal removal does not trigger Vengeance",
                "shield-blocked execution does not trigger Vengeance", "sacrifice bypasses shield and triggers Vengeance",
                "non-board target has no trigger or counter change", "Vengeance targets only remaining allies in same row",
                "non-Vengeance victim does not trigger", "one successful removal triggers once", "separate Vengeance victims trigger independently",
                "legacy counter counts effect removal", "legacy counter counts execution", "legacy counter counts sacrifice",
                "candidate registry has three explicit removal causes", "active special bindings use central removal routes",
                "active Devour and Blood Price bindings use sacrifice", "Rykard leader is active and uses sacrifice",
                "Devour handler ordering", "Blood Price handler triggers Vengeance", "Rykard +1 then +2 stacking",
                "round archive is not removal and does not increment bajas", "terminal round is not removal",
                "Noite/Chama relic is not removal", "Black Blade relic is not removal", "unknown legacy cause is not rejected",
                "legacy Vengeance uses habilidade string", "candidate/example effect ID naming mismatch", "baixas is not death-only"
            ], sorted(n for n in dir(GroupFRemovalCauseAudit) if n.startswith("test_"))), start=1)
        ],
        "source_references": {
            "central_removal": "sistemas/gwent.py:_remover_unidade",
            "round_archive": "sistemas/gwent.py:_resolve_round",
            "active_call_sites": [598, 1433, 1620, 1638, 1876],
            "candidate_registry": "data/card_game/removal-resurrection-registry-candidate.v1.json",
            "legacy_tests": "docs/scripts/test-card-removal-resurrection-candidate-v0.1.py"
        },
        "limitations": [
            "Fixtures are synthetic in-memory states; no HTTP, database, Discord, R2 or production environment was exercised.",
            "The 29 passing cases reproduce behavior and source facts; they do not approve the recommended new-game rules.",
            "Vengeance trigger policy for sacrifice, counters, additive Rykard balance and effect ID canonicalization remain owner decisions in Group F."
        ],
        "failures": [str(x[1]) for x in result.failures + result.errors]
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Group F audit: {report['passed']}/{report['total']} passed; {report['failed']} failed")
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    raise SystemExit(main())
