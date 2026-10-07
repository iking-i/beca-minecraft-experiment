"""Opt-in BPC-LIVE-1 live interpreter, outside all frozen earlier engines."""
from copy import deepcopy
from dataclasses import asdict

from .formal_l0 import FormalL0Engine
from .live_body_structure import LiveControls, advance_structure, consume_saved, empty_structure


class FormalLiveBodyEngine(FormalL0Engine):
    def __init__(self, caps, resource_caps, owner, controls=LiveControls()):
        super().__init__(caps, resource_caps)
        self.owner = tuple(owner)
        self.controls = controls

    def initial_structure(self):
        return empty_structure(self.owner, asdict(self.caps))

    def advance(self, current, frame, state_version, pending_actions, *, ports):
        if pending_actions:
            raise ValueError('BPC-LIVE-1 cannot receive action-selection material')
        graph = current['l0_state'].get('live_body_structure')
        if current['l0_state'].get('live_body_formation_status') == 'RESOURCE_LIMIT':
            raise RuntimeError('BPC-LIVE-1 RESOURCE_LIMIT: no automatic recovery/reconstruction')
        if (not graph or graph['owner'] != list(self.owner) or graph['caps'] != asdict(self.caps)
                or frame.frame_id != f'{self.owner[0]}:E{graph["last_sequence"] + 1}'
                or frame.sequence_id != graph['last_sequence'] + 1):
            raise ValueError('Live structure/identity/sequence boundary mismatch')
        prior_frame = current['l0_state'].get('previous_frame')
        if prior_frame and (prior_frame['encoding_namespace'] != frame.encoding_namespace
                            or prior_frame['body_epoch'] != frame.body_epoch):
            raise ValueError('Continuous body/encoding boundary changed')
        # Read BEFORE formation. It can only see the previously committed graph.
        read = consume_saved(graph, state_version - 1, self.controls.condition == 'NC4')
        internal, frame, journal = super().advance(current, frame, state_version, ())
        updated, formation = advance_structure(graph, frame, ports, state_version,
                                               internal, self.caps, self.controls)
        internal.l0_state['live_body_structure'] = updated
        internal.l0_state['live_body_formation_status'] = formation['status']
        internal.l0_state['live_body_read'] = deepcopy(read)
        for kind, partial in journal:
            if kind == 'RECURSIVE_PARTIAL_OUTPUT':
                # Actual recursive processing consumes the read, rather than just logging it.
                partial['processing']['live_body_connection_read'] = deepcopy(read)
                process = internal.active_processes[partial['process_id']]
                process['output']['live_body_connection_read'] = deepcopy(read)
        journal.append(('LIVE_BODY_CONNECTION_READ', deepcopy(read)))
        journal.append(('LIVE_BODY_STRUCTURE_FORMATION', formation))
        return internal, frame, journal
