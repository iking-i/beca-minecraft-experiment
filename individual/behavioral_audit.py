"""Offline behavioral-authorship audit, never a formal decision or memory port.

Only checkpointed databases are read (immutable SQLite). Uncheckpointed inputs
must first be copied with their WAL outside this auditor. Labels/references are
not accepted as proof that history authored a behavior.
"""
import argparse
from contextlib import closing
from copy import deepcopy
import json
from pathlib import Path
import sqlite3

from .decision_provenance import decision_authorship


def action_trace(action, events):
    """Resolve stored references and separate metadata from behavioral causes."""
    provenance = action.get('provenance', {})
    selection = provenance.get('selection', {})
    existing = decision_authorship(selection)
    before = provenance.get('source_state_version', -1)
    prior = [e for e in events if e['state_version'] <= before]
    integrations = {e['payload']['integration_id']: e for e in prior
                    if e['event_type'] == 'INTEGRATION_COMPLETED'}
    partials = {e['payload']['partial_id']: e for e in prior
                if e['event_type'] == 'RECURSIVE_PARTIAL_OUTPUT'}
    experiences = {e['payload']['experience_id']: e for e in prior
                   if e['event_type'] == 'EXPERIENCE_FORMED'}
    integration = integrations.get(provenance.get('integration_id'))
    links = []
    if integration:
        for pid in integration['payload'].get('input_partial_ids', []):
            partial = partials.get(pid)
            exp_id = (partial or {}).get('payload', {}).get('experience', {}).get('experience_id')
            exp = experiences.get(exp_id)
            matches = bool(partial and exp and partial['payload']['experience'] == exp['payload']
                           and exp_id in integration['payload'].get('experience_ids', [])
                           and exp['state_version'] <= partial['state_version'] <= integration['state_version'])
            links.append({'integration_id': integration['payload']['integration_id'],
                          'partial_id': pid, 'experience_id': exp_id,
                          'process_id': (partial or {}).get('payload', {}).get('process_id'),
                          'relation_refs': [o.get('relation_id') for o in integration['payload'].get('operations', [])],
                          'frame_ids': (exp or {}).get('payload', {}).get('frame_ids', []),
                          'references_resolved': matches,
                          'behavioral_dependency_proven': False})
    test = existing['aggregate_source'] == 'TEST_ONLY'
    formal = selection.get('policy_id') == 'formal.action_sampling'
    external = formal and existing['aggregate_source'] == 'EXTERNAL_FIXED_POLICY'
    bootstrap = external and not experiences
    classification = ('TEST_ONLY' if test else 'PURE_EXTERNAL_BOOTSTRAP' if bootstrap
                      else 'EXTERNAL_FIXED_POLICY' if external
                      else 'MIXED_POLICY' if existing['aggregate_source'] == 'MIXED_POLICY'
                      else 'UNVERIFIED_AUTHORSHIP')
    binding = selection.get('parameter_binding', {})
    choices = binding.get('choices', [])
    parameters = action.get('args', {}).get('parameters', {})
    parameter_sources = {}
    for key, value in parameters.items():
        matched = [deepcopy(c) for c in choices if c.get('parameter') == key and c.get('value') == value]
        parameter_sources[key] = {'value': deepcopy(value),
            'author': 'TEST_ONLY' if test else 'INITIAL_EXTERNAL_POLICY' if external else 'UNVERIFIED_AUTHORSHIP',
            'domain_source': 'ENVIRONMENT_CONSTRAINT', 'binding_record': matched,
            'binding_kind': 'external_domain_sample' if matched else 'external_fixed_binding' if external else 'unverified',
            'internal_history_dependency_proven': False}
    return {'action_id': action.get('action_id'), 'action_code': action.get('action_code'),
        'source_state_version': before, 'source_structure_revision': provenance.get('source_structure_revision'),
        'current_frame_id': provenance.get('frame_id'), 'reported_authorship': existing,
        'audited_authorship': classification,
        'bootstrap_eligible': bootstrap, 'ongoing_external_author': external and not bootstrap,
        'code_provenance': {'author': 'TEST_ONLY' if test else 'INITIAL_EXTERNAL_POLICY' if external else 'UNVERIFIED_AUTHORSHIP',
            'policy_id': selection.get('policy_id'), 'seed_before': selection.get('seed_before'),
            'seed_after': selection.get('tie_state'), 'available_codes': selection.get('available_codes'),
            'internal_history_dependency_proven': False},
        'parameter_provenance': parameter_sources, 'resolved_history': links,
        'integration_reference_present': bool(provenance.get('integration_id')),
        'integration_reference_resolved': integration is not None,
        'prior_experiences': len(experiences),
        'external_mechanism_contribution': ['numeric encoding', 'legal-domain exposure', 'perform transport', 'append-only recording'],
        'behavioral_causal_closure_proven': False,
        'reason': ('Explicit test command is not internally authored.' if test else
                   'Formal sampler and binder do not read history to determine behavioral content.' if external else
                   'No verified behavioral producer/readout and counterfactual witness are available.')}


def audit_behavior(database):
    path = Path(database).resolve()
    if not path.is_file():
        raise ValueError('Audit requires an existing checkpointed database')
    wal = Path(str(path) + '-wal')
    if wal.exists() and wal.stat().st_size:
        raise ValueError('Uncheckpointed WAL: audit a closed validation database or an isolated DB+WAL copy; never ignore live history')
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
        identity = db.execute('SELECT individual_id FROM experiment WHERE singleton=1').fetchone()[0]
        # Offline auditor may read the journal. This is not an A-facing memory expansion.
        events = [{'event_sequence': seq, 'state_version': v, 'event_type': k, 'payload': json.loads(p)}
                  for seq, v, k, p in db.execute('SELECT event_sequence,state_version,event_type,payload FROM events ORDER BY event_sequence')]
    traces = [action_trace(e['payload'], events) for e in events if e['event_type'] == 'ACTION_REQUESTED']
    return {'individual_id': identity, 'database': str(path), 'role': 'OFFLINE_AUDITOR',
        'BEHAVIORAL_CAUSAL_CLOSURE': 'failed' if any(t['ongoing_external_author'] for t in traces) else 'not_demonstrated',
        'actions': traces, 'internal_behavior_authorship_proven': False,
        'upward_recursion_claimed': False, 'audit_changes_behavior': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True, help='Explicit closed/checkpointed audit input; no automatic canonical selection')
    args = parser.parse_args()
    print(json.dumps(audit_behavior(args.db), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
