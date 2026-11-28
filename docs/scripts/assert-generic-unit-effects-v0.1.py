#!/usr/bin/env python3
"""Behavioral assertions for generic unit effects in the live Gwent engine.

This script deliberately excludes specials/relics (covered separately), identity
abilities (see assert-card-identity-behavior-v0.1.py), and lifecycle hooks.
It uses synthetic states and does not touch persistent data or production runtime.
"""
from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sistemas import gwent  # noqa: E402

SMOKE_PATH = ROOT / "docs" / "scripts" / "validate-card-effect-smoke-v0.1.py"
spec = importlib.util.spec_from_file_location("generic_effect_smoke_helpers", SMOKE_PATH)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)
OUT = ROOT / "docs" / "card-game-generic-unit-assertions-v0.1.json"


def play(skill: str, *, row="melee", round_no=1, configure=None):
    card = smoke.unit(f"generic_assert_{skill}", skill=skill, row=row, power=4, rarity="Comum")
    state = smoke.fixture(card, row)
    state["round"] = round_no
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["hand"] = [card, smoke.unit(f"reserve_{skill}", power=1)]
    p1["faction"] = "Lua Negra"
    p1["faction_boost_used"] = True
    p1["synergy_used"] = {}
    p2["faction"] = "Véu Carmesim"
    if configure:
        configure(state, p1, p2)
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row=row)
    assert "error" not in result, result
    after = result["state"]
    own, enemy = after["players"]["1"], after["players"]["2"]
    placed = next((x for x in own["board"] if x.get("id") == card["id"]), None)
    assert placed is not None, {"skill": skill, "board": [x.get("id") for x in own["board"]]}
    return after, placed, own, enemy


def find(side, card_id):
    return next((x for x in side.get("board", []) if x.get("id") == card_id), None)

cases=[]
def check(name: str, fn: Callable[[], dict[str, Any]]):
    try: cases.append({"case":name,"status":"passed",**fn()})
    except Exception as e: cases.append({"case":name,"status":"failed","error":f"{type(e).__name__}: {e}"})

# Positive branch tests for generic unit handlers.
def losing(s,p,o):
    p["board"]=[smoke.unit("own_low",power=1,row="siege")]
    o["board"]=[smoke.unit("enemy_high",power=9,row="melee",bonus=2)]
def winning(s,p,o):
    p["board"]=[smoke.unit("own_high",power=10,row="siege")]
    o["board"]=[smoke.unit("enemy_low",power=1,row="melee")]
def equal(s,p,o):
    p["board"]=[]; o["board"]=[]
