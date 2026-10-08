# FormalL0 Operative Adoption — TEST_ONLY preregistration

Date: 2026-10-08. Base: `0cd29715e59ec480a4d7acc8fb64de27a9763ec2`.
Status at preregistration: QUESTION_FROZEN / DESIGN_FROZEN / NOT_IMPLEMENTED.
This status is a historical design boundary; execution results belong in the new validation report.

## Question and scope

Can origin-supplied S0 and subsequently formed S1 of the same operative representation
in real `InternalState` become actual dependencies of the same ordinary
`FormalL0Engine.advance`, without provenance privilege, a specialized consumer,
an independent graph runtime, or post-processing attachment?

Scope: isolated synthetic numeric ObservationFrames, real FormalL0 interpreter,
real InternalState serialization, explicit default-off constructor option only.
No Minecraft, body execution, new real A, existing database writes or migration.
No changes to prior OH/BPC/FROI/GSC/CEC/Successor evidence or criteria.

## Source-grounded integration boundary

At the base commit, `individual/formal_l0.py:196–198` resolves
`feedback.next_relation_ref`, reads `InternalState.relations`, and supplies
`expected_outcomes` to the actual comparison in the partial-processing construction.
The relation insertion and feedback assignment are in the same advance.
`InternalState.l0_state` already serializes arbitrary local state through
`to_dict` / `from_dict`; no new default InternalState field is required.
`formal_boundary.validate_boundary` continues to enforce the original locked caps.
Core's normal interpreter constructors expose no experimental adoption option.

The opt-in integrates dependency interpretation at that existing operand read,
before comparison and before publication. It does not run a base advance and
then attach a detached answer. Neither prior TEST_ONLY Mechanism nor consumer is imported.

## Frozen minimal representation and mechanics

An explicit `test_only_operative_adoption=True` constructor option is required.
State is in `l0_state.operative_test_only`, with schema
`FORMALL0-OPERATIVE-TEST_ONLY-1`, an ordinary edge list and separate audit evidence.
Both S0 and S1 use exactly `{source: relation_id, target: relation_id}`.
Endpoints refer to ordinary records in the real `InternalState.relations`.
Edge identity hashes only the endpoint pair; provenance is never an execution operand.

The existing feedback reference is the initial entry operand. Initialization supplies
that reference once. In the opt-in scope, feedback preserves this ordinary entry
across rounds; no caller supplies a later S1 query. Default feedback assignment is unchanged.

One interpreter mechanism resolves the entry and every reachable dependency,
reading the actual relation records and collecting all exact outcome identities
without ranking or selecting a preferred operand. Every reachable edge is followed;
visited references bound execution. Missing/malformed endpoints are rejected,
never repaired or replaced with the original single-record result.
The reached records supply actual `expected_outcomes`. Prediction context is present
when the current experience root is among those reached records; that check feeds
the existing outcome-membership computation. Execution trace is supplementary evidence,
not the source of an answer after processing.

## Candidate formation law and witness

This TEST_ONLY candidate law applies inside the same FormalL0 advance:
after actual experience integration creates a previously absent lawful relation,
connect every terminal relation operand of this round's committed dependency execution
to that newly formed relation. A terminal operand has no outgoing edge in the prior graph.
Exclude self/existing edges. Use all eligible endpoints, no selector.
The new edge is installed only after this round's operand read; it first executes
on a later ordinary advance. Supports retain the actual experience, partial,
integration, frame, version and executed operand identities.

Origin supplies two opaque relation records and S0 between them, plus one feedback
entry. Sequential synthetic numeric frames produce actual units, experiences,
relations and feedback. The first eligible experience creates an absent relation
and S1 from the already participating terminal operand. No fixture injects the
complete S1 or calls a source/target edge builder for formation.
Subsequent ordinary frames follow the saved edge. Repeated frames can reuse it
without further relation creation or edge formation. This law is not a universal
Perfect Recursion rule or validated reality-facing learning law.

Edges share the existing relation-memory envelope with retained relation records.
Capacity failure rejects the entire new edge batch and records a raw consequence;
no eviction, cap increase, pruning, fallback or incomplete adoption as success.
No executable endpoint is admitted from a provenance label.

## Frozen acceptance and falsification

| Criterion | Required causal evidence |
|---|---|
| FA-T1 Origin Adoption | S0 changes the actual reached relation operands and expected-outcome computation in ordinary FormalL0 advance. |
| FA-T2 Internal Formation | S1 absent initially, formed only from a post-start actual experience/integration and executed terminal operand. |
| FA-T3 Canonical State Persistence | Same S1 stored in real InternalState; JSON serialization/restoration preserves it and later execution. Canonical here means the test's authoritative InternalState, not a production A database. |
| FA-T4 Same Representation and Execution | Same endpoint edge schema and the same interpreter loop for S0/S1. |
| FA-T5 Normal Reentry | Later advance starts from stored ordinary feedback, without an external S1 query or special consumer. |
| FA-T6 Actual Dependency Ablation | Remove only S1, retain all other state/input/mechanism: actual operands or comparison change. Trace-only/query-count differences cannot pass. |
| FA-T7 Provenance Neutrality | Remove/swap/unify audit labels without changing structures: actual execution and operand/comparison results equal. |
| FA-T8 Repeated Reuse | Multiple later ordinary advances retain and execute S1; no reformation is required. |
| FA-T9 Default Runtime Isolation | Default/explicit-off engine agrees with base-commit interpreter across identical inputs and deterministic UUID streams; existing full regressions pass. |
| FA-T10 No Detached Answer | No independent executor, specialized consumer, precomputed output, or post-advance attachment supplies operands; core rejects experimental state writeback. |

Negative controls include origin-edge ablation, S1-only ablation, absent experience,
malformed/missing endpoints, provenance neutralization, unrelated disconnected
structure and experimental-state use without the opt-in. Compare substantive
operands/computation, not UUIDs or event-count differences. Finite resource failures
remain failures, not adaptation rules.

Classification: PASS only if all ten necessary conditions are evidenced;
FAIL for a contradictory causal/control result; NOT_ESTABLISHED for missing causal
evidence; NOT_TESTABLE for an execution facility/material/environment failure.
Do not change these boundaries after seeing results.

## Isolation and nonclaims

No production CLI, launcher or Core path enables this option. FormalFROI and
FormalLiveBody constructors retain default-off behavior. Normal state schema and
semantics are unchanged. Experimental state is rejected without explicit opt-in
and cannot be committed through Core's formal state transition.
Only isolated in-memory state/JSON fixtures are used; no existing database is opened.

Even PASS does not establish live formal-A adoption, body/action/parameter authorship,
Minecraft behavior, autonomous goals, survival objectives, behavioral causal closure,
L1/upward recursion, all possible formed structures as executable, or universal
Perfect Recursion. This freezes one candidate integration realization, not the final
FormalL0 architecture. Implementation/validation is a separate evidence commit;
no next phase is started automatically.
