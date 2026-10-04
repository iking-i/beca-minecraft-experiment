"""Read-only policy boundary evidence. Parameter updates are not source migration."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sqlite3
from .decision_provenance import decision_authorship


def audit_policies(database):
    db = sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)
    try:
        db.execute('BEGIN')
        row = db.execute('SELECT state_version,snapshot FROM states ORDER BY state_version DESC LIMIT 1').fetchone()
        if row is None:
            raise ValueError('No experiment states')
        last_version, raw = row
        state = json.loads(raw)
        internal = state['internal_state']
        registry = internal.get('policy_registry')
        if not registry:
            return {'tracking_available': False, 'note': 'Legacy experiment; history was not backfilled.'}
        kinds = ('POLICY_REGISTRY_INITIALIZED', 'POLICY_REGISTRY_INHERITED', 'POLICY_PARAMETER_UPDATED', 'RECURSION_GENERATED',
                 'ACTION_REQUESTED', 'INTEGRATION_COMPLETED', 'RECURSIVE_PARTIAL_OUTPUT', 'DIRECT_EVIDENCE_INPUT')
        rows = db.execute(f"SELECT event_sequence,state_version,event_type,payload FROM events WHERE event_type IN ({','.join('?' for _ in kinds)}) ORDER BY event_sequence", kinds)
        counts = Counter()
        changes, integrations, partials, linked = {}, {}, {}, []
        action_checks, generation_checks = [], []
        authors, attribution_errors = Counter(), []
        for seq, version, kind, payload in rows:
            p = json.loads(payload)
            counts[kind] += 1
            record = {'event_sequence': seq, 'state_version': version, 'payload': p}
            if kind == 'INTEGRATION_COMPLETED':
                integrations[p['integration_id']] = record
            elif kind in ('RECURSIVE_PARTIAL_OUTPUT', 'DIRECT_EVIDENCE_INPUT'):
                partials[p['partial_id']] = record
            elif kind == 'POLICY_PARAMETER_UPDATED':
                changes[p['change_id']] = record
            elif kind == 'ACTION_REQUESTED' and p.get('provenance', {}).get('selection') is not None:
                selection = p['provenance']['selection']
                expected = decision_authorship(selection)
                authors[expected['aggregate_source']] += 1
                consistent = (p.get('initiator') == expected['initiator'] and
                              p['provenance'].get('decision_authorship') == expected)
                if not consistent:
                    attribution_errors.append({'event_sequence': seq, 'recorded_initiator': p.get('initiator'),
                                               'expected_authorship': expected})
                if selection.get('category') == 'TEST_ONLY':
                    action_checks.append(consistent)
                    continue
                if selection.get('policy_id') == 'formal.action_sampling':
                    binder = selection.get('parameter_binding')
                    action_checks.append(consistent and expected['initiator'] == 'external_fixed_policy'
                        and (not binder or expected['parameter_binding_source'] == 'INITIAL_EXTERNAL_POLICY')
                        and selection.get('source') == 'EXTERNAL_FIXED_POLICY'
                        and selection.get('uses_attempt_count') is False and selection.get('uses_unresolved') is False)
                    continue
                components = selection.get('score_components', {})
                valid = consistent and set(components) == set(selection.get('scores', {})) and bool(selection.get('policy_provenance'))
                for code, parts in components.items():
                    total = sum(parts[key]['value'] for key in ('initial_policy_component',
                        'internal_structure_component', 'temporary_evaluation_component'))
                    valid = valid and math.isclose(total, selection['scores'][code]) and math.isclose(
                        parts['final_score'], selection['scores'][code])
                action_checks.append(valid)
            elif kind == 'RECURSION_GENERATED':
                if p.get('layer') == 'L0':
                    generation_checks.append(p['requested_quantity'] == p['granted_quantity'] == 1
                        and p['source'] == 'EXTERNAL_FIXED_POLICY' and p['subsequent_quantity_adjustment'] is False)
                    continue
                decision = p.get('quantity_decision', {})
                resource = decision.get('resource_limit', {})
                selected = decision.get('current_internal_state', {}).get('selected_parameter', {})
                valid = bool(selected and decision.get('initial_policy_influence')) and (
                    p['granted_quantity'] == min(p['requested_quantity'], resource.get('available_after_eviction', -1)))
                generation_checks.append(valid)
                change = changes.get(selected.get('change_id'))
                if change and change['state_version'] < version:
                    provenance = change['payload']['metadata']['provenance']
                    integration = integrations.get(provenance['integration_id'])
                    inputs = [partials[x] for x in provenance['input_partial_ids'] if x in partials]
                    if integration and inputs and selected['value'] == change['payload']['after'] and (
                        change['payload']['before'] != change['payload']['after']):
                        linked.append({'past_evidence': provenance['trigger_reasons'],
                            'process_outputs': [{'event_sequence': r['event_sequence'],
                                'state_version': r['state_version'], 'partial_id': r['payload']['partial_id'],
                                'process_id': r['payload'].get('process_id'),
                                'publication_number': r['payload'].get('publication_number')} for r in inputs],
                            'integration_id': provenance['integration_id'],
                            'parameter_change': change, 'later_generation': record,
                            'source_migrated': selected['source'] == 'INTERNAL_VARIABLE_POLICY',
                            'fixed_rule_is_still_the_updater': selected['source'] == 'INITIAL_EXTERNAL_POLICY'})
        marker_rows = db.execute('SELECT COUNT(*),COUNT(DISTINCT individual_id),MIN(state_version),MAX(state_version) FROM states').fetchone()
        checks = {'one_marker_and_contiguous_versions': marker_rows == (last_version + 1, 1, 0, last_version),
                  'initialized_registry_recorded': counts['POLICY_REGISTRY_INITIALIZED'] + counts['POLICY_REGISTRY_INHERITED'] == 1,
                  'action_components_traceable': bool(action_checks) and all(action_checks),
                  'action_authorship_consistent': not attribution_errors,
                  'generation_three_inputs_traceable': bool(generation_checks) and all(generation_checks),
                  'internal_parameter_change_used_later': bool(linked),
                  'fixed_updates_not_falsely_promoted': all(
                      r['payload']['metadata']['source'] == 'INITIAL_EXTERNAL_POLICY'
                      for r in changes.values() if r['payload']['metadata']['value_origin'] == 'experience_triggered_external_policy')}
        sample = next((x for x in linked if x['parameter_change']['payload']['before'] == 2 and
                       x['parameter_change']['payload']['after'] == 3), linked[0] if linked else None)
        from .lifetime import history_summary
        return {**history_summary(database, db), 'audit_scope': 'lifetime',
                'tracking_available': True, 'individual_id': state['individual_id'],
                'last_state_version': last_version, 'counts': dict(counts), 'checks': checks,
                'boundary_checks_passed': all(value for key, value in checks.items() if key != 'internal_parameter_change_used_later'),
                'profile': internal.get('l0_state', {}).get('profile', 'legacy_policy_debug'),
                'formal_enabled_initial_policies': [key for key, r in registry.items()
                    if r['category']=='INITIAL_EXTERNAL_POLICY' and r.get('formal_path_enabled') is True],
                'formal_disabled_initial_policies': [key for key, r in registry.items()
                    if r['category']=='INITIAL_EXTERNAL_POLICY' and r.get('formal_path_enabled') is False],
                'source_categories': dict(Counter(r['category'] for r in registry.values())),
                'policy_migration_status': internal['policy_migration_status'],
                'linked_parameter_updates_used_later': len(linked),
                'verified_internal_policy_migrations': 0,
                'autonomous_policy_formation_proven': False,
                'action_decision_authors': dict(authors), 'action_attribution_errors': attribution_errors,
                'sample': sample,
                'note': 'Parameter changes and source migrations are measured separately from attribution validity. Formal mode disables legacy adaptation; remaining sampling is external policy.'}
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', help='Defaults to the selected individual lifetime')
    parser.add_argument('--output')
    args = parser.parse_args()
    if args.db is None:
        from .lifetime import resolve_runtime_database
        args.db = str(resolve_runtime_database())
    report = audit_policies(args.db)
    from .storage import save_report
    output = save_report(args.db, 'policy-audit', report, args.output)
    print(f'Report: {output}')
    print(json.dumps({key: value for key, value in report.items() if key not in ('sample', 'policy_migration_status')},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
