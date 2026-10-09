"""Exact native interface addresses, not internal Units or action recipes."""
from copy import deepcopy

from individual.action_space import CATALOG_DATA, DEFINITIONS
from individual.formal_l0 import digest
from experimental.native_body_operands.engine import typed_inputs

VERSION = 'BODY-INTERFACE-REFERENCES-TEST_ONLY-1'
KEY = 'body_interface_references_test_only'


def observed_catalog(frame):
    entries = deepcopy(frame.nearby_data.get('body', {}).get('action_space', []))
    # Reuse native declaration fidelity validation, but do not install its
    # temporary descriptor values into InternalState.units.
    typed_inputs({'frame_id': frame.frame_id, 'namespace': frame.encoding_namespace,
                  'body_epoch': frame.body_epoch, 'declarations': entries,
                  'numeric_channels': {}, 'references': []})
    if {e['code'] for e in entries} != set(DEFINITIONS):
        raise ValueError('Complete observed native catalog required')
    fields = ('code', 'category', 'parameter_schema', 'environment_requirement_codes', 'formal_enabled')
    declarations = sorted(({k: deepcopy(e[k]) for k in fields} for e in entries), key=lambda e: e['code'])
    return {'version': CATALOG_DATA['version'], 'id': digest(declarations),
            'declarations': declarations, 'namespace': frame.encoding_namespace,
            'body_epoch': frame.body_epoch}


def body_ref(catalog, kind, code, slot=None):
    ref = {'type': 'BodyRef', 'catalog_id': catalog['id'], 'catalog_version': catalog['version'],
           'namespace': catalog['namespace'], 'body_epoch': catalog['body_epoch'],
           'kind': kind, 'code': code}
    if slot is not None:
        ref['slot'] = slot
    resolve_body(catalog, ref)
    return ref


def resolve_body(catalog, ref):
    if not isinstance(catalog, dict) or not isinstance(ref, dict):
        raise ValueError('Missing observed catalog/reference')
    kind = ref.get('kind')
    keys = {'type', 'catalog_id', 'catalog_version', 'namespace', 'body_epoch', 'kind', 'code'}
    if kind in ('slot', 'domain'):
        keys.add('slot')
    if (set(ref) != keys or ref['type'] != 'BodyRef' or kind not in ('port', 'slot', 'domain')
            or type(ref['code']) is not int or type(ref['catalog_version']) is not int
            or type(ref['body_epoch']) is not int
            or any(ref[k] != catalog[v] for k, v in (
                ('catalog_id', 'id'), ('catalog_version', 'version'),
                ('namespace', 'namespace'), ('body_epoch', 'body_epoch')))):
        raise ValueError('Invalid or foreign body reference')
    entries = [e for e in catalog['declarations'] if e['code'] == ref['code']]
    if len(entries) != 1:
        raise ValueError('Unobserved native port')
    entry = entries[0]
    if kind == 'port':
        return {'type': 'NativePort', 'catalog_version': catalog['version'], 'code': ref['code']}
    name = ref['slot']
    schema = entry['parameter_schema']
    if type(name) is not str or name not in schema['properties']:
        raise ValueError('Undeclared native slot/domain')
    if kind == 'domain':
        return {'type': 'ParameterDomain', 'schema': deepcopy(schema['properties'][name])}
    return {'type': 'ParameterSlot', 'name': name,
            'port': body_ref(catalog, 'port', ref['code']),
            'domain': body_ref(catalog, 'domain', ref['code'], name),
            'required': name in schema['required']}


def resolve(internal, ref):
    if isinstance(ref, dict) and set(ref) == {'type', 'unit'} and ref['type'] == 'UnitRef':
        if type(ref['unit']) is not str or ref['unit'] not in internal.units:
            raise ValueError('Missing UnitRef endpoint')
        unit = internal.units[ref['unit']]
        if unit.get('unit_id') != ref['unit']:
            raise ValueError('UnitRef identity mismatch')
        node = unit['pattern']
        if isinstance(node, dict) and node.get('type') == 'ObservedReference':
            pool = internal.l0_state[KEY]
            source = pool['current_source']
            if (source is None or node['namespace'] != source['namespace']
                    or node['body_epoch'] != source['body_epoch']
                    or {'kind': node['kind'], 'token': node['token']} not in source['references']):
                raise ValueError('Stale observation reference')
        return deepcopy(node)
    return resolve_body(internal.l0_state[KEY]['catalog'], ref)


def validate_catalog(catalog):
    if catalog is None:
        return
    if (not isinstance(catalog, dict) or set(catalog) != {'version', 'id', 'declarations', 'namespace', 'body_epoch'}
            or type(catalog['version']) is not int or catalog['version'] != CATALOG_DATA['version']
            or type(catalog['namespace']) is not str or not catalog['namespace']
            or type(catalog['body_epoch']) is not int or catalog['body_epoch'] < 0):
        raise ValueError('Invalid interface catalog')
    from individual.observation import ObservationFrame
    entries = [{**e, 'currently_available': True} for e in catalog['declarations']]
    frame = ObservationFrame('catalog-check', 0, 'audit', catalog['namespace'], catalog['body_epoch'],
                             {}, {}, {'body': {'action_space': entries}}, {}, {})
    if observed_catalog(frame) != catalog:
        raise ValueError('Catalog identity/content mismatch')
