# FormalL0 Operative Adoption — TEST_ONLY validation

Date: 2026-10-08. Base commit: `0cd29715e59ec480a4d7acc8fb64de27a9763ec2`.
Final classification: **FAIL — mandatory full regression has a frozen-source guard failure**.
Implementation remains uncommitted; no successful acceptance commit is created.
Preregistration SHA-256: `7a8ba28254d942a6f4c382ac546d523408687ee32432a3172b9bd9242591ce1d`.
The preregistration was frozen before implementation and is unchanged.

## Object, formation and actual execution boundary

The authoritative state for this test is a real `InternalState`, serialized by its
existing `to_dict` / `from_dict`. Canonical persistence here means this isolated
test state chain and its JSON restoration; it does not mean an existing formal A
database was opened, migrated or updated.

S0 and S1 both use `{source: relation_id, target: relation_id}` in
`l0_state.operative_test_only.edges`. Ordinary endpoint records remain in
`InternalState.relations`; audit provenance is separate and not executable.
S0 is origin-supplied `opaque:origin -> opaque:operand`, with two ordinary relation
operands. No future unit/relation identity or S1 is supplied by initialization.

Synthetic numeric ObservationFrames E1–E5 are processed by the real FormalL0
interpreter. E2 creates an actual experience and an absent relation. The candidate
law inside that same advance connects the executed terminal operand to this new
relation, forming S1. It retains the actual experience, partial, integration,
frame and version supports. This is explicitly a TEST_ONLY candidate formation
law, not a universal law, semantic solution or history-reconstruction adapter.

`individual/formal_l0.py::_read_operative_operands` follows every reachable edge
and reads ordinary relation outcome identities. `advance` invokes it at the
existing feedback-reference read before constructing `expected_outcomes`, the
prediction-context operand and the existing outcome-membership comparison.
There is no separate graph interpreter, specialized consumer, `super().advance`
followed by attachment, or precomputed answer. Both S0 and S1 enter the same loop.
The supplemental dependency trace records the path; it is not the causal result.

The initial feedback entry is supplied once at origin and preserved in the opt-in
scope. Later callers supply only state and current frame, not a selected S1 query.
New dependencies are formed after the current read, then saved in the returned
state. E3 reads S1 from that previously committed state. E4/E5 reuse it without
calling formation or adding a replacement edge.

## Causal evidence and controls

| Criterion | Actual evidence | Result |
|---|---|---|
| FA-T1 | Removing only S0 removes `U-origin-1` from actual expected outcomes. | PASS |
| FA-T2 | S1 and its target relation are absent before E2; its supports identify E2's actual experience/integration and executed terminal operand. | PASS |
| FA-T3 | Full InternalState JSON round trip is equal; restored E2 state produces the same E3 operands. | PASS |
| FA-T4 | S0/S1 have identical edge schema and execute through the same operand-read loop. | PASS |
| FA-T5 | Ordinary E3 advance follows stored feedback and S1, with no external S1 query. | PASS |
| FA-T6 | S1-only ablation leaves all other state/input unchanged and changes real expected outcomes and comparison. | PASS |
| FA-T7 | Removing, unifying and swapping provenance preserves operands/comparison; malformed audit content also cannot affect read-only reuse. | PASS |
| FA-T8 | E3/E4/E5 traverse the same S1; E4/E5 retain identical operative state and do not invoke formation. | PASS |
| FA-T9 | Default/explicit-off behavioral equivalence passes, but mandatory full regression fails the old WORLD_ENTRY source hash guard. | FAIL |
| FA-T10 | Actual operand change occurs before processing construction; no side executor/consumer; Core rejects TEST_ONLY writeback. | PASS |

The decisive E4 paired comparison starts with exactly the same E3 committed state
and frame. The control removes only S1 from the operative edge list, retaining
both endpoint records, their outcome contents, audit evidence, feedback and all
other state. Reinstating that edge reproduces the original full input state.
The normal comparison is `outcome_previously_observed = True`; the ablation is
`None`, because the actual current relation operand is no longer reached.
The expected-outcome list also changes. This exceeds a trace/log/query-count effect.
The ablation is evaluated during actual advance, before this round's integration;
no control reconstructs S1 before the comparison.

