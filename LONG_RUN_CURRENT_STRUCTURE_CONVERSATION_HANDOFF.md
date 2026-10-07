# Long-run current-structure validation — formal conversation handoff

Date: 2026-10-07. Research-method guardrail: 00_DISCUSSION_CONSTRAINTS.md §§16–30.
**Memory/runtime boundary long-run validation: COMPLETED / FROZEN.**
**Next direction: initial-constraint / A0 constraint audit — NOT_STARTED / NOT_IMPLEMENTED / NOT_YET_SPECIFIED.**

## Stable baseline and evidence anchors

- Branch: `codex/operative-connection-correction`.
- Runtime implementation: `ed88877535375f42a51cd479518cbb5673f28db2`.
- Closeout anchor: commit containing this handoff; resolve with
  `git log -1 --format=%H -- LONG_RUN_CURRENT_STRUCTURE_CONVERSATION_HANDOFF.md`.
- Individual: `A-24f4fd0f-e83a-4ea2-9db6-2c351c9cfe05`.
- Session: `S-f4a2c0a1-b26e-4503-974c-ea9cf27e1834`.
- Local canonical evidence: `storage/individuals/A-24f4fd0f-e83a-4ea2-9db6-2c351c9cfe05/individual.db`;
  external process evidence: sibling `individual.supervisor.db` and
  `process-evidence/0bd7d1b28022402496cfa015808f8c15/`.
- Final committed state **A6327**, final event **62646**; external supervisor
  watermark **6341**. Repeated read-only audit watermarks were unchanged.
- Theory reference stays `iking-i/beca-architecture/main` at
  `546363ffd9e3f55cd22cd73ad2e91cc57f93bae3`; no theory changes or new theory rules.
- Full local databases/history/logs remain on this machine, unchanged and uncommitted.
  No unrelated untracked TEST_ONLY material is included in this closeout.

## Frozen run evidence

| Evidence | Value |
|---|---|
| Session start, Beijing | 2026-10-07 17:22:36.588105 |
| Last committed state time, Beijing | 2026-10-07 18:22:15.803658 |
| Recorded runtime span | 3579.215553 seconds, approximately 59 min 39.216 s |
| Actual process/session end time | UNKNOWN; last commit is not an exit timestamp |
| Observations | 2727 |
| Action requests | 1365 |
| Actions executed | 920 |
| Actions failed | 445 |
| Experiences | 2723 |
| Recursive partial outputs | 2723 |
| Integrations | 2723 |
| Reference-checked successful real complete loops | 920 |
| Core start RSS | 19.19140625 MiB |
| Core sampled peak RSS | 86.39453125 MiB |
| Core last sampled RSS | 50.36328125 MiB |
| Bridge sampled peak RSS | 283.28125 MiB |
| Bridge last sampled RSS | 105.85546875 MiB |
| Final compact UTF-8 InternalState | 625543 bytes, approximately 0.597 MiB |

Core means in four successive equal-sample-count segments were approximately
48.57 → 57.58 → 62.85 → 60.01 MiB. No sustained monotonic uncontrolled growth
was observed. These are process RSS samples, not A's internal memory size;
the sampled peak is not a continuous peak measurement and the last sample is
not a measurement taken at process exit.

The 920 loops were checked by action identity, exact request/receipt code and
parameters, prior frame/processing, renewed real frame, associated experience,
recursive partial and integration references. The recorded chain is:

```text
real Minecraft observation → A internal processing → action request
→ real execution receipt → renewed real Minecraft observation → experience
→ recursive partial output → integration → feedback / continuation
```

All 2722 submitted FROI jobs have returned records: 4 COMPLETE and 2718
RESOURCE_LIMIT. Another five execution records are CANCELLED with
`bridge_status_changed`; they do not constitute unreturned submitted jobs.
Final FROI RESOURCE_LIMIT was normally consumed at A6327. Its nodes request
was 259 against cap 16, before expansion (operations 0 / rounds 0).
This is not `core_ram_limit`; caps were not raised. Five persisted pending
consequences are recursive materials, not proof of pending computation.

Read-only integrity evidence: SQLite quick_check `ok`, no foreign-key violations,
and no states missing state_sessions mapping. Final persisted status remains
`running` because no session end was recorded; do not alter it to manufacture closure.

## Accepted operational conclusions and exact scope

```ini
MEMORY_RUNTIME_BOUNDARY = PASS
FULL_HISTORY_IN_LIVE_RUNTIME = NO
FULL_HISTORY_RAM_REGRESSION = NOT_OBSERVED
LONG_RUNNING_REAL_BODY_WORLD_LOOP = PASS
REAL_BODY_WORLD_LOOP_SUSTAINED = YES
CORE_RAM_LIMIT_RECURRED = NO
CORE_RAM_LIMIT_REGRESSION = NOT_OBSERVED
```

All 2722 formed organizations record `external_history_loaded=false`;
`FROI_INITIAL_CONDITION.raw_history_retained=false`. A uses its current retained
structure plus current input. Complete EventStore history remains external
experimental audit history, not live runtime memory. This is a scoped operational
result, not a universal memory/need/purpose rule.