def tests_positive():
    def run_bonus(skill, expect, config=None, row="melee", rnd=1):
        _, card, *_ = play(skill,row=row,round_no=rnd,configure=config)
        assert int(card.get("bonus",0)) == expect, {"skill":skill,"expected":expect,"actual":card.get("bonus")}
        return {"skill":skill,"expected_bonus":expect,"observed_bonus":card.get("bonus",0)}
    check("retaliacao_behind_plus1",lambda:run_bonus("retaliacao",1,losing))
    check("impeto_ahead_plus1",lambda:run_bonus("impeto",1,winning))
    check("ultimo_folego_round3_plus1",lambda:run_bonus("ultimo_folego",1,None,rnd=3))
    check("contragolpe_behind_plus2",lambda:run_bonus("contragolpe",2,losing))
    check("encadeamento_same_row_plus2",lambda:run_bonus("encadeamento",2,lambda s,p,o:p.update(last_row="melee")))
    check("adaptacao_other_row_plus1",lambda:run_bonus("adaptacao",1,lambda s,p,o:p.update(last_row="ranged")))
    check("sangue_frio_tied_plus2",lambda:run_bonus("sangue_frio",2,equal))
    check("instinto_behind_plus2",lambda:run_bonus("instinto",2,losing))
    check("precisao_ranged_plus1",lambda:run_bonus("precisao",1,None,row="ranged"))
    check("cacador_arcano_enemy_moon_plus1",lambda:run_bonus("cacador_arcano",1,None))
    check("quebra_ritmo_enemy_last_row_plus1",lambda:run_bonus("quebra_ritmo",1,lambda s,p,o:o.update(last_row="melee")))
    check("lei_primeva_round1_plus2",lambda:run_bonus("lei_primeva",2,None,rnd=1))
    check("decreto_soberano_reduces_all_enemy_bonuses",lambda:(
        (lambda x: (x is not None and x["bonus"] == 0) or (_ for _ in ()).throw(AssertionError(x))) (
            find(play("decreto_soberano",configure=lambda s,p,o:o.update(board=[smoke.unit("decree_target",bonus=2),smoke.unit("decree_target_b",bonus=1)]))[3],"decree_target")
        ) and {"skill":"decreto_soberano","target_bonus_after":0}
    ))
    check("olho_tempestade_weather_plus2",lambda:run_bonus("olho_tempestade",2,lambda s,p,o:s["weather"].update(melee=1)))
    check("fome_abismo_behind_plus2",lambda:run_bonus("fome_abismo",2,losing))
    check("paradoxo_eterno_round3_after_enemy_win_plus2",lambda:run_bonus("paradoxo_eterno",2,lambda s,p,o:s.update(rounds=[{"winner_id":"2"}]),rnd=3))
    check("guardiao_fileira_one_per_ally_capped_three",lambda:run_bonus("guardiao_fileira",2,lambda s,p,o:p.update(board=[smoke.unit("g1",row="melee"),smoke.unit("g2",row="melee") ])))
    check("cacador_solitario_empty_row_plus2",lambda:run_bonus("cacador_solitario",2,lambda s,p,o:p.update(board=[smoke.unit("elsewhere",row="ranged") ])))
    check("estandarte_buffs_same_row_allies",lambda:(
        (lambda own: all(find(own,x)["bonus"]==1 for x in ("banner_a","banner_b")) or (_ for _ in ()).throw(AssertionError(own))) (
            play("estandarte",configure=lambda s,p,o:p.update(board=[smoke.unit("banner_a",row="melee"),smoke.unit("banner_b",row="melee")]))[2]
        ) and {"skill":"estandarte","same_row_allies_buffed":2}
    ))
    check("resistencia_climatica_weather_resist_two",lambda:(
        (lambda card: (card.get("weather_resist")==2) or (_ for _ in ()).throw(AssertionError(card))) (
            play("resistencia_climatica",configure=lambda s,p,o:s["weather"].update(melee=2))[1]
        ) and {"skill":"resistencia_climatica","weather_resist":2}
    ))
    check("eco_arcano_special_discard_plus2",lambda:run_bonus("eco_arcano",2,lambda s,p,o:p.update(discard=[smoke.unit("discarded_special",special=True)])))
    check("escudo_ferro_enters_with_shield",lambda:(
        (lambda card: (card.get("escudo")==1) or (_ for _ in ()).throw(AssertionError(card))) (play("escudo_ferro")[1])
        and {"skill":"escudo_ferro","shield":1}
    ))
    check("devorar_sacrifices_weakest_and_caps_bonus",lambda:(
        (lambda res: (res[1]["bonus"]==3 and find(res[2],"devour_victim") is None and any(x["id"]=="devour_victim" for x in res[2]["discard"])) or (_ for _ in ()).throw(AssertionError(res[1]))) (
            play("devorar",configure=lambda s,p,o:p.update(board=[smoke.unit("devour_victim",power=3,row="melee"),smoke.unit("devour_other",power=9,row="melee")]))
        ) and {"skill":"devorar","victim":"devour_victim","card_bonus":3}
    ))
    check("ressurgir_revives_highest_power_le_five",lambda:(
        (lambda res: (find(res[2],"discard_unit_4") is not None and res[1]["bonus"]==0) or (_ for _ in ()).throw(AssertionError(res[2]["board"])))(play("ressurgir"))
        and {"skill":"ressurgir","revived":"discard_unit_4"}
    ))
    check("dupla_fornalha_same_row_plus2",lambda:run_bonus("dupla_fornalha",2,lambda s,p,o:p.update(board=[smoke.unit("dupla_ally",row="melee") ])))
    check("irmandade_veu_other_row_plus2",lambda:run_bonus("irmandade_veu",2,lambda s,p,o:p.update(board=[smoke.unit("irmandade_ally",row="ranged") ])))
    check("circulo_arcano_special_discard_plus2",lambda:run_bonus("circulo_arcano",2,lambda s,p,o:p.update(board=[],discard=[smoke.unit("circle_special",special=True)])))

