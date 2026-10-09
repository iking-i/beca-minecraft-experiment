# Isolation and storage semantics

Everything is opt-in under this directory. Production Core, EventStore, frozen
FormalL0, reference/effect engines, Pair rules and body files are not edited.
`ISOLATION.json` names the ten copied modules and their frozen LF source hashes.
The shared FormalL0 operative interpreter is imported unchanged.

The copies preserve ordinary traversal, integration, exact endpoint composition,
explicit Pair operand reuse, effect formation and native projection. Differences:

- reference version and pool schema explicitly distinguish this representation;
- `observations` is a fixed-size authority descriptor, not embedded history;
- `sources` maps Unit identity to first-incidence **frame identity**, not正文;
- `current_source` remains the complete current operand-source register;
- historical source metadata and bodies live in `os_sources`, with typed atom
  and channel membership indexes in `os_atoms` and `os_channels`;
- references use exact indexed lookup and verified supporting source reads;
- validation checks the authority boundary plus actual structure dependencies;
- lifecycle copies thread through the existing Full History option without
  changing recording semantics; only BoundaryCore is the supported entrypoint.

`SourceStore` is bound to one Core's own SQLite connection through a ContextVar
for the duration of a call. It is not an A-facing policy, cache in InternalState,
global monkeypatch, fallback, independent graph or alternate consumer. Its cache
holds at most eight decoded sources and is cleared at observation boundaries.
Atom witnesses are a mechanical exact-pattern index, not behavioral preference;
multiple different patterns at an identity are rejected, never arbitrated.

BoundaryCore changes **only its own already-created EventStore instance** to an
EventStore subclass before source-bearing origin publication. The subclass runs
source writes before the unchanged `_append_transition`, inside its existing
BEGIN IMMEDIATE/Current State transaction. There is no second commit, optional
history recovery, separate source DB, database migration or source deletion.
Fresh schema installation has no observation facts yet. A failed Core creation
is not silently resumed or converted. Old/default engines reject this lifecycle.

Startup validates mode, DB identity and referenced authority before lease/writer
side effects. Restart restores Current State, not states/events or a replay.
Full History OFF disables optional recording, not source authority. Interrupted
source publication rolls back together with state/index/head changes.

## Deliberate detection-time boundary

Old code scans and validates **every** source on every validation call. This
version verifies the commit-head descriptor and all actually accessed witnesses,
Unit incidence, edge/content addresses, current register and effect support
intervals. An unrelated archived body can be corrupt without blocking the next
ordinary cycle. Access to it fails; explicit streaming `audit` fails as well.
This is a documented integrity-detection-time change, not claimed equivalence
of all malformed-state executions. The corruption control verifies it directly.

All sources and their immutable metadata remain queryable. Nothing becomes
deletable because it was unused. Source history and indexes may grow on disk;
actual retained structures and unique future facts can still grow. This does not
prove bounded total RAM, infinite running, need/purpose retention or forgetting.

## Offline comparison interpretation

The saved checkpoints are fixture copies in a new independent source DB, not
live runs or a replacement A. Pair formation and effects execute inside the real
unchanged ordinary interpreter hooks. Both sides receive identical saved input,
pending action facts and state-version. Coupled fresh UUIDs remove irrelevant
journal randomness only; no operands/results/consumer are mocked. Expansion is
used outside execution solely to compare storage representations. Full-history
loading in the diagnostic fixture loader is not part of BoundaryCore.

No Minecraft or new real action is authorized by this report.
