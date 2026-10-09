# Observation Source Boundary — second real acceptance

Date: 2026-10-09, Asia/Shanghai. Baseline:
`f2d66102755038dad688a20189767ded24651b0e`.
Classification: **PARTIAL**. The complete eight-OFF/eight-ON protocol was **not completed**.
No existing implementation, previous PARTIAL report or offline result is replaced.

## Conditions and preflight

Port 63212 was confirmed by the experimenter. Peaceful difficulty is an
**EXPERIMENTER_SUPPLIED_ENVIRONMENT_CONDITION**, not A's capability or a native
measurement: the existing body observation interface does not expose difficulty.
Before creating A, the same new experiment body was connected and observed twice,
with no perform or respawn. Health was positive and did not fall; no hostile
entities or near observed damage blocks were found. This bounded sample is not
a proof that the entire world is safe. The probe was closed normally.

The two Core segments then used a new isolated database:
`.test-tmp/source-boundary-live-63212-20261009-peaceful1/individual.db`.
Original private configuration, preflight observations, per-frame raw inputs,
pre/post states, logs and RSS samples remain in that directory. No existing DB
was selected, migrated, overwritten or modified.

## Identity and actual lifecycle

Individual throughout: `A-87cd4a08-65a3-4d51-81ad-49b00343e8a4`.

| Segment | Core / Bridge PID | Session | Frames | Observation states | Shutdown |
|---|---|---|---:|---|---|
| OFF | 28160 / 29172 | `S-fc03952a-906e-43f0-94cb-7b4a82309dd0` | E1–E8: 8 | A5–A12 | A13, normal |
| ON | 34260 / 25928 | `S-47fcc6f7-e2a0-4097-a498-96853d34f4ac` | E9: 1 | A18 | A19, normal |

OFF ran 21:02:01–21:02:23; ON ran 21:02:24–21:02:28. At A14 the new
process opened a new Session from the same authoritative Current State. Its
restored InternalState exactly equalled the first segment's shutdown InternalState;
all eight source bodies and the two formed typed connections were retained.
No origin reinjection, replay or reconstruction occurred.

OFF formed seven experiences and seven integrations. ON committed E9 but formed
no E8→E9 experience/integration. No death, perform, sampler or binder call occurred.

## Why the second segment stopped

The existing `individual/events.py:251` `open_session()` sets a resumed Session's
carrier epoch to `max(previous.carrier_epoch, previous_frame.body_epoch) + 1`.
Thus normal process/Session restart changed epoch **0→1**, before real E9 arrived.
The unchanged ordinary FormalL0 processing recorded:

```
TEMPORAL_LINK_UNRESOLVED
frame_ids = [A-87cd4a08-65a3-4d51-81ad-49b00343e8a4:E8,
             A-87cd4a08-65a3-4d51-81ad-49b00343e8a4:E9]
reason = carrier_epoch_or_encoding_changed
state_version = 18
```

The current acceptance explicitly stops on epoch/temporal interruption. The
external recorder therefore stopped after E9 and closed normally. No suppression,
extra frames, respawn, silent repair or changed mechanism was used.

This is a documented lifecycle/temporal boundary, not observed death, corruption,
lost A identity, lost source data or a demonstrated storage defect. It nevertheless
prevents declaring the full requested protocol PASS. Identity/state continuity
must not be confused with uninterrupted physical/temporal sampling continuity.

## Per-frame resource measurements

Every frame retained all **376 numeric channels, 64 object references and 47 native
capabilities**. No capability/input filtering or cap increase occurred.

