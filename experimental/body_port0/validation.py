"""Executable BPC-0 acceptance; stdout only, no world or database writes."""
from dataclasses import asdict, is_dataclass, replace
import json
from unittest.mock import patch
from .prototype import (Sample, RecordingBody, Execution, Organization, Member,
                        Shared, bootstrap, encode_execution, form, consume, catalog_port)


def serial(value):
    if is_dataclass(value):
        return {'type': type(value).__name__, **{k: serial(v) for k, v in vars(value).items()}}
    if isinstance(value, (frozenset, set)):
        return sorted((serial(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(value, tuple):
        return [serial(v) for v in value]
    return value


def fixture(code=36, identity='receipt-a', scope='test-epoch-1'):
    body = RecordingBody(Sample(1, scope, ((101, 2),)))
    e = bootstrap(body, code, ((101, 5),), identity)
    m, c = encode_execution(e)
    return body, e, m, c


def run_validation():
    try:
        body, e, m, c = fixture()
    except ValueError as error:
        return {'status': 'NOT_TESTABLE', 'reason': str(error)}
    s = form(m)
    edge = Shared(frozenset((c, e.port)))
    expression = consume(s, c)
    missing = replace(m, facts=m.facts - {Member(e.identity, e.port)})
    screened = replace(s, facts=s.facts - {edge})
    proof_screened = replace(s, supports=frozenset(p for p in s.supports if p.conclusion != edge))
    checks = {
        'BPC_T1_NEW_SUPPORTED_LINK': edge not in m.facts and edge in s.facts,
        'BPC_T2_NATIVE_COMPLETE_EXPRESSION': expression == {'code': e.port.code, 'parameters': {}},
        'BPC_T3_NECESSARY_INPUT_ABLATION': consume(form(missing), c) is None,
        'BPC_T4_FORMED_EFFECT_ABLATION': consume(None, c) is None and consume(screened, c) is None
                                      and consume(proof_screened, c) is None,
    }
    with patch('individual.formal_l0.select_uniform_action', side_effect=AssertionError('selector')) as sampler, \
            patch('individual.action_space.bind_parameters', side_effect=AssertionError('binder')) as binder, \
            patch('experimental.body_port0.prototype.form', side_effect=AssertionError('recompute')):
        second = consume(s, c)
        before, after = body.execute(second, ((101, 8),))
        consume(None, c)
    checks['BPC_T5_NO_SELECTOR_BINDER_RECOMPUTATION'] = sampler.call_count == binder.call_count == 0
    _, _, other, oc = fixture(46)
    checks['BPC_T6_HISTORY_CONDITIONED_PORT'] = oc == c and consume(form(other), oc)['code'] == 46
    distractor_results = {}
    for count in (10, 100):
        facts, proofs = set(m.facts), set(m.supports)
        for i in range(count):
            _, _, d, _ = fixture(46, f'd-{i}', f'd-scope-{i}')
            facts.update(d.facts)
            proofs.update(d.supports)
        ds = form(Organization(frozenset(facts), frozenset(proofs), False))
        distractor_results[str(count)] = (consume(ds, c) == expression and
            {p for p in ds.supports if p.conclusion == edge} == {p for p in s.supports if p.conclusion == edge})
    checks['BPC_T7_DISTRACTOR_INVARIANCE'] = all(distractor_results.values())
    second_record = Execution('second-receipt', catalog_port(second['code']), before, after,
                              source='TEST_ONLY_FORMED_CONNECTION')
    renewed, nc = encode_execution(second_record)
    accumulated = Organization(m.facts | renewed.facts, m.supports | renewed.supports, False)
    checks['BPC_T8_SECOND_OUTPUT_AND_REENTRY'] = (len(body.commands) == 2 and
        body.commands[-1][0] == e.port and consume(form(accumulated), nc) == expression)
    _, _, alternate, _ = fixture(46, 'alternate-receipt')
    conflict = form(Organization(m.facts | alternate.facts, m.supports | alternate.supports, False))
    checks['BPC_T9_AMBIGUITY_NO_ARBITRATION'] = consume(conflict, c) is None
    return {'status': 'PASS' if all(checks.values()) else 'FAIL',
            'scope': 'TEST_ONLY synthetic history; parameterless native body ports; unique supported endpoint',
            'criteria': {k: 'PASS' if v else 'FAIL' for k, v in checks.items()},
            'world_facing_status': 'NOT_TESTABLE', 'distractor_controls': distractor_results,
            'bootstrap_author': 'TEST_ONLY_EXTERNAL_BOOTSTRAP',
            'second_expression_content_source': 'FORMED_SHARED_INCIDENCE',
            'query_author': 'TEST_ONLY_EXTERNAL_QUERY',
            'formation_law_author': 'EXTERNAL_FIXED_MECHANISM',
            'policy_adoption_autonomy_established': False,
            'material': serial(m), 'formed_organization': serial(s), 'expression': expression,
            'second_receipt': serial(second_record), 'renewed_structure': serial(nc),
            'first_failure': next((k for k, ok in checks.items() if not ok), None)}


if __name__ == '__main__':
    print(json.dumps(run_validation(), ensure_ascii=False, indent=2))
