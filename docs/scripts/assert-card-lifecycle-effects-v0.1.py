#!/usr/bin/env python3
"""Behavioral assertions for death-trigger and round-end card hooks."""
from __future__ import annotations
import importlib.util,json,sys
from pathlib import Path
from typing import Any,Callable
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from sistemas import gwent  # noqa: E402
SP=ROOT/"docs/scripts/validate-card-effect-smoke-v0.1.py"
spec=importlib.util.spec_from_file_location("lifecycle_smoke_helpers",SP)
smoke=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(smoke)
OUT=ROOT/"docs/card-game-lifecycle-assertions-v0.1.json"
cases=[]
def check(name,fn):
 try: cases.append({"case":name,"status":"passed",**fn()})
 except Exception as e: cases.append({"case":name,"status":"failed","error":f"{type(e).__name__}: {e}"})

def round_state(own,enemy,draw=None):
 dummy=smoke.unit("dummy")
 s=smoke.fixture(dummy,"melee")
 p1,p2=s["players"]["1"],s["players"]["2"]
 p1["board"]=own; p2["board"]=enemy
 p1["hand"]=[smoke.unit("kept_hand")]; p1["draw_pile"]=draw or []
 p2["hand"]=[smoke.unit("enemy_kept_hand")]
 p1["faction_boost_used"]=True; p2["faction_boost_used"]=True
 s["round"]=1; s["crowns"]={"1":0,"2":0}; s["rounds"]=[]
 return s,p1,p2

def test_vengeance():
 victim=smoke.unit("vengeance_victim",skill="vinganca",row="melee")
 same=smoke.unit("vengeance_same",row="melee",bonus=0)
 other=smoke.unit("vengeance_other",row="ranged",bonus=0)
 s,p,_=round_state([victim,same,other],[smoke.unit("foe",power=1)])
 event=gwent._remover_unidade(p,victim,"remocao")
 assert same["bonus"]==1 and other["bonus"]==0 and victim in p["discard"]
 return {"event":event,"same_row_bonus":same["bonus"],"other_row_bonus":other["bonus"]}

def test_vengeance_shield_blocks_hook():
 victim=smoke.unit("vengeance_shielded",skill="vinganca",row="melee",escudo=1)
 ally=smoke.unit("protected_ally",row="melee",bonus=0)
 s,p,_=round_state([victim,ally],[smoke.unit("foe",power=1)])
 event=gwent._remover_unidade(p,victim,"remocao")
 assert victim in p["board"] and ally["bonus"]==0 and victim["escudo"]==0
 return {"event":event,"victim_remains":True,"ally_bonus":0}

def test_espolios_winner_draws():
 loot=smoke.unit("loot_card")
 unit=smoke.unit("loot_unit",skill="espolios",power=8)
 s,p,_=round_state([unit],[smoke.unit("enemy",power=1)],[loot])
 before=len(p["hand"]); gwent._resolve_round(s)
 assert len(p["hand"])==before+1 and p["hand"][-1]["id"]=="loot_card"
 return {"cards_drawn":len(p["hand"])-before,"drawn":"loot_card"}

def test_espolios_loser_does_not_draw():
 loot=smoke.unit("loot_card_loser")
 unit=smoke.unit("loot_unit_loser",skill="espolios",power=1)
 s,p,_=round_state([unit],[smoke.unit("enemy_winner",power=9)],[loot])
 before=len(p["hand"]); gwent._resolve_round(s)
 assert len(p["hand"])==before and p["draw_pile"][0]["id"]=="loot_card_loser"
 return {"cards_drawn":0,"draw_pile_remaining":len(p["draw_pile"])}

def test_gloria_winner_keeps_strongest():
 weak=smoke.unit("gloria_weak",skill="gloria",power=5)
 strong=smoke.unit("gloria_strong",skill="gloria",power=9)
 other=smoke.unit("non_gloria_ally",power=4)
 s,p,_=round_state([weak,strong,other],[smoke.unit("enemy",power=1)])
 gwent._resolve_round(s)
 assert [x["id"] for x in p["board"]]==["gloria_strong"]
 assert {x["id"] for x in p["discard"]}>={"gloria_weak","non_gloria_ally"}
 return {"retained":"gloria_strong","discarded":["gloria_weak","non_gloria_ally"]}

def test_gloria_loser_discards_all():
 card=smoke.unit("gloria_loser",skill="gloria",power=1)
 s,p,_=round_state([card],[smoke.unit("enemy_winner",power=9)])
 gwent._resolve_round(s)
 assert not p["board"] and any(x["id"]=="gloria_loser" for x in p["discard"])
 return {"retained":False,"discarded":True}

def test_sobrevivente_keeps_strongest_regardless_of_result():
 card=smoke.unit("survivor_declared",skill="sobrevivente",power=9)
 s,p,_=round_state([card],[smoke.unit("enemy",power=1)])
 gwent._resolve_round(s)
 assert [x["id"] for x in p["board"]]==["survivor_declared"]
 return {"declared_effect":"survive round end","actual":"kept (hook implemented v0.1 deck-budget step)"}

for n,f in [
 ("vinganca_death_triggers_same_row_only",test_vengeance),
 ("vinganca_shield_blocks_death_trigger",test_vengeance_shield_blocks_hook),
 ("espolios_winner_draws",test_espolios_winner_draws),
 ("espolios_loser_does_not_draw",test_espolios_loser_does_not_draw),
 ("gloria_winner_keeps_only_strongest",test_gloria_winner_keeps_strongest),
 ("gloria_loser_discards_all",test_gloria_loser_discards_all),
 ("sobrevivente_keeps_strongest_round_end",test_sobrevivente_keeps_strongest_regardless_of_result),
]: check(n,f)

report={"metadata":{"document":"Lifecycle effect behavioral assertions v0.1","status":"DIAGNOSTIC ONLY; CONTROLLED ROUND-END/REMOVAL CASES","engine":"sistemas.gwent._remover_unidade and _resolve_round","baseline":"soulsbo-main(1).zip"},"counts":{"assertions":len(cases),"passed":sum(x["status"]=="passed" for x in cases),"failed":sum(x["status"]=="failed" for x in cases)},"cases":cases,"limitations":["Synthetic boards only; does not model player decision-making or full match win rate.","The suite tests the current hidden Gloria behavior as observed, not whether that behavior is approved design.","Sobrevivente's failure is evidence of a missing hook in the current source; it is not a claim that the card exists in the 137-card catalogue."]}
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report["counts"],ensure_ascii=False))
for c in cases:
 if c["status"]!="passed": print(json.dumps(c,ensure_ascii=False))
print(f"wrote {OUT}")
if report["counts"]["failed"]: raise SystemExit(1)