| Frame / state | Unit/content charge | InternalState bytes | Whole state JSON bytes | Source bodies / bytes | Runtime source reads / bytes | Processing seconds |
|---|---:|---:|---:|---:|---:|---:|
| E1 / A5 | 3/64 | 185,716 | 326,662 | 1 / 25,526 | 1 / 25,526 | 0.176 |
| E2 / A6 | 4/64 | 172,402 | 286,668 | 2 / 51,052 | 2 / 51,052 | 0.458 |
| E3 / A7 | 4/64 | 183,623 | 305,294 | 3 / 76,578 | 3 / 76,578 | 0.713 |
| E4 / A8 | 4/64 | 192,929 | 314,600 | 4 / 102,104 | 4 / 102,104 | 0.738 |
| E5 / A9 | 4/64 | 202,131 | 323,802 | 5 / 127,630 | 5 / 127,630 | 0.766 |
| E6 / A10 | 4/64 | 211,339 | 333,012 | 6 / 153,156 | 5 / 127,630 | 0.758 |
| E7 / A11 | 4/64 | 212,024 | 334,305 | 7 / 178,682 | 5 / 127,630 | 0.749 |
| E8 / A12 | 4/64 | 212,180 | 335,068 | 8 / 204,208 | 5 / 127,630 | 0.751 |
| E9 / A18 | 4/64 | 203,972 | 319,146 | 9 / 229,734 | 5 / 127,630 | 0.676 |

Four Units, two typed connections and zero Pair/EffectRoute remained at E9.
No live Pair formation or cross-process Pair reuse is claimed for this quiet run;
existing offline controls and the first live partial evidence remain separate.

| Segment | RSS initial | RSS sampled peak | RSS final | Total observation processing |
|---|---:|---:|---:|---:|
| OFF | 30.324 MiB | 52.473 MiB | 45.012 MiB | 5.109 s |
| ON | 30.562 MiB | 50.465 MiB | 41.945 MiB | 0.676 s |

RSS is sampled every 50ms for the complete worker, including external logs, state
copies and validation/audit instrumentation. Timings include access recording;
neither is an isolated A-only or dedicated benchmark. SQLite file/logical page
allocation after close: **4,960,256 bytes**; source bodies: **229,734 bytes**.
File size includes schema, indexes, current state and optional ON history, not
just source bodies.

The live state's observation archive is a fixed-size authority descriptor, not
the nine historical source bodies. It retains its current source and existing
bounded observation registers/window. State size still changes with actual
registers, metadata and structures. These nine frames prove neither constant
state/RSS nor unbounded future running. E6–E9 runtime access stayed at five decoded
body reads despite archive count increasing; this is a measured bounded interval,
not a general complexity proof.

## Persistence, references and evidence checks

- All nine committed current source registers exactly match their authoritative
  source rows. Their digests/index/hash-chain audit passes after close.
- Every live frame's Current State equals the published in-memory state. Source
  count and archive descriptor advance together through the existing transaction.
  No new crash injection is claimed; atomic fault controls remain offline evidence.
- OFF retains eight bodies despite zero optional observation events. The explicit
  audit gap is A0–A13. Optional states begin at A14, and the only recorded ON
  WORLD_OBSERVATION is E9. No OFF observations were backfilled into audit history.
- The new process restored the same A and parsed old authoritative facts during
  ordinary processing. Its separately labelled read-only E1 FactRef probe succeeded.
- Post-close probes resolve E1's exact frame/channel/digest and numeric ObservationRef.
  Old-epoch object references, forged digests and absent/foreign frames reject.
  These probes are external instrumentation, not new input or an autonomous query.
- Both session-end records exist; A19 matches final authoritative Current State.
- Known corruption-detection timing remains unchanged: accessed sources are checked
  during execution; unrelated corruption can require explicit full source audit.

Machine evidence: `LIVE_VALIDATION_2.json`, with hashes of public files in
`live_evidence_2/` and private-directory raw evidence files (excluding private config
and DB content). The SQLite DB itself has a separate digest.

Existing test logs remain **21 focused / 88 related / 784 full + 114 subtests**;
they were verified, not rerun or represented as new test executions. All eleven
offline evidence hashes, thirteen frozen LF hashes, 512 protected old files,
27 unrelated files, all preexisting uncommitted module/report files and both older
real DB digests match. No runtime/implementation, theory, old evidence or current
research index was modified. No commit, push or stage freeze.

## Accepted scope and remaining boundary

Real OFF source persistence, restored A/InternalState/source identity, ON recording
and exact historical numeric access are supported by this run. The full two-part
budget and additional ON experiences remain incomplete. Live Pair reuse and a new
body feedback loop were not demonstrated and are not required to invent an action.
The external peaceful environment is never attributed to A.

The earliest actual remaining boundary is **normal new-Session epoch advancement
plus the required stop at the resulting temporal-link gap**. No automatic mechanism
change or further run follows this report. Await the next decision.
