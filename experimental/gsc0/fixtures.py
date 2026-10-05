"""Finite TEST_ONLY inputs from specification section 13."""
from .model import Node, Variable, Value, Relation, Equality, Binding, Composite, Seed, Observation, difference
from .engine import Condition


def fixture(remove_history=None, remove_difference=None, conflict=False):
    a, b, c = (Node(x) for x in ("A", "B", "C"))
    x, y = Variable("X"), Variable("Y")
    v1, v2, v3 = Value(1), Value(2), Value(3)
    r1, r2, r3 = Relation("R1", "p1", (a, y)), Relation("R2", "p2", (x, b)), Relation("R3", "p3", (b, c))
    condition = Condition((a, b, c, x, y), (v1, v2, v3), tuple((p, ("node", "node")) for p in ("p1", "p2", "p3")))
    history = tuple(Seed(r, (r.name,)) for r in (r1, r2, r3) if r.name != remove_history)
    records = []
    if remove_difference != "D1":
        records.append(("D1", Binding(y, v3), "D1"))
    if remove_difference != "D2":
        records.append(("D2", Equality(y, x), "D2"))
    if conflict:
        records.append(("D3", Binding(y, v2), "D3"))
    delta = difference(Observation("O0", ()), Observation("O1", tuple(records)))
    expected = Composite((r1, r2, r3, Binding(x, v3)))
    return condition, history, delta, expected


def growth_fixture(count):
    """A connected chain of input relations; no new primitive or preference."""
    nodes = tuple(Node(f"N{i}") for i in range(count + 1))
    condition = Condition(nodes, (), (("p", ("node", "node")),))
    seeds = tuple(Seed(Relation(f"G{i}", "p", (nodes[i], nodes[i + 1])), (f"G{i}",)) for i in range(count))
    return condition, seeds
