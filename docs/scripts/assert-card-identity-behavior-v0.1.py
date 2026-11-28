#!/usr/bin/env python3
"""Behavioral assertions for every active card identity effect.

Diagnostic only. Runs the real Gwent resolver on isolated synthetic states;
does not modify the game runtime, database, or player data.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sistemas import cartas, gwent  # noqa: E402

SMOKE_PATH = ROOT / "docs" / "scripts" / "validate-card-effect-smoke-v0.1.py"
spec = importlib.util.spec_from_file_location("card_identity_smoke_helpers", SMOKE_PATH)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)

OUT = ROOT / "docs" / "card-game-identity-behavior-assertions-v0.1.json"


def setup(card_id: str, tweak: Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], None] | None = None):
    model = cartas.get_carta(card_id)
    assert model is not None, f"missing card model: {card_id}"
    card = model.para_dict()
    row = str(card.get("fileira") or model.fileira or "melee")
    card["raridade"] = "Comum"
    card["row"] = row
    card["fileira"] = row
    card["bonus"] = 0
    card["escudo"] = 0
    state = smoke.fixture(card, row)
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["hand"] = [card, smoke.unit(f"reserve_{card_id}", power=1)]
    p1["faction"] = "Lua Negra" if card.get("faccao") != "Lua Negra" else "Véu Carmesim"
    p1["faction_boost_used"] = True
    p1["synergy_used"] = {}
    p2["faction"] = "Ordem Áurea"
    if tweak:
        tweak(state, p1, p2)
    before = copy.deepcopy(state)
    result = gwent.aplicar_jogada(state, 1, card_id=card_id, action="play", row=row)
    assert "error" not in result, result
    after = result["state"]
    ap1, ap2 = after["players"]["1"], after["players"]["2"]
    played = next((x for x in ap1["board"] if x.get("id") == card_id), None)
    assert played is not None, {"card_id": card_id, "board": [x.get("id") for x in ap1["board"]]}
    return before, after, played, ap1, ap2, row


def unit_by_id(side: dict[str, Any], unit_id: str) -> dict[str, Any]:
    found = next((x for x in side.get("board", []) if x.get("id") == unit_id), None)
    assert found is not None, f"unit not found on board: {unit_id}"
    return found


cases: list[dict[str, Any]] = []

def check(name: str, fn: Callable[[], dict[str, Any]]) -> None:
    try:
        cases.append({"case": name, "status": "passed", **fn()})
    except Exception as exc:
        cases.append({"case": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})


# Positive cases: each active identity's distinguishing result is asserted.
def test_ash_guardian():
    def tweak(s, p, o):
        card_row = s["players"]["1"]["hand"][0]["row"]
        p["board"] = [smoke.unit("ash_ally", row=card_row, bonus=0)]
    _, _, played, own, _, row = setup("chefe_guardiao_cinzas", tweak)
    ally = unit_by_id(own, "ash_ally")
    assert played["bonus"] == 1 and ally["bonus"] == 1
    return {"effect": "ash_guardian", "card_bonus": played["bonus"], "ally_bonus": ally["bonus"]}


def test_void_rend():
    def tweak(s, p, o):
        o["board"] = [smoke.unit("void_target", row="melee", power=8, bonus=2)]
    _, _, _, _, enemy, _ = setup("chefe_dama_vazio", tweak)
    target = unit_by_id(enemy, "void_target")
    assert target["bonus"] == 0
    return {"effect": "void_rend", "target_bonus_after": target["bonus"]}


def test_abyss_tithe():
    _, _, played, *_ = setup("chefe_rei_afogado")
    assert played["bonus"] == 2
    return {"effect": "abyss_tithe", "card_bonus": played["bonus"]}


def test_ruin_omen():
    def tweak(s, p, o):
        o["board"] = [smoke.unit("omen_target", row="melee", power=9, bonus=2)]
        p["board"] = [smoke.unit("omen_weak_ally", row="ranged", power=1)]
    _, _, played, _, enemy, _ = setup("chefe_oraculo_ruina", tweak)
    assert played["bonus"] == 1
    assert unit_by_id(enemy, "omen_target")["bonus"] == 1
    return {"effect": "ruin_omen", "card_bonus": played["bonus"], "target_bonus": 1}


def test_twin_dance():
    _, _, played, *_ = setup("arma_duas_luas")
    assert played["bonus"] == 1
    return {"effect": "twin_dance", "card_bonus": played["bonus"]}


def test_last_bell():
    def tweak(s, p, o):
        o["board"] = [smoke.unit("bell_enemy", row="melee", power=10, bonus=4)]
        p["board"] = [smoke.unit("bell_ally", row="ranged", power=1)]
    _, _, played, *_ = setup("arma_grande_sino", tweak)
    assert played["bonus"] == 2
    return {"effect": "last_bell", "card_bonus": played["bonus"]}


def test_vigil_seal():
    def tweak(s, p, o):
        row = s["players"]["1"]["hand"][0]["row"]
        p["board"] = [smoke.unit("vigil_ally", row=row, bonus=0)]
        s["weather"][row] = 1
    _, _, played, own, _, _ = setup("magia_selo_vigilia", tweak)
    ally = unit_by_id(own, "vigil_ally")
    assert played["weather_resist"] == 1 and ally["bonus"] == 1
    return {"effect": "vigil_seal", "weather_resist": played["weather_resist"], "ally_bonus": ally["bonus"]}


def test_hollow_thunder():
    def tweak(s, p, o):
        row = s["players"]["1"]["hand"][0]["row"]
        o["board"] = [smoke.unit("hollow_target", row=row, power=3, bonus=2)]
    _, _, _, _, enemy, _ = setup("magia_trovao_oco", tweak)
    assert unit_by_id(enemy, "hollow_target")["bonus"] == 1
    return {"effect": "hollow_thunder", "target_bonus_after": 1}


def test_ancient_mist():
    def tweak(s, p, o):
        s["weather"] = {"melee": 0, "ranged": 1, "siege": 0}
    _, _, played, *_ = setup("magia_nevoa_antiga", tweak)
    assert played["bonus"] == 2
    return {"effect": "ancient_mist", "card_bonus": played["bonus"]}


def test_devouring_eclipse():
    def tweak(s, p, o):
        o["board"] = [smoke.unit("eclipse_target", row="melee", power=3, bonus=1)]
    _, _, played, *_ = setup("magia_sol_negro", tweak)
    assert played["bonus"] == 2
    return {"effect": "devouring_eclipse", "card_bonus": played["bonus"]}


def test_veiled_moon():
    def tweak(s, p, o):
        row = s["players"]["1"]["hand"][0]["row"]
        other_row = "melee" if row != "melee" else "ranged"
        p["board"] = [smoke.unit("moon_ally", row=other_row, power=1, bonus=0)]
    _, _, played, own, *_ = setup("covenant_lua_velada", tweak)
    assert played["bonus"] == 1 and unit_by_id(own, "moon_ally")["bonus"] == 1
    return {"effect": "veiled_moon", "card_bonus": played["bonus"], "ally_bonus": 1}


def test_scarlet_bloom():
    def tweak(s, p, o):
        row = s["players"]["1"]["hand"][0]["row"]
        # A carta é Primordial no runtime; o smoke usa Comum como padrão para
        # isolar os demais efeitos, então restauramos a raridade canônica aqui.
        p["hand"][0]["raridade"] = "Primordial"
        o["board"] = [smoke.unit("scarlet_old_mark", row=row, power=5, bonus=2, podrida=1), smoke.unit("scarlet_new_mark", row=row, power=4, bonus=0)]
    _, _, _, _, enemy, _ = setup("chefe_malenia_lamina_miquella", tweak)
    old = unit_by_id(enemy, "scarlet_old_mark")
    new = unit_by_id(enemy, "scarlet_new_mark")
    assert old["podrida"] == 2 and old["bonus"] == 0 and new["podrida"] == 1
    return {"effect": "scarlet_bloom", "old_mark": old["podrida"], "old_target_bonus": old["bonus"], "new_mark": new["podrida"]}


def test_star_gravity():
    def tweak(s, p, o):
        o["board"] = [smoke.unit("gravity_target", row="melee", power=9, bonus=3)]
    _, _, _, _, enemy, row = setup("chefe_radahn_flagelo_estrelas", tweak)
    target = unit_by_id(enemy, "gravity_target")
    assert target["row"] == row and target["bonus"] == 1, {"expected_row": row, "target": target}
    return {"effect": "star_gravity", "target_row_after": target["row"], "target_bonus_after": target["bonus"]}


def test_destined_death():
    def tweak(s, p, o):
        o["board"] = [smoke.unit("death_target", row="melee", power=9, bonus=3)]
    _, _, _, _, enemy, _ = setup("chefe_maliketh_morte_destinada", tweak)
    assert unit_by_id(enemy, "death_target")["bonus"] == 1
    return {"effect": "destined_death", "target_bonus_after": 1}


def test_impaling_spear():
    def tweak(s, p, o):
        row = s["players"]["1"]["hand"][0]["row"]
        o["board"] = [smoke.unit("spear_old_mark", row=row, power=5, bonus=3, sangramento=1), smoke.unit("spear_new_mark", row=row, power=4, bonus=0)]
    _, _, _, _, enemy, _ = setup("chefe_messmer_impalador", tweak)
    old = unit_by_id(enemy, "spear_old_mark")
    new = unit_by_id(enemy, "spear_new_mark")
    assert old["sangramento"] == 0 and old["bonus"] == 1 and new["sangramento"] == 1
    return {"effect": "impaling_spear", "second_mark_target_bonus": old["bonus"], "new_target_mark": new["sangramento"]}


def test_time_storm():
    def tweak(s, p, o):
        row = s["players"]["1"]["hand"][0]["row"]
        o["board"] = [smoke.unit("storm_a", row=row, power=3), smoke.unit("storm_b", row=row, power=4)]
    _, _, played, _, enemy, _ = setup("chefe_placidusax_lorde_dragao", tweak)
    assert played["bonus"] == 2
    assert all(unit_by_id(enemy, x)["geada"] == 1 for x in ("storm_a", "storm_b"))
    return {"effect": "time_storm", "card_bonus": played["bonus"], "enemy_marks": [1, 1]}


def test_v75_golden_vow():
    def tweak(s, p, o):
        row = s["players"]["1"]["hand"][0]["row"]
        p["board"] = [smoke.unit("gold_vow_weak", row=row, power=1), smoke.unit("gold_vow_strong", row=row, power=8)]
    _, _, played, own, *_ = setup("gwent_v75_ordem_veterano_juramento", tweak)
    assert played["bonus"] == 1 and unit_by_id(own, "gold_vow_weak")["bonus"] == 1
    return {"effect": "v75_golden_vow", "card_bonus": played["bonus"], "weakest_ally_bonus": 1}


def test_v75_grace_mender():
    def tweak(s, p, o):
        row = s["players"]["1"]["hand"][0]["row"]
        p["board"] = [smoke.unit("grace_ally_a", row=row, power=1, geada=1, sangramento=1), smoke.unit("grace_ally_b", row=row, power=2, podrida=1)]
    _, _, _, own, *_ = setup("gwent_v75_ordem_confessora_graca", tweak)
    a, b = unit_by_id(own, "grace_ally_a"), unit_by_id(own, "grace_ally_b")
    assert all(a[k] == 0 for k in ("geada", "sangramento", "podrida", "loucura"))
    assert all(b[k] == 0 for k in ("geada", "sangramento", "podrida", "loucura"))
    assert a["bonus"] == 1 and b["bonus"] == 1
    return {"effect": "v75_grace_mender", "purified": 2, "bonuses": [1, 1]}


def test_v75_blood_mark():
    def tweak(s, p, o):
        row = s["players"]["1"]["hand"][0]["row"]
        o["board"] = [smoke.unit("blood_mark_target", row=row, power=7, bonus=3, sangramento=1)]
    _, _, played, _, enemy, _ = setup("gwent_v75_veu_acolito_sangue", tweak)
    target = unit_by_id(enemy, "blood_mark_target")
    assert target["sangramento"] == 0 and target["bonus"] == 1 and played["bonus"] == 1
    return {"effect": "v75_blood_mark", "target_bonus": target["bonus"], "card_bonus": played["bonus"]}


def test_v75_blood_price():
    def tweak(s, p, o):
        row = s["players"]["1"]["hand"][0]["row"]
        p["board"] = [smoke.unit("blood_price_victim", row=row, power=2), smoke.unit("blood_price_other", row=row, power=6)]
    _, _, played, own, *_ = setup("gwent_v75_veu_carrasco_preco", tweak)
    assert not any(x["id"] == "blood_price_victim" for x in own["board"])
    assert any(x["id"] == "blood_price_victim" for x in own["discard"])
    assert played["bonus"] == 2
    return {"effect": "v75_blood_price", "sacrificed": "blood_price_victim", "card_bonus": played["bonus"]}


def test_v75_frost_oracle():
    def tweak(s, p, o):
        row = s["players"]["1"]["hand"][0]["row"]
        o["board"] = [smoke.unit("frost_oracle_target", row=row, power=8, geada=1)]
    _, _, played, _, enemy, _ = setup("gwent_v75_lua_oraculo_geada", tweak)
    target = unit_by_id(enemy, "frost_oracle_target")
    assert target["geada"] == 2 and played["bonus"] == 1
    return {"effect": "v75_frost_oracle", "target_geada": target["geada"], "card_bonus": played["bonus"]}


def test_v75_gravity_shear():
    def tweak(s, p, o):
        row = s["players"]["1"]["hand"][0]["row"]
        o["board"] = [smoke.unit("shear_a", row=row, bonus=3), smoke.unit("shear_b", row=row, bonus=1), smoke.unit("shear_zero", row=row, bonus=0)]
    _, _, played, _, enemy, _ = setup("gwent_v75_lua_graviturgista", tweak)
    assert played["bonus"] == 1
    assert [unit_by_id(enemy, x)["bonus"] for x in ("shear_a", "shear_b", "shear_zero")] == [2, 0, 0]
    return {"effect": "v75_gravity_shear", "card_bonus": played["bonus"], "enemy_bonuses": [2, 0, 0]}


positive_tests = [
    ("identity_ash_guardian", test_ash_guardian),
    ("identity_void_rend", test_void_rend),
    ("identity_abyss_tithe", test_abyss_tithe),
    ("identity_ruin_omen", test_ruin_omen),
    ("identity_twin_dance", test_twin_dance),
    ("identity_last_bell", test_last_bell),
    ("identity_vigil_seal", test_vigil_seal),
    ("identity_hollow_thunder", test_hollow_thunder),
    ("identity_ancient_mist", test_ancient_mist),
    ("identity_devouring_eclipse", test_devouring_eclipse),
    ("identity_veiled_moon", test_veiled_moon),
    ("identity_scarlet_bloom", test_scarlet_bloom),
    ("identity_star_gravity", test_star_gravity),
    ("identity_destined_death", test_destined_death),
    ("identity_impaling_spear", test_impaling_spear),
    ("identity_time_storm", test_time_storm),
    ("identity_v75_golden_vow", test_v75_golden_vow),
    ("identity_v75_grace_mender", test_v75_grace_mender),
    ("identity_v75_blood_mark", test_v75_blood_mark),
    ("identity_v75_blood_price", test_v75_blood_price),
    ("identity_v75_frost_oracle", test_v75_frost_oracle),
    ("identity_v75_gravity_shear", test_v75_gravity_shear),
]
for name, fn in positive_tests:
    check(name, fn)

# Negative/limit cases for conditional identities: confirm they do not grant
# their conditional value when the precondition is absent.
def negative_case(card_id: str, configure, check_fn):
    _, _, played, own, enemy, row = setup(card_id, configure)
    check_fn(played, own, enemy, row)


def no_same_row_ally(s, p, o):
    row = s["players"]["1"]["hand"][0]["row"]
    p["board"] = [smoke.unit("only_other_row", row="melee" if row != "melee" else "ranged")]

def test_ash_guardian_negative():
    _, _, played, own, _, row = setup("chefe_guardiao_cinzas", no_same_row_ally)
    assert played["bonus"] == 0
    assert all(u["row"] != row for u in own["board"] if u["id"] != "chefe_guardiao_cinzas")
    return {"effect": "ash_guardian", "without_same_row_ally_card_bonus": 0}


def test_last_bell_negative():
    def cfg(s,p,o):
        row=s["players"]["1"]["hand"][0]["row"]
        p["board"]=[smoke.unit("bell_lead_ally",row="melee",power=10,bonus=5)]
        o["board"]=[smoke.unit("bell_low_enemy",row=row,power=1,bonus=0)]
    _,_,played,*_=setup("arma_grande_sino",cfg)
    assert played["bonus"] == 0
    return {"effect":"last_bell","not_behind_card_bonus":0}


def test_ancient_mist_negative():
    def cfg(s,p,o): s["weather"]={"melee":0,"ranged":0,"siege":0}
    _,_,played,*_=setup("magia_nevoa_antiga",cfg)
    assert played["bonus"] == 0
    return {"effect":"ancient_mist","no_weather_card_bonus":0}


def test_eclipse_negative():
    def cfg(s,p,o): o["board"]=[smoke.unit("unbuffed_enemy",bonus=0)]
    _,_,played,*_=setup("magia_sol_negro",cfg)
    assert played["bonus"] == 0
    return {"effect":"devouring_eclipse","no_positive_enemy_bonus":0}


def test_twin_dance_negative():
    def cfg(s,p,o):
        row=s["players"]["1"]["hand"][0]["row"]
        p["board"]=[smoke.unit("same_row_only",row=row)]
    _,_,played,*_=setup("arma_duas_luas",cfg)
    assert played["bonus"] == 0
    return {"effect":"twin_dance","no_other_row_ally":0}


def test_void_rend_no_target():
    def cfg(s,p,o): o["board"]=[]
    _,_,_,_,enemy,_=setup("chefe_dama_vazio",cfg)
    assert not enemy["board"]
    return {"effect":"void_rend","empty_enemy_board":"no-op without error"}


def test_time_storm_no_target():
    def cfg(s,p,o): o["board"]=[]
    _,_,played,*_=setup("chefe_placidusax_lorde_dragao",cfg)
    assert played["bonus"] == 0
    return {"effect":"time_storm","empty_enemy_board_card_bonus":0}


def test_gravity_shear_one_target():
    def cfg(s,p,o):
        row=s["players"]["1"]["hand"][0]["row"]
        o["board"]=[smoke.unit("shear_one",row=row,bonus=2),smoke.unit("shear_zero",row=row,bonus=0)]
    _,_,played,_,enemy,_=setup("gwent_v75_lua_graviturgista",cfg)
    assert played["bonus"] == 0 and unit_by_id(enemy,"shear_one")["bonus"] == 1
    return {"effect":"v75_gravity_shear","one_eligible_target_no_self_bonus":0}


def test_frost_oracle_no_target():
    def cfg(s,p,o): o["board"]=[]
    _,_,played,*_=setup("gwent_v75_lua_oraculo_geada",cfg)
    assert played["bonus"] == 0
    return {"effect":"v75_frost_oracle","empty_enemy_row_card_bonus":0}


def test_blood_price_no_victim():
    def cfg(s,p,o): p["board"]=[]
    _,_,played,own,*_=setup("gwent_v75_veu_carrasco_preco",cfg)
    assert played["bonus"] == 1
    return {"effect":"v75_blood_price","no_victim_fallback_bonus":1}


def test_grace_mender_empty_row():
    def cfg(s,p,o): p["board"]=[]
    _,_,played,*_=setup("gwent_v75_ordem_confessora_graca",cfg)
    assert played["bonus"] == 1
    return {"effect":"v75_grace_mender","no_allies_fallback_bonus":1}


negative_tests = [
    ("negative_ash_guardian_no_same_row_ally", test_ash_guardian_negative),
    ("negative_last_bell_not_behind", test_last_bell_negative),
    ("negative_ancient_mist_no_weather", test_ancient_mist_negative),
    ("negative_devouring_eclipse_no_positive_enemy", test_eclipse_negative),
    ("negative_twin_dance_no_other_row_ally", test_twin_dance_negative),
    ("negative_void_rend_no_enemy_target", test_void_rend_no_target),
    ("negative_time_storm_no_enemy_target", test_time_storm_no_target),
    ("negative_gravity_shear_only_one_target", test_gravity_shear_one_target),
    ("negative_frost_oracle_no_enemy_target", test_frost_oracle_no_target),
    ("negative_blood_price_no_victim", test_blood_price_no_victim),
    ("negative_grace_mender_empty_row", test_grace_mender_empty_row),
]
for name, fn in negative_tests:
    check(name, fn)

report = {
    "metadata": {
        "document": "Card identity behavioral assertions v0.1",
        "status": "DIAGNOSTIC ONLY; ALL ACTIVE IDENTITY EFFECTS EXERCISED IN SELECTED CONTROLLED STATES",
        "baseline": "soulsbo-main(1).zip",
        "engine": "sistemas.gwent.aplicar_jogada / _aplicar_habilidade_identidade",
        "method": "One positive assertion for each active mapping plus selected negative/limit cases; Common rarity isolates identity behavior from rarity amplification.",
    },
    "counts": {
        "active_identity_effects": len(gwent.CARD_IDENTITY_ABILITIES),
        "positive_assertions": len(positive_tests),
        "negative_or_limit_assertions": len(negative_tests),
        "total_assertions": len(cases),
        "passed": sum(c["status"] == "passed" for c in cases),
        "failed": sum(c["status"] == "failed" for c in cases),
    },
    "cases": cases,
    "limitations": [
        "One controlled positive scenario per active identity is not exhaustive branch coverage; multi-target caps, empty/blocked/duplicate targets and all status thresholds still require more cases.",
        "All cards use Common rarity to isolate base identity effects; interaction with RARITY_EFFECT_BUDGET is not tested here.",
        "Synthetic boards do not estimate activation frequency, expected value, deck synergy, or match win rate.",
        "No database, Discord, web API, frontend, image pipeline, or production game session is involved.",
    ],
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report["counts"], ensure_ascii=False))
for c in cases:
    if c["status"] != "passed":
        print(json.dumps(c, ensure_ascii=False))
print(f"wrote {OUT}")
if report["counts"]["failed"]:
    raise SystemExit(1)
