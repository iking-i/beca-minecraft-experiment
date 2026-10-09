# Observation Source Boundary — TEST_ONLY preregistration

Baseline: f2d66102755038dad688a20189767ded24651b0e.
This is representation/persistence isolation, not forgetting, need or purpose.
No Minecraft, existing DB writes, cap changes or default runtime adoption.

Acceptance (frozen before implementation verification):

1. OS-T1: New opt-in lifecycle rejects old/foreign DBs before writes; default
   paths and frozen files stay unchanged.
2. OS-T2: Complete sources, metadata and exact identity retained in authoritative
   SQLite tables independent of Full Audit History. Same transaction as state.
3. OS-T3: Indexed ObservationRef and exact FactRef preserve types, namespace,
   ambiguity rejection, frame/channel/digest and current object epoch/membership.
4. OS-T4: Saved E1–E32 transition inputs produce identical ordinary results,
   Units, relations, Pair/dependency/effect contents, modulo storage representation.
5. OS-T5: Existing source incidence, route supports, body schema and capacity
   checks remain active; access is not a new selector or construction rule.
6. OS-T6: OFF, restart in a new process, ON/OFF/ON preserve same A/current state
   and full sources; never reconstruct from optional audit history.
7. OS-T7: Failed publication rolls back source, index, watermark and current state;
   rejected computation leaves no registered source or partial state.
8. OS-T8: Missing/corrupt referenced sources fail closed. Full explicit source
   audit detects corruption anywhere, including currently unused history.
9. OS-T9: Measure state JSON size, RSS, source reads/bytes and elapsed time in
   separate processes. No unconditional full-history body loading per cycle.
10. OS-T10: Focused/related/full regression, JSON, preserved inputs and frozen
    hashes. Report actual failures without changing acceptance.

Intentional detection-time difference: frozen validator validates every historic
body every cycle. This version validates indexed facts/sources upon actual access
and validates the authoritative archive boundary at transition/startup. Corruption
of an unaccessed body/index row can remain undetected until access or explicit full
source audit. Do not call this complete validation-semantics equivalence.

All structural execution, Pair reuse and effect rules are unchanged. Copies of
frozen modules are isolated imports; their edits are limited to storage access,
validation and explicit lifecycle setup. Provenance remains evidence, not policy.
Offline saved-input comparison is not a new live run or behavioral PASS.
