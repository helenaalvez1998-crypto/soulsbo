#!/usr/bin/env python3
"""Behavioral assertions for all current Gwent leader effects.

Invokes the real `aplicar_jogada(..., action="leader")` on synthetic match states.
This is a controlled unit/integration harness, not a production match simulation.
"""
from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sistemas import gwent  # noqa: E402

SP = ROOT / "docs/scripts/validate-card-effect-smoke-v0.1.py"
spec = importlib.util.spec_from_file_location("leader_effect_smoke_helpers", SP)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)
OUT = ROOT / "docs/card-game-leader-assertions-v0.1.json"

LEADERS = {
    "godfrey": ("comandante_fornalha", "Ordem Áurea"),
    "morgott": ("bastiao_ancestral", "Ordem Áurea"),
    "radagon": ("juiz_cerco", "Ordem Áurea"),
    "mohg": ("mestre_veu", "Véu Carmesim"),
    "rykard": ("sombra_caminhante", "Véu Carmesim"),
    "esgar": ("voz_caidos", "Véu Carmesim"),
    "papa": ("lider_papa_esquecido", "Os Esquecidos"),
    "abadessa": ("lider_abadessa_ruinas", "Os Esquecidos"),
    "martir": ("lider_martir_vigilia", "Os Esquecidos"),
    "rennala": ("arquimaga_eclipse", "Lua Negra"),
    "astel": ("mestre_eclipse", "Lua Negra"),
    "loretta": ("oraculo_tempestade", "Lua Negra"),
}

cases: list[dict[str, Any]] = []
def check(name: str, fn: Callable[[], dict[str, Any]]) -> None:
    try:
        cases.append({"case": name, "status": "passed", **fn()})
    except Exception as exc:
        cases.append({"case": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})

def state_for(leader_key: str, *, row: str = "melee"):
    leader_id, faction = LEADERS[leader_key]
    base = smoke.unit("leader_fixture")
    state = smoke.fixture(base, row)
    p = state["players"]["1"]
    p["faction"] = faction
    p["leader_id"] = leader_id
    p["leader_used"] = False
    p["hand"] = [smoke.unit("leader_hand_reserve")]
    p["passed"] = False
    state["turn"] = "1"
    return state

def activate(leader_key: str, *, row: str = "melee", configure=None):
    state = state_for(leader_key, row=row)
    p, o = state["players"]["1"], state["players"]["2"]
    if configure:
        configure(state, p, o)
    result = gwent.aplicar_jogada(state, 1, action="leader", row=row)
    # The engine returns a new serialized state; positive assertions must inspect it.
    resolved = result.get("state", state) if isinstance(result, dict) else state
    return result, resolved, resolved["players"]["1"], resolved["players"]["2"]

def card(side, cid):
    return next((x for x in side.get("board", []) if x.get("id") == cid), None)

def test_godfrey():
    def cfg(s,p,o):
        p["board"] = [smoke.unit("g_melee_a",row="melee"), smoke.unit("g_melee_b",row="melee"), smoke.unit("g_ranged",row="ranged")]
    result,s,p,o=activate("godfrey",configure=cfg)
    assert "error" not in result, result
    assert [card(p,x)["bonus"] for x in ("g_melee_a","g_melee_b","g_ranged")] == [2,2,0]
    assert p["leader_used"] is True
    return {"leader":"Godfrey","bonuses":[2,2,0],"only_melee":True}

def test_morgott():
    def cfg(s,p,o):
        p["board"]=[smoke.unit("m_best",row="siege",power=9),smoke.unit("m_second",row="siege",power=6),smoke.unit("m_third",row="siege",power=2),smoke.unit("m_other_row",row="ranged",power=10)]
    result,s,p,o=activate("morgott",row="siege",configure=cfg)
    assert "error" not in result,result
    assert [(card(p,x)["bonus"],card(p,x)["escudo"]) for x in ("m_best","m_second","m_third","m_other_row")] == [(1,1),(1,1),(0,0),(0,0)]
    return {"leader":"Morgott","selected_two_strongest":["m_best","m_second"],"unselected_unchanged":True}

