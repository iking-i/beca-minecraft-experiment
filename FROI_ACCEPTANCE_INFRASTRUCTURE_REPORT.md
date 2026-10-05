# FROI-1 acceptance infrastructure completion

Scope: EXPERIMENTER / TEST_ONLY / AUDIT tooling only. The normative FROI-1
acceptance criteria, runtime semantics, GSC rules, codec and formal caps are
unchanged. This report is about facilities, not a formal FROI result.

## Facilities delivered

| Item | Facility | Status |
|---|---|---|
| Artifact | Immutable ordered JSON; typed safe decoding; checkpoint/request/job/history/handle/source bindings; full graph/supports/roots/registry; original and next-round records | READY |
| T1 | Read-only source DB verification, complete prefix, current and historical raw frame encoding, feedback/origin, seeds/declarations/roots/lineage and incomplete-experience exclusion | READY |
| T2 | Explicit paired recorded prefixes; fixed union Condition and caps; existing producer; dedicated historical-intervention adapter; identical checkpoint/request; real consumer and shared resume | READY |
| T3 | Saved handle recovery without closure; exact normal replay gate; fixed journal exclusions and original post-read entropy; same checkpoint/handle normal versus effect-screened resume | READY |
| T4 | Exact raw consequence chain tracer and isolated continuation with the next actual recorded observation | READY |
| T5 | PRE/POST sources, commit, manifest, database content/files/ranges and immutable input checks; frozen-code binding to engineering controls; COMPLETE gate for all used graphs | READY |
| Unified entry | `python -m debug.froi_acceptance export/validate` with independent item statuses and exclusive external output files | READY |

All these additions are experimenter measurement/recovery tools. No missing
facility is filled by adding an A capability. The frozen runtime continues to
reject detached writeback and alternative formal checkpoint cutoffs.

## Engineering validation

- Full Python regression: **226 tests, zero failures/errors**. This includes
  **30 new acceptance-facility controls** and the existing checkpoint/FROI,
  worker, launcher, formal runtime and world-entry regressions.
- Frozen GSC-0/GSC-1 regression: **44 tests passed**.
- Existing result-dependence controls: **8 tests passed**; both classifications
  remain DERIVED_RESULT_NOT_CAUSALLY_NECESSARY.
- Minecraft body regression: **42 tests passed**. The restricted initial run
  passed 40 and hit sandbox EACCES on two local transport tests; the authorized
  local-fixture rerun passed all 42. No Minecraft world was contacted.
- After the final provenance/manifest-freeze checks, the **30 facility tests**
  were rerun. Their result is recorded in the machine-readable report.

One intermediate full regression encountered the unchanged Supervisor's
storage-sampling race: a SQLite `-shm` file disappeared between is_file() and
stat(). The isolated scheduling test passed on rerun. The error evidence is
retained in the JSON report and the final full-regression rerun is recorded
separately. No Supervisor repair or test relaxation was made in this scope.

The tests use isolated TEST_ONLY material. They do not substitute for real
T1--T5 acceptance. No formal T1--T5 was automatically executed, no new formal
A was started, and no existing database was modified.

## Protection and baseline

The received workspace already contained the explicit ReadCheckpoint work in
individual/core.py, individual/formal_froi.py, integration/froi.py,
integration/read_checkpoint.py and tests/test_read_checkpoint.py. Those pending
changes are preserved and included as the prerequisite source boundary when
recording the frozen implementation commit. This round does not change their
received contents or the live path semantics.

Before/after SHA-256 comparison covers **78 received runtime/config/spec files**
and **6 original database/WAL files**. The changed sets are empty. Machine-local
port configuration and selected lifetime pointers are not pinned as source
mechanisms by the portable freeze manifest; actual identity, caps, history and
database contents remain bound in each exported artifact.

## Remaining material prerequisites, not missing facilities

- A unique saved exact read checkpoint and COMPLETE handle at a specified
  actual round. Older rounds without that record are not reconstructed by
  guessing UUIDs or rerunning the prefix.
- Two explicitly predeclared complete recorded historical prefixes, both
  producing COMPLETE organizations under the unchanged caps and common domain.
- The next real observation for a claimed re-entry or detached continuation.
- A quiescent source database whose freeze remains unchanged during acceptance.

Unavailable inputs return MATERIAL_UNAVAILABLE or NOT_TESTABLE. Unsuccessful
counterfactual or ablation effects return their actual result. An incomplete
graph or mere causal trace through RESOURCE_LIMIT cannot satisfy the formal
all-COMPLETE condition. No favorable history search, cap increase, pruning,
query substitution, semantic routing or action authorship is supplied.

## Frozen operation

Usage and exact boundaries are documented in FROI_ACCEPTANCE_HARNESS.md.
The implementation commit, regression evidence and protected file hashes are
recorded in FROI_ACCEPTANCE_FREEZE.json and the corresponding JSON report.

**FROI-1 ACCEPTANCE HARNESS FROZEN** is valid only when the final engineering
controls and frozen source/hash checks in that report pass. Future live results
must not trigger changes to v1. A genuine tool bug requires a versioned harness
and an explicit re-audit of prior applicability.

```text
FROI_ACCEPTANCE_INFRASTRUCTURE: COMPLETE
T1_INFRASTRUCTURE: READY
T2_INFRASTRUCTURE: READY
T3_INFRASTRUCTURE: READY
T4_INFRASTRUCTURE: READY
T5_INFRASTRUCTURE: READY
LIVE_RUNTIME_SEMANTICS_CHANGED: NO
A_CAPABILITIES_CHANGED: NO
GSC_RULES_CHANGED: NO
FROI_CODEC_CHANGED: NO
CAPS_CHANGED: NO

Formal T1: NOT_EXECUTED
Formal T2: NOT_EXECUTED
Formal T3: NOT_EXECUTED
Formal T4: NOT_EXECUTED
Formal T5: NOT_EXECUTED
```
