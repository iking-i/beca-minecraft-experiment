# BPC-LIVE-1 implementation / pure-code validation

Definition freeze: `6d7b469c9943ab42aa2e8bee7bcf313b613d3bc3`.
Branch: `codex/bpc-live-1`. This report does not change the frozen experiment definition.
Implementation is opt-in; real Minecraft acceptance has **NOT_EXECUTED** status.
Synthetic sensor tests are implementation evidence, not canonical real-world PASS evidence.

## Actual online path

```text
ACore(... live_body_connection=True, initialize_lifetime=True)
→ unused database / new individual / one runtime and session
→ actual incoming actionSpace validated against the native catalog
→ independent BodyPort(catalog_version, code) facts before recursive formation
→ current encoded frame and exact live difference
→ CurrentChange and current record Member incidence
→ supported Shared(CurrentChange, BodyPort)
→ InternalState.l0_state.live_body_structure
→ existing EventStore state/event transaction
→ next incoming frame / same Core
→ consume_saved(previous committed structure, saved endogenous feedback)
→ actual recursive partial.processing and process.output
```

`individual/core.py` adds explicit opt-in constructor/CLI boundaries. Existing default
FormalL0/FROI behavior remains on its existing path. The new live mode rejects existing
database paths (including resume), legacy policy injection, FROI, session replacement,
body/encoding discontinuity and post-registration measurement-condition changes.
The Core tick is observation-only; raw/discrete execution methods are disabled, including
the pause-time stop command. The sampler/binder policy records are marked disabled for
this path. No expression or perform is generated.

`individual/formal_live_body.py` uses the unchanged FormalL0 engine for its existing
recursive process, then integrates the new live structure into that same working state.
It consumes the previously committed graph **before** this round's formation. The query
root is the preceding live formation's saved CurrentChange reference, not an external
query argument. Read results enter the actual recursive partial processing and process
output; audit events record that use rather than substituting for it.

`individual/live_body_structure.py` owns ordinary serializable facts and direct supports.
Frame roots contain exact encoded numbers and observed native port identities. C retains
the exact channel/kind/before/after/delta and real frame boundary, without action semantics.
O comes from observed capability entries, not from an action record or old validation file.
Member records expose common current-record incidence. Shared edges are derived from
that incidence. All observed endpoints participate; no endpoint is selected by code order,
availability, ranking, or usefulness. Multiple supported ports are reported in full without
choosing one or creating an expression.

This is **shared live-record co-observation**, not execution-receipt attribution and not
proof that any O caused C. There is no action-to-effect claim or imitation claim.

## Persistence and provenance boundaries

Facts, every direct support, saved connection identities and the endogenous read root live
inside A's serialized InternalState. Later consumption checks existing facts/supports and
returns native identities only through saved Shared edges. It never invokes formation,
imports experimental BPC adapters, reads event history or reconstructs an organization.
Checking stored support validity is not publication of a newly reconstructed edge.

Each fresh run records its individual/session/runtime owner, measurement condition and
runtime-source hashes. The condition is external measurement metadata, not recursive input.
Existing databases, artifacts and lifetime-selection files are not used as formation sources.

The existing FormalLimits/resource-cap values are not modified. New endpoints/changes and
connections share the existing units/relations envelope with the ordinary FormalL0 records;
retained source frames obey the existing history capacity and direct-premise counts obey
the evidence-window bound. A rejected formation reports RESOURCE_LIMIT, does not publish
a partial graph, and prevents automatic continued reconstruction/recovery. There is no
eviction, pruning, cap increase, history deletion or fallback.

## Pure-code controls

Each control uses its own fresh database and new individual, through the same Core/engine:

- NC1: exclude O endpoints from formation; current observed metadata cannot substitute.
- NC2: exclude current C from formation; ordinary temporal records cannot substitute.
- NC3: form locally but do not commit the connection/supports; the subsequent read fails.
- NC4: keep the committed structure and block connection access only at the live consumer;
  later processing differs, without producer rerun or deleted history.
- NC5: the production path has no detached artifact importer; forbidden-source checks and
  injected irrelevant artifact payload tests verify it cannot supply a connection.
- NC6: fresh-only startup and no event-reader path exclude old-history material; patched
  historical loaders and store-history access cannot be used by formation/consumption.

Additional tests cover missing connection/support/root/C/O, multiple ports, entire actual
capability catalog, unchanged next input, uncommitted future state, transaction persistence,
UUID/individual/session continuity, serializability, invalid metadata, interruption, no
actions/fallback, and unchanged capacities under resource rejection.

## Execution evidence and limits

Final test counts and commands are recorded in `IMPLEMENTATION_VALIDATION.json`.
Pytest temporary files/databases and transcripts are isolated under `.test-tmp/`.
The first test invocation could not create its sandbox-default temporary directory;
subsequent invocations used fresh workspace-local temporary directories without changing
test assertions, runtime caps, input semantics or the acceptance definition.

No real Minecraft run, canonical acceptance run, body action or live NC run was performed.
Existing Python regression transport tests use their existing fake body adapters; they are
not BPC-LIVE-1 real-world evidence. Successor-0 tests are excluded from regression to avoid
reopening that frozen stage. No frozen evidence, theory, caps or research-status indices
are updated. There is no commit or push in this implementation task.

The implementation does not establish behavioral authorship, parameters, goals, world-effect
causal law, behavioral causal closure, upward recursion or universal generative dynamics.
Real BPC-LIVE-1 classification remains unclaimed until its frozen live protocol is executed.
