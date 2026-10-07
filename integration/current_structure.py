"""Current-state FROI input adapter. EventStore is an external audit sink.

No history selection, eviction or reconstruction occurs here. Every outcome in
the already retained relation structure is represented, without weighting it.
The historical FROI codec remains available to explicit audit/test callers.
"""
from dataclasses import dataclass
from hashlib import sha256
import json

from experimental.gsc0.engine import Condition
from experimental.gsc0.model import Node, Variable, Value, Relation, Binding, Seed, encode
from integration.froi import (VERSION, SIGNATURES, EncodedInput, ReferenceOrigin,
                              OrganizationSession, canonical)

SOURCE_VERSION = 'FROI-CURRENT-STRUCTURE-1'


@dataclass(frozen=True)
class CurrentStructureSource:
    individual_id: str
    state_version: int
    event_cutoff: int  # Compatibility boundary token: state version, NOT an event scan.
    body_epoch: int
    structure_json: str
    version: str = SOURCE_VERSION

    @classmethod
    def capture(cls, state):
        internal = state.internal_state
        local = internal.get('l0_state', {})
        # These are current, retained objects. No EventStore connection is used.
        content = {'relations': internal.get('relations', {}),
                   'feedback': local.get('feedback', {}),
                   'integration': internal.get('latest_integration', {})}
        return cls(state.individual_id, state.state_version, state.state_version,
                   state.carrier_epoch, canonical(content))

    @property
    def source_id(self):
        return f'CURRENT_STATE:{self.individual_id}:A{self.state_version}'

    def origin(self, feedback):
        content = json.loads(self.structure_json)
        integration = content['integration']
        if (feedback != content['feedback'] or not feedback.get('partial_id')
                or feedback.get('integration_id') != integration.get('integration_id')):
            raise ValueError('Read does not originate in current retained feedback')
        experiences = integration.get('experience_ids', [])
        if len(experiences) != 1:
            raise ValueError('Current feedback has no unique experience provenance')
        return ReferenceOrigin(SOURCE_VERSION, self.body_epoch, experiences[0],
                               feedback['partial_id'], self.source_id)

    def encode_current(self, request):
        if (request.individual_id != self.individual_id
                or self.state_version >= request.source_state_version
                or request.origin != self.origin(json.loads(self.structure_json)['feedback'])):
            raise ValueError('Current-state read boundary mismatch')
        content = json.loads(self.structure_json)
        registry = {self.source_id: {'source': 'CURRENT_RETAINED_STRUCTURE',
                    'individual_id': self.individual_id, 'state_version': self.state_version,
                    'structure': content},
                    'RUNTIME_SOURCE': {'version': SOURCE_VERSION,
                     'external_history_loaded': False, 'cutoff_kind': 'state_version'}}
        nodes, values, seeds = {}, {}, []
        for key, record in content['relations'].items():
            if key != record['relation_id']:
                raise ValueError('Current relation identity mismatch')
            node = Node(key, namespace=VERSION, scope=request.scope)
            for outcome_key, outcome in record['outcomes'].items():
                if outcome_key != outcome['unit_id']:
                    raise ValueError('Current outcome identity mismatch')
                identity = sha256(canonical((key, outcome_key)).encode()).hexdigest()
                variable = Variable('current:' + identity, 'UnitRef', VERSION, request.scope)
                value = Value(outcome_key, 'UnitRef')
                relation = Relation('current:' + identity, 'froi.record', (node, variable),
                                    source=VERSION, scope=request.scope)
                source = self.source_id + ':relation:' + identity
                registry[source] = {'source_state': self.source_id,
                                    'relation_id': key, 'outcome_id': outcome_key}
                seeds.extend((Seed(relation, (source,)), Seed(Binding(variable, value), (source,))))
                nodes.update({node.key: node, variable.key: variable})
                values[value.key] = value
        read = request.relation
        nodes[read.ports[0].key] = read.ports[0]
        current = 'CURRENT_FRAME:' + request.frame['frame_id']
        reference = 'CURRENT_REFERENCE:' + request.origin.partial_id
        registry[current] = {'frame': request.frame, 'source_state_version': request.source_state_version}
        registry[reference] = {'reference': request.reference, 'origin': request.origin.__dict__}
        seeds.append(Seed(read, (current, reference)))
        condition = Condition(tuple(sorted(nodes.values(), key=lambda n: encode(n.key))),
                              tuple(sorted(values.values(), key=lambda v: encode(v.key))), SIGNATURES)
        for declaration in (*condition.nodes, *condition.values):
            registry['DECL:' + encode(declaration.key)] = {
                'source': 'EXTERNAL_FIXED_MECHANISM', 'codec': SOURCE_VERSION,
                'declaration': declaration.key}
        return EncodedInput(condition, tuple(seeds), canonical(registry))


def current_organization(store, state, caps):
    """Default live source; deliberately does not access store or its connection."""
    return OrganizationSession(CurrentStructureSource.capture(state), caps)
