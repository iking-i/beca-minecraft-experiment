# Formal A Continuous Operative Reentry — validation

2026-10-08. Base: `76fee923fd1ea2d3b4697e299f1c35f9d6c8817e`.
**Classification: PASS. CR-T1–CR-T10 PASS.**
The containing independent implementation/validation commit is the evidence anchor.
The original NOT_TESTABLE report and JSON remain byte-for-byte under
`history/tk_not_testable_original/`. Original failed runs remain historical failures.
No old test, criterion, frozen hash or operative rule was changed to obtain PASS.

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
| ON | A-6d7863ca-15e6-4139-b79c-eb019b9fef18 | 3568 / 31852 | S0 A1; formation A3; shutdown A4; restart A5; shutdown A9 | 10 / 58 |
| OFF | A-9936dfcc-503f-4bb3-bcd4-ff0441f572ee | 2828 / 6552 | S0 A1; formation A3; shutdown A4; restart A5; shutdown A9 | 0 / 0 |

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
| CR-T10 | PASS | Original complete suite passes without exclusions; all 13 frozen hashes match; default/GUI tests unchanged. |

The paired controls enter through an independently restored Core's ordinary
accept_observation. After its normal carrier-gap input, each branch has exactly
the same current state, observation, version and pending actions. Only the engine
input edge S1 is masked, with all relation records, feedback and supports retained.
Reinserting S1 gives exact input equality. Both branches execute actual engine
processing and are stopped at `_commit_observation` before any control commit;
neither supplies an answer through a side consumer. No formal history is altered.
The normal result is True and S1-only branch None in both ON/OFF measurements.

## Revalidation and Tcl/Tk responsibility boundary

- focused: **28 passed / 0 subtests passed**, 17.49 s; no exclusions.
- related: **161 passed / 23 subtests passed**, 39.78 s; no exclusions.
- frozen_guard: **1 passed / 13 subtests passed**, 0.16 s; no exclusions.
- full_regression: **560 passed / 114 subtests passed**, 327.22 s; no exclusions.
- original_environment_full: **560 passed / 114 subtests passed**, 330.44 s; no exclusions.

The original 559-pass/1-failure run remains NOT_TESTABLE, not retroactively PASS.
The exact failing Monitor test raises inside `tk.Tk()` before Monitor/Core creation.
The direct cause is Tcl/Tk bootstrap reporting that `ttk/utils.tcl` could not be read.
Subsequent file checks, the same-interpreter single test, pure Tk and 30 successive
pure Tk initializations all pass. The original HEAD's identical Monitor test also
passes. Current recording-option -> Monitor sequence passes. The original HEAD's
sequence has three non-GUI failures due solely to absent ignored
`minecraft/config.json`; its Monitor tests pass. No baseline environment was patched.

A read-only full-run probe records unmodified tkinter module/class, library hashes
and relevant environment at each Monitor test; that original-environment full run
passes. The original error's triggering cause remains NOT_ESTABLISHED: these checks
do not prove permanent missing files, DLL damage, an operative regression or a
particular test-order leak.

Final verification uses the identical Python interpreter and DLLs, with a complete
1265-file byte-identical Tcl/Tk script library copied outside the repository. Only
verification child-process TCL_LIBRARY/TK_LIBRARY paths are bound to that copy.
Its real Tk initializes successfully at both current and original HEAD; the final
unmodified `python -m pytest` collection includes Monitor and passes in full.
This supplies a functioning independent verification environment, not a proven
permanent cure for an unknown intermittent host trigger. System configuration,
production startup and test expectations are unchanged. No skip, xfail or Tk mock
was introduced. See `TK_DIAGNOSIS.json` and `TK_LIBRARY_MANIFEST.json`.

The process-restart, authoritative-current-state, S1-only actual-operand ablation
and provenance controls were rerun. New complete machine evidence is in
`VALIDATION.json`; no earlier causal PASS was merely carried forward.
All raw logs are preserved locally; because repository *.log files are ignored,
`history/RAW_LOGS.json` commits lossless base64 raw bytes, raw SHA-256 and UTF-8 text
for both original failures and new passes. Earlier facility and related failures
and the original NOT_TESTABLE narrative are retained without rewriting.

## Preservation and limits

FormalL0 LF-normalized SHA-256 remains
`1b6abea5d568c349bf7c181ecd771fc6f08cd0f1791fa49be7434c4acd354b62`.
All 13 frozen component hashes match. Previous FA/OH/BPC/FROI/GSC/CEC/Successor
source, tests, specs, validation, failures and state closeouts remain byte-identical.
No database outside independent test directories, body, sampler/binder, caps,
selection, theory or unrelated untracked material is changed. Research-state
indexes are not updated. No Minecraft or real mainline A is created.

The accepted claim is restricted to an independent TEST_ONLY ACore lifecycle:
S0 and experience-formed S1 use the same representation/execution mechanism; S1
is saved by authoritative Current State, survives an actual process restart, and
becomes an ordinary recursive dependency with actual-computation ablation evidence.
It does not establish canonical Minecraft authorship, arbitrary structural execution,
philosophical consciousness continuity, behavioral closure or L1.

Independent implementation/validation commit only; no push, phase closeout,
research-state update or next-stage implementation is performed here.
