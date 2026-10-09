# Isolation and representation accounting

This package is an explicit TEST_ONLY Core/engine, not a migration of the frozen
NativeEngine or BindingEngine. Existing default Core, body, sampler, binder,
FormalL0, TC/NBO/Binding/Content implementations and all previous evidence are
unchanged. No import was added to the default runtime. No database selection is
changed; every witness uses a new experimental DB. Restart restores that DB's
authoritative Current State, never full history or an old witness.

`ReferenceCore` uses ACore.accept_observation/_commit_observation/_transition and
the existing opt-in operative lifecycle. Its own version/database/individual
metadata is checked before reopening. Default ACore rejects these operative
states. Its action methods explicitly reject; FakeBridge also rejects calls.

`ReferenceEngine` inherits TestOnlyFormalL0Engine's ordinary transition. The
_read_operative_operands hook supplies actual expected_outcomes before processing;
the _form_operative_dependencies hook executes inside ordinary integration. No
post-advance processing attachment, detached graph answer or external consumer.

Adapted blocks and source lineage:

- native declaration and observed material validation: frozen
  experimental/native_body_operands/engine.py (2577891 line, unchanged).
- actual connection-to-Pair construction and numeric before/after formation:
  experimental/typed_operative_connection/engine.py (95d54d5 line, unchanged).
- synthetic receipt incidence and exact endpoint composition:
  experimental/native_parameter_binding_extension/engine.py (7cdd14c line,
  unchanged). Exact-key indexing produces all supported candidates; no ranking.
- Pair(previous content, current UnitRef) reuse: operative_content/engine.py
  (89f1167 line, unchanged). Body-bearing content additionally requires exact
  currently executable connection/incidence support. This is structural
  dependency, not origin/provenance permission.

The endpoint adaptation is new: a BodyRef resolves the existing observed native
interface rather than a synthetic Unit. Slot owner/domain incidence is already
declared by that interface. Its Pair construction is mechanical and audited as
external declaration support; it is not an internally discovered parameter law.
Receipt slot/value premises are external; numeric transitions and composed
slot/value candidates arise during integration. These origins do not choose or
authorize an expression. The code16 fixture is an external measurement address.

All 47 declarations and parameter schemas remain in ObservationFrame and the
existing body_capabilities provisioning record. The reference register retains
validated declaration identity/provenance, not a Unit disguising that catalog.
No 118 internal nodes are allocated for unused declarations. Every materialized
BodyRef/UnitRef/Pair counts as one actual content node, added to actual Units
against the existing 64 limit. Graph connections share the existing 96 relation
limit, including ordinary relations and operative edges. Whole invalid batches
reject before Core commits; the canonical state is not modified by controls.

Native catalog/code/slot identity survives a new session sampling epoch. The
BodyRef's initial catalog generation is persisted; changing it is invalid.
Observed entity/block tokens remain current-epoch/current-token scoped. No gap
is silently bridged: after restarting, the first frame establishes the new
sampling epoch and the following frame runs ordinary recursion.

This fixes body-reference admission only. The old Minimal Native Expression
reader/OneAttempt is deliberately unchanged and is not a consumer for this new
Core representation. No complete expression object, adoption relation, body
execution authority or real-world loop has been established.
