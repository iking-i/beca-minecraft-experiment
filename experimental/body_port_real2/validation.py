"""Detached controls first; one real perform only when all gates are satisfied."""
from dataclasses import asdict
import argparse
import json
from pathlib import Path
import time
from unittest.mock import patch

from .prototype import (ROOT, BodyPort, Shared, Support, Organization, FIXED_PORT,
                        MaterialUnavailable, load_fixed, expression_from_formed)
from experimental.body_port_real1.prototype import screen
from individual.action_space import CATALOG_DATA, DEFINITIONS
from individual.bridge import MinecraftBridge, BridgeError, parse_minecraft_port


LEDGER = ROOT / 'storage/validation/BPC-R2-ONE-PERFORM.json'


def offline(material):
    s, c = material.organization, material.current
    resolved = expression_from_formed(s, c)
    edge = Shared(frozenset((c, FIXED_PORT)))
    observed = {}
    def forbidden(name):
        def call(*args, **kwargs):
            observed[name] = observed.get(name, 0) + 1
            raise AssertionError(name + ' may not author expression')
        return call
    with patch('individual.formal_l0.select_uniform_action', side_effect=forbidden('sampler')), \
         patch('individual.action_space.bind_parameters', side_effect=forbidden('binder')), \
         patch('experimental.body_port0.prototype.form', side_effect=forbidden('formation')), \
         patch('experimental.body_port_real1.prototype.form', side_effect=forbidden('formation')), \
         patch('individual.bridge.MinecraftBridge.call', side_effect=forbidden('bridge')):
        controls = {
            'formed_connection_removed': expression_from_formed(screen(s, (edge,)), c) is None,
            'necessary_port_support_removed': expression_from_formed(screen(s, (FIXED_PORT,)), c) is None,
            'organization_inaccessible': expression_from_formed(None, c) is None,
        }
        alternative = BodyPort(FIXED_PORT.version, 1)
        additional_edge = Shared(frozenset((c, alternative)))
        ambiguous = Organization(s.facts | {alternative, additional_edge}, s.supports |
                                 {Support(alternative, 'TEST_ONLY_INPUT', frozenset()),
                                  Support(additional_edge, 'TEST_ONLY_INTERVENTION', frozenset((c, alternative)))})
        controls['ambiguous_supported_ports'] = expression_from_formed(ambiguous, c) is None
        distraction = ('TEST_ONLY_DISCONNECTED', 1)
        distracted = Organization(s.facts | {distraction}, s.supports |
                                 {Support(distraction, 'TEST_ONLY_INPUT', frozenset())})
        controls['unrelated_distractor'] = expression_from_formed(distracted, c) == resolved
        controls['invalid_connection_no_sampler_fallback'] = expression_from_formed(screen(s, (edge,)), c) is None
        controls['binder_forbidden_valid_expression'] = expression_from_formed(s, c) == resolved
        controls['no_sampler_binder_formation_bridge_calls'] = not observed
    authored = (resolved is not None and resolved['port'] == FIXED_PORT and
                resolved['expression'] == {'code': resolved['port'].code, 'parameters': {}})
    return {'offline_status': 'PASS' if authored and all(controls.values()) else 'FAIL',
            'controls': controls, 'forbidden_call_counts': observed,
            'expression': resolved['expression'] if resolved else None,
            'port': asdict(resolved['port']) if resolved else None,
            'code_author': 'SUPPORTED_FORMED_CONNECTION',
            'query_and_trigger_author': 'TEST_ONLY_EXPERIMENTER',
            'source_digest': material.source_digest}


def catalog_compatible():
    definition = DEFINITIONS.get(FIXED_PORT.code)
    return (CATALOG_DATA['version'] == FIXED_PORT.version and definition is not None
            and definition['formal_enabled'] and definition['parameters'] == {})


