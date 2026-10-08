"""Immutable structural execution inputs and separate audit evidence."""
from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Node:
    identity: str

    def __post_init__(self):
        if not isinstance(self.identity, str) or not self.identity:
            raise ValueError('Nonempty exact node identity required')


@dataclass(frozen=True, order=True)
class Edge:
    source: Node
    target: Node


@dataclass(frozen=True)
class Input:
    active: frozenset[Node] = frozenset()
    observed: frozenset[Node] = frozenset()


@dataclass(frozen=True)
class Processing:
    participating: tuple[Node, ...] = ()
    dependencies: tuple[Edge, ...] = ()


@dataclass(frozen=True)
class Evidence:
    edge: Edge
    provenance: str
    formed_version: int
    support: tuple[str, ...]


@dataclass(frozen=True)
class Cycle:
    version: int
    input: Input
    processing: Processing
    formed: tuple[Edge, ...]


@dataclass(frozen=True)
class State:
    nodes: frozenset[Node]
    edges: frozenset[Edge]
    audit: tuple[Evidence, ...] = ()
    history: tuple[Cycle, ...] = ()
    version: int = 0
    previous: Processing = Processing()
