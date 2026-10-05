"""TEST_ONLY finite least fixed point. No production runtime dependencies.

COMPOSE supports use a lossless finite join index: all connected support masks
and all incidence witnesses. Every direct proof is enumerable, not first-proof
memoization. This represents an enormous finite graph without expanding trees.
"""
from dataclasses import dataclass, field
from itertools import combinations, combinations_with_replacement
from hashlib import sha256
from .model import (Node, Variable, Value, Reference, Relation, Equality, Binding,
                    PortBinding, Conflict, Composite, Change, Seed, Support,
                    Witness, encode, incidence)

RULES = ("ALIGN-REFL", "ALIGN-SYM", "ALIGN-TRANS", "PROP-ALIAS", "PROP-PORT", "CONFLICT")
LEAF_TYPES = (Relation, Equality, Binding, PortBinding, Conflict, Change)


@dataclass(frozen=True)
class Caps:
    structures: int = 200000
    provenance_entries: int = 200000
    workspace_items: int = 300000
    operations: int = 20000000
    rounds: int = 100
    nodes: int = 16
    values: int = 16
    relation_types: int = 16
    inputs: int = 64

    def __post_init__(self):
        if any(type(v) is not int or v < 1 for v in self.__dict__.values()):
            raise ValueError("Caps must be positive exact integers")


@dataclass(frozen=True)
class Condition:
    nodes: tuple
    values: tuple
    signatures: tuple  # (opaque type_id, tuple of node/variable/reference/value port types)
    references: tuple = ()
    version: str = "GSC-0-TEST_ONLY-v1"


@dataclass
class State:
    condition: Condition
    facts: dict = field(default_factory=dict)
    proofs: dict = field(default_factory=dict)
    roots: set = field(default_factory=set)
    composition: object | None = None
    input_records: set = field(default_factory=set)

    def clone(self):
        return State(self.condition, dict(self.facts), {k: set(v) for k, v in self.proofs.items()},
                     set(self.roots), self.composition, set(self.input_records))

    def canonical_digest(self):
        digest = sha256()
        for key in sorted(self.facts, key=encode):
            digest.update(encode((key, repr(self.facts[key]))).encode())
            for support in sorted(self.proofs.get(key, ()), key=lambda p: (p.rule, encode(p.premises))):
                digest.update(encode((support.rule, support.premises)).encode())
        digest.update(encode(sorted(self.roots, key=encode)).encode())
        digest.update(encode(sorted(self.input_records, key=encode)).encode())
        if self.composition:
            digest.update(self.composition.digest().encode())
        return digest.hexdigest()

    def direct_supports(self, key):
        yield from self.proofs.get(key, ())
        if key[0] == "Composite" and self.composition:
            yield from self.composition.for_conclusion(key)

    def root_witnesses(self):
        """Least positive root reachability, retaining all roots even in cyclic graphs."""
        roots = {key: {key} for key in self.roots}
        while True:
            changed = False
            for key, proofs in self.proofs.items():
                for proof in proofs:
                    if all(p in roots for p in proof.premises):
                        sources = set().union(*(roots[p] for p in proof.premises))
                        target = roots.setdefault(key, set())
                        if not sources <= target:
                            target.update(sources)
                            changed = True
            if not changed:
                break
        if self.composition:
            for mask in self.composition.masks:
                if mask.bit_count() < 2:
                    continue
                key = self.composition.support_key(mask)
                members = self.composition.member_keys(mask)
                sources = set().union(*(roots.get(p, set()) for p in members))
                for w, a, b in self.composition.index:
                    if (mask & a) and (mask & b):
                        sources.update(roots.get(w.key, set()))
                roots[key] = sources
        return roots


