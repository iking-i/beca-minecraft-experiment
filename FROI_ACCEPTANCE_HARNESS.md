# FROI-1 acceptance harness v1

This is EXPERIMENTER / TEST_ONLY / AUDIT tooling. It supplies measurement,
restoration and intervention facilities, not A capabilities or a new FROI
criterion. The frozen specification remains
`FORMAL_RECURSIVE_ORGANIZATION_INTEGRATION_SPEC.md`.

## Boundaries and entry point

`debug/froi_acceptance_material.py` defines the immutable, digest-bound typed
JSON artifact and read-only SQLite export. `debug/froi_acceptance_checks.py`
provides T1--T5 controls. `debug/froi_acceptance.py` is the explicit external
entry point. None is imported by the formal runtime. No tooling calls
EventStore transitions, creates A, executes actions or connects Minecraft.

Artifacts and reports must be saved externally, for example under
`storage/acceptance/`. They never enter HISTORY_TYPES, GSC input or A memory.
Existing output files are never overwritten. Evidence packs can be large and
contain real observations; they belong in ignored local storage, not Git.

Explicit future usage (not executed by the facility-completion work):

```powershell
.\.venv\Scripts\python.exe -B -m debug.froi_acceptance export --database "storage/individuals/A-.../individual.db" --version 123 --output "storage/acceptance/read-123.json"
.\.venv\Scripts\python.exe -B -m debug.froi_acceptance validate --artifact "storage/acceptance/read-123.json" --pair-versions 80 100 --limit-id "recorded-limit-uuid" --continuation --output "storage/acceptance/validation-123.json"
```

The versions are explicit, pre-supplied complete recorded prefixes of the SAME
individual's history, not an automatic search for useful answers. Do not replace
them after seeing a result. All declarations required by both histories form
one fixed union Condition. Original frozen caps remain unchanged. If either
closure is incomplete, T2 returns NOT_TESTABLE, never partial success.

Use quiescent, unchanged source databases. Export records both database content
and file hashes; later changes, including legitimate ongoing A writes, invalidate
that particular exported acceptance artifact. Read access uses mode=ro and
query_only under transactions. SQLite WAL/SHM are included in the file freeze;
an active writer or SQLite sidecar changes cannot be treated as invariant.

## Exact recovery and T1

Export requires a unique saved exact ReadCheckpoint and unique COMPLETE
FROI_ORGANIZATION_FORMED at the requested version. No prefix is rerun. Old
rounds without this boundary return HISTORICAL_CHECKPOINT_NOT_RECONSTRUCTABLE;
this tool does not manufacture A33/A36 checkpoints.

The saved graph's typed keys and full fact content are restored without running
closure. The codec's seeded Relations reconstruct the omitted Relation table;
the GSC rules do not generate extra Relation instances. This reconstruction is
only handle restoration: the consumer still reads actual Shared/PortBind and
never substitutes raw-history answers. Restored full audit content, digest,
request, cutoff and checkpoint binding must agree with the saved evidence.

T1 independently rereads the DB, verifies complete historical prefixes and all
source identities, actual feedback/origin, current WORLD_OBSERVATION encoding,
recorded frame, codec declarations, seed records, finite roots and lineage
coverage. Current incomplete experience is excluded. TEST_ONLY markers and
known fixture database paths are rejected for formal acceptance. These checks
establish consistency with recorded carrier events, not cryptographic proof that
an adversary could never fabricate a database outside this experiment.

## T2 historical intervention versus T3 screening

T2 uses a dedicated HistoricalIntervention adapter around the unchanged original
checkpoint. It validates each original producer handle against its own verified
real history cutoff and the joint Condition, while requiring the exact original
ReadRequest. It explicitly records that the intervened producer history may not
naturally lead to the fixed interpreter state. It does NOT edit/rebind a
ReadCheckpoint or modify/relax its formal verify_handle contract. The formal
checkpoint continues rejecting an alternative cutoff.

Both T2 branches call existing produce(), consume() and the SAME formal
resume_from_read_checkpoint(..., detached=True). Complete graph content,
actual read keys/supports/roots/conflicts and interpreter outputs are retained.
Graph differences without a real read/check effect cannot pass T2.

T3 first performs UNSCREENED REPLAY. Original post-read UUID creation entropy is
recovered in journal order for CURRENT_LIMIT_ENCOUNTER, RECURSIVE_PARTIAL_OUTPUT
and INTEGRATION_COMPLETED and reinjected ONLY into this isolated replay. The
production UUID rule is untouched. Creation count/order, original UUID links,
semantic journal, whole interpreter state and frame must match. Existing
deterministic carrier provisioning is replayed at the recorded commit boundary;
no sampler or action is run. No broad UUID stripping is permitted.

The fixed journal measurement exclusions are WORLD_OBSERVATION, STATE_UPDATED,
SENSOR_DEBUG_MAPPING, worker submission/execution and carrier provisioning
records; the latter's state effects are still checked in full. The only audit
artifact exclusion is FROI_READ_CHECKPOINT_AUDIT. No exclusions may be selected
after seeing replay differences. A failed replay prevents screening.

Then both normal and screened branches share one original immutable checkpoint
and handle and call existing resume_detached(). No prefix/producer reruns.
Only consumer effect is screened. A PASS requires a change in actual read
success, expected outcomes, context or membership processing, not UUID/log
differences. Detached states retain the existing formal writeback prohibition.

## T4 and detached continuation

The read-only tracer follows a specified real read-failure limit_id through
organization/consumer, exact raw consequence, experience, partial, feedback,
pending state, next actual observation/frame, next experience/partial and
LIMIT_FEEDBACK_REENTERED_RECURSION. Full raw payload equality is required.

Isolated continuation uses the NEXT stored WORLD_OBSERVATION and recorded
actions as provenance, not an invented observation or executed action. The
branch's completed history events form an explicitly TEST_ONLY in-memory
ledger; they are never advertised as real paired history or saved to A. The
existing producer/interpreter can consume this ledger in the isolated next
round. A missing real next observation returns MATERIAL_UNAVAILABLE. A sampling
gap or unsuccessful re-entry cannot be asserted to have passed.

T2 continuation retains the explicitly intervened producer history, not the
original artifact history. If the fixed checkpoint's newly completed experience
references a prior frame absent from that shorter prefix, only the exact already
recorded required frame is included as disclosed TEST_ONLY checkpoint material.
No omitted historical experience, binding or answer is copied into the branch.

## T5 and freeze policy

PRE and POST bind source commit/hashes, database files/content/state ranges and
the immutable artifact's caps, Condition, codec, exact request/checkpoint,
handle, graph and registry. Frozen source hashes bind the executed regression
controls for no recent-N, pruning, composition skipping, incomplete-as-COMPLETE,
legacy fallback, query substitution, fixture pollution, favorable record
selection, worker-fault relabeling and detached persistence. Keyword scans are
not used as proof. New or changed protected sources reject the frozen contract.
Machine-local Minecraft connection configuration and selected lifetime pointers
are not source mechanisms; caps and actual identity are bound in the artifact.

`FROI_ACCEPTANCE_FREEZE.json` pins the implementation and engineering regression
counts. Documentation-only commits may follow the pinned implementation commit;
current commit is still captured and must remain invariant during validation.

No acceptance status propagates from another item. Allowed item states are
PASS, FAIL, PARTIAL, NOT_EXECUTED, NOT_TESTABLE, MATERIAL_UNAVAILABLE. Missing
real material remains missing even though engineering fixture controls pass.

After freezing, do not edit v1 because a live result is undesirable. A genuine
harness bug requires a new version and explicit re-audit of prior applicability.
