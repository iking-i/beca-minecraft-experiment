"""TEST_ONLY schema controls. Synthetic unit records are not live acceptance."""
from dataclasses import replace
from unittest.mock import patch
import json

import pytest

from experimental.body_port_real1.prototype import (
    Evidence, RealExperience, BodyPort, Shared, Support, Organization, Member,
    canonical, number, encode_real, connections, screen, form, verified_change)
from individual.action_space import CATALOG_DATA, DEFINITIONS
from individual.observation import FrameEncoder
from individual.change_detection import detect_changes


def fixture(code=4, group='unit-experience', after_value=1.25):
    individual, session = 'TEST_ONLY_UNIT', 'unit-session'
    def evidence(identity, kind, payload):
        return Evidence(identity, canonical({'event_id': identity, 'individual_id': individual,
                         'session_id': session, 'event_type': kind, 'payload': payload}))
    raw_before = {'timestamp': 'before', 'position': {'x': 0.5, 'y': 0, 'z': 0},
                  'nearbyBlocks': [], 'nearbyEntities': [], 'inventory': [], 'coverage': {},
                  'encoding': {'protocol_version': 'unit-protocol'}}
    raw_after = {**raw_before, 'timestamp': 'after', 'position': {'x': after_value, 'y': 0, 'z': 0}}
    before = FrameEncoder(individual).encode(raw_before, 1, 2)
    after = FrameEncoder(individual).encode(raw_after, 2, 2)
    after.delta = detect_changes(before, after, ['action-1']).to_dict()
    version = CATALOG_DATA['version']
    xp = {'experience_id': group, 'action_ids': ['action-1'], 'action_statuses': ['executed'],
          'action_parameters': [{}], 'action_reason_codes': [None], 'action_code': code,
          'frame_ids': [before.frame_id, after.frame_id], 'frame_id': after.frame_id,
          'sequence_id': 2, 'change_id': after.delta['change_id'], 'causality': 'temporal_association_only'}
    req = {'action_id': 'action-1', 'action_code': code, 'status': 'requested', 'method': 'perform',
           'args': {'code': code, 'parameters': {}}, 'provenance': {'frame_id': before.frame_id}}
    receipt = {**req, 'status': 'executed', 'result': {'code': code, 'parameters': {},
               'result': {'input_sent': 1, 'effect_acknowledged': 0}, 'started_at': 's', 'finished_at': 't',
               'before': {}, 'after': {}, 'effect_attribution': 'temporal_observation_only'}}
    provision = {'after': {'version': version, 'actions': [{'code': code, 'formal_enabled': True,
                                                         'parameter_schema': {'properties': {}}}]}}
    return RealExperience(individual, session, group, 'action-1', BodyPort(version, code), 'executed',
        evidence('before', 'OBSERVATION_FRAME', before.to_dict()), evidence('after', 'OBSERVATION_FRAME', after.to_dict()),
        evidence('receipt', 'ACTION_EXECUTED', receipt), evidence('experience', 'EXPERIENCE_FORMED', xp),
        evidence('request', 'ACTION_REQUESTED', req), evidence('provision', 'BODY_CAPABILITIES_PROVISIONED', provision),
        evidence('raw-before', 'WORLD_OBSERVATION', {'frame_id': before.frame_id, 'observation': raw_before}),
        evidence('raw-after', 'WORLD_OBSERVATION', {'frame_id': after.frame_id, 'observation': raw_after}),
        Evidence(session, canonical({'individual_id': individual, 'session_id': session,
                                     'environment': {'minecraft_connection': {'host': 'unit-fixture'}}})))


def modify(e, field, fn):
    root = getattr(e, field)
    obj = json.loads(root.content)
    fn(obj['payload'])
    return replace(e, **{field: replace(root, content=canonical(obj))})


def test_real_schema_float_formation_not_synthetic_sample():
    e = fixture()
    material, c = encode_real(e)
    edge = Shared(frozenset((c, e.port)))
    assert edge not in material.facts
    organization = form(material)
    assert connections(organization, c) == {'status': 'CONNECTED', 'ports': (e.port,)}
    assert any(p.conclusion == edge and p.rule == 'SHARED_INCIDENCE' for p in organization.supports)
    assert c.changes[0][2] == ('float', 0.5.hex())