def test_radagon():
    def cfg(s,p,o):
        p["board"]=[smoke.unit("r_bleed",sangramento=1),smoke.unit("r_frost",geada=2),smoke.unit("r_rot",podrida=1),smoke.unit("r_mad",loucura=1),smoke.unit("r_healthy",bonus=0)]
    result,s,p,o=activate("radagon",configure=cfg)
    assert "error" not in result,result
    for cid in ("r_bleed","r_frost","r_rot","r_mad"):
        u=card(p,cid); assert all(u[k]==0 for k in ("sangramento","geada","podrida","loucura")) and u["bonus"]==1
    assert card(p,"r_healthy")["bonus"]==0
    return {"leader":"Radagon","four_negative_status_types_removed":True,"purified_units":4}

def test_mohg():
    def cfg(s,p,o):
        o["board"]=[smoke.unit("h_top",row="melee",power=9,sangramento=1,bonus=4),smoke.unit("h_second",row="melee",power=7),smoke.unit("h_third",row="melee",power=2),smoke.unit("h_other_row",row="ranged",power=10)]
    result,s,p,o=activate("mohg",configure=cfg)
    assert "error" not in result,result
    assert (card(o,"h_top")["sangramento"],card(o,"h_top")["bonus"])==(0,2)
    assert card(o,"h_second")["sangramento"]==1
    assert card(o,"h_third")["sangramento"]==0 and card(o,"h_other_row")["sangramento"]==0
    return {"leader":"Mohg","top_two_marked":True,"second_mark_triggers_minus_two":True}

def test_rykard():
    def cfg(s,p,o):
        p["board"]=[smoke.unit("y_victim",row="ranged",power=1,escudo=1),smoke.unit("y_survivor_a",row="ranged",power=5),smoke.unit("y_survivor_b",row="ranged",power=4),smoke.unit("y_other_row",row="melee",power=3)]
    result,s,p,o=activate("rykard",row="ranged",configure=cfg)
    assert "error" not in result,result
    assert card(p,"y_victim") is None
    assert card(p,"y_survivor_a")["bonus"]==2 and card(p,"y_survivor_b")["bonus"]==2
    assert card(p,"y_other_row")["bonus"]==0
    assert any(x.get("id")=="y_victim" for x in p["discard"])
    return {"leader":"Rykard","weakest_sacrificed_even_with_shield":True,"remaining_row_allies_bonus":2}

def test_esgar():
    def cfg(s,p,o):
        p["discard"]=[smoke.unit("e_power4",power=4),smoke.unit("e_power5",power=5,geada=1),smoke.unit("e_power6",power=6)]
    result,s,p,o=activate("esgar",row="siege",configure=cfg)
    assert "error" not in result,result
    revived=card(p,"e_power5")
    assert revived and revived["row"]=="siege" and revived["bonus"]==1 and revived["geada"]==0
    assert card(p,"e_power4") is None and card(p,"e_power6") is None
    assert not any(x.get("id")=="e_power5" for x in p["discard"])
    return {"leader":"Esgar","strongest_eligible_revived":"e_power5","row":"siege"}

def test_papa():
    def cfg(s,p,o):
        p["board"]=[smoke.unit("p_forget_a",row="ranged",faction="Os Esquecidos"),smoke.unit("p_forget_b",row="ranged",faction="Os Esquecidos"),smoke.unit("p_other_faction",row="ranged",faction="Lua Negra"),smoke.unit("p_other_row",row="melee",faction="Os Esquecidos")]
    result,s,p,o=activate("papa",row="ranged",configure=cfg)
    assert "error" not in result,result
    assert [card(p,x)["bonus"] for x in ("p_forget_a","p_forget_b","p_other_faction","p_other_row")] == [1,1,0,0]
    return {"leader":"Papa Esquecido","only_forgotten_selected_row":True}

