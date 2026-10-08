# Formal A Continuous Operative Reentry — validation

2026-10-08. Base: `76fee923fd1ea2d3b4697e299f1c35f9d6c8817e`.
**Classification: NOT_TESTABLE. Implementation commit: NONE.**
The causal witness passes CR-T1–CR-T9, but required complete regression is not
green. CR-T10 is NOT_TESTABLE at a host Tcl/Tk initialization boundary. No final
PASS is claimed. Per instruction, stop with uncommitted implementation/evidence;
no old test, frozen hash, runtime environment or next phase is changed.

## Preregistration and reused mechanism

`FORMAL_A_CONTINUOUS_OPERATIVE_REENTRY_SPEC.md` was written before implementation
and remains unchanged. The opt-in channel uses exactly the frozen
`TestOnlyFormalL0Engine` from implementation `8b33097`; no formation/execution
rule or body policy is redesigned. Only ACore gains explicit TEST_ONLY selection,
read-only admission and a validated writeback exception. EventStore and Current
State implementations are unchanged. Default engine selection remains FormalL0;
marked states cannot pass default admission or ordinary writeback.

The mode/version/resolved database path are recorded in initial session environment
before S0 initialization, and then bound to the individual in authoritative
`l0_state.operative_core_test_only`. A failed origin commit cannot leave an
unmarked database available for default adoption. Existing ordinary/old databases,
wrong versions/paths, repeated origin, invalid structures and incompatible modes
are refused before opening a writer. Admission is repeated under the existing
lease. Session operations validate lifecycle metadata; transitions validate both
old/new states and reject removal of committed edges. No CLI/launcher exposes
this experimental engine and no selected/mainline individual is modified.

## Actual subprocess evidence

Machine-readable `VALIDATION.json` contains complete state snapshots, raw test
observations, post-commit journals, S0/S1 and formation supports for both runs.
The recorder shares only measurement functions with the dedicated tests; each
subprocess runner imports and executes real ACore, not the tests, graph runtime
or standalone witness answer. Its FakeBridge forbids body calls.

| Recording mode | TEST_ONLY individual | Create / restart PID | State chain | Audit states / events |
|---|---|---|---|---|
| ON | A-af565031-3dee-4bc7-a30f-a07ed16252fa | 3036 / 22784 | S0 A1; formation A3; shutdown A4; restart A5; shutdown A9 | 10 / 58 |
| OFF | A-e101dcf2-c476-43ef-b718-94da7397f186 | 17060 / 32844 | S0 A1; formation A3; shutdown A4; restart A5; shutdown A9 | 0 / 0 |

Each row uses its own independent test database and one individual throughout its
real process restart. The original process ends normally, closes store/releases
lease, and exits. The next distinct OS process opens the same database and takes
its state from `current_state`, not a Python object supplied by the parent.
Session identity changes; individual and version lineage remain continuous.
Both SQLite integrity checks are `ok`. OFF has an explicit audit gap and no
historical states/events to replay. SQL tracing verifies current-snapshot restore
and no states/events SELECT or complete verify in restore/reentry.

S0: `opaque:origin -> opaque:operand`, origin supplied only at creation.
S1: `opaque:operand -> U-cdb3852bc0eebc2503db:-1`, absent initially, formed after
E2 actual experience/integration, with preserved direct formation evidence.
The new S1 is absent from formation-round dependencies. Entire operative collection
and support evidence are exactly restored; the existing S1 is not reconstructed
or reformed after restart. New later experiences may lawfully add other edges.

The first restart observation E3 is processed normally but is a carrier-epoch
transition: the existing mechanism records `TEMPORAL_LINK_UNRESOLVED` and does
not publish a partial. E4/E5 in that same new process publish partials with S1 in
actual operative dependencies. The gap is not removed, mislabeled as success or
used to change the criterion. The preregistered 0,1,2,3,4 witness is unchanged.

## Causal controls and criterion audit

