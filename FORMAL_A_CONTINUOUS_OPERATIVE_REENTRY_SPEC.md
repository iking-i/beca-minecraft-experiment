# Formal A Continuous Operative Reentry — TEST_ONLY preregistration

Base: 76fee923fd1ea2d3b4697e299f1c35f9d6c8817e. Date: 2026-10-08.
Status at registration: DEFINED / NOT_IMPLEMENTED. This is a historical registration
status; implementation/validation result belongs to separate VALIDATION artifacts.

## Frozen question and claim boundary

Can one independent TEST_ONLY ACore individual use origin S0 and subsequently
formed S1 of the already frozen operative representation, commit S1 atomically to
authoritative Current State, terminate its Core process normally, recover from the
same database in a new process, and use persisted S1 through ordinary
ACore.accept_observation without reformation, history replay or a special consumer?

ACore -> authoritative Current State -> S0 -> ordinary synthetic experience -> S1
-> atomic state/event commit -> normal shutdown/lease release/process exit
-> new Core process/same DB/same engine version -> same individual
-> ordinary accept_observation -> persisted S1 -> changed actual operands/computation.

Identity continuity is experimentally verifiable, not philosophical consciousness.
No Minecraft, mainline A, selected individual, body, sampler/binder, theory or old
frozen reports/tests may be changed. Frozen FormalL0 and WORLD_ENTRY hashes stay fixed.
The engine/formation law are reused unchanged from 8b33097, not redesigned.

## Lifecycle interfaces and minimal isolation boundary

ACore currently restores via EventStore.latest_state/current_row and opens a new
session under ExperimentLease; shutdown ends session, closes store and releases lease.
EventStore.transition commits Current State and optional audit events in the same
SQLite transaction with version/identity checks. These lifecycle interfaces can be
reused; no new persistence engine or snapshot replay is needed.

An explicit TEST_ONLY constructor configuration binds one resolved database path,
one mechanism version and fresh-only origin scaffold. Default is absent. Read-only
mode/state/version/database/structure checks precede EventStore/session writes and
are repeated under lease. Existing ordinary/old databases cannot be converted.
Lifecycle metadata in authoritative internal state binds TEST_ONLY mode, version,
database and individual. Restart requires that same explicit configuration/version;
no origin scaffold may be re-supplied. Default Core rejects marked experiment state.
The existing transition rejection gets only a metadata-validated experimental
exception, not global removal. The experiment does not expose a production CLI switch.

S0 is supplied only at first initialization and committed through Core; S1 is absent
then. S1 forms under unchanged actual experience/integration mechanics and joins
S0's same edge collection. Formation-round dependencies exclude new S1. Later
execution consumes persisted edges; provenance stays non-executable audit material.

## Fixed witness and independent controls

Use an offline FakeBridge (no perform) and ordinary valid raw observations encoded
by Core FrameEncoder. Numeric position sequence 0,1,2,3,4, with otherwise fixed
sensor values, supplies consecutive synthetic experiences. First process initializes
S0 and accepts observations through S1 formation. Second process restores and
accepts subsequent observations, capturing operands and comparisons. If the
registered sequence does not establish the claim, report FAIL; do not select a
favorable substitute or redesign formation.

The exact registered S0 is opaque:origin -> opaque:operand with ordinary relation
records/outcomes U-origin-0/U-origin-1. Only those origin objects are supplied;
no S1 endpoint/edge is injected. Actual relation identities come from encoding.
Both Full History ON and OFF are exercised; OFF proves audit history is not a
restore dependency. No states/events enumeration or verify/replay is allowed in
restore/read. Evidence extraction of recorded events by the external harness is
separate from runtime execution.

Edge-only paired control intercepts the engine input reached through restored
ACore.accept_observation, holds state/frame/version/pending actions fixed, removes
only S1, computes actual outputs and stops before commit. The normal/control
calculations cannot modify canonical evidence. No side consumer supplies answers.
Provenance removed/swapped/unified controls use the same boundary. Invalid-version,
wrong DB/default mode/legacy conversion, missing endpoint/entry, malformed/duplicate
edge and lease conflict must reject safely. A failed commit must roll back both
Current State and event inserts, leaving Core's in-memory state unchanged.

## Frozen criteria

| Criterion | Required evidence |
|---|---|
| CR-T1 TEST_ONLY Core Isolation | Default off; default Core rejects marked state before writes; ordinary path unchanged. |
| CR-T2 Single Individual Identity | Same ID across creation/formation/shutdown/restart; monotonically consecutive persisted state versions, session may change. |
| CR-T3 S1 Real Formation | S1 absent at origin, actual current experience/integration supports it, not executed during formation. |
| CR-T4 Authoritative Persistence | S1 and metadata are committed Current State; transaction failure rolls back; no in-memory restore. |
| CR-T5 Restart Recovery | Distinct OS process/new Core recovers exact same S1 from same DB/version; no S0 reinitialization/reformation. |
| CR-T6 Normal Operative Reentry | Restored ACore.accept_observation actually uses S1 and changes operands/computation. |
| CR-T7 Edge-Only Ablation | Only S1 masked; actual operands/comparison change, not just logging. |
| CR-T8 Provenance Neutrality | Removed/swapped/unified origin labels do not change executed operands. |
| CR-T9 Version and Failure Safety | Version/mode/structure/DB/lease errors rejected before persistent side effects, no repair/fallback/new A. |
| CR-T10 Historical Compatibility | Frozen hashes, old/default tests and complete regression pass; old evidence untouched. |

PASS requires every CR-T1..T10 and all necessary causal controls. FAIL means an
executed test contradicts a criterion. NOT_TESTABLE means carrier/environment
prevents execution; NOT_ESTABLISHED means required evidence is absent. Missing
proof cannot be reported as PASS. The strongest PASS is independent TEST_ONLY
ACore lifecycle adoption, not canonical Minecraft authorship, arbitrary structure
execution, consciousness continuity, behavioral closure or L1/upward recursion.

Only implementation/validation is authorized. Stop with complete evidence;
no next phase or theory update is started.
