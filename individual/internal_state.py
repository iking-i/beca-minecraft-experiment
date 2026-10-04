"""Finite working structure, with no preassigned Minecraft meanings."""

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import secrets

from .policies import PolicyRegistry, initial_generation_parameters


@dataclass
class PhysicalCaps:
    processes: int = 8
    units: int = 64
    relations: int = 96
    history: int = 6
    evidence_window: int = 4
    condition_channels: int = 16
    outcomes_per_relation: int = 64


@dataclass
class InternalState:
    units: dict = field(default_factory=dict)
    relations: dict = field(default_factory=dict)
    active_processes: dict = field(default_factory=dict)
    observation_history_window: list = field(default_factory=list)
    action_history_window: list = field(default_factory=list)
    detected_changes: dict = field(default_factory=dict)
    resource_state: dict = field(default_factory=dict)
    generation_parameters: dict = field(default_factory=initial_generation_parameters)
    exploration_state: dict = field(default_factory=lambda: {'random_state': secrets.randbits(32), 'attempts': {}})
    process_archive: list = field(default_factory=list)
    continuity_incidents: list = field(default_factory=list)
    latest_integration: dict = field(default_factory=dict)
    latest_feedback: dict = field(default_factory=dict)
    latest_generation: dict = field(default_factory=dict)
    latest_action: dict | None = None
    latest_structure_changes: dict = field(default_factory=dict)
    structure_revision: int = 0
    policy_registry: dict = field(default_factory=dict)
    parameter_sources: dict = field(default_factory=dict)
    policy_migration_status: dict = field(default_factory=dict)
    body_capabilities: dict = field(default_factory=dict)
    l0_state: dict = field(default_factory=dict)

    def __post_init__(self):
        PolicyRegistry(self).initialize()

    def to_dict(self):
        return deepcopy(asdict(self))

    @classmethod
    def from_dict(cls, value):
        legacy = 'policy_registry' not in value
        result = cls(**deepcopy(value))
        if legacy:
            result.policy_registry = {}
            result.parameter_sources = {}
            result.policy_migration_status = {}
            PolicyRegistry(result).initialize(legacy=True)
        return result

    def archive_unit(self, unit_id):
        return self.units.pop(unit_id, None)

    def merge_units(self, target, sources):
        """Explicit structural operator; callers must supply an evidence-based reason."""
        if target in sources or target not in self.units:
            raise ValueError('Invalid unit merge')
        merged = self.units[target]
        for source in sources:
            unit = self.units.pop(source)
            merged.setdefault('lineage', []).append(source)
            merged['strength'] += unit.get('strength', 0)
            for relation in self.relations.values():
                if relation.get('antecedent') == source:
                    relation['antecedent'] = target
                for outcome in relation.get('outcomes', {}).values():
                    if outcome.get('unit_id') == source:
                        outcome['unit_id'] = target
        self.structure_revision += 1

