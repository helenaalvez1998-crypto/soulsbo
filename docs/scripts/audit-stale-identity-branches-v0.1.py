#!/usr/bin/env python3
"""Classify identity resolver branches that are not reachable from active cards.

This is a static inventory and recommendation register, not an auto-delete tool.
"""
from __future__ import annotations
import ast, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from sistemas import cartas,gwent  # noqa: E402
OUT=ROOT/"docs"/"card-game-stale-identity-disposition-v0.1.json"
SOURCE=ROOT/"sistemas"/"gwent.py"
tree=ast.parse(SOURCE.read_text(encoding="utf-8"))

def get_assign(name):
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets):
            return ast.literal_eval(n.value)
    raise KeyError(name)

def find_fn(name):
    return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)

def compared_values(fn, var):
    out=set()
    for n in ast.walk(fn):
        if isinstance(n,ast.Compare):
            names={x.id for x in ast.walk(n.left) if isinstance(x,ast.Name)}
            if var in names:
                for c in n.comparators:
                    out.update(x.value for x in ast.walk(c) if isinstance(x,ast.Constant) and isinstance(x.value,str))
    return out

source_map=get_assign("CARD_IDENTITY_ABILITIES")
identity_fn=find_fn("_aplicar_habilidade_identidade")
branch_effects=compared_values(identity_fn,"effect")
active_effects={v["effect"] for v in gwent.CARD_IDENTITY_ABILITIES.values()}
stale=sorted(branch_effects-active_effects)

# Card IDs whose previous identity definitions are still present in the source
# dictionary but are removed at runtime by CARTAS_SEM_EFEITO_IDS.
inactive_identity=[]
for cid, data in source_map.items():
    if cid in gwent.CARD_IDENTITY_ABILITIES:
        continue
    model=cartas.get_carta(cid)
    inactive_identity.append({
        "card_id":cid,
        "card_name":model.nome if model else None,
        "effect_id":data["effect"],
        "effect_name":data["name"],
        "description":data["text"],
        "runtime_habilidade":getattr(model,"habilidade",None) if model else None,
        "is_in_v18_no_effect_set":cid in cartas.CARTAS_SEM_EFEITO_IDS,
        "synergy_tags":sorted(gwent.CARD_SYNERGY_TAGS.get(cid,set())),
        "strict_pure_after_v18":bool(model and not getattr(model,"habilidade","") and not gwent.CARD_SYNERGY_TAGS.get(cid,set())),
        "recommendation":"ARCHIVE_THEN_REMOVE_HANDLER_IF_CARD_REMAINS_PURE; otherwise explicitly re-enable through canonical schema",
        "recommendation_reason":"V18 filters this card out of CARD_IDENTITY_ABILITIES and clears its generic skill; retaining the branch creates unreachable resolver code.",
    })

v75_card_map={
 "v75_crucible_guard":"gwent_v75_ordem_guardiao_crisol",
 "v75_golden_standard":"gwent_v75_ordem_arauto_estandarte",
 "v75_blood_feast":"gwent_v75_veu_devota_hemorragia",
 "v75_blood_pursuit":"gwent_v75_veu_cacador_sangue",
 "v75_lunar_cartography":"gwent_v75_lua_cartografo_lunar",
 "v75_moon_ward":"gwent_v75_lua_guardia",
}
# Four effect branches are not tied to any entry in the original identity-card
# map, but their names may appear on current/legacy Carta.habilidade fields.
legacy_unmapped={
 "devoto":{"recommendation":"REWRITE_AS_CANONICAL_EFFECT_OR_CLEAR_CARD_FIELDS","reason":"Effect code exists only inside identity resolver; no active card-ID mapping dispatches it.","meaning":"+1 when at least two allied units of the same faction are already on board."},
 "legado":{"recommendation":"REWRITE_AS_CANONICAL_EFFECT_OR_CLEAR_CARD_FIELDS","reason":"Effect code exists only inside identity resolver; no active card-ID mapping dispatches it. It also relies on legado_vitoria being set during round resolution.","meaning":"+2 if the player won the immediately previous round."},
 "escolha_ritmo":{"recommendation":"REMOVE_OR_REDESIGN; CURRENT_BRANCH_DOES_NOT_IMPLEMENT_THE_TEXTUAL_CHOICE_OR_RETENTION","reason":"No active identity mapping or HABILIDADES entry points to this branch; its implementation merely grants +1 and does not model the described row choice/retention.","meaning":"Current branch grants +1 unconditionally; comment describes a row choice and persistence that are not implemented here."},
 "sinergia_faccao":{"recommendation":"REWRITE_AS_CANONICAL_EFFECT_OR_CLEAR_CARD_FIELDS","reason":"Effect code exists only inside identity resolver; no active card-ID mapping dispatches it.","meaning":"+1 for each allied unit of the same faction."},
}
for effect in legacy_unmapped:
    refs=[]
    for cid, model in cartas.CARTAS_POR_ID.items():
        if getattr(model,"habilidade","")==effect:
            refs.append({"card_id":cid,"card_name":model.nome,"faction":model.faccao,"rarity":model.raridade})
    legacy_unmapped[effect]["current_card_field_references"]=refs