class CompositionIndex:
    """Finite complete COMPOSE predicate, with exact proof/edge cardinalities."""
    def __init__(self, leaves, masks, witnesses):
        self.leaves = tuple(leaves)
        self.masks = frozenset(masks)
        positions = {key: 1 << i for i, key in enumerate(leaves)}
        self.index = tuple(sorted(((w, positions[w.left_leaf], positions[w.right_leaf]) for w in witnesses),
                                  key=lambda x: encode(x[0].key)))

    def member_keys(self, mask):
        return tuple(key for i, key in enumerate(self.leaves) if mask & (1 << i))

    def support_key(self, mask):
        members = self.member_keys(mask)
        return members[0] if len(members) == 1 else Composite(members).key

    def digest(self):
        return sha256(encode((self.leaves, sorted(self.masks), [w.key for w, _, _ in self.index])).encode()).hexdigest()

    def shared(self, key):
        members = set(key[1])
        return tuple(w for w, _, _ in self.index if w.left_leaf in members and w.right_leaf in members)

    def for_conclusion(self, key):
        members = set(key[1])
        mask = sum(1 << i for i, leaf in enumerate(self.leaves) if leaf in members)
        if mask not in self.masks or len(members) != mask.bit_count():
            return
        operands = sorted(m for m in self.masks if m & mask == m)
        for s, t in combinations_with_replacement(operands, 2):
            if s | t != mask:
                continue
            for w, a, b in self.index:
                if (s & a and t & b) or (s & b and t & a):
                    yield Support("COMPOSE", (self.support_key(s), self.support_key(t), w.key))

    def counts(self):
        membership = [{m for m in self.masks if m & (1 << i)} for i in range(len(self.leaves))]
        instances = self_instances = 0
        for _, a, b in self.index:
            left, right = membership[a.bit_length() - 1], membership[b.bit_length() - 1]
            overlap = len(left & right)
            if a == b:
                n = len(left)
                instances += n * (n + 1) // 2 - 1  # exclude singleton union
                self_instances += n - 1
            else:
                instances += len(left) * len(right) - overlap * (overlap - 1) // 2
                self_instances += overlap
        return instances, 3 * instances - self_instances


@dataclass
class Result:
    status: str
    state: State
    closure_rounds: int
    operations: int
    limit: dict | None = None
    pending: tuple = ()

    @property
    def closure_complete(self):
        return self.status == "COMPLETE"

    def stats(self):
        explicit = [(key, p) for key, proofs in self.state.proofs.items() for p in proofs]
        compose, edges = self.state.composition.counts() if self.state.composition else (0, 0)
        return {"status": self.status, "closure_complete": self.closure_complete,
                "leaf_count": sum(isinstance(x, LEAF_TYPES) for x in self.state.facts.values()),
                "composite_count": sum(isinstance(x, Composite) for x in self.state.facts.values()),
                "rule_instance_count": len(explicit) + compose,
                "lineage_edge_count": sum(len(p.premises) for _, p in explicit) + edges,
                "closure_rounds": self.closure_rounds,
                "stored_support_index_entries": len(explicit) + (len(self.state.composition.masks) + len(self.state.composition.index) if self.state.composition else 0),
                "operations": self.operations}


class ResourceStop(Exception):
    def __init__(self, resource, used, cap, requested):
        self.resource, self.used, self.cap, self.requested = resource, used, cap, requested