def test_abadessa():
    status_keys = ("sangramento", "geada", "podrida", "loucura")
    def cfg(s,p,o):
        p["board"] = [
            smoke.unit("ab_top", row="siege", faction="Os Esquecidos", power=7, sangramento=1, geada=1),
            smoke.unit("ab_second", row="siege", faction="Os Esquecidos", power=6, podrida=1),
            smoke.unit("ab_third", row="siege", faction="Os Esquecidos", power=3, loucura=1),
            smoke.unit("ab_foreign", row="siege", faction="Lua Negra", power=9, sangramento=1),
            smoke.unit("ab_other_row", row="ranged", faction="Os Esquecidos", power=10, geada=1),
        ]
    result,s,p,o=activate("abadessa",row="siege",configure=cfg)
    assert "error" not in result,result
    for cid in ("ab_top", "ab_second"):
        u=card(p,cid)
        assert all(u[key] == 0 for key in status_keys)
        assert u["bonus"] == 1
    assert card(p,"ab_third")["loucura"] == 1
    assert card(p,"ab_foreign")["sangramento"] == 1
    assert card(p,"ab_other_row")["geada"] == 1
    return {"leader":"Abadessa das Ruínas","purified_two_strongest_eligible_forgotten_allies":True}

def test_martir():
    def cfg(s,p,o):
        p["discard"] = [
            smoke.unit("mar_small", faction="Os Esquecidos", power=3),
            smoke.unit("mar_strong", faction="Os Esquecidos", power=5, bonus=2, escudo=1, sangramento=1, geada=1, podrida=1, loucura=1),
            smoke.unit("mar_foreign", faction="Lua Negra", power=8),
            smoke.unit("mar_over_cap", faction="Os Esquecidos", power=6),
            smoke.unit("mar_special", faction="Os Esquecidos", power=0, special=True),
        ]
    result,s,p,o=activate("martir",row="ranged",configure=cfg)
    assert "error" not in result,result
    revived=card(p,"mar_strong")
    assert revived is not None and revived["row"] == "ranged" and revived["fileira"] == "ranged"
    assert revived["bonus"] == 3 and not revived.get("escudo")
    assert all(revived[key] == 0 for key in ("sangramento", "geada", "podrida", "loucura"))
    assert {x["id"] for x in p["discard"]} == {"mar_small", "mar_foreign", "mar_over_cap", "mar_special"}
    return {"leader":"Mártir da Vigília","revived_strongest_forgotten_base_power_5_or_less":True,"cleared_status_and_shield":True}

def test_rennala():
    def cfg(s,p,o):
        p["board"]=[smoke.unit("rn_siege_frost",row="siege",geada=1),smoke.unit("rn_siege_rot",row="siege",podrida=2),smoke.unit("rn_melee_frost",row="melee",geada=1),smoke.unit("rn_healthy",row="siege")]
    result,s,p,o=activate("rennala",configure=cfg)
    assert "error" not in result,result
    for cid in ("rn_siege_frost","rn_siege_rot","rn_melee_frost"):
        u=card(p,cid); assert u["geada"]==0 and u["podrida"]==0
    assert card(p,"rn_siege_frost")["bonus"]==1 and card(p,"rn_siege_rot")["bonus"]==1
    assert card(p,"rn_melee_frost")["bonus"]==0 and card(p,"rn_healthy")["bonus"]==0
    return {"leader":"Rennala","purified":3,"only_siege_purified_buffed":True}

def test_astel():
    def cfg(s,p,o):
        o["board"]=[smoke.unit("a_top",row="siege",power=9),smoke.unit("a_second",row="siege",power=7),smoke.unit("a_third",row="siege",power=5,geada=2),smoke.unit("a_fourth",row="siege",power=1),smoke.unit("a_other",row="ranged",power=10)]
    result,s,p,o=activate("astel",row="siege",configure=cfg)
    assert "error" not in result,result
    assert [card(o,x)["geada"] for x in ("a_top","a_second","a_third","a_fourth","a_other")] == [1,1,2,0,0]
    return {"leader":"Astel","top_three_marked_with_cap":True}

