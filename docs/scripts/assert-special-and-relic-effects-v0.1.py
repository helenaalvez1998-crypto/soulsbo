#!/usr/bin/env python3
"""Behavioral assertions for the special-card and relic handlers.

Uses real aplicar_jogada() in synthetic match states. Not a production integration test.
"""
from __future__ import annotations
import importlib.util,json,sys
from pathlib import Path
from typing import Any,Callable
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from sistemas import gwent  # noqa: E402
SP=ROOT/"docs/scripts/validate-card-effect-smoke-v0.1.py"
spec=importlib.util.spec_from_file_location("special_effect_smoke_helpers",SP)
smoke=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(smoke)
OUT=ROOT/"docs/card-game-special-relic-assertions-v0.1.json"
cases=[]
def check(name,fn):
 try: cases.append({"case":name,"status":"passed",**fn()})
 except Exception as e: cases.append({"case":name,"status":"failed","error":f"{type(e).__name__}: {e}"})

def play_special(skill, *, row="melee", configure=None, target_id=None):
 card=smoke.unit(f"special_{skill}",skill=skill,special=True,power=0,rarity="Comum")
 s=smoke.fixture(card,row)
 p,o=s["players"]["1"],s["players"]["2"]
 p["hand"]=[card,smoke.unit(f"reserve_{skill}")]
 p["faction"]="Lua Negra"; p["faction_boost_used"]=True; p["synergy_used"]={}
 if configure: configure(s,p,o)
 result=gwent.aplicar_jogada(s,1,card_id=card["id"],action="play",row=row,target_id=target_id)
 assert "error" not in result, result
 st=result["state"]
 assert any(x["id"]==card["id"] for x in st["players"]["1"]["discard"])
 return st,st["players"]["1"],st["players"]["2"]

def play_relic(relic_id, *, row="melee", mode=None, configure=None, target_id=None):
 # The actual relic action loads the equipped relic into a temporary hand slot
 # and resolves it through the standard special-card branch.
 dummy=smoke.unit("relic_fixture")
 s=smoke.fixture(dummy,row)
 p,o=s["players"]["1"],s["players"]["2"]
 p["hand"]=[smoke.unit("reserve_relic")]
 p["equipped_relic_id"]=relic_id; p["relic_card_owned"]=True; p["relic_used"]=False
 p["faction_boost_used"]=True
 if configure: configure(s,p,o)
 result=gwent.aplicar_jogada(s,1,action="relic",row=row,target_id=(mode or target_id))
 assert "error" not in result,result
 st=result["state"]
 return st,st["players"]["1"],st["players"]["2"]

def find(side,cid): return next((x for x in side.get("board",[]) if x.get("id")==cid),None)

# Additional special-card handlers not covered by the original 13 assertion pack.
def test_clima():
 st,_,_=play_special("gwent_clima",row="ranged")
 assert st["weather"]["ranged"]==1
 return {"skill":"gwent_clima","weather_ranged":1}

def test_nevoa():
 def cfg(s,p,o): o["board"]=[smoke.unit("rot_a",row="melee"),smoke.unit("rot_b",row="melee")]
 _,_,o=play_special("gwent_nevoa",configure=cfg)
 assert [find(o,x)["podrida"] for x in ("rot_a","rot_b")] == [1,1]
 return {"skill":"gwent_nevoa","enemy_marks":[1,1]}

def test_geada():
 def cfg(s,p,o): o["board"]=[smoke.unit("frost_a",row="melee"),smoke.unit("frost_b",row="siege")]
 _,_,o=play_special("gwent_geada",configure=cfg)
 assert [find(o,x)["geada"] for x in ("frost_a","frost_b")] == [1,1]
 return {"skill":"gwent_geada","all_enemy_marks":[1,1]}

def test_chuva():
 def cfg(s,p,o): o["board"]=[smoke.unit("rain_a",row="siege",sangramento=1,bonus=3),smoke.unit("rain_b",row="siege",sangramento=0)]
 _,_,o=play_special("gwent_chuva",configure=cfg)
 assert find(o,"rain_a")["sangramento"]==0 and find(o,"rain_a")["bonus"]==1
 assert find(o,"rain_b")["sangramento"]==1
 return {"skill":"gwent_chuva","second_mark_bonus_after":1,"new_mark":1}

def test_medico():
 target=smoke.unit("doctor_target",power=4)
 def cfg(s,p,o): p["discard"]=[target]
 st,p,_=play_special("gwent_medico",configure=cfg,target_id="doctor_target")
 assert any(x["id"]=="doctor_target" for x in p["hand"]) and not any(x["id"]=="doctor_target" for x in p["discard"])
 return {"skill":"gwent_medico","returned_to_hand":"doctor_target"}

