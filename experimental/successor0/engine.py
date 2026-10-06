"""Exact requirement-rooted activation; no composition or candidate selection."""
from collections import defaultdict, deque
from .model import (Activation, ActivatedSupport, Bind, Demand, Formation, Port,
                    RequireBound, SupportEdge, Transfer, Value)


def form(history, requirement=None):
    # Registration/validation may scan all input. It performs no propagation.
    history = frozenset(history)
    ports, values = {}, {}
    producers, bindings = defaultdict(set), defaultdict(set)
    try:
        for fact in history:
            if isinstance(fact, (Port, Value)):
                table = ports if isinstance(fact, Port) else values
                if fact.identity in table and table[fact.identity] != fact:
                    raise ValueError("inconsistent declaration")
                table[fact.identity] = fact
            elif not isinstance(fact, (Bind, Transfer)):
                raise ValueError("unsupported history fact")
        def compatible(p, v):
            return (p.type, p.scope) == (v.type, v.scope)
        adjacency, indegree = defaultdict(set), dict.fromkeys(ports, 0)
        for fact in history:
            if isinstance(fact, Bind):
                if not compatible(ports[fact.port], values[fact.value]):
                    raise ValueError("invalid seed binding")
                bindings[fact.port].add(fact)
            elif isinstance(fact, Transfer):
                a, b = ports[fact.input], ports[fact.output]
                if (a.type, a.scope) != (b.type, b.scope):
                    raise ValueError("invalid Transfer type/scope")
                producers[fact.output].add(fact)
                if fact.output not in adjacency[fact.input]:
                    adjacency[fact.input].add(fact.output)
                    indegree[fact.output] += 1
        queue = deque(p for p, degree in indegree.items() if degree == 0)
        visited = 0
        while queue:
            p = queue.popleft()
            visited += 1
            for target in adjacency[p]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
        if visited != len(ports):
            raise ValueError("cyclic fixture outside frozen scope")
        if requirement is not None:
            if not isinstance(requirement, RequireBound):
                raise ValueError("invalid requirement")
            p = ports[requirement.port]
            if (p.type, p.scope) != (requirement.type, requirement.scope):
                raise ValueError("invalid requirement type/scope")
    except (KeyError, ValueError) as exc:
        return Formation("INVALID_FIXTURE", None, (), str(exc))
    if requirement is None:
        return Formation("NO_REQUIREMENT", None, ())

    facts, edges, trace = set(), set(), []
    def add(fact, rule, *premises):
        facts.add(fact)
        edges.add(SupportEdge(fact, rule, frozenset(premises)))
    def leaf(fact):
        add(fact, "INPUT")
    def materialize_binding(binding):
        leaf(ports[binding.port])
        leaf(values[binding.value])
        if binding in history:
            leaf(binding)
    leaf(requirement)
    leaf(ports[requirement.port])
    add(Demand(requirement.port), "ROOT", requirement, ports[requirement.port])
    invalid = []

    def resolve(p):
        current = bindings[p]
        if len(current) > 1:
            for binding in current:
                materialize_binding(binding)
            trace.append(("CONFLICT", p))
            return False
        if len(current) == 1:
            binding, = current
            materialize_binding(binding)
            return True
        candidates = producers[p]
        trace.append(("LOOKUP", p, len(candidates)))
        if len(candidates) > 1:
            invalid.append(p)
            return False
        if not candidates:
            trace.append(("GAP", p))
            return False
        relation, = candidates  # Cardinality already checked; never choose a producer.
        leaf(relation)
        leaf(ports[relation.input])
        leaf(ports[relation.output])
        active = Activation(relation)
        add(active, "ACTIVATE", Demand(p), relation, ports[p])
        trace.append(("ACTIVATE", relation))
        if not bindings[relation.input]:
            add(Demand(relation.input), "INPUT_DEMAND", active, ports[relation.input])
        if not resolve(relation.input):
            return False
        source, = bindings[relation.input]
        result = Bind(p, source.value)
        leaf(values[result.value])
        add(result, "TRANSFER", active, relation, source, ports[p], values[result.value])
        bindings[p].add(result)
        trace.append(("DERIVE", result))
        return True

    try:
        resolved = resolve(requirement.port)
        status = ("INVALID_FIXTURE" if invalid else
                  "COMPLETE_LOCAL_SUPPORT" if resolved else "UNRESOLVED")
    except RecursionError:
        status = "RESOURCE_LIMIT"
    organization = ActivatedSupport(requirement, status, frozenset(facts), frozenset(edges))
    return Formation(status, organization, tuple(trace),
                     "multiple producers" if invalid else None)


def counts(formation):
    s = formation.organization
    return {"activated_relation_count": sum(isinstance(x, Activation) for x in s.facts) if s else 0,
            "derived_binding_count": sum(e.rule == "TRANSFER" for e in s.supports) if s else 0,
            "formed_support_count": sum(e.rule != "INPUT" for e in s.supports) if s else 0}