Other controls cover missing endpoint/entry, malformed schema, duplicate edge,
absent prior experience, disconnected relations, identity renaming and every
eligible terminal being used rather than choosing the first one. The finite
existing relation cap jointly bounds records and edges. Over-cap formation rejects
the new edge batch and exposes an ordinary raw limit consequence; it does not
evict, increase caps, prune or use fallback. No resource failure is counted as PASS.

## Default isolation and attribution

The constructor flag is explicit and default off. Production constructors do not
pass it. A default interpreter rejects marked experimental state; Core additionally
rejects formal writeback even if a caller tries to inject such state. No default
InternalState field/schema, Formal boundary, FROI/GSC rules, body, sampler/binder,
action selection, caps, old database or frozen report was changed.

Default equivalence loads the immutable base FormalL0 source solely as a test
oracle. It compares full returned InternalState, ObservationFrame and journal,
including failures, over eight inputs, for both default and explicit-off modes.
The test controls both interpreter UUIDs and the formal-boundary condition UUID;
production UUID rules are untouched. The main operative witness does not obtain
an answer from that oracle or from the old Operative Handoff mechanism.

The fixed execution/formation law is programmer-supplied TEST_ONLY capability;
S0 and initial entry are creator-supplied. S1's particular endpoint comes from
the actual subsequent history/current integration under that law. Its provenance
has no execution privilege. This claim does not attribute the fixed interpreter
or initialization itself to A.

## Verification record

Final execution counts and source hashes are recorded in `VALIDATION.json`.
Focused tests: 25 passed. Related regressions: 94 passed / 24 subtests passed.
Full regression: **527 passed / 113 subtests passed / 1 failed subtest**, 316.26 s.
No test exclusion was used. The failed check is
`LiveEvidenceTests.test_frozen_boundary_matches_exact_sources_and_keeps_debug_macros_separate`,
subtest `path='individual/formal_l0.py'` at `tests/test_live_evidence.py:117`.
The immutable `WORLD_ENTRY_FREEZE.json` expects LF-normalized SHA-256
`1b6abea5d568c349bf7c181ecd771fc6f08cd0f1791fa49be7434c4acd354b62`;
the current authorized opt-in implementation is
`fe5d97ae4b203d4f2e487ae0a82e45775d66c9ac9f3afcff0ae3421007647718`.
This is a source-identity mismatch, not an observed default-behavior mismatch.
The old freeze, its test and historical evidence are untouched. No guard was
bypassed or weakened. The mandatory regression gate remains unsatisfied, so
focused causal results cannot be promoted to overall PASS. The isolated validator
explicitly reports full regression as NOT_ESTABLISHED until an external result
is incorporated; this report incorporates the actual failed result as FA-T9 FAIL.

The first focused run had 21 passed / 4 failed. The failures exposed test-facility
issues: a docstring was mistaken for executable provenance access; the baseline
comparison did not align the separate condition UUID; and an extra malformed-audit
test attempted new audit writing instead of isolating existing-edge execution.
Executable AST access checks, aligned UUID streams and a normal reuse checkpoint
correct these facilities. The frozen FA criteria and operative production methods
were not changed to obtain those passes. Required remove/swap/unify provenance
checks also execute a round that can form new state. No prior result is rewritten.

## Evidenced causal scope, overall failure and nonclaims

The focused controls evidence that within this frozen TEST_ONLY synthetic-frame scope, origin and history-formed
dependencies of one representation become actual operands of the same FormalL0
advance, persist in real test InternalState, naturally re-enter and alter actual
comparison under edge-only ablation without provenance privilege or side consumer.
This is not an overall accepted PASS: FA-T9's full-regression requirement failed.
No independent implementation/validation commit is made under the conditional
authorization to commit only after successful acceptance. Work stops here rather
than changing a frozen guard or introducing an alternative execution bypass.

This does not establish adoption by a running formal A, Minecraft behavioral
authorship, action/parameter authorship, autonomous goals, behavioral causal
closure, L1/upward recursion, all formed structures as executable, or universal
Perfect Recursion. Existing OH/BPC/FROI/GSC/CEC/Successor claims and evidence stay
frozen. No Minecraft or new real A was run. No next phase is started.
