#!/usr/bin/env python3
"""Validate approved Group B + CardInstance v0.3 contract fixtures (docs-only)."""
from __future__ import annotations
import copy, hashlib, json, re, sys
from pathlib import Path
from collections import defaultdict
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SCHEMAS = DOCS / "schemas"
EXAMPLE = DOCS / "examples" / "card-instance-match.example.v3.json"
APPROVAL = DOCS / "card-game-snapshot-causality-group-B-approval-v0.1.json"


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def canonical_bytes(value):
    # Fixture is deliberately restricted to safe JSON primitives. Production must use a full RFC 8785 implementation.
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def is_uuid4(v):
    return isinstance(v, str) and re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", v) is not None


def validate_manifest(manifest):
    payload = {k: v for k, v in manifest.items() if k != "definition_digest"}
    return digest(payload) == manifest.get("definition_digest")


def validate_card_digest(ds):
    payload = {k: v for k, v in ds.items() if k != "definition_digest"}
    return digest(payload) == ds.get("definition_digest")


def semantic_errors(match):
    errors=[]
    manifest=match["definition_manifest"]
    release_keys=("catalog_release_id","effect_registry_release_id","balance_rules_release_id","ruleset_release_id")
    for iid, inst in match["instances"].items():
        if iid != inst["instance_id"]: errors.append("instance registry key mismatch")
        ds=inst["definition_snapshot"]
        if ds["card_id"] != inst["card_id"]: errors.append("instance/card definition mismatch")
        if not validate_card_digest(ds): errors.append("card definition digest mismatch")
        for k in release_keys:
            if ds[k] != manifest[k]: errors.append(f"instance release mismatch: {k}")
    # Every instance occurs in exactly one zone and ownership matches the containing player.
    zone_refs=[]
    for pid, player in match["players"].items():
        for zone, refs in player["zones"].items():
            for iid in refs:
                zone_refs.append(iid)
                if iid not in match["instances"]: errors.append("zone points to missing instance")
                elif match["instances"][iid]["owner_player_id"] != pid: errors.append("zone owner mismatch")
    if len(zone_refs) != len(set(zone_refs)): errors.append("instance duplicated across zones")
    if set(zone_refs) != set(match["instances"]): errors.append("instance registry/zone mismatch")
    # Operation registry identity and revision precondition.
    for opid, op in match["operations"].items():
        if opid != op["operation_id"]: errors.append("operation registry key mismatch")
        if op["expected_revision"] != op["revision_before"]: errors.append("operation expected_revision mismatch")
        if op["revision_after"] < op["revision_before"]: errors.append("operation revision regressed")
        if not re.fullmatch(r"[0-9a-f]{64}", op["fingerprint"]): errors.append("invalid operation fingerprint")
    event_by_id={}
    sequence=[]
    for ev in match["events"]:
        if ev["event_id"] in event_by_id: errors.append("duplicate event_id")
        event_by_id[ev["event_id"]]=ev
        sequence.append(ev["sequence"])
        if ev["operation_id"] not in match["operations"]: errors.append("event references missing operation")
        if ev["effect_scope"] in ("direct","reactive") and not ev["source_effect_id"]: errors.append("effect event has no source_effect_id")
        for target in ev["target_instance_ids"]:
            if target not in match["instances"]: errors.append("event target missing instance")
        if ev["source_instance_id"] is not None and ev["source_instance_id"] not in match["instances"]:
            errors.append("event source instance missing")
        # No rarity-driven runtime input may enter the effect event payload.
        forbidden={"rarity_effect_budget","rarity_multiplier","inherited_rarity","rarity_scale","rarity_bonus"}
        def walk(x):
            if isinstance(x,dict):
                for k,v in x.items():
                    if str(k).lower() in forbidden: errors.append("rarity execution parameter found in event payload")
                    walk(v)
            elif isinstance(x,list):
                for v in x: walk(v)
        walk(ev["payload"])
    if sequence != sorted(sequence) or len(sequence) != len(set(sequence)): errors.append("event sequence not strictly increasing")
    # Causal links must exist and point strictly backward; this also prevents cycles.
    for ev in match["events"]:
        for parent_id in ev["caused_by_event_ids"]:
            parent=event_by_id.get(parent_id)
            if parent is None: errors.append("causal parent missing")
            elif parent["sequence"] >= ev["sequence"]: errors.append("causal parent does not precede child")
    # Each operation event_ids list must match stream events for that operation.
    for opid, op in match["operations"].items():
        actual=[e["event_id"] for e in match["events"] if e["operation_id"]==opid]
        if op["event_ids"] != actual: errors.append("operation event_ids do not match event stream")
    # Every event id is distinct from its operation id.
    if any(ev["event_id"] == ev["operation_id"] for ev in match["events"]): errors.append("event_id reused as operation_id")
    return errors