def test_vinculo():
 def cfg(s,p,o): p["board"]=[smoke.unit("vow_a",row="melee"),smoke.unit("vow_b",row="melee")]
 _,p,_=play_special("gwent_vinculo",configure=cfg,row="melee")
 assert [find(p,x)["bonus"] for x in ("vow_a","vow_b")] == [2,2]
 return {"skill":"gwent_vinculo","ally_bonuses":[2,2]}

def test_muralha():
 def cfg(s,p,o): p["board"]=[smoke.unit("wall_a",row="ranged"),smoke.unit("wall_b",row="ranged"),smoke.unit("wall_other",row="melee")]
 _,p,_=play_special("gwent_muralha",configure=cfg,row="ranged")
 assert [find(p,x)["bonus"] for x in ("wall_a","wall_b","wall_other")] == [1,1,0]
 return {"skill":"gwent_muralha","target_bonuses":[1,1,0]}

def test_geada_cariana():
 def cfg(s,p,o): o["board"]=[smoke.unit("carian_a",row="melee"),smoke.unit("carian_b",row="melee",geada=2)]
 _,_,o=play_special("gwent_geada_cariana",configure=cfg,row="melee")
 assert [find(o,x)["geada"] for x in ("carian_a","carian_b")] == [1,2]
 return {"skill":"gwent_geada_cariana","marks_after":[1,2]}

def test_podrida():
 def cfg(s,p,o): o["board"]=[smoke.unit("rot_old",row="melee",podrida=1,bonus=3),smoke.unit("rot_fresh",row="melee",podrida=0,bonus=2)]
 _,_,o=play_special("gwent_podrida",configure=cfg,row="melee")
 assert find(o,"rot_old")["podrida"]==2 and find(o,"rot_old")["bonus"]==2
 assert find(o,"rot_fresh")["podrida"]==1 and find(o,"rot_fresh")["bonus"]==2
 return {"skill":"gwent_podrida","old_mark_target":[2,2],"fresh_mark_target":[1,2]}

def test_loucura():
 def cfg(s,p,o): o["board"]=[smoke.unit("mad_old",row="melee",loucura=1,bonus=3),smoke.unit("mad_new",row="melee",loucura=0,bonus=2)]
 _,_,o=play_special("gwent_loucura",configure=cfg,row="melee")
 assert find(o,"mad_old")["loucura"]==2 and find(o,"mad_old")["bonus"]==0
 assert find(o,"mad_new")["loucura"]==1 and find(o,"mad_new")["bonus"]==2
 return {"skill":"gwent_loucura","old_mark_target":[2,0],"fresh_mark_target":[1,2]}

def test_chama():
 def cfg(s,p,o): p["board"]=[smoke.unit("flame_frost",row="melee",geada=2,bonus=0),smoke.unit("flame_clear",row="melee",geada=0,bonus=0)]
 _,p,_=play_special("gwent_chama",configure=cfg)
 assert find(p,"flame_frost")["geada"]==0 and find(p,"flame_frost")["bonus"]==1
 assert find(p,"flame_clear")["bonus"]==0
 return {"skill":"gwent_chama","purified_unit_bonus":1,"untouched_unit_bonus":0}

for n,f in [
 ("special_clima_sets_weather",test_clima),("special_nevoa_marks_row",test_nevoa),
 ("special_geada_marks_all_enemies",test_geada),("special_chuva_second_mark_bleeds",test_chuva),
 ("special_medico_returns_discard_to_hand",test_medico),("special_vinculo_buffs_two_allies",test_vinculo),
 ("special_muralha_buffs_selected_row",test_muralha),("special_geada_cariana_caps_existing_marks",test_geada_cariana),
 ("special_podrida_second_mark_corrosion",test_podrida),("special_loucura_second_mark_removes_positive_bonus",test_loucura),
 ("special_chama_purifies_frost_and_buffs",test_chama)
]: check(n,f)

# All six relics are exercised through the public `action="relic"` path.
def test_godrick():
 def cfg(s,p,o): p["board"]=[smoke.unit("godrick_a"),smoke.unit("godrick_b",row="ranged")]
 _,p,_=play_relic("reliquia_grande_runa_godrick",configure=cfg)
 assert [x["bonus"] for x in p["board"]]==[1,1]
 return {"relic":"reliquia_grande_runa_godrick","ally_bonuses":[1,1]}