def execute_once(result, port, output, bridge_factory=MinecraftBridge, ledger=LEDGER):
    """One isolated physical-body session. No Core, canonical DB, retry or selector."""
    report = dict(result, classification='NOT_TESTABLE', perform_attempts=0,
                  live_body_identity='BPC_R2_Test', real_body_is_formal_A=False,
                  automatic_retry=False, reconnect_enabled=False)
    if result['offline_status'] != 'PASS':
        report.update(classification='FAIL', reason='OFFLINE_ACCEPTANCE_FAILED')
        return report
    if not catalog_compatible():
        report['reason'] = 'NATIVE_CATALOG_INCOMPATIBLE'
        return report
    if Path(ledger).exists():
        report['reason'] = 'SOLE_PERFORM_ATTEMPT_ALREADY_RESERVED_NO_RETRY'
        return report
    config = json.loads((ROOT / 'minecraft/config.json').read_text(encoding='utf-8'))
    if config['auth'] != 'offline':
        report['reason'] = 'TEST_BODY_OFFLINE_IDENTITY_UNAVAILABLE'
        return report
    config.update(port=parse_minecraft_port(port), username='BPC_R2_Test')
    config['reconnect']['enabled'] = False
    config_path = Path(output) / 'body-config.test-only.json'
    config_path.write_text(json.dumps(config, indent=2), encoding='utf-8')
    bridge = bridge_factory(config_path, log=lambda line: append_log(output, line))
    try:
        bridge.launch()
        status = bridge.call('start')
        deadline = time.monotonic() + config['connectTimeoutMs'] / 1000 + 1
        while not status.get('connected'):
            if status.get('lastError') or status.get('state') in ('dead', 'disconnected', 'stopped') or time.monotonic() >= deadline:
                report.update(reason='MINECRAFT_BRIDGE_UNAVAILABLE', preflight_status=status)
                return report
            time.sleep(0.1)
            status = bridge.call('status')
        before = bridge.call('observe')
        report['before_observation'] = before
        entries = [x for x in before.get('actionSpace', ()) if x.get('code') == FIXED_PORT.code]
        if (len(entries) != 1 or not entries[0].get('formal_enabled') or not entries[0].get('currently_available')
                or entries[0].get('parameter_schema', {}).get('required') != []
                or entries[0].get('parameter_schema', {}).get('properties') != {}):
            report['reason'] = 'NATIVE_CAPABILITY_CURRENTLY_INCOMPATIBLE_OR_UNAVAILABLE'
            return report
        expression = result['expression']
        if expression != {'code': FIXED_PORT.code, 'parameters': {}} or result['port'] != asdict(FIXED_PORT):
            report.update(classification='FAIL', reason='FORMED_OUTPUT_FIXED_WITNESS_MISMATCH')
            return report
        reservation = {'stage': 'BPC-R2', 'source_digest': result['source_digest'],
                       'output': str(Path(output).resolve()), 'expression': expression,
                       'meaning': 'reserved before dispatch; uncertain result still forbids replay'}
        Path(ledger).parent.mkdir(parents=True, exist_ok=True)
        try:
            with Path(ledger).open('x', encoding='utf-8') as stream:
                json.dump(reservation, stream, indent=2)
        except FileExistsError:
            report['reason'] = 'SOLE_PERFORM_ATTEMPT_ALREADY_RESERVED_NO_RETRY'
            return report
        report.update(perform_attempts=1, transmitted_expression=expression,
                      dispatch_authorship='EXTERNAL_FIXED_MECHANISM', catalog_version=CATALOG_DATA['version'])
        receipt = bridge.call('perform', expression)
        report['receipt'] = receipt
        exact = (receipt.get('code') == expression['code'] and receipt.get('parameters') == expression['parameters']
                 and receipt.get('result') == {'input_sent': 1, 'effect_acknowledged': 0}
                 and receipt.get('effect_attribution') == 'temporal_observation_only'
                 and receipt.get('started_at') and receipt.get('finished_at'))
        report.update(classification='PASS' if exact else 'FAIL',
                      reason='MATCHING_REAL_INPUT_EXECUTION_RECEIPT' if exact else 'RECEIPT_EXPRESSION_MISMATCH',
                      world_effect_causality_claimed=False)
        return report
    except BridgeError as error:
        uncertain = error.code in {'BRIDGE_TIMEOUT', 'BRIDGE_EXITED', 'DISCONNECTED', 'ACTION_TIMEOUT', 'KICKED'}
        report.update(classification='NOT_TESTABLE' if uncertain or report['perform_attempts'] == 0 else 'FAIL',
                      reason=error.code, error={'code': error.code, 'details': error.details})
        return report
    finally:
        bridge.close()


def append_log(output, line):
    with (Path(output) / 'bridge.log').open('a', encoding='utf-8') as stream:
        stream.write(str(line) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--port')
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    try:
        result = offline(load_fixed())
        (output / 'offline.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        if args.live and args.port:
            result = execute_once(result, args.port, output)
        else:
            result.update(classification='NOT_TESTABLE' if result['offline_status'] == 'PASS' else 'FAIL',
                          reason='REAL_EXECUTION_NOT_PERFORMED', perform_attempts=0)
    except MaterialUnavailable as error:
        result = {'classification': 'NOT_TESTABLE', 'reason': str(error), 'perform_attempts': 0}
    (output / 'validation.json').write_text(json.dumps(result, indent=2, ensure_ascii=True), encoding='utf-8')
    summary = {k: v for k, v in result.items() if k not in ('before_observation', 'receipt')}
    (output / 'validation.md').write_text('# BPC-R2 acceptance\n\n```json\n' + json.dumps(summary, indent=2) + '\n```\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
