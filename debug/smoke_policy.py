"""DEBUG_ONLY deterministic movement probe; excluded from default formal runtime."""


class DeterministicPolicy:
    def __init__(self, wait_seconds=1.0, move_ms=200):
        self.wait_seconds = wait_seconds
        self.move_ms = move_ms
        self.phase = 'observe_first'
        self.due = None
        self.last_sequence = None

    def next_action(self, state, now):
        if self.phase == 'observe_first' and state.environment_sequence:
            self.phase = 'wait'
            self.due = now + self.wait_seconds
        if self.phase == 'wait' and now >= self.due:
            self.phase = 'moving'
            return {'method': 'move', 'args': {'direction': 'forward', 'durationMs': self.move_ms}}
        if self.phase == 'stop':
            self.phase = 'stopping'
            return {'method': 'move', 'args': {'direction': 'stop'}}
        if self.phase == 'observe_after' and state.environment_sequence > self.last_sequence:
            self.phase = 'complete'
        return None

    def action_finished(self, success, state):
        if not success:
            self.phase = 'complete'  # An uncertain action is never automatically replayed.
        elif self.phase == 'moving':
            self.phase = 'stop'
        elif self.phase == 'stopping':
            self.phase = 'observe_after'
            self.last_sequence = state.environment_sequence

