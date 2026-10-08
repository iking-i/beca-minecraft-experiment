# FormalL0 Operative Adoption — TEST_ONLY validation

Date: 2026-10-08. **FORMALL0_OPERATIVE_ADOPTION_TEST_ONLY = PASS**.
Base: `0cd29715e59ec480a4d7acc8fb64de27a9763ec2`.
Unchanged preregistration SHA-256: `7a8ba28254d942a6f4c382ac546d523408687ee32432a3172b9bd9242591ce1d`.
The question, formation law and FA-T1–FA-T10 are unchanged. Physical isolation is
explicitly authorized by the follow-up; detailed source/copy analysis is in
`ISOLATION.md` and `BASE_ADVANCE_DIFF.txt`.

## Preserved attempt and compatibility repair

The previous implementation and failed reports are retained byte-for-byte in
`history/formal_l0_pre_isolation.py.txt`, `history/PRE_ISOLATION_VALIDATION.md`
and `history/PRE_ISOLATION_VALIDATION.json`. A complete tracked binary diff,
all then-uncommitted files and hash manifest were saved before any change.

Prior full result: 527 passed / 113 subtests passed / one failed hash subtest.
No other regression failure was recorded. The test was
`LiveEvidenceTests.test_frozen_boundary_matches_exact_sources_and_keeps_debug_macros_separate`
at `tests/test_live_evidence.py:117`, subtest `individual/formal_l0.py`.
Its LF-normalized expected SHA-256 was
`1b6abea5d568c349bf7c181ecd771fc6f08cd0f1791fa49be7434c4acd354b62`;
the modified source was
`fe5d97ae4b203d4f2e487ae0a82e45775d66c9ac9f3afcff0ae3421007647718`.
The restored production file now matches the expected hash and exact base blob.
All WORLD_ENTRY components match; the freeze, old tests and historical PASS
results are unchanged. No hash replacement, test exclusion or weakened predicate
is used. Nine unrelated untracked files were byte-checked against the saved manifest.

## Real state and isolated FormalL0 transition

`experimental/formall0_operative/engine.py::TestOnlyFormalL0Engine` is a derived,
explicitly opt-in interpreter using actual production InternalState, frames,
change detection, pattern identities, caps, boundaries and consequence utilities.
Default off delegates directly to unchanged production FormalL0. No production
CLI, launcher or Core selects this class. Core retains only the existing two-line
TEST_ONLY state-writeback rejection; normal production processing is unchanged.

The enabled transition copies the complete FormalL0 advance with the previously
validated operative hooks. Prefix, experience formation, operand reads, comparison,
integration, feedback, edge formation and return run in one state transition.
It does not first run the frozen advance and attach a result. The copied transition
and two hooks are AST-identical to the saved implementation except for the method
name. Eight rounds also compare full InternalState/frame/journal with equal UUID
streams, including capacity consequences. Both equivalence checks pass.

Copy source: base 0cd29715 FormalL0.advance lines 57–293 (237 lines). The saved enabled
variant is lines 130–384 (255 lines), now engine.py lines 111–365. FormalLimits,
digest and the sampler are not copied. ISOLATION.md enumerates every opt-in
semantic difference from baseline; those are the original registered hooks,
not a new formation/execution law. This is a scoped derived realization, not
operative adoption by the unmodified production engine or a running formal A.

S0 and S1 are identical `{source: relation_id, target: relation_id}` edge records
in `InternalState.l0_state.operative_test_only.edges`, with endpoints in ordinary
`InternalState.relations`. Separate audit evidence is never an execution operand.
Canonical persistence means the authoritative test InternalState and exact JSON
restoration, not an existing formal database. No such database is opened or written.

## Newly executed causal evidence

S0 is origin-supplied `opaque:origin -> opaque:operand`, with two ordinary origin
relation operands and one initial feedback entry. No future relation or S1 is
supplied at origin. Synthetic numeric E1–E5 frames enter the enabled transition.
E2 forms an actual experience and inserts a previously absent relation. Afterwards,
the same candidate law connects all executed terminal operands to that relation,
forming S1 with actual experience, partial, integration, frame and version supports.
New edges first execute in E3. E4/E5 reuse S1 without invoking formation.

