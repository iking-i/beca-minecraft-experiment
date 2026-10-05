"""Two isolated histories with literally shared current input, schema and domain."""
from dataclasses import dataclass
from experimental.gsc0.model import Variable, Value, Binding, Equality, Seed
from experimental.gsc0.engine import Condition, Engine
from .model import OutputPort, OutwardSchema


@dataclass(frozen=True)
class PairedFixture:
    condition: Condition
    schema: OutwardSchema
    sources: tuple
    history_a: tuple
    history_b: tuple
    current_input: tuple


def paired_fixture():
    types = ('TypeA', 'TypeB', 'TypeC')
    sources = tuple(Variable(f'h{i}', t, 'gsc1', 'q') for i, t in enumerate(types))
    outputs = tuple(Variable(f'p{i}', t, 'gsc1', 'q') for i, t in enumerate(types))
    values = tuple(Value(f'{letter}{n}', t) for letter, t in zip('ABC', types) for n in (0, 1))
    schema = OutwardSchema('O', tuple(OutputPort(f'p{i}', p, t)
                                    for i, (p, t) in enumerate(zip(outputs, types))))
    history_a = tuple(Seed(Binding(h, Value(f'{letter}0', t)), (f'H{i}',))
                      for i, (h, letter, t) in enumerate(zip(sources, 'ABC', types)))
    history_b = tuple(Seed(Binding(h, Value(f'{letter}{n}', t)), (f'H{i}',))
                      for i, (h, letter, t, n) in enumerate(zip(sources, 'ABC', types, (1, 0, 1))))
    current = tuple(Seed(Equality(h, p), (f'D{i}',)) for i, (h, p) in enumerate(zip(sources, outputs)))
    return PairedFixture(Condition(sources + outputs, values, ()), schema,
                         sources, history_a, history_b, current)


def close_history(fixture, history, current=None, **engine_options):
    initial = Engine(fixture.condition, **engine_options).run(history)
    if not initial.closure_complete:
        return initial, initial
    inputs = fixture.current_input if current is None else current
    return initial, Engine(fixture.condition, **engine_options).run(inputs, previous=initial.state)
