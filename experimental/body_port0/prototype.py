"""History incidence -> supported connection -> native parameterless expression."""
from dataclasses import dataclass
from itertools import combinations
from individual.action_space import CATALOG_DATA, DEFINITIONS, formal_command


@dataclass(frozen=True)
class BodyPort:
    version: str
    code: int


def catalog_port(code):
    if type(code) is not int:
        raise ValueError('Exact numeric port identity required')
    entry = DEFINITIONS.get(code)
    if not entry or not entry.get('formal_enabled') or entry['parameters']:
        raise ValueError('Existing formal parameterless endpoint required')
    return BodyPort(CATALOG_DATA['version'], code)


@dataclass(frozen=True)
class Sample:
    sequence: int
    scope: str
    channels: tuple

    def __post_init__(self):
        if type(self.sequence) is not int or not self.scope:
            raise ValueError('Invalid sample identity')
        if self.channels != tuple(sorted(self.channels)) or len(dict(self.channels)) != len(self.channels):
            raise ValueError('Canonical distinct channels required')
        if any(type(k) is not int or type(v) is not int for k, v in self.channels):
            raise ValueError('TEST_ONLY exact integer channel domain required')


@dataclass(frozen=True)
class Execution:
    identity: str
    port: BodyPort
    before: Sample
    after: Sample
    source: str = 'TEST_ONLY_BOOTSTRAP'
    completed: bool = True
    parameters: tuple = ()


@dataclass(frozen=True)
class Pattern:
    scope: str
    changes: tuple


@dataclass(frozen=True)
class Member:
    group: str
    object: object


@dataclass(frozen=True)
class Shared:
    endpoints: frozenset


@dataclass(frozen=True)
class Support:
    conclusion: object
    rule: str
    premises: frozenset


@dataclass(frozen=True)
class Organization:
    facts: frozenset
    supports: frozenset
    complete: bool = True


def encode_execution(execution):
    """Reify an actual fixture receipt, not a supplied C-to-O answer relation."""
    e = execution
    if (not e.identity or not e.completed or e.source not in (
            'TEST_ONLY_BOOTSTRAP', 'TEST_ONLY_FORMED_CONNECTION')
            or e.parameters or e.port != catalog_port(e.port.code)
            or e.before.scope != e.after.scope or e.after.sequence != e.before.sequence + 1):
        raise ValueError('Invalid consecutive execution material')
    before, after = dict(e.before.channels), dict(e.after.channels)
    if before.keys() != after.keys():
        raise ValueError('Coverage change outside frozen fixture scope')
    c = Pattern(e.after.scope, tuple((k, before[k], after[k], after[k] - before[k])
                                    for k in sorted(before) if before[k] != after[k]))
    if not c.changes:
        raise ValueError('Nonempty experienced change required')
    facts = frozenset((e, e.before, e.after, e.port, c,
                       Member(e.identity, c), Member(e.identity, e.port)))
    proofs = {Support(f, 'INPUT', frozenset()) for f in (e, e.before, e.after, e.port)}
    proofs.add(Support(c, 'DIFFERENCE', frozenset((e.before, e.after))))
    proofs.add(Support(Member(e.identity, c), 'RECORD_INCIDENCE', frozenset((e, c))))
    proofs.add(Support(Member(e.identity, e.port), 'RECORD_INCIDENCE', frozenset((e, e.port))))
    return Organization(facts, frozenset(proofs), False), c


def form(material):
    """Uniform local co-incidence law, no special Pattern/BodyPort branch."""
    facts, proofs = set(material.facts), set(material.supports)
    groups = {}
    for f in facts:
        if isinstance(f, Shared):
            raise ValueError('Connections must form, not be supplied as seed answers')
        if isinstance(f, Member):
            groups.setdefault(f.group, set()).add(f)
    for members in groups.values():
        for a, b in combinations(members, 2):
            if a.object != b.object:
                edge = Shared(frozenset((a.object, b.object)))
                facts.add(edge)
                proofs.add(Support(edge, 'SHARED_INCIDENCE', frozenset((a, b))))
    return Organization(frozenset(facts), frozenset(proofs))


def consume(organization, current):
    """Only formed graph/support access. No history/solver/selector arguments."""
    if organization is None or not organization.complete or current not in organization.facts:
        return None
    proofs = {}
    for p in organization.supports:
        proofs.setdefault(p.conclusion, set()).add(p)
    def supported(f, visiting=frozenset()):
        if f not in organization.facts or f in visiting:
            return False
        return any(all(supported(x, visiting | {f}) for x in p.premises)
                   for p in proofs.get(f, ()))
    ports = set()
    for f in organization.facts:
        if isinstance(f, Shared) and current in f.endpoints and supported(f):
            ports.update(x for x in f.endpoints if isinstance(x, BodyPort) and supported(x))
    if len(ports) != 1:
        return None
    port, = ports
    if port != catalog_port(port.code):
        return None
    return formal_command(port.code, {})['args']


class RecordingBody:
    """TEST_ONLY transport recorder; renewed numeric input supplied by fixture.

    Does not simulate Minecraft action semantics or infer a world consequence.
    """
    def __init__(self, sample):
        self.sample = sample
        self.commands = []

    def execute(self, expression, renewed_channels):
        if set(expression) != {'code', 'parameters'} or expression['parameters'] != {}:
            raise ValueError('Exact parameterless body expression required')
        port = catalog_port(expression['code'])
        before = self.sample
        self.sample = Sample(before.sequence + 1, before.scope, renewed_channels)
        self.commands.append((port, ()))
        return before, self.sample


def bootstrap(body, code, renewed_channels, identity):
    port = catalog_port(code)
    before, after = body.execute({'code': port.code, 'parameters': {}}, renewed_channels)
    return Execution(identity, port, before, after)