def test_renala():
 def cfg(s,p,o): p["board"]=[smoke.unit("renala_a",geada=1),smoke.unit("renala_b",podrida=2,bonus=0)]
 _,p,_=play_relic("reliquia_runa_nao_nascidos",configure=cfg)
 assert all(x["geada"]==0 and x["podrida"]==0 and x["bonus"]==1 for x in p["board"])
 return {"relic":"reliquia_runa_nao_nascidos","purified":2}

def test_morte():
 def cfg(s,p,o): o["board"]=[smoke.unit("death_melee",row="melee",bonus=3),smoke.unit("death_siege",row="siege",bonus=1),smoke.unit("death_other",row="melee",bonus=2)]
 _,_,o=play_relic("reliquia_runa_morte",configure=cfg)
 assert find(o,"death_melee")["bonus"]==1 and find(o,"death_other")["bonus"]==2 and find(o,"death_siege")["bonus"]==0
 return {"relic":"reliquia_runa_morte","row_targets_after":[1,0],"non_selected_bonus":2}

def test_noite_chama():
 def cfg(s,p,o): o["board"]=[smoke.unit("night_a",row="melee"),smoke.unit("night_b",row="melee")]
 _,_,o=play_relic("reliquia_noite_chama",configure=cfg,row="melee",mode="noite")
 assert [find(o,x)["geada"] for x in ("night_a","night_b")] == [1,1]
 return {"relic":"reliquia_noite_chama","mode":"night","enemy_marks":[1,1]}

def test_lamina_negra():
 def cfg(s,p,o): o["board"]=[smoke.unit("black_blade_target",row="ranged",bonus=4)]
 st,p,o=play_relic("reliquia_lamina_negra",configure=cfg,row="ranged",target_id="black_blade_target")
 target=find(o,"black_blade_target")
 assert target["bonus"]==1 and p["relic_used"] is True
 return {"relic":"reliquia_lamina_negra","target_bonus_after":1,"relic_consumed":True}

def test_algemas():
 def cfg(s,p,o): o["board"]=[smoke.unit("chains_positive",row="siege",bonus=4),smoke.unit("chains_negative",row="siege",bonus=-1)]
 _,_,o=play_relic("reliquia_algemas_margit",configure=cfg,row="siege",target_id="chains_positive")
 assert find(o,"chains_positive")["bonus"]==0 and find(o,"chains_negative")["bonus"]==-1
 return {"relic":"reliquia_algemas_margit","positive_zeroed":True,"negative_preserved":True}

for n,f in [("relic_godrick_allies_plus1",test_godrick),("relic_renala_purifies",test_renala),("relic_morte_reduces_best_bonus_per_row",test_morte),("relic_night_mode_applies_frost",test_noite_chama),("relic_black_blade_targets_and_consumes",test_lamina_negra),("relic_margit_cuffs_zeroes_positive_bonus",test_algemas)]: check(n,f)

# Negative/blocked cases for critical boundaries.
def test_relic_black_blade_shield_not_consumed():
 def cfg(s,p,o): o["board"]=[smoke.unit("black_blade_shield",row="ranged",bonus=4,escudo=1)]
 _,p,o=play_relic("reliquia_lamina_negra",configure=cfg,row="ranged",target_id="black_blade_shield")
 t=find(o,"black_blade_shield")
 assert t["escudo"]==0 and t["bonus"]==4 and p["relic_used"] is False
 return {"relic":"reliquia_lamina_negra","shield_consumed":True,"relic_still_available":True}
check("negative_relic_black_blade_shield_blocks_without_consuming_relic",test_relic_black_blade_shield_not_consumed)

report={"metadata":{"document":"Special and relic effect behavioral assertions v0.1","status":"DIAGNOSTIC ONLY; SELECTED SPECIAL/RELIC BRANCHES","baseline":"soulsbo-main(1).zip","engine":"sistemas.gwent.aplicar_jogada; public relic action path tested"},"counts":{"assertions":len(cases),"passed":sum(x["status"]=="passed" for x in cases),"failed":sum(x["status"]=="failed" for x in cases)},"cases":cases,"limitations":["These tests cover the additional special handlers and all six relics in selected Common/specific states; rarity scaling is not tested.","Multiple-target caps, shield/target edge cases for every special, and full UI target-option parity remain open.","Leader abilities are not included in this suite and need their own action tests.","Synthetic boards do not estimate the frequency or competitive value of the effects.","No persistent database, API, site, Discord, R2, or production match is involved."]}
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report["counts"],ensure_ascii=False))
for c in cases:
 if c["status"]!="passed": print(json.dumps(c,ensure_ascii=False))
print(f"wrote {OUT}")
if report["counts"]["failed"]: raise SystemExit(1)
