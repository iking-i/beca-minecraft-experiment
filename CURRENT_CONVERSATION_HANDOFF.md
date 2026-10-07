# Current conversation handoff — 2026-10-07

**Status:** ACTIVE WORKING HANDOFF — not a formal phase closeout.

## Repository-state warning

This handoff records the latest state reported from the user's local worktree. The accessible remote branch is older than that local state.

Locally reported commits not present on the accessible remote branch:
- `ca956f4832e680d31bb7c8eaa79a1e46663aa1d7` — current-structure / live FROI memory-runtime correction
- `ed88877535375f42a51cd479518cbb5673f28db2` — termination observability
- `6c017dc58ca8e38696ba1db5c402e186cfad0aa3` — long-run current-structure closeout

The startup-validation repair was reported as uncommitted.

Do not use remote main or this handoff branch alone to infer the current local implementation. The local worktree and executed evidence remain authoritative.

## Completed long-run evidence

Latest completed long-run:
- Individual: `A-24f4fd0f-e83a-4ea2-9db6-2c351c9cfe05`
- Session: `S-f4a2c0a1-b26e-4503-974c-ea9cf27e1834`
- Final state: `A6327`
- Final event sequence: `62646`
- Observations: 2727
- Actions executed: 920
- Experiences: 2723
- Recursive outputs: 2723
- Integrations: 2723
- Core RSS peak: 86.39 MiB
- Final InternalState: about 0.597 MiB

Accepted closeout:
```text
MEMORY_RUNTIME_BOUNDARY = PASS
LONG_RUNNING_REAL_BODY_WORLD_LOOP = PASS
FULL_HISTORY_RAM_REGRESSION = NOT_OBSERVED
CORE_RAM_LIMIT_REGRESSION = NOT_OBSERVED
TERMINATION_OBSERVABILITY = NOT_VALIDATED
STOP_REASON = USER_CLOSED_TERMINAL
```

Do not reopen or rerun this stage without new contradictory evidence.

## Memory / history boundary

```text
CURRENT STATE      = required for continuation
FULL AUDIT HISTORY = optional external evidence
```

Full EventStore history is not A's operating memory. Runtime recursion uses current retained structure rather than replaying the complete historical EventStore.

## Startup verification repair

The Launcher full-history verification bottleneck was identified and repaired locally.

Reported result:
```text
STARTUP_FULL_HISTORY_SCAN = NO
NORMAL_START_CALLS_FULL_VERIFY = NO
FULL_VERIFY_PRESERVED = YES
A_RUNTIME_CHANGED = NO
HISTORY_MODIFIED = NO
```

Measured locally:
- Launcher ready: about 0.646 s
- lifetime list: about 0.239 s
- lightweight current-boundary validation: about 0.024 s
- read-only prepare with locks/caps: about 0.148 s
- regression: 451 passed, 114 subtests passed

Reported modified files:
- `launcher.py`
- `individual/storage.py`
- `individual/startup_validation.py`
- `tests/test_startup_validation.py`

At handoff this repair was not committed or pushed.

## Current persistence blocker

The requested Launcher option “Save full history” has not been implemented yet.

Read-only audit established that current-state persistence and full audit history are coupled in the same append-only transition path. Simply disabling history writes would make resume restore an older state.

Current status:
```text
CURRENT_STATE_STORE_ADDED = NO
FULL_HISTORY_OPTION_ADDED = NO
EXISTING_HISTORY_MODIFIED = NO
```

Immediate authorized engineering work:
```text
decouple authoritative Current State persistence
from
optional Full Audit History persistence
```

Required semantics:
```text
CURRENT_STATE_PERSISTENCE = ALWAYS_ON
FULL_AUDIT_HISTORY        = OPTIONAL
```

Existing historical rows must not be deleted, pruned, VACUUMed, compacted, or rewritten.

After the persistence split is verified, add the Launcher Full History ON/OFF control.

## Current formal runtime and research boundary

Current formal runtime uses FormalFROI + asynchronous worker + current retained structure.

Current evidence establishes:
```text
real input
-> internal relation/evidence/organization changes
-> those changes can affect later internal read/processing
```

Current formal body-action path remains:
```text
available native action codes
-> select_uniform_action()
-> fixed LCG/modulo selects action code
-> bind_parameters()
-> fixed/LCG parameter-domain selection
-> formal command
-> body execution
-> renewed real observation
```

Formed relation/organization/feedback does not currently enter the formal action-code or parameter-selection formula.

Therefore:
```text
formed internal structure -> later internal processing   YES
formed internal structure -> formal body-action content NOT YET ESTABLISHED
```

This is not evidence that A was taught Minecraft. A may have a high origin point without being given Minecraft knowledge.

## Next research causal boundary

After persistence maintenance is complete, the next research question is:

```text
Can A's own later-formed internal structure become the source of a body expression
that is only mechanically validated and then executed through the existing body?
```

This research stage is NOT_STARTED.

Do not prewrite Minecraft goals, walkthroughs, reward scoring, selectors, success-action repetition, hidden preference/ranking, fixed long-term purpose, or solutions to future limits.

The host may validate and execute an expression that A has formed. The host must not author the expression content merely to create a predetermined next step.

## Theory reference

Theory repository: `iking-i/beca-architecture`, branch `main`.

Current theory HEAD at handoff:
`a3a3d1e5eb1157f499894200286320c2093ee199`

Current theory points:
- `B0` body, `E0` environment, `I0` internal are origin-given constraints.
- Their shared property is `NOT_SELF_AUTHORED_AT_ORIGIN`, not permanent immutability.
- `Need_origin + Purpose_origin` may determine origin conditions, but do not automatically become A's own need/purpose.
- From an individual-local viewpoint the two primitive recursive domains are environment recursion and individual recursion.
- New individuals / recursive origins are possible recursive results, not a third primitive domain.
- Recursive-domain direction is distinct from downward/upward recursive-layer direction.

## Resume point

On the next conversation:
1. read this handoff first;
2. inspect the actual local Git state;
3. continue only the already-authorized Current State / Full Audit History persistence split;
4. then add the Full History control;
5. only after infrastructure is stable, return to the formed-internal-structure -> body-expression research boundary.

Do not invent another research phase merely because the conversation ended.

## 12. Assistant-generation inheritance

The collaboration-generation handoff from 四号 to 六号 is preserved separately in [ASSISTANT_GENERATION_INHERITANCE.md](ASSISTANT_GENERATION_INHERITANCE.md).

This record is collaboration provenance only. It does not change research authorship, theory authorship, or experiment evidence status.