tests_positive()

# Negative/limit conditions where the effect should not supply its conditional bonus.
def run_zero(skill, config=None, row="melee", rnd=1):
    _, card, *_ = play(skill,row=row,round_no=rnd,configure=config)
    assert int(card.get("bonus",0)) == 0, {"skill":skill,"actual":card.get("bonus")}
    return {"skill":skill,"without_condition_bonus":0}

check("negative_retaliacao_not_behind",lambda:run_zero("retaliacao",winning))
check("negative_impeto_not_ahead",lambda:run_zero("impeto",losing))
check("negative_primeira_luz_not_round1",lambda:run_zero("primeira_luz",None,rnd=2))
check("negative_ultimo_folego_not_round3",lambda:run_zero("ultimo_folego",None,rnd=2))
check("negative_encadeamento_other_row",lambda:run_zero("encadeamento",lambda s,p,o:p.update(last_row="ranged")))
check("negative_adaptacao_no_previous_row",lambda:run_zero("adaptacao",lambda s,p,o:p.update(last_row=None)))
check("negative_sangue_frio_not_tied",lambda:run_zero("sangue_frio",losing))
check("negative_precisao_not_ranged",lambda:run_zero("precisao",None,row="melee"))
check("negative_quebra_ritmo_different_enemy_row",lambda:run_zero("quebra_ritmo",lambda s,p,o:o.update(last_row="ranged")))
check("negative_olho_tempestade_no_weather",lambda:run_zero("olho_tempestade",lambda s,p,o:s.update(weather={"melee":0,"ranged":0,"siege":0})))
check("negative_cacador_solitario_same_row_ally",lambda:run_zero("cacador_solitario",lambda s,p,o:p.update(board=[smoke.unit("same_row_ally",row="melee")])))
check("negative_eco_arcano_no_special_discard",lambda:run_zero("eco_arcano",lambda s,p,o:p.update(discard=[smoke.unit("normal_discard")])))

report={
 "metadata":{"document":"Generic unit effect behavioral assertions v0.1","status":"DIAGNOSTIC ONLY; SELECTED UNIT SKILL BRANCHES","baseline":"soulsbo-main(1).zip","engine":"sistemas.gwent.aplicar_jogada","method":"Positive branch tests for selected generic unit effects plus negative condition tests; synthetic fixtures; Common rarity."},
 "counts":{"assertions":len(cases),"passed":sum(x["status"]=="passed" for x in cases),"failed":sum(x["status"]=="failed" for x in cases)},
 "cases":cases,
 "limitations":[
  "This suite covers generic unit effects, not all 56 direct handler IDs; special cards and relics remain partly covered by the original 13 behavior assertions and smoke tests.",
  "Conditional unit effects are checked in selected positive and negative states only; multi-state thresholds and all rarity interactions remain open.",
  "Synthetic fixtures do not estimate condition frequency, effect EV, faction win rate, or real deck behavior.",
  "No production database, server, Discord action, web frontend, or image pipeline is involved."
 ]
}
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report["counts"],ensure_ascii=False))
for x in cases:
 if x["status"]!="passed": print(json.dumps(x,ensure_ascii=False))
print(f"wrote {OUT}")
if report["counts"]["failed"]: raise SystemExit(1)
