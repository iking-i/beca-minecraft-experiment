"""Reads only an immutable formed organization; never calls formation."""
from .model import Activation, Bind, Demand, Port, ReadResult, RequireBound, Transfer, Value


def consume(organization_handle, q):
    s = organization_handle
    unresolved = ReadResult("UNRESOLVED", q)
    if s is None or s.status != "COMPLETE_LOCAL_SUPPORT" or s.requirement.port != q:
        return unresolved
    proofs = {}
    for edge in s.supports:
        proofs.setdefault(edge.conclusion, set()).add(edge)
    ports = {f.identity: f for f in s.facts if isinstance(f, Port)}
    values = {f.identity: f for f in s.facts if isinstance(f, Value)}
    bindings = {}
    for f in s.facts:
        if isinstance(f, Bind):
            bindings.setdefault(f.port, set()).add(f)
    memo, visiting = {}, set()

    def valid(fact):
        if fact in memo:
            return memo[fact]
        if fact not in s.facts or fact in visiting:
            return False
        visiting.add(fact)
        accepted = False
        for e in proofs.get(fact, ()):
            expected = None
            if e.rule == "INPUT" and isinstance(fact, (Port, Value, Transfer, RequireBound, Bind)):
                expected = frozenset()
                if isinstance(fact, RequireBound) and fact != s.requirement:
                    continue
                if isinstance(fact, Bind):
                    p, v = ports.get(fact.port), values.get(fact.value)
                    if p is None or v is None or (p.type, p.scope) != (v.type, v.scope):
                        continue
                    if len(bindings[fact.port]) != 1 or not valid(p) or not valid(v):
                        continue
            elif e.rule == "ROOT" and fact == Demand(q):
                p = ports.get(q)
                if p and (p.type, p.scope) == (s.requirement.type, s.requirement.scope):
                    expected = frozenset((s.requirement, p))
            elif e.rule == "ACTIVATE" and isinstance(fact, Activation):
                r = fact.relation
                p = ports.get(r.output)
                if p:
                    expected = frozenset((Demand(r.output), r, p))
            elif e.rule == "INPUT_DEMAND" and isinstance(fact, Demand):
                activations = [p for p in e.premises if isinstance(p, Activation)]
                if len(activations) == 1 and activations[0].relation.input == fact.port:
                    p = ports.get(fact.port)
                    if p:
                        expected = frozenset((activations[0], p))
            elif e.rule == "TRANSFER" and isinstance(fact, Bind):
                activations = [p for p in e.premises if isinstance(p, Activation)]
                if len(activations) == 1:
                    a = activations[0]
                    r = a.relation
                    source = Bind(r.input, fact.value)
                    p, v = ports.get(fact.port), values.get(fact.value)
                    ip = ports.get(r.input)
                    if (r.output == fact.port and p and ip and v
                            and (p.type, p.scope) == (ip.type, ip.scope) == (v.type, v.scope)
                            and len(bindings.get(r.input, ())) == 1
                            and len(bindings.get(fact.port, ())) == 1 and valid(ip)):
                        expected = frozenset((a, r, source, p, v))
            if expected is not None and e.premises == expected and all(valid(p) for p in expected):
                accepted = True
        visiting.remove(fact)
        memo[fact] = accepted
        return accepted

    candidates = bindings.get(q, ())
    if len(candidates) != 1 or not valid(Demand(q)):
        return unresolved
    binding, = candidates
    return ReadResult("RESOLVED", q, binding.value) if valid(binding) else unresolved
