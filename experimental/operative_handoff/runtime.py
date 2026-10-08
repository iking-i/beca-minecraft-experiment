"""TEST_ONLY continuous state chain: execute, form, commit, ordinary reentry."""
from dataclasses import replace
from .mechanism import Mechanism
from .model import Cycle, Edge, Evidence, State


def form(prior, observed):
    """Temporal frontier incidence, uniformly for every exact endpoint.

    A frontier is a previously participating node with no outgoing dependency
    in the prior operative graph. All frontier/observed pairs are formed; no
    candidate is ranked or selected. This fixed witness law is not universal.
    """
    sources = {e.source for e in prior.edges}
    frontier = set(prior.previous.participating) - sources
    return tuple(sorted({Edge(source, target) for source in frontier for target in observed
                         if source != target} - prior.edges))


class Runtime:
    def __init__(self, nodes, edges, mechanism=None):
        nodes, edges = frozenset(nodes), frozenset(edges)
        if any(e.source not in nodes or e.target not in nodes for e in edges):
            raise ValueError('Initial edge outside declared nodes')
        self.state = State(nodes, edges, tuple(Evidence(e, 'ORIGIN_SUPPLIED', 0,
                                                      ('initial structural input',)) for e in sorted(edges)))
        self.mechanism = mechanism if mechanism is not None else Mechanism()

    @classmethod
    def from_state(cls, state, mechanism=None):
        runtime = cls(state.nodes, state.edges, mechanism)
        runtime.state = state
        return runtime

    def advance(self, current):
        prior = self.state
        if not current.observed <= prior.nodes:
            raise ValueError('Observed endpoint outside declared nodes')
        processing = self.mechanism.advance(prior.nodes, prior.edges, current.active)
        # Formation cannot execute: new edges become visible only after commit.
        formed = form(prior, current.observed) if current.observed else ()
        version = prior.version + 1
        evidence = tuple(Evidence(e, 'INTERNALLY_FORMED', version,
                                 (f'processing:{prior.version}',
                                  f'observed:{version}:{e.target.identity}')) for e in formed)
        cycle = Cycle(version, current, processing, formed)
        self.state = replace(prior, edges=prior.edges | frozenset(formed),
                             audit=prior.audit + evidence, history=prior.history + (cycle,),
                             version=version, previous=processing)
        return processing