The operative read precedes actual expected-outcome/context/membership computation.
Reached relation records supply those operands; the supplemental trace only
records the path. There is no detached graph runtime, specialized consumer,
external S1 query, precomputed answer or post-advance answer attachment. The fixed
law and initial scaffold are experimenter-supplied; the particular S1 arises from
subsequent history under that scoped law, without provenance execution privilege.

| Criterion | Re-executed evidence | Result |
|---|---|---|
| FA-T1 | S0-only ablation removes U-origin-1 from real expected outcomes. | PASS |
| FA-T2 | S1/target absent before E2; actual history/integration supports formation. | PASS |
| FA-T3 | Full InternalState JSON equality and identical restored E3 operands. | PASS |
| FA-T4 | Identical edge schema and same execution loop for S0/S1. | PASS |
| FA-T5 | E3 reads stored entry/S1 without a special external query. | PASS |
| FA-T6 | S1-only removal changes real operands and comparison. | PASS |
| FA-T7 | Removed/unified/swapped provenance leaves execution unchanged. | PASS |
| FA-T8 | Multiple subsequent advances use the same S1 without reformation. | PASS |
| FA-T9 | Default full behavioral equivalence, frozen hashes and full regression pass. | PASS |
| FA-T10 | Enabled path cannot delegate then attach; no side executor/consumer. | PASS |

The decisive paired E4 uses identical E3 state and current frame. Only S1 is
removed; endpoint records, outcome contents, provenance, feedback and all other
state remain unchanged. Reinstating S1 gives the exact original input state.
Actual expected outcomes change; `outcome_previously_observed` changes **True -> None**
because the actual current relation operand is no longer reached. The comparison
precedes integration; no control rebuilds S1 before measuring its effect.

Other independent controls cover absent prior experience, missing endpoint/entry,
malformed schema, duplicate edge, disconnected structure, identity renaming and
all eligible terminals forming rather than selecting one. Provenance neutralization
is also checked during a round that can form new state; malformed audit cannot
influence read-only reuse. Records plus edges share the original relation cap.
Over-cap formation rejects the new edge batch and exposes a raw consequence,
without eviction, cap increase, fallback or incomplete adoption as success.

## Verification record

| Newly executed check | Result |
|---|---|
| Dedicated tests and independent controls | **30 passed** |
| Related FormalL0/boundary/FROI/scheduling/checkpoint plus dedicated tests | **99 passed / 24 subtests**, 26.35 s |
| Complete Python suite, no exclusions, fresh writable basetemp | **532 passed / 114 subtests**, 316.01 s |
| Original WORLD_ENTRY hash test, separately | **1 passed / 13 subtests** |
| Preserved transition and hook AST identity | PASS |
| Eight-round enabled migration full state/frame/journal equivalence | PASS |
| Eight-round production/default/explicit-off vs immutable base equivalence | PASS |
| JSON, source/evidence hashes, original spec hash, diff check | PASS |

The first isolation AST check failed because the checking facility dedented
literal docstring whitespace. Full module AST comparison corrected that facility;
no interpreter/hook or criterion was changed. The subsequent focused and complete
runs passed. Original first-attempt failures remain in preserved reports.

The standalone CLI regenerates focused evidence and reports the separate full
regression as NOT_ESTABLISHED; it cannot invent a full-suite result. VALIDATION.json
incorporates the actual completed regression to issue final PASS. It records
fresh canonical test states, causal controls, provenance and source hashes.
The independent commit containing these files is the implementation/validation anchor.

## Accepted claim and stopping boundary

Within this isolated TEST_ONLY FormalL0-derived synthetic-frame scope, origin S0
and history-formed S1 of one representation become actual dependencies of one
ordinary transition, persist in real test InternalState, naturally re-enter and
change real operands/comparison under edge-only ablation without provenance
privilege, specialized consumer or detached answer.

This does not prove production/live A adoption, Minecraft behavioral authorship,
action or parameter formation, autonomous goals, behavioral causal closure,
L1/upward recursion, all formed structures as executable, or universal Perfect
Recursion. No Minecraft, new real A, existing database, body or theory is changed.
Old OH/BPC/Successor/FROI/GSC/CEC results remain frozen. No next phase begins.