## Stop provenance and termination-observability boundary

The user's post-run clarification establishes that the observer intentionally
closed the terminal hosting the experiment. It was not an in-program controlled
Ctrl+C shutdown. This clarification is observer testimony, not a recovered
supervisor termination event or inferred exit code.

```ini
SYSTEM_SELF_TERMINATION = NO
OBSERVER_INTENTIONAL_STOP = YES
STOP_METHOD = USER_CLOSED_TERMINAL
PROGRAMMATIC_CONTROLLED_STOP = NO
SESSION_ENDED_RECORDED = NO
TERMINATION_EVIDENCE_COMPLETE = NO
TERMINATION_OBSERVABILITY_VALIDATED = NO
TERMINATION_OBSERVABILITY = NOT_VALIDATED
STOP_REASON = USER_CLOSED_TERMINAL
```

SYSTEM_SELF_TERMINATION=NO means no evidence of a system decision to end or
recursive completion causing termination; it is not a reconstructed OS root cause.
Core PID 24004, Bridge PID 54108 and supervisor/host PID 704 were absent at audit.
No final Core/Bridge exit code, kernel exit time/order, MANUAL_CONTROL,
TERMINATION_REQUESTED, kill request or supervisor finalization record exists.
Thus observer intent is established by testimony, while the programmatic stop
and exit evidence remain unavailable.

The external instrument retained stdout/stderr and 522 child exit observations,
but this does not validate final controlled termination. Terminal closure bypassed
the program-internal controlled stop path; missing final evidence must not be
classified as observability implementation FAIL, nor may the partial capture be
classified PASS. No controlled-stop test is added or rerun in this closeout.

Local log evidence anchors:

- `core.stdout.log`: 223366197 bytes;
  SHA256 `3db3e736fe686e95c0fe18ac19875d0a6cb5c92c4829ee9d131ec0934a873033`.
- `core-and-forwarded-bridge.stderr.log`: 858 bytes;
  SHA256 `30b27822b727aa169b41c87076ddf7da617b2a7b8c5d939ece25ba0e3531ce5a`.
- No persisted supervisor traceback file was found; captured stderr contains no
  traceback establishing the final stop cause. Do not fabricate missing evidence.

## Minimal historical comparison

| Evidence | Old full-history RAM-limited run | This current-structure long run |
|---|---|---|
| Individual | A-9896e8eb-990e-48c7-ac30-694c2686d438 | A-24f4fd0f-e83a-4ea2-9db6-2c351c9cfe05 |
| Session | S-ae0b5775-0bd6-4e91-bc4b-85f9ce603779 | S-f4a2c0a1-b26e-4503-974c-ea9cf27e1834 |
| Final state | A603 | A6327 |
| Observations | 130 | 2727 |
| Successful complete loops | 44 | 920 |
| Core sampled peak | 555.203125 MiB | 86.39453125 MiB |
| SESSION_ENDED | YES; core_ram_limit | NO; observer closed terminal |
| core_ram_limit | Recorded, above 512 MiB | Not observed |

The comparison supplies evidence that the old full-history runtime memory blocker
was removed and real recursion continued at a longer scale in this implementation.
It is not a same-individual randomized control, does not solve memory universally,
and supports no additional theory conclusion. Old evidence is not overwritten.

## Nonclaims, verification and next handoff

- No specific world-effect causal law or internally authored behavior is proved.
- No L1/upward recursion, universal dynamics or validation of all Perfect Recursion.
- No universal memory solution, indefinite resource adequacy, or internal need/purpose mechanism.
- No successful or failed controlled-termination-observability validation.
- Prior BPC / Successor / FROI / GSC / CEC results and their interpretation boundaries
  remain frozen; formal default sampler/binder authorship remains external.
- This is documentation-only closeout. No runtime, tests, caps, policy, process
  initialization, temporal relation evaluation, memory logic, FROI/GSC or termination
  observability changes; no A/Minecraft, experiment, Ctrl+C test or regression rerun.
  Text diff, JSON parsing and preservation checks only; no new test PASS is claimed.
- Sections 29/30 are unchanged; their discussion content is not converted into
  implementation or new theory rules.
- Known pre-closeout regression record at the implementation anchor: process
  evidence dedicated tests 10 passed; full Python regression 433 passed,
  1 failed, 114 subtests passed. The old behavioral audit's `canonical_unchanged`
  guard failed on canonical SQLite `-shm` mtime change with unchanged content hash,
  also reproduced with the baseline Supervisor restored in memory. That result
  remains historical; this archive neither fixes it nor claims a new green suite.

**Current standing: memory/runtime boundary long-run validation completed.**
Next direction is initial-constraint / A0 constraint audit only:
**NOT_STARTED / NOT_IMPLEMENTED / NOT_YET_SPECIFIED**. No initial-constraint
conclusion, research question, acceptance boundary, implementation or experiment
is supplied here. Do not begin that audit or repair termination observability
as part of this archive. Stop after the local documentation commit; do not push.
