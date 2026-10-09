# Observation Source Boundary — offline validation

**OFFLINE_PASS; implemented and validated, not closed/frozen.**
Baseline f2d66102755038dad688a20189767ded24651b0e. No commit/push or stage-index
change. No Minecraft, real action or default-A adoption in this task.

## Adopted boundary

Complete original `sensor_source` bodies (all canonical operand facts, not an
extra claim to preserve every raw Minecraft JSON audit field), frame identity,
namespace, epoch, channel identity and timestamp/sequence/digest metadata live
in immutable authoritative `os_sources`. Exact typed-atom and channel indexes
provide runtime access. The authority head and Current State commit together
in the owning EventStore transaction. This authority is not optional events or
states history and survives Full History OFF.

InternalState keeps a constant-size authority descriptor (`observations`),
Unit→first-incidence frame identities (`sources`), and one complete current
source register (`current_source`). Actual Units, Pairs, connections, supports
and effect rules are unchanged. There is no internal virtual Unit, cap exemption,
selection, purpose, forgetting or historical fact deletion. See ISOLATION.patch
for every change to copied modules and ISOLATION.json for their frozen sources.

Historical ObservationRef uses exact namespace/node indexing with verified
witnesses; inconsistent matches reject. FactRef verifies exact frame/channel and
source digest. Equal values do not merge frame/channel facts. Object epoch and
current membership checks remain. The source cache is external, at most8 decoded
sources, cleared at observation boundaries; no full-history load inside advance.

## E1–E32 paired offline comparison

All32 saved input/checkpoint pairs agree after representation expansion:
complete interpreter state, output ObservationFrame and journal. Both ordinary
interpreters actually execute; coupled fresh UUIDs control irrelevant diagnostic
journal identity only. Expansion occurs outside execution. All32 sources pass
explicit complete authority/index audit, and original input hashes match.

Every frame preserves376 numeric channels,64 object references and47 native
capabilities. Final structure remains8 Units,9 Pairs,31/64 charged structures.
No source is dropped. These are saved-real-data offline results, not live replay
accepted as a new Minecraft run or a new body-loop PASS.

| InternalState JSON | frozen representation | new equivalent representation |
|---|---:|---:|
| E1 |236,219 bytes|185,312 bytes|
| E6 |575,368 bytes|267,453 bytes|
| E32 |1,247,906 bytes|270,011 bytes|

New equivalent size is270,011 bytes throughout E16–E32; E32 is78.36% smaller.
The figures measure equivalent saved state, excluding extra live lifecycle
bookkeeping. They do not imply constant size for all future actual structures.

## Process memory and access

Separate processes execute the32 saved checkpoints. RSS includes fixture loading;
advance timing excludes loading and includes new-source publication. These are
shared-machine measurements, not dedicated benchmark or live performance proof.

| Measurement | old | new |
|---|---:|---:|
| initial RSS |29.699 MiB|29.914 MiB|
| peak RSS sampled at10ms |66.902 MiB|68.293 MiB|
| final RSS |47.312 MiB|45.754 MiB|
| summed advance/commit |376.375 s|51.864 s|

Peak RSS did **not** decrease. Fixture loading and Python allocation contribute;
JSON shrinkage is not RSS equivalence or a proof of bounded RAM.
At E32,7 historical bodies /179,087 bytes are decoded, with363 exact atom-index
reads. E16–E32 body reads remain7;32 full bodies are not reloaded every cycle.
All-source audit is explicit and is not a recursive-cycle prerequisite.

## Integrity timing — deliberate semantic difference

Frozen validation checks every archived body each time. This version checks the
authority head and accessed current/Unit/edge/content/route witnesses, with a
separate full streaming audit. Deliberately corrupting an unused E7 body allows
a later ordinary cycle, then direct access and complete audit both reject.
Missing current source, bad index witness, ambiguity, foreign/digest/channel or
object-epoch errors fail closed. Never recover from optional history or regenerate
missing sources. We claim lawful-data recursive equivalence on these witnesses,
**not** equivalent detection time for all malformed histories.

## Persistence and controls

Tests cover OFF restoration of the same A, ON/OFF/ON and preserved audit gaps,
new-process continuation, and actual process exit73 after source/index/head writes
inside the transaction before state publication. Restart sees rollback, keeps
the same individual, and continues from authoritative Current State. Publication
fault and real64-capacity rejection leave no partial source or state. EffectRoute
ablation/restoration still changes actual operations; no Pair rule is changed.
Old/default Core takeover and wrong version/path refuse before writer effects.

## Recorded checks

- Focused:21 passed.
- Related:88 passed (overlap with focused; do not sum).
- Final complete regression:784 passed /114 subtests passed,513.61s.
- Earlier complete collection:781 passed /114 subtests,535.92s (18 new cases);
  final collection also includes the three later-added controls.
-13 frozen LF-normalized hashes MATCH.
-512 earlier protected files and27 unrelated files unchanged; original real
  database SHA unchanged; current tracked diff empty.
- Syntax, JSON, evidence hashes and diff/whitespace checks PASS.

Initial new implementation/diagnostic failures remain in INITIAL_FAILURES.json
and the raw initial capacity-control log. Existing frozen failures are untouched.

## Remaining boundary

Offline evidence supports requesting a separately authorized real validation of
this opt-in version. No real run is started here. We do not establish infinite
operation, bounded total memory, purpose/need retention, forgetting, autonomous
action selection, default FormalL0 adoption, world law or new live body closure.
Source and index disk storage can grow; actual structure can still exhaust64.
