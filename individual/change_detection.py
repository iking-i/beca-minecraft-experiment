"""Descriptive numeric differences and temporal order; no causal or value labels."""

from dataclasses import asdict, dataclass


@dataclass
class ChangeSet:
    change_id: str
    previous_frame_id: str | None
    frame_id: str
    changes: list
    maintained_channels: list
    cochanged_channels: list
    after_action_ids: list
    sample_gap: bool
    missing_values_are_unobserved: bool

    def to_dict(self):
        return asdict(self)


def detect_changes(previous, current, action_ids=()):
    before = previous.numeric_channels if previous else {}
    after = current.numeric_channels
    changes, maintained = [], []
    uncertain = bool(current.coverage.get('unloadedBlocks') or current.coverage.get('blocksTruncated')
                     or current.coverage.get('entitiesTruncated'))
    for channel in sorted(before.keys() | after.keys(), key=int):
        a, b = before.get(channel), after.get(channel)
        if channel not in before:
            kind = 'appeared'
        elif channel not in after:
            kind = 'unobserved' if uncertain else 'disappeared'
        elif a == b:
            maintained.append(channel)
            continue
        else:
            kind = 'increased' if b > a else 'decreased'
        changes.append({'channel_id': channel, 'kind': kind, 'before': a, 'after': b,
                        'delta': b - a if a is not None and b is not None else None})
    gap = previous is not None and (previous.body_epoch != current.body_epoch or
                                    previous.encoding_namespace != current.encoding_namespace)
    return ChangeSet(f'{current.frame_id}:D', previous.frame_id if previous else None,
                     current.frame_id, changes, maintained, [item['channel_id'] for item in changes],
                     list(action_ids), gap, uncertain)

