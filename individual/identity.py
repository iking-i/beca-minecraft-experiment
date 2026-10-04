"""Lifetime identity and one live writer per individual database."""

import os
from pathlib import Path
from uuid import uuid4


class ExperimentInUse(RuntimeError):
    pass


def new_individual_id():
    return f"A-{uuid4()}"


class ExperimentLease:
    def __init__(self, database):
        self.path = Path(str(Path(database).resolve()) + '.lock')
        self._file = None

    def acquire(self):
        if self._file is not None:
            raise ExperimentInUse('This lease is already held')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open('a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                if self.path.stat().st_size == 0:
                    handle.write(b'0')
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            handle.close()
            raise ExperimentInUse(f'Individual lifetime already running: {self.path}') from error
        self._file = handle
        return self

    def release(self):
        if self._file is None:
            return
        if os.name == 'nt':
            import msvcrt
            self._file.seek(0)
            msvcrt.locking(self._file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        self._file.close()
        self._file = None

