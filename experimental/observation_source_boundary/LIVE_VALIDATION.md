# Observation Source Boundary — isolated real validation

Baseline: `f2d66102755038dad688a20189767ded24651b0e`.
Classification: **PARTIAL**. Complete two-process OFF→ON acceptance: **NOT_TESTABLE**.
This report does not freeze the stage or replace the saved offline validation.

## Run and stopping boundary

The world was reached at the user-confirmed port 63212. A fresh independent database
and individual were created; no bootstrap, world intervention, sampler, binder,
synthetic receipt, replay, reconstruction, reconnect, or respawn was used.

- Individual: `A-d5b960f4-ba3d-44b2-a6bc-a94096fe17e7`.
- Session: `S-631c3b69-a8dc-4768-8d56-25247c877cbd`.
- One Core process, Full History OFF, four committed real frames E1–E4.
- Three experiences and three integrations; final observation state A8.
- Native BODY_DIED was received with body timestamp `2026-10-09T12:33:46.121Z`.
  The event was consumed after the in-progress observation processing, at A9.
  Physical cause of death is not established by this storage validation.
- Normal external shutdown completed at A10. The reduced session-end record is
  present. No second process/session or ON segment was started after death.

Private configuration and the independent SQLite database remain under
`.test-tmp/source-boundary-live-63212-20261009-run3/`; they are not public evidence.
The saved raw frames, pre/post states, transport, stderr, and 50ms RSS samples are
retained there. Public exact canonical source rows, observed transitions and
measurements are in `live_evidence/`; hashes are in `LIVE_VALIDATION.json`.

## Actual measurements

| Frame / state | Numeric channels / objects / ports | Unit/content charge | Pairs | InternalState bytes | Whole current-state JSON bytes | Source bodies / bytes | Runtime body reads / bytes | Index reads | Processing seconds |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| E1 / A5 | 376 / 64 / 47 | 3/64 | 0 | 185,661 | 326,638 | 1 / 25,523 | 1 / 25,523 | 0 | 0.270 |
| E2 / A6 | 384 / 66 / 47 | 4/64 | 0 | 174,697 | 290,800 | 2 / 51,340 | 2 / 51,340 | 44 | 0.480 |
| E3 / A7 | 384 / 66 / 47 | 5/64 | 0 | 192,182 | 315,679 | 3 / 77,155 | 3 / 77,155 | 377 | 1.880 |
| E4 / A8 | 384 / 66 / 47 | 26/64 | 7 | 226,922 | 350,872 | 4 / 102,969 | 4 / 102,969 | 1,074 | 5.494 |

At E4 there are six Units, twenty content nodes (thirteen ObservationRef and seven
Pair), sixteen typed connections and zero EffectRoute. No capacity cap changed.
No perform request or execution occurred; this is not a body-loop failure criterion.

RSS: initial 30.273 MiB, sampled peak 47.664 MiB, final 43.434 MiB. This is the
worker process including bounded external recording, state copies and diagnostic
work, not an isolated measurement of A's structure alone. Processing timings
include source-access instrumentation; they are not a clean speed benchmark.
This four-frame run cannot establish bounded long-run memory or read complexity.

## Storage and reference evidence

For each committed frame the live state equalled authoritative Current State and
the descriptor count matched committed source rows. Full History OFF left optional
`states` and `events` empty while all four source bodies remained authoritative.
The normal session-end and audit-gap metadata were retained independently.
External transition observations are explicitly labelled external evidence; they
are not fabricated database events.

During ordinary E2–E4 processing, exact historical source reads were observed.
E4's ordinary constructor consumed seven typed connections and produced seven
Pair, with exact endpoint/support identities retained in the evidence. Separate
read-only historical ObservationFactRef probes also resolved E1 by frame, channel
and digest; these probes were not fed into A and are not claimed as autonomous
recursive queries. Pair reuse on a subsequent live frame was not reached.

After shutdown, an independent read-only reopening audited all four sources and
their index/hash-chain consistency. Missing source, wrong individual identity and
wrong digest each rejected in separate SQLite backup controls, with no writes
during validation. The actual real-run database hash remained unchanged by these
checks. No corruption was introduced into the real database.

Same-transaction source/state publication is observed at successful real commits.
Crash/rollback fault safety remains supported by existing offline tests; no live
fault injection was performed. The known change in corruption detection timing
remains: accessed witnesses are checked during processing; unused old bodies may
require direct access or explicit full audit for detection.

## Completed and outstanding scope

- Real observation admission, ordinary structure construction and OFF authoritative
  source persistence: supported for the four committed frames.
- Post-close exact historical access and full source audit: PASS.
- Fresh-process restoration of this same real A and OFF→ON continuation: NOT_TESTABLE
  in this attempt, because the body died before the first eight-frame segment ended.
- No empirical claim of long-run memory boundedness, purpose/need-based retention,
  autonomous action choice, world causal law or renewed body feedback loop.

The environment death is new live evidence, not a demonstrated source-storage bug.
The full planned real acceptance is incomplete, so no full real PASS/freeze is
declared. A closeout can preserve this partial attempt; a successful two-segment
real validation closeout is not yet justified.

## Existing tests and preservation

Saved logs and all eleven evidence hashes were checked, without repeating offline
research: 21 focused, 88 related, 784 full regression / 114 subtests passed.
These results predate the added external live recorder; no new full regression is
claimed. Recorder import and actual execution were checked.

512 protected old files, 27 unrelated files and 13 LF-normalized frozen component
hashes match. No tracked file changed, no old evidence/database was rewritten,
and no current research index, theory, runtime or cap was changed. No commit/push.

Earlier attempts remain preserved: run1 failed before Core/Bridge creation because
of the recorder's child-module invocation; that external invocation was corrected.
Run2 obtained zero observations due to sandbox EACCES. Run3 used authorized local
network execution. These records are not converted into successful experiments.
