# FormalL0 Operative Adoption TEST_ONLY — phase closeout

Date: 2026-10-08. Branch: `codex/operative-connection-correction`.

```text
FORMALL0_OPERATIVE_ADOPTION_TEST_ONLY = PASS / COMPLETED / FROZEN
IMPLEMENTATION_COMMIT = 8b33097b746931b788ab5e72de66dd483af18edc
FROZEN_FORMALL0_SOURCE_HASH = MATCH
DEFAULT_RUNTIME_UNCHANGED = YES
```

This is the separate research-state closeout of the implementation/validation
anchor above. Its containing commit supplies the closeout anchor; no new mechanism,
experiment, acceptance criterion or theory change is introduced.

## Evidence and object boundary

Read the unchanged [preregistration](FORMALL0_OPERATIVE_ADOPTION_TEST_ONLY_SPEC.md),
[validation](experimental/formall0_operative/VALIDATION.md),
[machine-readable evidence](experimental/formall0_operative/VALIDATION.json),
[isolation record](experimental/formall0_operative/ISOLATION.md),
[explicit transition diff](experimental/formall0_operative/BASE_ADVANCE_DIFF.txt),
and [dedicated tests](tests/test_formall0_operative_adoption.py).
The earlier [Operative Handoff closeout](OPERATIVE_HANDOFF_TEST_ONLY_CLOSEOUT.md)
retains its own scope, counts and conclusion.

The accepted object is the explicitly enabled, isolated
`experimental.formall0_operative.engine.TestOnlyFormalL0Engine`. It derives from
frozen FormalL0 and uses actual production `InternalState` and ordinary relation
operands. It is not the unmodified production engine or an ACore live integration.
S0/S1 share `{source: relation_id, target: relation_id}` records in
`InternalState.l0_state.operative_test_only.edges`; their endpoints are ordinary
`InternalState.relations`. Separate formation evidence does not dispatch execution.

S0 is the creator-supplied `opaque:origin -> opaque:operand` scaffold. S1 arises
after startup in the synthetic E1–E5 sequence: E2 forms an actual experience and
new relation under the registered candidate law. The resulting edge is
`opaque:operand -> U-77aff4c774f87f3af1a7:-1`. Its evidence includes experience
`1ac16c4a-022f-48e9-9de8-d0167948f3c3`, E1/E2 frame identities, actual partial and
integration references and state version 2. It first executes in E3 and is reused
in E4/E5. These are canonical test-state identities, not real Minecraft evidence.

The enabled transition computes actual expected-outcome and comparison operands
through the operative dependencies before integration. It does not run
`super().advance()` and attach an answer, use a detached graph executor, or obtain
S1 through a dedicated external query/consumer. Persistence here means actual
test InternalState serialization and restoration, not authoritative Core/EventStore
writeback. Core explicitly rejects the marked TEST_ONLY state; its default engine
selection is unchanged.

## Accepted claim

Within the isolated TEST_ONLY FormalL0-derived synthetic-frame scope, origin-supplied
S0 and history-formed S1 share one operative representation and execution mechanism
in actual test InternalState; persisted S1 naturally changes subsequent ordinary
advance operands and comparison, with edge-only causal ablation, repeated reuse
and provenance-neutral execution. This does not establish adoption by canonical
FormalL0, ACore or a continuously running real A.

## Criterion audit

| Criterion | Existing causal evidence | Frozen result |
|---|---|---|
| FA-T1 Origin Adoption | S0 supplies real expected-outcome operands; S0-only ablation removes them. | PASS |
| FA-T2 Internal Formation | S1 and its endpoint were absent initially; E2 experience/integration supports formation. | PASS |
| FA-T3 Canonical State Persistence | Exact test InternalState JSON round-trip preserves the edge and restored operands. | PASS |
| FA-T4 Same Representation and Execution | S0/S1 use the same reference-edge schema and interpreter loop. | PASS |
| FA-T5 Normal Reentry | Later ordinary experimental advance reads the persisted entry/edge without an S1 query. | PASS |
| FA-T6 Actual Dependency Ablation | Only S1 removed; expected operands change and comparison changes True to None. | PASS |
| FA-T7 Provenance Neutrality | Removing, swapping or unifying provenance leaves execution unchanged. | PASS |
| FA-T8 Repeated Reuse | Multiple later advances consume S1 without reformation. | PASS |
| FA-T9 Default Runtime Isolation | Default equivalence, original frozen hashes and complete regression all pass. | PASS |
| FA-T10 No Detached Answer | Actual transition supplies its own operands; no post-advance attachment or side consumer. | PASS |

