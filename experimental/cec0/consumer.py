"""TEST_ONLY consumer: formed direct Shared incidence only, no history argument."""
from dataclasses import dataclass, replace
from experimental.gsc0.model import Node, Relation, Witness, encode


@dataclass(frozen=True)
class Read:
    status: str
    endpoints: tuple
    record_keys: tuple
    witness_keys: tuple
    direct_supports: tuple
    root_witnesses: tuple
    endpoint_evidence: tuple = ()


def consume(organization, query):
    if organization.status != 'COMPLETE':
        return Read(organization.status, (), (), (), (), ())
    facts = {f.key: f for f in organization.facts}
    if facts.get(query.key) != query:
        raise ValueError('Exact query not in formed organization')
    if query.type_id == 'cec.query.control':
        match_port, result_port = 1, 2
    elif query.type_id == 'cec.query.consequence':
        match_port, result_port = 2, 1
    else:
        raise ValueError('Unknown query signature')
    values, records, witnesses, evidence = {}, set(), set(), {}
    for f in organization.facts:
        if not isinstance(f, Witness):
            continue
        for a, ai, b, bi in ((f.left_leaf, f.left_port, f.right_leaf, f.right_port),
                             (f.right_leaf, f.right_port, f.left_leaf, f.left_port)):
            r = facts.get(b)
            if a == query.key and ai == 0 and bi == match_port and isinstance(r, Relation) and r.type_id == 'cec.record':
                if r.ports[match_port] != query.ports[0]:
                    raise ValueError('Witness endpoints not exact identities')
                v = r.ports[result_port]
                if not isinstance(v, Node):
                    raise ValueError('Record endpoint not an opaque Node')
                values[v.key] = v; records.add(r.key); witnesses.add(f.key)
                evidence.setdefault(v.key, set()).add((r.key, f.key))
    supports, roots = dict(organization.supports), dict(organization.roots)
    used = records | witnesses | set(values)
    return Read('READ_ALL', tuple(values[k] for k in sorted(values, key=encode)),
                tuple(sorted(records, key=encode)), tuple(sorted(witnesses, key=encode)),
                tuple((k, supports[k]) for k in sorted(used, key=encode)),
                tuple((k, roots[k]) for k in sorted(used, key=encode)),
                tuple((k, tuple(sorted(evidence[k], key=encode))) for k in sorted(evidence, key=encode)))


def screen_witnesses(organization, keys):
    """Detached effect screen: retains input, Condition, sources, records and proofs."""
    keys = frozenset(keys)
    facts = {f.key: f for f in organization.facts}
    if any(not isinstance(facts.get(k), Witness) for k in keys):
        raise ValueError('Only formed Shared witnesses may be screened')
    return replace(organization, facts=tuple(f for f in organization.facts if f.key not in keys))
