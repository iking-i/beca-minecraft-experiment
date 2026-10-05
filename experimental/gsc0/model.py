"""Immutable typed objects. Keys encode content, never traversal order or proofs."""
from dataclasses import dataclass
import json


def encode(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


@dataclass(frozen=True)
class Node:
    name: str
    namespace: str = "fixture"
    scope: str = "q"
    kind: str = "node"

    @property
    def key(self):
        return ("Node", self.namespace, self.scope, self.kind, self.name)


@dataclass(frozen=True)
class Variable:
    name: str
    value_type: str = "Int"
    namespace: str = "fixture"
    scope: str = "q"

    @property
    def key(self):
        return ("Node", self.namespace, self.scope, "variable", self.name)


@dataclass(frozen=True)
class Value:
    value: int | str
    value_type: str = "Int"

    def __post_init__(self):
        if self.value_type == "Int" and type(self.value) is not int:
            raise ValueError("Int requires an exact integer, excluding bool/float")
        if self.value_type != "Int" and type(self.value) is not str:
            raise ValueError("Other finite value types require exact strings")

    @property
    def key(self):
        return ("Value", self.value_type, self.value)


@dataclass(frozen=True)
class Reference:
    token: str
    target: Node | Variable
    issuer: str = "fixture"
    epoch: str = "q"

    @property
    def anchor(self):
        return (self.issuer, self.epoch, self.token)

    @property
    def key(self):
        return ("Reference", *self.anchor, self.target.key)


@dataclass(frozen=True)
class Relation:
    name: str
    type_id: str
    ports: tuple
    source: str = "fixture"
    scope: str = "q"

    @property
    def key(self):
        return ("Relation", self.source, self.scope, self.name)


@dataclass(frozen=True)
class Equality:
    left: Node | Variable
    right: Node | Variable

    @property
    def key(self):
        return ("Eq", self.left.key, self.right.key)


@dataclass(frozen=True)
class Binding:
    variable: Variable
    value: Value

    @property
    def key(self):
        return ("Bind", self.variable.key, self.value.key)


@dataclass(frozen=True)
class PortBinding:
    relation: Relation
    port: int
    variable: Variable
    value: Value

    @property
    def key(self):
        return ("PortBind", self.relation.key, self.port, self.variable.key, self.value.key)


@dataclass(frozen=True)
class Conflict:
    variable: Variable
    values: tuple[Value, Value]

    def __post_init__(self):
        if len(self.values) != 2 or self.values[0] == self.values[1]:
            raise ValueError("Conflict requires two distinct values")
        object.__setattr__(self, "values", tuple(sorted(self.values, key=lambda v: encode(v.key))))

    @property
    def key(self):
        return ("Conflict", self.variable.key, tuple(v.key for v in self.values))


@dataclass(frozen=True)
class Composite:
    members: tuple

    def __post_init__(self):
        flat = set()
        for member in self.members:
            if isinstance(member, Composite):
                flat.update(member.members)
            else:
                key = member.key if hasattr(member, "key") else member
                if not isinstance(key, tuple) or key[0] == "Composite":
                    raise ValueError("Nested canonical keys must be expanded explicitly")
                flat.add(key)
        if len(flat) < 2:
            raise ValueError("Composite requires at least two distinct leaves")
        object.__setattr__(self, "members", tuple(sorted(flat, key=encode)))

    @property
    def key(self):
        return ("Composite", self.members)


@dataclass(frozen=True)
class Change:
    observation_pair: tuple[str, str]
    channel: str
    kind: str
    before: tuple | None
    after: tuple | None

    @property
    def key(self):
        return ("Difference", self.observation_pair, self.channel, self.kind, self.before, self.after)


@dataclass(frozen=True)
class Seed:
    fact: object
    sources: tuple[str, ...]
    rule: str = "INPUT"


@dataclass(frozen=True)
class Observation:
    identity: str
    records: tuple[tuple[str, object, str], ...]
    complete_coverage: bool = True


def difference(before, after):
    """Exact record comparison; no deletion, target substitution, or value judgment."""
    def records(observation):
        result = {}
        for channel, fact, source in observation.records:
            if channel in result:
                raise ValueError("Duplicate observation channel")
            result[channel] = (fact, source)
        return result
    old, new = records(before), records(after)
    seeds = []
    for channel in sorted(old.keys() | new.keys()):
        a, b = old.get(channel), new.get(channel)
        if a and b and a[0] == b[0]:
            if a[1] != b[1]:
                seeds.append(Seed(b[0], (b[1],), "OBSERVED"))
            continue
        kind = "Appeared" if a is None else "Changed" if b else "Removed" if after.complete_coverage else "Unobserved"
        sources = tuple(sorted({x[1] for x in (a, b) if x}))
        notice = Change((before.identity, after.identity), channel, kind,
                        a[0].key if a else None, b[0].key if b else None)
        seeds.append(Seed(notice, sources, "DIFF-" + kind.upper()))
        if b:
            seeds.append(Seed(b[0], sources, "DIFF-" + kind.upper()))
    return tuple(seeds)


def incidence(fact):
    if isinstance(fact, Relation):
        return tuple((i, p.target if isinstance(p, Reference) else p)
                     for i, p in enumerate(fact.ports) if isinstance(p, (Node, Variable, Reference)))
    if isinstance(fact, Equality):
        return ((0, fact.left), (1, fact.right))
    if isinstance(fact, (Binding, PortBinding, Conflict)):
        return ((0, fact.variable),)
    # Difference notices record input lineage, but assert no invented object incidence.
    return ()


@dataclass(frozen=True)
class Support:
    rule: str
    premises: tuple

    def __post_init__(self):
        object.__setattr__(self, "premises", tuple(sorted(set(self.premises), key=encode)))


@dataclass(frozen=True)
class Witness:
    left_leaf: tuple
    left_port: int
    right_leaf: tuple
    right_port: int

    @property
    def key(self):
        return ("Shared", self.left_leaf, self.left_port, self.right_leaf, self.right_port)
