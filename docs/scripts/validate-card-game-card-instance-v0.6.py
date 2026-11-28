#!/usr/bin/env python3
"""Validate CardInstance v0.6 and approved Group F semantics; no runtime integration."""
from __future__ import annotations
import json, unittest
from pathlib import Path
import jsonschema
ROOT=Path(__file__).resolve().parents[2]
DOCS=ROOT/'docs'; SCHEMAS=DOCS/'schemas'; EXAMPLES=DOCS/'examples'
def load(p): return json.loads(p.read_text(encoding='utf-8'))
class CardInstanceV06Validation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema=load(SCHEMAS/'card-game-card-instance-match.schema.v6.json')
        cls.event_schema=load(SCHEMAS/'card-game-domain-event.schema.v2.json')
        cls.cause_schema=load(SCHEMAS/'card-game-removal-cause.schema.v1.json')
        cls.example=load(EXAMPLES/'card-instance-match.example.v6.json')
        cls.fapproval=load(DOCS/'card-game-removal-causes-group-F-approval-v0.1.json')
        cls.fregister=load(DOCS/'card-game-removal-causes-group-F-decisions-v0.1.json')
        cls.e_decisions=load(DOCS/'card-game-persistence-group-E-decisions-v0.1.json')
    def test_match_schema_is_valid(self): jsonschema.Draft202012Validator.check_schema(self.schema)
    def test_v6_example_matches_schema(self): jsonschema.Draft202012Validator(self.schema).validate(self.example)
    def test_root_version_is_six(self): self.assertEqual(6,self.schema['properties']['schema_version']['const'])
    def test_instance_version_is_six(self): self.assertEqual(6,self.schema['$defs']['card_instance']['properties']['schema_version']['const'])
    def test_group_f_approval_exists(self): self.assertEqual('OWNER_APPROVED',self.fapproval['status'])
    def test_f_register_has_five_approved_decisions(self):
        self.assertEqual(5,len(self.fregister['decisions']))
        self.assertTrue(all(x['status']=='OWNER_APPROVED' for x in self.fregister['decisions']))
    def test_group_e_remains_pending(self): self.assertEqual('PENDING_OWNER_APPROVAL',self.e_decisions['status'])
    def test_removal_causes_are_closed(self):
        self.assertEqual({'normal_removal','execution','sacrifice'},set(self.schema['$defs']['removal_cause_id']['enum']))
    def test_round_archive_is_not_a_removal_cause(self): self.assertNotIn('round_archive',self.schema['$defs']['removal_cause_id']['enum'])
    def test_vengeance_instance_uses_canonical_id(self):
        self.assertEqual('effect.vengeance_on_removal',self.example['instances']['00000000-0000-4000-8000-000000000004']['definition_snapshot']['effect_id'])
    def test_vengeance_event_uses_canonical_id(self):
        e=next(x for x in self.example['events'] if x['kind']=='vengeance_bonus_applied')
        self.assertEqual('effect.vengeance_on_removal',e['source_effect_id'])
    def test_unit_removed_event_has_canonical_cause_payload(self):
        e=next(x for x in self.example['events'] if x['kind']=='unit_removed')
        self.assertEqual('normal_removal',e['payload']['cause_id'])
        self.assertEqual('board',e['payload']['from_zone'])
        self.assertEqual('discard',e['payload']['to_zone'])
    def test_invalid_removal_cause_is_rejected(self):
        x=json.loads(json.dumps(self.example)); e=next(x for x in x['events'] if x['kind']=='unit_removed'); e['payload']['cause_id']='round_archive'
        with self.assertRaises(jsonschema.ValidationError): jsonschema.Draft202012Validator(self.schema).validate(x)
    def test_sacrifice_cannot_be_a_shield_blocked_cause(self):
        e={'event_id':'00000000-0000-4000-8000-000000000091','operation_id':'00000000-0000-4000-8000-000000000010','sequence':9,'caused_by_event_ids':[],'kind':'unit_removal_blocked','effect_scope':'direct','source_effect_id':'special.remove_units','source_instance_id':'00000000-0000-4000-8000-000000000005','target_instance_ids':['00000000-0000-4000-8000-000000000004'],'payload':{'cause_id':'sacrifice','from_zone':'board','to_zone':'board','affected_player_id':'2002','protection_grant_id':'00000000-0000-4000-8000-000000000033'}}
        with self.assertRaises(jsonschema.ValidationError): jsonschema.Draft202012Validator(self.schema['$defs']['domain_event']).validate(e)
    def test_player_counters_are_nonnegative_projections(self):
        for p in self.example['players'].values():
            self.assertGreaterEqual(p['counters']['board_removal_count'],0)
            self.assertGreaterEqual(p['counters']['sacrifice_count'],0)
    def test_legacy_baixas_projection_is_sum(self):
        p=self.example['players']['2002']['counters']
        self.assertEqual(1,p['board_removal_count']+p['sacrifice_count'])
    def test_expected_revision_is_still_bound_to_result(self):
        for k,op in self.example['operations'].items():
            self.assertEqual(k,op['operation_id']); self.assertEqual(k,op['result']['operation_id'])
            self.assertEqual(op['expected_revision'],op['result']['revision_before'])
    def test_operation_event_references_are_valid(self):
        ev={x['event_id'] for x in self.example['events']}; ops=set(self.example['operations'])
        for op in self.example['operations'].values(): self.assertTrue(set(op['result']['event_ids']).issubset(ev))
        self.assertTrue(all(x['operation_id'] in ops for x in self.example['events']))
    def test_player_counter_semantics_are_documented(self):
        text=(DOCS/'card-game-card-instance-contract-v0.6.md').read_text(encoding='utf-8')
        self.assertIn('board_removal_count',text); self.assertIn('sacrifice_count',text); self.assertIn('nunca semântica de mortes',text)
    def test_rykard_and_vengeance_sources_remain_independent(self):
        text=(DOCS/'card-game-card-instance-contract-v0.6.md').read_text(encoding='utf-8')
        self.assertIn('leader.rykard_devour',text); self.assertIn('effect.vengeance_on_removal',text); self.assertIn('não ficam congelados',text)
    def test_group_e_blocks_persistence_integration(self):
        text=(DOCS/'card-game-card-instance-contract-v0.6.md').read_text(encoding='utf-8')
        self.assertIn('Grupo E permanece aberto',text); self.assertIn('Não executar migrador',text)
    def test_event_schema_v2_id(self): self.assertTrue(self.schema['$defs']['domain_event']['$id'].endswith('card-game-domain-event.v2.json'))
    def test_standalone_domain_event_schema_is_valid(self): jsonschema.Draft202012Validator.check_schema(self.event_schema)
    def test_standalone_removal_cause_schema_is_valid_and_closed(self):
        jsonschema.Draft202012Validator.check_schema(self.cause_schema)
        v=jsonschema.Draft202012Validator(self.cause_schema)
        for cause in ('normal_removal','execution','sacrifice'): v.validate(cause)
        with self.assertRaises(jsonschema.ValidationError): v.validate('round_archive')
if __name__=='__main__': unittest.main(verbosity=2)