v75=[]
for effect,cid in v75_card_map.items():
    model=cartas.get_carta(cid)
    v75.append({
      "effect_id":effect,
      "associated_current_card_id":cid,
      "card_name":model.nome if model else None,
      "current_habilidade":getattr(model,"habilidade",None) if model else None,
      "current_description":getattr(model,"descricao",None) if model else None,
      "synergy_tags":sorted(gwent.CARD_SYNERGY_TAGS.get(cid,set())),
      "recommendation":"REMOVE_STALE_IDENTITY_BRANCH_AFTER_ARCHIVING",
      "recommendation_reason":"Current card declares no individual skill and the resolver branch has no active CARD_IDENTITY_ABILITIES mapping.",
    })

extra_branch_ids=sorted(set(stale)-set(x["effect_id"] for x in inactive_identity)-set(v75_card_map))
assert set(extra_branch_ids)==set(legacy_unmapped), (extra_branch_ids, set(legacy_unmapped))

hidden_gloria=[]
for cid,model in cartas.CARTAS_POR_ID.items():
    if getattr(model,"habilidade","")=="gloria":
        hidden_gloria.append({"card_id":cid,"card_name":model.nome,"faction":model.faccao,"rarity":model.raridade,"hook":"_resolve_round()"})

report={
 "metadata":{"document":"Stale identity branch disposition audit v0.1","status":"STATIC SOURCE AUDIT; RECOMMENDATIONS NOT YET APPLIED","baseline":"soulsbo-main(1).zip","source_files":["sistemas/gwent.py","sistemas/cartas.py"]},
 "counts":{"identity_resolver_effect_branches":len(branch_effects),"active_identity_effect_ids":len(active_effects),"stale_branches":len(stale),"v18_filtered_identity_cards":len(inactive_identity),"unmapped_legacy_field_effects":len(legacy_unmapped),"stale_v75_effects":len(v75),"hidden_gloria_cards":len(hidden_gloria)},
 "v18_filtered_identity_candidates":inactive_identity,
 "unmapped_legacy_field_effect_candidates":legacy_unmapped,
 "stale_v75_effect_candidates":v75,
 "separate_lifecycle_findings":{
   "gloria":{"status":"EXECUTES_AT_ROUND_END_BUT_ABSENT_FROM_HABILIDADES","cards":hidden_gloria,"recommendation":"PROMOTE_TO_CANONICAL_LIFECYCLE_EFFECT_OR_REMOVE_FIELDS_AND_HOOK_AFTER_DESIGN_DECISION"},
   "sobrevivente":{"status":"DECLARED_IN_HABILIDADES_BUT_NO_HANDLER_REFERENCE_FOUND","recommendation":"IMPLEMENT_EXPLICIT_ROUND_END_RULE_OR_REMOVE_CATALOG_ENTRY"}
 },
 "non_destructive_policy":"No branch or card field is deleted by this audit. Archive the complete inventory and obtain the final keep/merge/redesign/remove decision before runtime cleanup."
}
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report["counts"],ensure_ascii=False,indent=2))
print("unmapped field references:")
for k,v in legacy_unmapped.items(): print(k, [x["card_id"] for x in v["current_card_field_references"]])
print(f"wrote {OUT}")
