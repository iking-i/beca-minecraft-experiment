# Current-state runtime source (engineering boundary)

The normal `main.py --froi` / launcher FROI route now prepares an organization
from the current retained `InternalState.relations`, feedback and integration.
It does not query the EventStore input history. The existing GSC rules, caps,
Shared/PortBind consumer, read checkpoint/resume interpreter and body path remain.

`CurrentStructureSource` mechanically represents **all retained relation
outcomes**, with current-state provenance. It does not rank, select a history
window, evict, decay, infer need/purpose, or substitute a semantic answer.
Failure/RESOURCE_LIMIT remains a failure, with no historical fallback.

The compatibility field named `history` in JobSpec holds this immutable current
source, not History.events. `event_cutoff` / `history_cutoff` is a state-version
boundary token on this path; `runtime_source.cutoff_kind = state_version`
explicitly distinguishes it from the frozen historical event cutoff.
Its provenance attests current retained structures, **not reconstructed raw
experiences or historical frame geometry**. Existing evidence references remain
in the retained relation records and external append-only audit database.

The original History, codec and OrganizationSession remain for explicit offline
historical controls and frozen FROI evidence. The two historical test setup
helpers explicitly inject that source; the production CLI/launcher offers no
history-source switch. Their assertions/acceptance predicates are unchanged.
Old FROI acceptance PASS is not re-attributed to this runtime-source change.

`PhysicalCaps.history = 6` still bounds the existing active frame-record space;
it is not a new last-N EventStore memory source. All caps are unchanged.

Offline engineering check (no body, no canonical DB writes):

```powershell
.\.venv\Scripts\python.exe -m debug.current_structure_pressure
```

`--current-state-db PATH` reads only the latest stored snapshot through SQLite
read-only, then measures preparation in independent TEST_ONLY processes. The
temporary external audit DB grows by 0/1000/10000 records while that current
state remains fixed. SQLite authorization forbids external event reads during
measurement. This checks history-driven input growth, not perpetual RAM safety,
human memory, endogenous purpose, or new world-loop acceptance.