def test_loretta():
    def cfg(s,p,o):
        p["board"]=[smoke.unit("l_top",row="ranged",power=8),smoke.unit("l_second",row="ranged",power=6),smoke.unit("l_third",row="ranged",power=2),smoke.unit("l_other",row="melee",power=10)]
    result,s,p,o=activate("loretta",row="ranged",configure=cfg)
    assert "error" not in result,result
    assert [card(p,x)["bonus"] for x in ("l_top","l_second","l_third","l_other")] == [2,2,0,0]
    return {"leader":"Loretta","top_two_ranged_allies_buffed":True}

for name, fn in [
    ("leader_godfrey_buffs_all_melee_only",test_godfrey),
    ("leader_morgott_shields_and_buffs_two_strongest_selected_row",test_morgott),
    ("leader_radagon_purifies_all_four_status_types",test_radagon),
    ("leader_mohg_marks_two_and_triggers_second_mark_hemorrhage",test_mohg),
    ("leader_rykard_sacrifices_weakest_and_buffs_remaining_row_allies",test_rykard),
    ("leader_esgar_revives_strongest_eligible_discard_unit",test_esgar),
    ("leader_papa_buffs_only_forgotten_in_selected_row",test_papa),
    ("leader_abadessa_purifies_two_strongest_affected_forgotten_allies",test_abadessa),
    ("leader_martir_revives_strongest_eligible_forgotten_unit",test_martir),
    ("leader_rennala_purifies_and_buffs_only_siege",test_rennala),
    ("leader_astel_marks_top_three_selected_row_with_stack_cap",test_astel),
    ("leader_loretta_buffs_top_two_ranged",test_loretta),
]: check(name,fn)

# Negative/limit cases: errors must not consume the leader action.
def negative_case(name, leader_key, *, row="melee", configure=None, expected_error=None):
    result,s,p,o=activate(leader_key,row=row,configure=configure)
    assert "error" in result, result
    if expected_error:
        assert expected_error in result["error"], result["error"]
    assert p["leader_used"] is False, "Invalid activation must not consume leader action"
    return {"leader":leader_key,"rejected":True,"error":result["error"]}