@pytest.mark.parametrize('field', ['experience', 'port', 'after', 'receipt', 'request', 'provisioning', 'raw_before', 'raw_after', 'session'])
def test_necessary_provenance_screening(field):
    e = fixture()
    m, c = encode_real(e)
    org = form(m)
    screened = screen(org, [getattr(e, field)])
    with patch('experimental.body_port_real1.prototype.form', side_effect=AssertionError('No recompute')):
        assert connections(screened, c)['status'] == 'UNRESOLVED'
    assert connections(org, c)['status'] == 'CONNECTED'


@pytest.mark.parametrize('field,fn', [
    ('experience', lambda p: p.update(action_ids=[])),
    ('experience', lambda p: p.update(action_ids=['a', 'b'])),
    ('receipt', lambda p: p.update(status='failed')),
    ('receipt', lambda p: p['result'].update(code=5)),
    ('request', lambda p: p['args'].update(parameters={'extra': 1})),
    ('provisioning', lambda p: p['after'].update(version='other')),
    ('after', lambda p: p['delta'].update(changes=[])),
    ('after', lambda p: p.update(body_epoch=3)),
    ('after', lambda p: p['numeric_channels'].update({next(iter(p['numeric_channels'])): 99})),
])
def test_invalid_or_missing_material_rejected(field, fn):
    with pytest.raises(ValueError):
        encode_real(modify(fixture(), field, fn))


def test_empty_observed_change_rejected():
    with pytest.raises(ValueError):
        encode_real(fixture(after_value=0.5))


def test_distractor_and_order_independence():
    e = fixture()
    m, c = encode_real(e)
    d = Member('other', ('opaque', 1)), Member('other', ('opaque', 2))
    dm = Organization(m.facts | frozenset(d), m.supports | frozenset(Support(f, 'INPUT', frozenset()) for f in d), False)
    original, added = form(m), form(dm)
    assert connections(original, c) == connections(added, c)
    edge = Shared(frozenset((c, e.port)))
    assert {p for p in original.supports if p.conclusion == edge} == {p for p in added.supports if p.conclusion == edge}
    assert form(Organization(frozenset(reversed(tuple(dm.facts))), dm.supports, False)) == added


def test_multiple_native_ports_no_adoption():
    e, alternative = fixture(), fixture(code=5, group='other-experience')
    m, c = encode_real(e)
    n, other_c = encode_real(alternative)
    assert c == other_c
    org = form(Organization(m.facts | n.facts, m.supports | n.supports, False))
    assert connections(org, c) == {'status': 'AMBIGUOUS', 'ports': (e.port, alternative.port)}


def test_consumer_uses_formed_structure_only_no_execution():
    e = fixture()
    m, c = encode_real(e)
    with patch('individual.bridge.MinecraftBridge.call', side_effect=AssertionError('No execution')), \
         patch('individual.formal_l0.select_uniform_action', side_effect=AssertionError('No selector')), \
         patch('individual.action_space.bind_parameters', side_effect=AssertionError('No binder')):
        org = form(m)
        with patch('experimental.body_port_real1.prototype.verified_change', side_effect=AssertionError('No raw read')):
            assert connections(org, c)['status'] == 'CONNECTED'
            assert connections(screen(org, [Shared(frozenset((c, e.port)))]), c)['status'] == 'UNRESOLVED'
            assert connections(None, c)['status'] == 'UNRESOLVED'


def test_exact_numeric_identity_no_rounding():
    assert number(1) != number(1.0)
    assert number(0.0) != number(-0.0)
    assert number(1.0) != number(1.0000000000000002)
    with pytest.raises(ValueError):
        number(float('nan'))


def test_parameterized_port_not_accepted():
    code = next(k for k, d in DEFINITIONS.items() if d['parameters'])
    with pytest.raises(ValueError):
        verified_change(fixture(code=code))


@pytest.mark.parametrize('field', ['experience', 'port', 'after'])
def test_preformation_input_deletion_no_supported_connection(field):
    e = fixture()
    m, c = encode_real(e)
    assert connections(form(screen(m, [getattr(e, field)])), c)['status'] == 'UNRESOLVED'
    with pytest.raises(ValueError):
        encode_real(replace(e, **{field: None}))


def test_wrong_event_type_rejected():
    e = fixture()
    obj = json.loads(e.receipt.content)
    obj['event_type'] = 'TEST_ONLY_FAKE_RECEIPT'
    with pytest.raises(ValueError):
        encode_real(replace(e, receipt=replace(e.receipt, content=canonical(obj))))
