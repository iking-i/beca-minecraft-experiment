"""Capability/knowledge boundary and full A -> RPC -> body -> frame provenance."""
from contextlib import closing
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest

from individual.action_space import DEFINITIONS, bind_parameters
from individual.actions import select_action
from individual.bridge import MinecraftBridge, ROOT
from individual.core import ACore
from individual.inspect import verify
from individual.internal_state import InternalState
from individual.observation import FrameEncoder
from individual.policies import PolicyRegistry
from individual.policy_audit import audit_policies


class ActionSpaceTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / '.test-tmp'
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'body.db'
        self.bridge = MinecraftBridge(ROOT / 'minecraft/config.json', adapter=ROOT / 'tests/fixtures/capability_body.js')
        self.core = ACore(self.db, self.bridge, initialize_lifetime=True)
        self.addCleanup(self.core.shutdown)
        self.core.start()
        deadline = time.monotonic() + 10
        while not self.bridge.call('status')['connected']:
            if time.monotonic() > deadline:
                self.fail('Body fixture did not spawn')
            time.sleep(0.01)
        self.refresh()

    def refresh(self):
        self.core.accept_observation(self.bridge.call('observe'))

    def events(self, kind):
        with closing(sqlite3.connect(self.db)) as connection:
            return [json.loads(row[0]) for row in connection.execute('SELECT payload FROM events WHERE event_type=? ORDER BY rowid', (kind,))]

    def run_action(self, name, parameters=None, success=True):
        if name in ('DROP_ITEM','MOVE_INVENTORY_ITEM','EQUIP_FROM_SLOT','MOVE_CONTAINER_ITEM','TAKE_CONTAINER_ITEM','PUT_CONTAINER_ITEM','MOVE_ITEM_TO_CRAFT_SLOT','TAKE_CRAFT_RESULT'):
            p = parameters
            body = self.core.state.observation_frame['nearby_data']['body']
            win = body.get('container') or body['inventory_screen']
            def click(slot,button=0,mode=0,ok=True):
                return self.run_action('SLOT_INPUT', {'container_id':win['container_id'],'slot':slot,'mode':mode,'button':button},success=ok)
            if name == 'DROP_ITEM':
                for _ in range(p['amount']): final=click(p['slot'],mode=4)
                return final
            if name == 'EQUIP_FROM_SLOT':
                dest = [36+body['selected_hotbar_slot'],5,6,7,8,45][p['equipment_slot']]
                click(p['source_slot']); return click(dest)
            source = win['result_slot'] if name == 'TAKE_CRAFT_RESULT' else p['source_slot']
            if not success: return click(source,ok=False)
            click(source)
            if name == 'TAKE_CRAFT_RESULT': return click(p['target_slot'])
            for _ in range(p['amount']): final=click(p['target_slot'],button=1)
            cursor = self.core.state.observation_frame['nearby_data']['body']['inventory_screen']['cursor']
            if body.get('container'): cursor=self.core.state.observation_frame['nearby_data']['body']['container']['cursor']
            if cursor['count']: final=click(source)
            return final
        code = next(c for c, definition in DEFINITIONS.items() if definition['action_id'] == name)
        self.assertEqual(self.core.execute_discrete_action(code, parameters), success)
        final = self.core.state.latest_action
        self.assertEqual(final['method'], 'perform')
        self.assertEqual(final['args']['code'], code)
        self.refresh()
        self.assertIn(final['action_id'], self.core.state.observation_frame['delta']['after_action_ids'])
        return final

    def new_fixture_session(self, window, die=False):
        self.core.shutdown()
        config = Path(self.temp.name) / 'fixture.json'
        config.write_text(json.dumps({'fixture_window': window, 'fixture_die_after_observation': die}), encoding='utf-8')
        self.bridge = MinecraftBridge(config, adapter=ROOT / 'tests/fixtures/capability_body.js')
        self.core = ACore(self.db, self.bridge)
        self.addCleanup(self.core.shutdown)
        self.core.start()
        deadline = time.monotonic() + 10
        while not self.bridge.call('status')['connected']:
            if time.monotonic() > deadline:
                self.fail('Body fixture did not spawn')
            time.sleep(0.01)
        self.refresh()

    def test_preserved_identity_and_immutable_capability_provisioning(self):
        before = self.core.state
        self.assertEqual(len(before.internal_state['body_capabilities']['actions']), len(DEFINITIONS))
        event = self.events('BODY_CAPABILITIES_PROVISIONED')[0]
        self.assertEqual(event['source'], 'BODY_CAPABILITY')
        self.assertFalse(event['learned'])
        self.run_action('SWING_ARM')
        self.assertEqual(len(self.events('BODY_CAPABILITIES_PROVISIONED')), 1)
        self.assertEqual(self.core.state.individual_id, before.individual_id)
        self.assertGreater(self.core.state.state_version, before.state_version)
        self.assertTrue(self.core.state.continuity_required)
        self.assertTrue(verify(self.db)['valid_state_chain'])

    def test_formal_sampler_and_parameter_binding_have_external_authorship_across_rpc(self):
        self.core.execute_discrete_action()
        action = self.core.state.latest_action
        self.assertEqual(action['initiator'], 'external_fixed_policy')
        selection = action['provenance']['selection']
        self.assertEqual(selection['source'], 'EXTERNAL_FIXED_POLICY')
        self.assertEqual(selection['parameter_binding']['source']['category'], 'INITIAL_EXTERNAL_POLICY')
        self.assertEqual(action['provenance']['decision_authorship']['aggregate_source'], 'EXTERNAL_FIXED_POLICY')
        proof = audit_policies(self.db)
        self.assertTrue(proof['boundary_checks_passed'])
        self.assertNotIn('INTERNAL_VARIABLE_STRUCTURE', proof['action_decision_authors'])
        self.assertFalse(proof['autonomous_policy_formation_proven'])

    def test_explicit_capability_test_remains_test_authorship(self):
        final = self.run_action('SWING_ARM')
        self.assertEqual(final['initiator'], 'capability_test')
        self.assertEqual(final['provenance']['decision_authorship']['aggregate_source'], 'TEST_ONLY')

    def test_existing_lifetime_schema_gets_an_append_only_upgrade_without_resetting_history(self):
        marker = self.core.state.individual_id
        old = deepcopy(self.core.state.internal_state)
        old.pop('body_capabilities')
        old['policy_registry'].pop('action.parameter_binding')
        old['policy_migration_status'].pop('action.parameter_binding')
        old['parameter_sources'] = {k: v for k, v in old['parameter_sources'].items() if not k.startswith('action.parameter_binding.')}
        old['exploration_state']['attempts']['legacy:1'] = 7
        self.core._transition('TEST_LEGACY_SCHEMA', {'category': 'TEST_ONLY'}, internal_state=old)
        previous_version = self.core.state.state_version
        units = set(old['units'])
        self.refresh()
        now = self.core.state
        self.assertEqual(now.individual_id, marker)
        self.assertEqual(now.state_version, previous_version + 1)
        self.assertEqual(now.internal_state['exploration_state']['attempts']['legacy:1'], 7)
        self.assertTrue(units <= set(now.internal_state['units']))
        self.assertEqual(now.internal_state['policy_registry']['action.parameter_binding']['created_at'], f'A{now.state_version}')
        with closing(sqlite3.connect(self.db)) as connection:
            saved = json.loads(connection.execute('SELECT snapshot FROM states WHERE state_version=?', (previous_version,)).fetchone()[0])
            self.assertNotIn('body_capabilities', saved['internal_state'])
        self.assertTrue(verify(self.db)['valid_state_chain'])

    def test_place_dig_and_world_slot_changes_reach_the_recursive_engine(self):
        frame = self.core.state.observation_frame
        ref = frame['nearby_data']['blocks'][0]['target_ref']
        prior = self.core.state.state_version
        final = self.run_action('PLACE_BLOCK', {'inventory_slot': 36, 'reference_block': ref, 'face': 1})
        self.assertEqual(final['provenance']['internal_state_before_version'], prior)
        self.assertEqual(len(final['result']['after']['blocks']), 2)
        result_frame = self.core.state.observation_frame
        self.assertTrue(result_frame['delta']['changes'])
        experience = next(e for e in self.events('EXPERIENCE_FORMED') if final['action_id'] in e['action_ids'])
        self.assertEqual(experience['action_parameters'], [{'inventory_slot': 36, 'reference_block': ref, 'face': 1}])
        self.assertEqual(experience['change_id'], result_frame['delta']['change_id'])
        self.assertTrue(self.events('RECURSIVE_PROCESS_CREATED'))
        self.run_action('DIG', {'block_ref': ref})
        self.assertTrue(self.events('ACTION_EXECUTED'))

    def test_all_basic_item_and_inventory_operations_cross_the_rpc_boundary(self):
        self.run_action('SELECT_HOTBAR_SLOT', {'slot': 0})
        self.run_action('USE_HELD_ITEM', {'duration_ms': 1})
        self.run_action('MOVE_INVENTORY_ITEM', {'source_slot': 10, 'target_slot': 12, 'amount': 2})
        self.run_action('EQUIP_FROM_SLOT', {'source_slot': 12, 'equipment_slot': 5})
        self.run_action('DROP_ITEM', {'slot': 36, 'amount': 1})
        body = self.core.state.observation_frame['nearby_data']['body']
        self.assertEqual(body['inventory_slots'][45]['count'], 2)
        self.assertEqual(body['inventory_slots'][36]['count'], 7)

    def test_block_and_entity_interactions_and_crafting_are_formal_capabilities(self):
        nearby = self.core.state.observation_frame['nearby_data']
        self.run_action('INTERACT_BLOCK', {'block_ref': nearby['blocks'][0]['target_ref']})
        self.run_action('INTERACT_ENTITY', {'entity_ref': nearby['entities'][0]['target_ref']})
        self.run_action('ATTACK_ENTITY', {'entity_ref': nearby['entities'][0]['target_ref']})
        self.run_action('OPEN_CRAFTING_INTERFACE')
        self.run_action('MOVE_ITEM_TO_CRAFT_SLOT', {'source_slot': 10, 'target_slot': 1, 'amount': 1})
        failed = self.run_action('TAKE_CRAFT_RESULT', {'target_slot': 13}, success=False)
        self.assertEqual(failed['reason_code'], 'NO_EFFECT')
        self.run_action('CLOSE_CRAFTING_INTERFACE')

    def test_failures_have_reason_trace_and_do_not_replace_the_individual(self):
        marker = self.core.state.individual_id
        ref = self.core.state.observation_frame['nearby_data']['blocks'][0]['target_ref']
        failed = self.run_action('PLACE_BLOCK', {'inventory_slot': 20, 'reference_block': ref, 'face': 1}, success=False)
        self.assertEqual(failed['reason_code'], 'EMPTY_SLOT')
        self.assertFalse(failed['error']['details']['corrective_action_taken'])
        self.assertEqual(self.core.state.individual_id, marker)
        experience = next(e for e in self.events('EXPERIENCE_FORMED') if failed['action_id'] in e['action_ids'])
        self.assertEqual(experience['action_reason_codes'], ['EMPTY_SLOT'])

    def test_a_can_open_move_take_put_and_close_a_container(self):
        marker = self.core.state.individual_id
        self.new_fixture_session('container')
        self.assertEqual(self.core.state.individual_id, marker)
        ref = self.core.state.observation_frame['nearby_data']['blocks'][0]['target_ref']
        self.run_action('INTERACT_BLOCK', {'block_ref': ref})
        body = self.core.state.observation_frame['nearby_data']['body']
        self.assertIsNotNone(body['container'])
        cid = body['container']['container_id']
        self.run_action('TAKE_CONTAINER_ITEM', {'container_id': cid, 'source_slot': 0, 'target_slot': 9, 'amount': 1})
        self.run_action('PUT_CONTAINER_ITEM', {'container_id': cid, 'source_slot': 9, 'target_slot': 1, 'amount': 1})
        self.run_action('MOVE_CONTAINER_ITEM', {'container_id': cid, 'source_slot': 1, 'target_slot': 2, 'amount': 1})
        body = self.core.state.observation_frame['nearby_data']['body']
        self.assertEqual(body['container']['slot_state'][2]['count'], 1)
        self.run_action('CLOSE_CONTAINER', {'container_id': cid})
        self.assertIsNone(self.core.state.observation_frame['nearby_data']['body']['container'])

    def test_a_operates_a_table_grid_and_takes_only_an_observed_output(self):
        self.new_fixture_session('crafting')
        ref = self.core.state.observation_frame['nearby_data']['blocks'][0]['target_ref']
        self.run_action('INTERACT_BLOCK', {'block_ref': ref})
        self.run_action('OPEN_CRAFTING_INTERFACE')
        self.assertEqual(len(self.core.state.observation_frame['nearby_data']['body']['crafting']['input_slots']), 9)
        self.run_action('MOVE_ITEM_TO_CRAFT_SLOT', {'source_slot': 10, 'target_slot': 9, 'amount': 1})
        self.run_action('TAKE_CRAFT_RESULT', {'target_slot': 11})
        body = self.core.state.observation_frame['nearby_data']['body']
        self.assertEqual(body['container']['slot_state'][11]['item_type_id'], 2)
        self.run_action('CLOSE_CRAFTING_INTERFACE')
        self.assertTrue(verify(self.db)['valid_state_chain'])

    def test_normal_runtime_can_choose_beyond_three_codes_with_honest_policy_sources(self):
        codes = set()
        for _ in range(40):
            self.core.execute_discrete_action()
            final = self.core.state.latest_action
            codes.add(final['action_code'])
            self.assertEqual(final['method'], 'perform')
            binding = final['provenance']['selection']['parameter_binding']
            self.assertEqual(binding['source']['category'], 'INITIAL_EXTERNAL_POLICY')
            self.assertFalse(binding['item_semantics_used'])
            self.assertFalse(binding['learned'])
            self.refresh()
        self.assertTrue(codes - {0, 1, 2}, codes)
        self.assertTrue(verify(self.db)['valid_state_chain'])

    def test_semantic_debug_rename_cannot_change_formal_frame_or_bindings(self):
        raw = self.bridge.call('observe')
        encoded = FrameEncoder('A-test')
        a = encoded.encode(raw, 1).to_dict()
        changed = deepcopy(raw)
        for row in changed['inventory'] + changed['nearbyBlocks'] + changed['nearbyEntities']:
            row['name'] = 'unrelated_human_word'; row['displayName'] = 'unrelated'; row['username'] = 'unrelated'
        for action in changed['actionSpace']:
            action['action_id'] = 'human_label_changed'
            action['environment_requirements'] = ['human_usage_changed']
        b = encoded.encode(changed, 1).to_dict()
        self.assertEqual(a, b)
        ia = InternalState.from_dict(self.core.state.internal_state)
        ib = InternalState.from_dict(self.core.state.internal_state)
        for code in (13, 14, 15, 20, 21, 23, 24):
            self.assertEqual(bind_parameters(code, a, ia, {}), bind_parameters(code, b, ib, {}))

    def test_new_body_inputs_cross_rpc_with_numeric_codec_and_external_provisioning(self):
        marker = self.core.state.individual_id
        initial = self.core.state.state_version
        self.run_action('CONTROL_INPUT', {'control': 0, 'pressed': 1})
        self.run_action('CONTROL_INPUT', {'control': 4, 'pressed': 1})
        body = self.core.state.observation_frame['nearby_data']['body']
        self.assertTrue(body['control_modes']['0'])
        self.assertTrue(body['control_modes']['4'])
        self.run_action('CONTROL_INPUT', {'control': 0, 'pressed': 0})
        self.run_action('CONTROL_INPUT', {'control': 4, 'pressed': 0})
        self.run_action('USE_START', {'hand': 1})
        self.assertEqual(self.core.state.observation_frame['nearby_data']['body']['inputs']['using_item'], 1)
        self.run_action('USE_RELEASE')
        ref = self.core.state.observation_frame['nearby_data']['body']['crosshair']['target_ref']
        self.run_action('DIG_START', {'block_ref': ref})
        self.run_action('DIG_CANCEL')
        self.run_action('DIG_START', {'block_ref': ref})
        self.run_action('DIG_FINISH')
        self.run_action('SWAP_HANDS')
        self.assertEqual(self.core.state.individual_id, marker)
        self.assertGreater(self.core.state.state_version, initial)
        actions = self.core.state.internal_state['body_capabilities']['actions']
        self.assertTrue(all('action_id' not in a and 'environment_requirements' not in a for a in actions))
        self.assertTrue(all(not p['learned'] and p['source'] == 'BODY_CAPABILITY' for p in self.events('BODY_CAPABILITIES_PROVISIONED')))
        self.assertTrue(verify(self.db)['valid_state_chain'])

    def test_formal_macros_refuse_execution_and_preserve_history(self):
        failed = self.run_action('PLACE_BLOCK', {'inventory_slot': 10,
            'reference_block': self.core.state.observation_frame['nearby_data']['blocks'][0]['target_ref'], 'face': 1}, success=False)
        self.assertEqual(failed['reason_code'], 'HELD_SLOT_MISMATCH')
        body = self.core.state.observation_frame['nearby_data']['body']
        self.assertEqual(body['inventory_slots'][10]['count'], 4)
        for code, definition in DEFINITIONS.items():
            if definition.get('formal_enabled') is False:
                self.assertFalse(next(a for a in body['action_space'] if a['code'] == code)['currently_available'])
                self.assertFalse(self.core.execute_discrete_action(code, {}))
                self.assertEqual(self.core.state.latest_action['reason_code'], 'MACRO_NOT_FORMAL')
                self.refresh()

    def test_dead_body_observation_and_normal_tick_can_request_respawn_without_a_new_identity(self):
        marker = self.core.state.individual_id
        self.new_fixture_session(None, die=True)
        deadline = time.monotonic() + 5
        while not self.events('BODY_RESPAWNED'):
            self.core.tick()
            if time.monotonic() > deadline:
                self.fail('Dead-state input channel did not permit explicit respawn')
            time.sleep(0.05)
        requests = self.events('ACTION_REQUESTED')
        self.assertTrue(any(a.get('action_code') == 40 for a in requests))
        self.assertTrue(self.events('BODY_DIED'))
        self.assertEqual(self.core.state.individual_id, marker)
        self.assertTrue(verify(self.db)['valid_state_chain'])

    def test_disabled_capabilities_are_excluded_without_semantic_safety_predictions(self):
        internal = InternalState.from_dict(self.core.state.internal_state)
        internal.exploration_state['random_state'] = 1
        chosen, selection = select_action(internal, 'sample', [18])
        self.assertEqual(chosen, 18)
        self.assertEqual(set(selection['scores']), {'18'})
        self.assertTrue(all('action_id' not in entry for entry in internal.body_capabilities['actions']))
        self.assertEqual(PolicyRegistry(internal).reference('action.parameter_binding')['category'], 'INITIAL_EXTERNAL_POLICY')