The decisive E4 pair preserves the complete E3 input state/current frame except
S1 itself. Relation records, feedback and audit provenance remain fixed. Reinserting
S1 restores the exact original input state. The changed computation is real
`outcome_previously_observed` membership, not just a trace or query count.
Negative controls also reject missing endpoints/entries, malformed/duplicate edges
and absent experience; disconnected structure, renaming and all eligible terminal
formation are covered. Joint relation/edge capacity failures retain raw consequences;
no cap increase, eviction or fallback is introduced.

## Recorded regression and closeout checks

| Recorded implementation check | Result |
|---|---|
| Dedicated tests and independent controls | 30 passed |
| Related regressions including dedicated tests | 99 passed / 24 subtests passed |
| Complete Python regression, no exclusions | 532 passed / 114 subtests passed; 0 failures |
| Original WORLD_ENTRY frozen guard separately | 1 passed / 13 subtests passed |
| Preserved transition/hook AST and eight-round enabled equivalence | PASS |
| Production/default/explicit-off full state/frame/journal equivalence | PASS |

These counts are read from the frozen VALIDATION.md/JSON, not rerun or newly
claimed closeout executions. Source/evidence hash checks and stored causal pairs
are consistent, so no completed experiment or test is repeated for closeout.
This documentation-only closeout checks JSON parsing, current-index consistency,
source/evidence preservation, unrelated untracked byte preservation and git diff.

## Preserved compatibility failure

The pre-isolation attempt remains **FAIL**, with FA-T9 FAIL, 527 passed /
113 subtests passed and one frozen hash subtest failure; no other regression
failure was recorded. Its full source and reports remain unchanged under
[history](experimental/formall0_operative/history/PRE_ISOLATION_VALIDATION.md).
The failed subtest was `individual/formal_l0.py` in
`LiveEvidenceTests.test_frozen_boundary_matches_exact_sources_and_keeps_debug_macros_separate`.

LF-normalized SHA-256:

- Original frozen and restored source: `1b6abea5d568c349bf7c181ecd771fc6f08cd0f1791fa49be7434c4acd354b62`.
- Previous modified source: `fe5d97ae4b203d4f2e487ae0a82e45775d66c9ac9f3afcff0ae3421007647718`.

All 13 WORLD_ENTRY component hashes match. WORLD_ENTRY_FREEZE, old tests, the
preregistered criterion and historical failures/PASS reports are not rewritten.
ISOLATION.md records the copied transition's source version/range and opt-in
semantic differences. The PASS is a scoped derived realization, not a claim of
canonical adoption obtained merely by making the frozen-source check green.

## Nonclaims and protected boundaries

```text
CANONICAL_FORMALL0_ADOPTION = NOT_ESTABLISHED
REAL_A_CONTINUOUS_OPERATIVE_ADOPTION = NOT_ESTABLISHED
CORE_EVENTSTORE_INTEGRATION = NOT_ESTABLISHED
MINECRAFT_WORLD_FACING_AUTHORSHIP = NOT_ESTABLISHED
BEHAVIORAL_CAUSAL_CLOSURE = NOT_ESTABLISHED
L1_UPWARD_RECURSION = NOT_ESTABLISHED
```

No general action/parameter formation, autonomous goals, all structures as
executable, universal generative dynamics or Perfect Recursion overall proof is
established. The fixed scaffold and candidate formation law are experimenter
supplied; particular S1 arises from subsequent test history under that law.
Existing OH/BPC/Successor/FROI/GSC/CEC and infrastructure results retain their
historical scopes. No runtime, tests, caps, old evidence, database or theory file
is modified by closeout; no Minecraft or real A is started.

## Next question only — QUESTION_FROZEN / implementation NOT_STARTED

在不改变原有冻结 FormalL0 的前提下，如何让已经通过 TEST_ONLY 的 operative adoption 通过明确版本化的实验执行路径进入 ACore 和权威 Current State，使同一个实验个体在连续状态转换中真正使用后来形成的 operative structure？

```text
ACore
  -> authoritative Current State
  -> versioned operative engine
  -> formation + persistence
  -> next ordinary advance
  -> formed operative dependency
```

This records the user's next research boundary only. No next acceptance criteria,
engine design, Core wiring, state migration or experiment is defined/implemented.
A standalone prototype cannot substitute for evidence of Core integration.
Next implementation and experiment remain NOT_STARTED. Stop after this closeout.
