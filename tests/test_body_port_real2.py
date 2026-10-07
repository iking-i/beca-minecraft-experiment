"""BPC-R2 isolated controls. Fake bridge receipts never count as live PASS."""
from dataclasses import replace
import json
from unittest.mock import patch

import pytest

from experimental.body_port_real2.prototype import (
    MaterialUnavailable, load_fixed, expression_from_formed, BodyPort, Shared,
    Organization, Support, FIXED_PORT)
from experimental.body_port_real2.validation import offline, execute_once
from experimental.body_port_real1.prototype import screen
from individual.bridge import BridgeError


@pytest.fixture
def material():
    return load_fixed()


def test_saved_exact_material_no_reformation(material):
    with patch('experimental.body_port_real1.prototype.form', side_effect=AssertionError('No formation')), \
         patch('experimental.body_port_real1.prototype.load_candidates', side_effect=AssertionError('No history')):
        again = load_fixed()
    assert again == material
    assert expression_from_formed(again.organization, again.current)['expression'] == {'code': 0, 'parameters': {}}


def test_all_frozen_offline_controls(material):
    result = offline(material)
    assert result['offline_status'] == 'PASS'
    assert all(result['controls'].values())
    assert result['forbidden_call_counts'] == {}


@pytest.mark.parametrize('kind', ['connection', 'port', 'organization'])
def test_removal_no_expression(material, kind):
    s, c = material.organization, material.current
    edge = Shared(frozenset((c, FIXED_PORT)))
    modified = None if kind == 'organization' else screen(s, [edge if kind == 'connection' else FIXED_PORT])
    assert expression_from_formed(modified, c) is None


def test_code_is_read_port_not_fixed_zero_or_historical_request(material):
    # Detached producer-output intervention; never used by the live path.
    s, c = material.organization, material.current
    s = screen(s, [Shared(frozenset((c, FIXED_PORT)))])
    other = BodyPort(FIXED_PORT.version, 1)
    edge = Shared(frozenset((c, other)))
    modified = Organization(s.facts | {other, edge}, s.supports |
                           {Support(other, 'TEST_ONLY', frozenset()),
                            Support(edge, 'TEST_ONLY', frozenset((c, other)))})
    assert expression_from_formed(modified, c)['expression'] == {'code': 1, 'parameters': {}}
    # Historical action code remains 0 inside unchanged original roots.


def test_missing_material_not_reselected(tmp_path):
    with pytest.raises(MaterialUnavailable):
        load_fixed(tmp_path / 'missing.json')


class FakeBridge:
    instances = []
    available = True
    behavior = 'success'

    def __init__(self, config, log=None):
        self.config = json.loads(config.read_text())
        self.calls = []
        self.closed = False
        self.__class__.instances.append(self)

    def launch(self):
        pass

    def call(self, method, args=None):
        self.calls.append((method, args))
        if method in ('start', 'status'):
            return {'connected': True, 'state': 'ready'}
        if method == 'observe':
            return {'actionSpace': [{'code': 0, 'formal_enabled': True, 'currently_available': self.available,
                                    'parameter_schema': {'required': [], 'properties': {}}}]}
        if method == 'perform':
            if self.behavior == 'timeout':
                raise BridgeError('BRIDGE_TIMEOUT', 'uncertain')
            if self.behavior == 'failed':
                raise BridgeError('NO_EFFECT', 'definite failure')
            return {'code': 1 if self.behavior == 'mismatch' else args['code'], 'parameters': args['parameters'],
                    'result': {'input_sent': 1, 'effect_acknowledged': 0},
                    'started_at': 's', 'finished_at': 'f', 'effect_attribution': 'temporal_observation_only'}
        raise AssertionError(method)

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def reset_fake():
    FakeBridge.instances = []
    FakeBridge.available = True
    FakeBridge.behavior = 'success'


def run_fake(material, tmp_path):
    return execute_once(offline(material), 12345, tmp_path, bridge_factory=FakeBridge, ledger=tmp_path / 'once.json')


def test_one_send_exact_expression_and_isolated_config(material, tmp_path):
    report = run_fake(material, tmp_path)
    assert report['classification'] == 'PASS'  # UNIT fixture status, not real acceptance.
    fake = FakeBridge.instances[0]
    assert [args for method, args in fake.calls if method == 'perform'] == [{'code': 0, 'parameters': {}}]
    assert fake.config['username'] == 'BPC_R2_Test'
    assert fake.config['reconnect']['enabled'] is False
    assert fake.closed
    assert (tmp_path / 'once.json').exists()


@pytest.mark.parametrize('behavior,status', [('timeout', 'NOT_TESTABLE'), ('failed', 'FAIL'), ('mismatch', 'FAIL')])
def test_failure_or_uncertainty_no_retry(material, tmp_path, behavior, status):
    FakeBridge.behavior = behavior
    report = run_fake(material, tmp_path)
    assert report['classification'] == status
    assert report['perform_attempts'] == 1
    assert sum(method == 'perform' for method, _ in FakeBridge.instances[0].calls) == 1
    FakeBridge.behavior = 'success'
    again = run_fake(material, tmp_path)
    assert again['perform_attempts'] == 0
    assert len(FakeBridge.instances) == 1


def test_unavailable_preflight_no_perform(material, tmp_path):
    FakeBridge.available = False
    report = run_fake(material, tmp_path)
    assert report['classification'] == 'NOT_TESTABLE'
    assert report['perform_attempts'] == 0
    assert not (tmp_path / 'once.json').exists()
    assert all(method != 'perform' for method, _ in FakeBridge.instances[0].calls)


def test_failed_offline_no_bridge(material, tmp_path):
    result = offline(material)
    result['offline_status'] = 'FAIL'
    report = execute_once(result, 12345, tmp_path, FakeBridge, tmp_path / 'once.json')
    assert report['classification'] == 'FAIL'
    assert not FakeBridge.instances


def test_catalog_incompatible_no_bridge(material, tmp_path):
    with patch('experimental.body_port_real2.validation.catalog_compatible', return_value=False):
        report = run_fake(material, tmp_path)
    assert report['classification'] == 'NOT_TESTABLE'
    assert not FakeBridge.instances


def test_ledger_blocks_even_with_different_output_directory(material, tmp_path):
    first = tmp_path / 'first'
    second = tmp_path / 'second'
    first.mkdir(); second.mkdir()
    ledger = tmp_path / 'fixed-ledger.json'
    assert execute_once(offline(material), 12345, first, FakeBridge, ledger)['perform_attempts'] == 1
    assert execute_once(offline(material), 12345, second, FakeBridge, ledger)['perform_attempts'] == 0
    assert len(FakeBridge.instances) == 1