| Criterion | Result | Evidence |
|---|---|---|
| CR-T1 | PASS | Default absent, default admission/writeback rejection; no mode conversion. |
| CR-T2 | PASS | Exact individual identity, consecutive committed versions, one experiment row across distinct processes. |
| CR-T3 | PASS | Actual experience/integration supports; S1 absent at origin/not executed in formation round. |
| CR-T4 | PASS | Committed current snapshot equals captured shutdown state; induced transaction failure rolls back state/events/Core state. |
| CR-T5 | PASS | New OS process/new Core, same DB/version, exact S1/evidence restored, S0 not initialized again. |
| CR-T6 | PASS | Ordinary accept_observation invokes existing engine and later partial uses persisted S1. |
| CR-T7 | PASS | Only S1 masked; real expected outcomes/dependency path differ, comparison True -> None. |
| CR-T8 | PASS | Removed/swapped/unified provenance leaves actual operands unchanged. |
| CR-T9 | PASS | Default/version/path/identity/lease/structure/capacity/initialization failures safely reject; no fallback or alternate A. |
| CR-T10 | NOT_TESTABLE | Frozen hashes and related/default tests pass, but full regression has Tcl/Tk carrier failure. |

The paired controls enter through an independently restored Core's ordinary
accept_observation. After its normal carrier-gap input, each branch has exactly
the same current state, observation, version and pending actions. Only the engine
input edge S1 is masked, with all relation records, feedback and supports retained.
Reinserting S1 gives exact input equality. Both branches execute actual engine
processing and are stopped at `_commit_observation` before any control commit;
neither supplies an answer through a side consumer. No formal history is altered.
The normal result is True and S1-only branch None in both ON/OFF measurements.

## Tests and retained failure records

- Focused: **28 passed**, 19.85 s.
- Related: **160 passed / 23 subtests**, 39.78 s.
- Original WORLD_ENTRY guard separately: **1 passed / 13 subtests**.
- Full Python suite, no exclusions: **559 passed / 114 subtests / 1 failed**, 337.23 s.

The full failing test is
`tests/test_runtime_monitor.py::MonitorTests::test_window_can_open_idle_and_close_without_experiment`
at line 341, `tk.Tk()` -> `_tkinter.create`. Failure happens before Monitor or Core
construction. Tcl reports it cannot initialize tk.tcl while sourcing
`C:/Users/i/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/tcl/tk8.6/ttk/utils.tcl`.
A subsequent read-only path check finds that file present: permanent absence or
precise host cause is therefore NOT_ESTABLISHED. No environment repair, failure
exclusion, old-test edit or repeated full run is used to claim PASS.
Raw complete logs are preserved under `history/`, including the earlier related
failure, final related/focused/frozen checks and this full failure.

The first focused facility result was 14 passed / 6 failed: it expected a partial
at a carrier-gap boundary. Fixing that measurement assumption preserved the frozen
question/criteria/mechanism. The first related result was 157 passed / 23 subtests /
2 failed: only the new empty-file/old uninitialized-Core admission handling was
corrected; old tests stayed unchanged. The first standalone recorder had a Windows
read-connection cleanup error; its read connection now explicitly closes. These
attempts are recorded, not retroactively claimed PASS.

## Preservation and limits

FormalL0 LF-normalized SHA-256 remains
`1b6abea5d568c349bf7c181ecd771fc6f08cd0f1791fa49be7434c4acd354b62`.
All 13 frozen component hashes match. Previous FA/OH/BPC/FROI/GSC/CEC/Successor
source, tests, specs, validation, failures and state closeouts remain byte-identical.
No database outside independent test directories, body, sampler/binder, caps,
selection, theory or unrelated untracked material is changed. Research-state
indexes are not updated. No Minecraft or real mainline A is created.

The strongest observed causal evidence is isolated TEST_ONLY ACore lifecycle
adoption with authoritative persistence and process recovery. Because complete
regression has not passed, this stage is not accepted/frozen PASS. Even a later
PASS could not establish canonical Minecraft authorship, arbitrary structural
execution, philosophical consciousness continuity, behavioral closure or L1.
Stop here; no implementation commit, push, closeout or next stage.
