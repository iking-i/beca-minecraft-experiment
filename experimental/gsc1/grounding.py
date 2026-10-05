"""Read-only exact binding cardinality check. No inference or output execution."""
from experimental.gsc0.engine import Result
from experimental.gsc0.model import Variable, Binding, encode
from .model import (OutputPort, OutwardSchema, BindingEvidence, PortAssessment,
                    GroundedOutwardStructure, GroundingResult)


def check_grounding(closure, schema):
    if not isinstance(closure, Result):
        return GroundingResult('INVALID', reason='Expected a GSC-0 Result')
    if not closure.closure_complete:
        status = 'RESOURCE_LIMIT' if closure.status == 'RESOURCE_LIMIT' else 'INVALID'
        return GroundingResult(status, reason='Upstream closure is not COMPLETE')
    if not isinstance(schema, OutwardSchema) or not schema.name or not schema.ports:
        return GroundingResult('INVALID', reason='Required nonempty typed schema')
    if any(not isinstance(p, OutputPort) or not isinstance(p.variable, Variable)
           or not p.name or p.value_type != p.variable.value_type for p in schema.ports):
        return GroundingResult('INVALID', reason='Invalid output port declaration')
    if len({p.name for p in schema.ports}) != len(schema.ports):
        return GroundingResult('INVALID', reason='Duplicate output port name')
    state = closure.state
    declared = {v.key: v for v in state.condition.nodes}
    if any(declared.get(p.variable.key) != p.variable or
           state.facts.get(p.variable.key) != p.variable for p in schema.ports):
        return GroundingResult('INVALID', reason='Port is not an exactly declared ordinary variable')
    assessments = []
    roots = state.root_witnesses()
    for port in schema.ports:
        bindings = {}
        for fact in state.facts.values():
            if isinstance(fact, Binding) and fact.variable.key == port.variable.key:
                if (fact.variable != port.variable or fact.value.value_type != port.value_type
                        or fact.value not in state.condition.values):
                    return GroundingResult('INVALID', reason='Malformed upstream binding')
                bindings[fact.value.key] = fact
        # Canonical serialization of ALL bindings, never a retention order.
        ordered = tuple(bindings[k] for k in sorted(bindings, key=encode))
        values = tuple(b.value for b in ordered)
        evidence = tuple(BindingEvidence(
            b.key, tuple(sorted(state.direct_supports(b.key), key=lambda s: (s.rule, encode(s.premises)))),
            frozenset(roots.get(b.key, ()))) for b in ordered)
        if any(not e.input_roots or not e.direct_supports for e in evidence):
            return GroundingResult('INVALID', reason='Binding lacks input-rooted lineage')
        status = 'UNRESOLVED' if len(values) == 0 else 'GROUNDED' if len(values) == 1 else 'CONFLICT'
        assessments.append(PortAssessment(port.name, status, values, evidence))
    digest = state.canonical_digest()
    ports = tuple(assessments)
    if any(p.status == 'CONFLICT' for p in ports):
        return GroundingResult('CONFLICT', ports, closure_digest=digest)
    if any(p.status == 'UNRESOLVED' for p in ports):
        return GroundingResult('UNRESOLVED', ports, closure_digest=digest)
    fields = []
    for port in ports:
        (unique_value,) = port.values  # Unpack a proved singleton, never pick among values.
        fields.append((port.name, unique_value))
    outward = GroundedOutwardStructure(schema.key, tuple(fields))
    return GroundingResult('COMPLETE_GROUNDED', ports, outward, digest)
