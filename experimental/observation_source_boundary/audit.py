"""Explicit read-only full source audit, never an ordinary-cycle prerequisite."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from individual.current_state import current_row
from .store import SourceStore
from .reference.references import KEY


def audit(database):
    path = Path(database).resolve()
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
        db.execute('PRAGMA query_only=ON')
        store = SourceStore(db)
        state = json.loads(current_row(db)[3])
        store.boundary(state['internal_state']['l0_state'][KEY]['observations'])
        return store.audit()


if __name__ == '__main__':
    import sys
    print(json.dumps(audit(sys.argv[1])))
