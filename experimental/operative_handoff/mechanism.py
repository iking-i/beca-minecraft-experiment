"""One generic structural dependency execution path. No audit input."""
from collections import defaultdict, deque
from .model import Processing


class Mechanism:
    def advance(self, nodes, edges, active):
        if not active <= nodes or any(e.source not in nodes or e.target not in nodes for e in edges):
            raise ValueError('Execution endpoint outside declared nodes')
        outgoing = defaultdict(list)
        for edge in sorted(edges):
            outgoing[edge.source].append(edge)
        queue = deque(sorted(active))
        scheduled = set(active)
        participating, dependencies = [], []
        while queue:
            node = queue.popleft()
            participating.append(node)
            for edge in outgoing[node]:
                dependencies.append(edge)
                if edge.target not in scheduled:
                    scheduled.add(edge.target)
                    queue.append(edge.target)
        return Processing(tuple(participating), tuple(dependencies))