class Engine:
    def __init__(self, condition, caps=None, rule_order=RULES, queue_order="forward"):
        if set(rule_order) != set(RULES) or len(rule_order) != len(RULES):
            raise ValueError("Every structural rule must be processed")
        if queue_order not in ("forward", "reverse", "interleaved"):
            raise ValueError("Unknown exhaustive scheduling order")
        self.condition, self.caps, self.rule_order, self.queue_order = condition, caps or Caps(), tuple(rule_order), queue_order
        self.operations = self.rounds = 0

    def ordered(self, values):
        values = list(values)
        return values[::-1] if self.queue_order == "reverse" else values[::2] + values[1::2] if self.queue_order == "interleaved" else values

    def round(self):
        self.rounds += 1
        if self.rounds > self.caps.rounds:
            raise ResourceStop("rounds", self.rounds - 1, self.caps.rounds, self.rounds)

    def subsets(self, length, size):
        # Change exhaustive enumeration order without allocating a combination
        # queue outside the workspace budget.
        indices = self.ordered(range(length))
        return combinations(indices, size)

    def charge(self):
        self.operations += 1
        if self.operations > self.caps.operations:
            raise ResourceStop("operations", self.operations - 1, self.caps.operations, self.operations)

    def check(self, state, workspace=0, factor_entries=None):
        if factor_entries is None:
            factor_entries = (len(state.composition.masks) + len(state.composition.index)) if state.composition else 0
        for label, used, cap in (("structures", len(state.facts), self.caps.structures),
                                 ("provenance_entries", sum(map(len, state.proofs.values())) + factor_entries, self.caps.provenance_entries),
                                 ("workspace_items", workspace, self.caps.workspace_items)):
            if used > cap:
                raise ResourceStop(label, 0, cap, used)

    def validate(self, fact):
        nodes = {n.key: n for n in self.condition.nodes}
        values = set(self.condition.values)
        references = {r.key: r for r in self.condition.references}
        def node(n):
            if nodes.get(n.key) != n:
                raise ValueError("Undeclared or incompatible exact node identity")
        def value(v):
            if v not in values:
                raise ValueError("Value outside the declared finite domain")
        if isinstance(fact, (Node, Variable)):
            node(fact)
        elif isinstance(fact, Value):
            value(fact)
        elif isinstance(fact, Reference):
            if references.get(fact.key) != fact:
                raise ValueError("Unknown exact reference; no rebinding")
            node(fact.target)
        elif isinstance(fact, Relation):
            signatures = dict(self.condition.signatures)
            sig = signatures.get(fact.type_id)
            if sig is None or len(sig) != len(fact.ports):
                raise ValueError("Relation signature mismatch")
            for expected, p in zip(sig, fact.ports):
                ok = {"node": isinstance(p, (Node, Variable, Reference)), "variable": isinstance(p, Variable),
                      "reference": isinstance(p, Reference), "value": isinstance(p, Value)}.get(expected, False)
                if not ok:
                    raise ValueError("Relation port type mismatch")
                self.validate(p)
        elif isinstance(fact, Equality):
            node(fact.left); node(fact.right)
            a, b = fact.left, fact.right
            if type(a) is not type(b) or a.namespace != b.namespace or a.scope != b.scope:
                raise ValueError("Equality crosses roles/namespace/scope")
            if isinstance(a, Variable) and a.value_type != b.value_type:
                raise ValueError("Equality crosses variable types")
            if isinstance(a, Node) and a.kind != b.kind:
                raise ValueError("Equality crosses node kinds")
        elif isinstance(fact, (Binding, PortBinding, Conflict)):
            node(fact.variable)
            if not isinstance(fact.variable, Variable):
                raise ValueError("Binding needs a variable")
            vs = fact.values if isinstance(fact, Conflict) else (fact.value,)
            for v in vs:
                value(v)
                if v.value_type != fact.variable.value_type:
                    raise ValueError("Binding value type mismatch")
            if isinstance(fact, PortBinding):
                self.validate(fact.relation)
                if not 0 <= fact.port < len(fact.relation.ports):
                    raise ValueError("Invalid port")
                target = fact.relation.ports[fact.port]
                target = target.target if isinstance(target, Reference) else target
                if target != fact.variable:
                    raise ValueError("Port binding does not match its declared variable")
        elif not isinstance(fact, Change):
            raise ValueError("Unknown input structure")

    def consequences(self, state):
        nodes = [f for f in state.facts.values() if isinstance(f, (Node, Variable))]
        eqs = [f for f in state.facts.values() if isinstance(f, Equality)]
        binds = [f for f in state.facts.values() if isinstance(f, Binding)]
        relations = [f for f in state.facts.values() if isinstance(f, Relation)]
        for rule in self.rule_order:
            if rule == "ALIGN-REFL":
                for n in self.ordered(nodes):
                    self.charge(); yield Equality(n, n), Support(rule, (n.key,))
            elif rule == "ALIGN-SYM":
                for e in self.ordered(eqs):
                    self.charge(); yield Equality(e.right, e.left), Support(rule, (e.key,))
            elif rule == "ALIGN-TRANS":
                for a in self.ordered(eqs):
                    for b in self.ordered(eqs):
                        self.charge()
                        if a.right == b.left:
                            yield Equality(a.left, b.right), Support(rule, (a.key, b.key))
            elif rule == "PROP-ALIAS":
                for b in self.ordered(binds):
                    for e in self.ordered(eqs):
                        self.charge()
                        if b.variable == e.left:
                            yield Binding(e.right, b.value), Support(rule, (b.key, e.key))
            elif rule == "PROP-PORT":
                for r in self.ordered(relations):
                    for i, n in incidence(r):
                        for b in self.ordered(binds):
                            self.charge()
                            if n == b.variable:
                                premises = (r.key, b.key) + ((r.ports[i].key,) if isinstance(r.ports[i], Reference) else ())
                                yield PortBinding(r, i, n, b.value), Support(rule, premises)
            else:
                for a, b in combinations(self.ordered(binds), 2):
                    self.charge()
                    if a.variable == b.variable and a.value != b.value:
                        yield Conflict(a.variable, (a.value, b.value)), Support(rule, (a.key, b.key))

    def run(self, seeds=(), previous=None):
        self.operations = self.rounds = 0
        state = previous.clone() if previous else State(self.condition)
        if state.condition != self.condition:
            raise ValueError("Cannot change a closure's condition")
        pending = tuple(seeds)
        phase = "input"
        try:
            for label, used, cap in (("nodes", len(self.condition.nodes), self.caps.nodes),
                                     ("values", len(self.condition.values), self.caps.values),
                                     ("relation_types", len(self.condition.signatures), self.caps.relation_types),
                                     ("inputs", len(state.input_records | {(s.fact.key, s.sources, s.rule) for s in pending}), self.caps.inputs)):
                if used > cap:
                    raise ResourceStop(label, 0, cap, used)
            declarations = (*self.condition.nodes, *self.condition.values, *self.condition.references)
            declared = {}
            for d in declarations:
                if d.key in declared and declared[d.key] != d:
                    raise ValueError("Conflicting declarations of one identity")
                declared[d.key] = d
                for label in d.key[:5]:
                    if isinstance(label, str) and len(label.encode('utf-8')) > 256:
                        raise ValueError("Identity token exceeds the declared encoding bound")
            if len(dict(self.condition.signatures)) != len(self.condition.signatures):
                raise ValueError("Duplicate relation type declaration")
            anchors = {}
            for ref in self.condition.references:
                if ref.anchor in anchors and anchors[ref.anchor] != ref.target:
                    raise ValueError("Same reference identity with different target")
                anchors[ref.anchor] = ref.target
            batch = state.clone()
            for seed in (*[Seed(d, ("DECL:" + encode(d.key),)) for d in declarations], *pending):
                self.validate(seed.fact)
                if seed.fact.key in batch.facts and batch.facts[seed.fact.key] != seed.fact:
                    raise ValueError("Same identity with conflicting content")
                batch.facts[seed.fact.key] = seed.fact
                roots = tuple(("Root", s) for s in seed.sources)
                if not roots:
                    raise ValueError("Every input must have root provenance")
                batch.roots.update(roots)
                batch.proofs.setdefault(seed.fact.key, set()).add(Support(seed.rule, roots))
            batch.input_records.update((s.fact.key, s.sources, s.rule) for s in pending)
            self.check(batch, len(batch.facts))
            state = batch
            phase = "alignment-propagation-conflict"
            # COMPOSE never produces bindings/equalities/business relations. Thus
            # stratification is exhaustive, not semantic pruning or rule priority.
            while True:
                self.round()
                batch = state.clone()
                for fact, proof in self.consequences(state):
                    batch.facts[fact.key] = fact
                    batch.proofs.setdefault(fact.key, set()).add(proof)
                    self.check(batch, len(batch.facts) + sum(map(len, batch.proofs.values())))
                if batch.facts == state.facts and batch.proofs == state.proofs:
                    break
                state = batch
            phase = "shared-incidence"
            leaves = tuple(sorted((key for key, f in state.facts.items() if isinstance(f, LEAF_TYPES)), key=encode))
            eqs = {f.key for f in state.facts.values() if isinstance(f, Equality)}
            ports = [(key, i, n) for key in leaves for i, n in incidence(state.facts[key])]
            witnesses = {}
            batch = state.clone()
            for a, b in combinations_with_replacement(ports, 2):
                self.charge()
                w = Witness(a[0], a[1], b[0], b[1])
                for e in (Equality(a[2], b[2]), Equality(b[2], a[2])):
                    if e.key in eqs:
                        witnesses[w.key] = w
                        batch.facts[w.key] = w
                        batch.proofs.setdefault(w.key, set()).add(Support("SHARED", (a[0], b[0], e.key)))
                        self.check(batch, len(batch.facts) + sum(map(len, batch.proofs.values())))
            state = batch
            phase = "composition"
            adjacency = [0] * len(leaves)
            position = {key: i for i, key in enumerate(leaves)}
            for w in witnesses.values():
                i, j = position[w.left_leaf], position[w.right_leaf]
                adjacency[i] |= 1 << j; adjacency[j] |= 1 << i
            masks = {1 << i for i in range(len(leaves))}
            masks.update(sum(1 << position[leaf] for leaf in f.members)
                         for f in state.facts.values() if isinstance(f, Composite))
            # Enumerate every subset; use connectivity only as COMPOSE's exact
            # structural precondition. No output subsets are ranked or discarded.
            for size in range(2, len(leaves) + 1):
                batch = state.clone()
                new_masks = set()
                for subset in self.subsets(len(leaves), size):
                    self.charge()
                    mask = sum(1 << i for i in subset)
                    seen = 1 << subset[0]
                    while True:
                        grown = seen
                        for i in subset:
                            if seen & (1 << i):
                                grown |= adjacency[i] & mask
                        if grown == seen:
                            break
                        seen = grown
                    if seen == mask:
                        composite = Composite(tuple(leaves[i] for i in subset))
                        batch.facts[composite.key] = composite
                        new_masks.add(mask)
                        self.check(batch, len(new_masks) + len(batch.facts), len(masks) + len(new_masks) + len(witnesses))
                self.round()
                masks.update(new_masks)
                batch.composition = CompositionIndex(leaves, masks, witnesses.values())
                state = batch
            phase = "provenance-closure"
            state.composition = CompositionIndex(leaves, masks, witnesses.values())
            self.check(state, len(masks) + len(witnesses), len(masks) + len(witnesses))
            self.round()
            return Result("COMPLETE", state, self.rounds, self.operations)
        except ResourceStop as error:
            # Only fully committed phase/size batches are exposed. The failed
            # delta and pending inputs are never relabeled as a successful closure.
            committed_used = error.used
            if error.resource == "structures":
                committed_used = len(state.facts)
            elif error.resource == "provenance_entries":
                committed_used = sum(map(len, state.proofs.values()))
                if state.composition:
                    committed_used += len(state.composition.masks) + len(state.composition.index)
            return Result("RESOURCE_LIMIT", state, self.rounds, self.operations,
                          {"phase": phase, "resource_port": error.resource, "used": committed_used,
                           "capacity": error.cap, "requested_or_lower_bound": error.requested,
                           "closure_complete": False, "rule_version": self.condition.version}, pending)