check("negative_godfrey_requires_melee_ally",lambda: negative_case("godfrey_no_melee","godfrey",configure=lambda s,p,o:p.update(board=[smoke.unit("only_ranged",row="ranged")]),expected_error="Corpo a Corpo"))
check("negative_morgott_rejects_if_all_selected_allies_shielded",lambda: negative_case("morgott_shielded","morgott",row="melee",configure=lambda s,p,o:p.update(board=[smoke.unit("shielded",escudo=1)]),expected_error="sem Escudo"))
check("negative_radagon_requires_negative_status",lambda: negative_case("radagon_clean","radagon",configure=lambda s,p,o:p.update(board=[smoke.unit("clean")]),expected_error="Nenhum aliado"))
check("negative_mohg_requires_enemy_in_selected_row",lambda: negative_case("mohg_empty","mohg",configure=lambda s,p,o:o.update(board=[smoke.unit("enemy_other_row",row="ranged")]),expected_error="Não há inimigos"))
check("negative_rykard_requires_two_allies",lambda: negative_case("rykard_one","rykard",configure=lambda s,p,o:p.update(board=[smoke.unit("one_ally")]),expected_error="ao menos 2"))
check("negative_esgar_requires_eligible_discard_unit",lambda: negative_case("esgar_empty","esgar",configure=lambda s,p,o:p.update(discard=[smoke.unit("special",special=True,power=0),smoke.unit("too_strong",power=6)]),expected_error="poder 5 ou menos"))
check("negative_papa_requires_forgotten_in_selected_row",lambda: negative_case("papa_none","papa",configure=lambda s,p,o:p.update(board=[smoke.unit("not_forgotten",faction="Lua Negra")]),expected_error="Esquecidos"))
check("negative_abadessa_requires_affected_forgotten_ally",lambda: negative_case("abadessa_clean","abadessa",row="siege",configure=lambda s,p,o:p.update(board=[smoke.unit("clean_forgotten",faction="Os Esquecidos",row="siege")]),expected_error="afetado na fileira"))
check("negative_martir_requires_eligible_forgotten_discard_unit",lambda: negative_case("martir_empty","martir",configure=lambda s,p,o:p.update(discard=[smoke.unit("foreign_unit",faction="Lua Negra",power=4),smoke.unit("forgotten_over_cap",faction="Os Esquecidos",power=6)]),expected_error="poder-base até 5"))
check("negative_rennala_requires_frost_or_rot",lambda: negative_case("rennala_clean","rennala",configure=lambda s,p,o:p.update(board=[smoke.unit("clean")]),expected_error="Geada ou Podridão"))
check("negative_astel_requires_enemy_in_selected_row",lambda: negative_case("astel_empty","astel",configure=lambda s,p,o:o.update(board=[smoke.unit("enemy_other",row="ranged")]),expected_error="Não há inimigos"))
check("negative_loretta_rejects_non_ranged_row",lambda: negative_case("loretta_wrong_row","loretta",row="melee",configure=lambda s,p,o:p.update(board=[smoke.unit("l_melee",row="melee")]),expected_error="Longa Distância"))
check("negative_loretta_requires_ranged_ally",lambda: negative_case("loretta_no_ranged","loretta",row="ranged",configure=lambda s,p,o:p.update(board=[smoke.unit("l_melee_only",row="melee")]),expected_error="Longa Distância"))
def test_leader_reuse():
    first,state,p,o=activate("godfrey",configure=lambda s,p,o:p.update(board=[smoke.unit("reusable_melee")]))
    assert "error" not in first, first
    # The real first activation passes the turn; reset only the turn pointer so
    # the second call can reach the one-use guard rather than the turn guard.
    state["turn"] = "1"
    second=gwent.aplicar_jogada(state,1,action="leader",row="melee")
    assert "error" in second and "já foi usada" in second["error"], second
    assert p["leader_used"] is True
    return {"leader":"Godfrey","second_activation_rejected":True}

check("negative_leader_cannot_be_reused",test_leader_reuse)

report={
    "metadata":{
        "document":"Leader effect behavioral assertions v0.1",
        "status":"DIAGNOSTIC ONLY; ALL TWELVE LEADER HANDLERS, SELECTED POSITIVE AND NEGATIVE SCENARIOS",
        "baseline":"soulsbo-main(1).zip",
        "engine":"sistemas.gwent.aplicar_jogada(..., action='leader')",
        "scope":"Synthetic controlled states; no database/API/site/Discord/R2/production match"
    },
    "counts":{"assertions":len(cases),"passed":sum(x["status"]=="passed" for x in cases),"failed":sum(x["status"]=="failed" for x in cases)},
    "cases":cases,
    "limitations":[
        "All twelve leader branches are exercised at least once, with selected negative/limit conditions; exhaustive combinations of board states are not covered.",
        "The tests use rarity-independent synthetic unit records; leadership upgrades or external campaign modifiers are not represented.",
        "The action flow is exercised in memory; persistent match serialization, HTTP API, frontend target choices, Discord command flow and production database are not tested.",
        "Passing behavior assertions do not measure strategic strength, balance or win rate."
    ]
}
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report["counts"],ensure_ascii=False))
for c in cases:
    if c["status"]!="passed": print(json.dumps(c,ensure_ascii=False))
print(f"wrote {OUT}")
if report["counts"]["failed"]: raise SystemExit(1)