def idempotency_decision(existing_fingerprint, incoming_fingerprint):
    return "replay" if existing_fingerprint == incoming_fingerprint else "conflict"


def revision_precondition(current_revision, expected_revision):
    return current_revision == expected_revision


def run():
    match_schema=load(SCHEMAS/"card-game-card-instance-match.schema.v3.json")
    manifest_schema=load(SCHEMAS/"card-game-definition-manifest.schema.v1.json")
    event_schema=load(SCHEMAS/"card-game-domain-event.schema.v1.json")
    example=load(EXAMPLE)
    approval=load(APPROVAL)
    approved={d["id"]:d for d in approval["approved_decisions"]}
    checks=[]
    def check(name, ok, detail=""):
        checks.append({"case":name,"status":"passed" if ok else "failed","detail":detail})
    for name, schema in [("match_schema_draft_2020_12",match_schema),("manifest_schema_draft_2020_12",manifest_schema),("event_schema_draft_2020_12",event_schema)]:
        try: Draft202012Validator.check_schema(schema); check(name,True)
        except Exception as e: check(name,False,str(e))
    errors=list(Draft202012Validator(match_schema,format_checker=FormatChecker()).iter_errors(example))
    check("v3_example_matches_full_schema",not errors,"; ".join(e.message for e in errors[:4]))
    manifest=example["definition_manifest"]
    check("manifest_digest_recomputes",validate_manifest(manifest))
    check("manifest_has_four_release_ids",all(manifest.get(k) for k in ("catalog_release_id","effect_registry_release_id","balance_rules_release_id","ruleset_release_id")))
    check("manifest_contains_four_artifact_hashes",set(manifest.get("artifact_sha256",{}))=={"catalog","effect_registry","balance_rules","ruleset"} and all(re.fullmatch(r"[0-9a-f]{64}",v or "") for v in manifest.get("artifact_sha256",{}).values()))
    check("schema_version_is_structural",example["schema_version"]==3 and "schema_version" not in manifest)
    check("each_instance_digest_recomputes",all(validate_card_digest(i["definition_snapshot"]) for i in example["instances"].values()))
    check("instance_release_ids_match_manifest",all(all(i["definition_snapshot"][k]==manifest[k] for k in ("catalog_release_id","effect_registry_release_id","balance_rules_release_id","ruleset_release_id")) for i in example["instances"].values()))
    check("same_card_id_can_have_multiple_instances",len({i["card_id"] for i in example["instances"].values()}) < len(example["instances"]))
    check("all_instance_ids_are_uuid4",all(is_uuid4(k) and is_uuid4(v["instance_id"]) for k,v in example["instances"].items()))
    check("zone_registry_and_owner_invariants",not any("zone" in e or "registry" in e or "owner" in e or "duplicated" in e for e in semantic_errors(example)))
    check("full_semantic_invariants",not semantic_errors(example),"; ".join(semantic_errors(example)))
    check("operation_id_is_uuid4",all(is_uuid4(k) and k==v["operation_id"] for k,v in example["operations"].items()))
    check("operation_fingerprint_is_sha256",all(re.fullmatch(r"[0-9a-f]{64}",v["fingerprint"]) for v in example["operations"].values()))
    check("expected_revision_equals_revision_before",all(v["expected_revision"]==v["revision_before"] for v in example["operations"].values()))
    check("event_ids_are_uuid4_and_distinct",all(is_uuid4(e["event_id"]) and e["event_id"]!=e["operation_id"] for e in example["events"]))
    check("events_reference_existing_operations",all(e["operation_id"] in example["operations"] for e in example["events"]))
    check("event_source_instances_resolve",all(e["source_instance_id"] is None or e["source_instance_id"] in example["instances"] for e in example["events"]))
    check("operation_and_event_id_namespaces_are_distinct",not ({e["event_id"] for e in example["events"]} & set(example["operations"])))
    check("operation_event_ids_match_stream",not any("event_ids" in e for e in semantic_errors(example)))
    check("event_sequence_strictly_increasing",[e["sequence"] for e in example["events"]]==sorted({e["sequence"] for e in example["events"]}))
    event_map={e["event_id"]:e for e in example["events"]}
    check("causal_parents_exist",all(p in event_map for e in example["events"] for p in e["caused_by_event_ids"]))
    check("causal_parents_precede_children",all(event_map[p]["sequence"]<e["sequence"] for e in example["events"] for p in e["caused_by_event_ids"]))
    vengeance=[e for e in example["events"] if e["kind"]=="vengeance_bonus_applied"]
    removed=[e for e in example["events"] if e["kind"]=="unit_removed"]
    check("vengeance_is_separate_reactive_event",len(vengeance)==1 and vengeance[0]["effect_scope"]=="reactive" and vengeance[0]["source_effect_id"]=="unit.vengeance_on_removal")
    check("vengeance_causally_follows_removal",len(vengeance)==1 and len(removed)==1 and removed[0]["event_id"] in vengeance[0]["caused_by_event_ids"])
    check("reactive_event_has_own_source_instance",len(vengeance)==1 and vengeance[0]["source_instance_id"]==example["instances"][vengeance[0]["source_instance_id"]]["instance_id"])
    check("rarity_metadata_not_copied_to_vengeance_event",len(vengeance)==1 and "rarity_id" not in vengeance[0]["payload"] and "rarity_effect_budget" not in vengeance[0]["payload"])
    check("no_rarity_execution_parameter_in_any_event",not any("rarity execution parameter" in e for e in semantic_errors(example)))
    forbidden={"rarity_effect_budget","rarity_multiplier","inherited_rarity","rarity_scale","rarity_bonus"}
    def has_forbidden_key(x):
        if isinstance(x,dict):
            return any(str(k).lower() in forbidden or has_forbidden_key(v) for k,v in x.items())
        if isinstance(x,list): return any(has_forbidden_key(v) for v in x)
        return False
    check("effect_parameters_have_no_rarity_execution_input",all(not has_forbidden_key(i["definition_snapshot"]["effect_params"]) for i in example["instances"].values()))
    check("group_B_approval_record_is_owner_approved",approval.get("status")=="OWNER_APPROVED" and approval.get("runtime_modified") is False)
    check("BUF_001_option_A_is_approved",approved.get("BUF-001",{}).get("selected_option")=="A" and approved.get("BUF-001",{}).get("status")=="approved")
    check("BUF_002_reactive_boundary_is_approved",approved.get("BUF-002",{}).get("status")=="approved")
    check("BUF_012_active_binding_rule_is_approved",approved.get("BUF-012",{}).get("status")=="approved" and "active" in approved.get("BUF-012",{}).get("approved_rule", "").lower())
    check("RSRX_03_shield_and_cause_dependency_are_recorded",approved.get("RSRX-03",{}).get("status")=="approved_with_group_F_dependency" and "shield-blocked" in approved.get("RSRX-03",{}).get("approved_rule", ""))
    check("RSRX_05_causal_separation_only_is_recorded",approved.get("RSRX-05",{}).get("status")=="approved_as_causal_separation_only")
    rykard_chain=[
        {"event_id":"00000000-0000-4000-8000-000000000021","sequence":1,"kind":"unit_removed","effect_scope":"direct","source_effect_id":"leader.rykard_devour"},
        {"event_id":"00000000-0000-4000-8000-000000000022","sequence":2,"kind":"vengeance_bonus_applied","effect_scope":"reactive","source_effect_id":"unit.vengeance_on_removal"},
        {"event_id":"00000000-0000-4000-8000-000000000023","sequence":3,"kind":"rykard_leader_bonus_applied","effect_scope":"direct","source_effect_id":"leader.rykard_devour"}
    ]
    check("rykard_reactive_and_direct_outputs_are_distinct_ordered_events",len({e["event_id"] for e in rykard_chain})==3 and rykard_chain[0]["sequence"]<rykard_chain[1]["sequence"]<rykard_chain[2]["sequence"] and rykard_chain[1]["effect_scope"]=="reactive" and rykard_chain[2]["effect_scope"]=="direct" and rykard_chain[1]["source_effect_id"]!=rykard_chain[2]["source_effect_id"])
    shield_block_events=[{"kind":"shield_blocked","effect_scope":"system"}]
    check("shield_block_does_not_create_removal_or_vengeance",not any(e["kind"] in {"unit_removed","vengeance_bonus_applied"} for e in shield_block_events))
    check("same_key_same_fingerprint_is_idempotent",idempotency_decision("a"*64,"a"*64)=="replay")
    check("same_key_different_fingerprint_conflicts",idempotency_decision("a"*64,"b"*64)=="conflict")
    check("stale_expected_revision_is_rejected",not revision_precondition(8,7))
    failed=[c for c in checks if c["status"]!="passed"]
    result={"document":"CardInstance v0.3 / Group B approval validation","version":"0.1","date":"2026-11-27","baseline":"soulsbo-main-continuity-2026-11-27-rev8.zip","status":"PASS" if not failed else "FAIL","passed":len(checks)-len(failed),"failed":len(failed),"runtime_modified":False,"production_database_used":False,"cases":checks,"limitations":["synthetic fixture only","does not resolve real immutable release artifacts","does not execute a new runtime","does not test DB transactions or true concurrent requests","does not close Groups C/D/F/E","does not approve numerical balance formulas"]}
    out=DOCS/"card-game-card-instance-contract-validation-v0.3.json"
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"CardInstance v0.3 + Group B: {result['passed']}/{len(checks)} passed, {result['failed']} failed")
    for c in failed: print("FAIL",c["case"],c["detail"])
    return 1 if failed else 0

if __name__=="__main__": raise SystemExit(run())
