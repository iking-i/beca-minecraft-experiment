"""Exact schemas, cardinality assessments and mechanical output packaging."""
from dataclasses import dataclass
from experimental.gsc0.model import Variable, Value, Support


@dataclass(frozen=True)
class OutputPort:
    name: str
    variable: Variable
    value_type: str

    @property
    def key(self):
        return (self.name, self.variable.key, self.value_type)


@dataclass(frozen=True)
class OutwardSchema:
    name: str
    ports: tuple[OutputPort, ...]  # All listed ports are required; order is declared.

    @property
    def key(self):
        return ('OutwardSchema', self.name, tuple(p.key for p in self.ports))


@dataclass(frozen=True)
class BindingEvidence:
    binding_key: tuple
    direct_supports: tuple[Support, ...]
    input_roots: frozenset


@dataclass(frozen=True)
class PortAssessment:
    name: str
    status: str
    values: tuple[Value, ...]
    evidence: tuple[BindingEvidence, ...]


@dataclass(frozen=True)
class GroundedOutwardStructure:
    schema_key: tuple
    fields: tuple[tuple[str, Value], ...]

    @property
    def key(self):
        return ('GroundedOutwardStructure', self.schema_key,
                tuple((name, value.key) for name, value in self.fields))


@dataclass(frozen=True)
class GroundingResult:
    status: str
    ports: tuple[PortAssessment, ...] = ()
    outward: GroundedOutwardStructure | None = None
    closure_digest: str | None = None
    reason: str | None = None

    @property
    def complete(self):
        return self.status == 'COMPLETE_GROUNDED'
