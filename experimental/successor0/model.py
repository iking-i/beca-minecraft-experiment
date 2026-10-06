"""Immutable, content-identified structures for the frozen unique-producer scope."""
from dataclasses import asdict, dataclass
import hashlib
import json


@dataclass(frozen=True)
class Port:
    identity: str
    type: str
    scope: str


@dataclass(frozen=True)
class Value:
    identity: str
    type: str
    scope: str


@dataclass(frozen=True)
class RequireBound:
    port: str
    type: str
    scope: str


@dataclass(frozen=True)
class Bind:
    port: str
    value: str


@dataclass(frozen=True)
class Transfer:
    input: str
    output: str


@dataclass(frozen=True)
class Demand:
    port: str


@dataclass(frozen=True)
class Activation:
    relation: Transfer


@dataclass(frozen=True)
class SupportEdge:
    conclusion: object
    rule: str
    premises: frozenset


def content(item):
    if isinstance(item, (tuple, frozenset)):
        return sorted((content(x) for x in item), key=canonical)
    if isinstance(item, SupportEdge):
        return {"kind": "SupportEdge", "conclusion": content(item.conclusion),
                "rule": item.rule, "premises": content(item.premises)}
    return {"kind": type(item).__name__, **asdict(item)}


def canonical(item):
    return json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class ActivatedSupport:
    requirement: RequireBound
    status: str
    facts: frozenset
    supports: frozenset

    def logical_content(self):
        return {"requirement": content(self.requirement), "status": self.status,
                "facts": content(self.facts), "supports": content(self.supports)}

    @property
    def identity(self):
        return hashlib.sha256(canonical(self.logical_content()).encode()).hexdigest()


@dataclass(frozen=True)
class Formation:
    status: str
    organization: ActivatedSupport | None
    trace: tuple
    diagnostic: str | None = None


@dataclass(frozen=True)
class ReadResult:
    status: str
    port: str
    value: str | None = None
