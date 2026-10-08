# Frozen-source compatibility — authorized isolation record

Date: 2026-10-08. Base: `0cd29715e59ec480a4d7acc8fb64de27a9763ec2`.
This addresses source compatibility only. The existing formation law, operand
semantics, S0/S1 representation, negative controls and FA-T1–FA-T10 are unchanged.
The user's follow-up explicitly permits an opt-in experimental/derived interpreter
and source copying, provided actual FormalL0 operand causality is retained.
The original preregistration remains byte-for-byte unchanged; its in-place file
locations describe the original attempt. This record documents the authorized
physical isolation, not revised acceptance criteria or a redesigned mechanism.

## Preserve first; restore only the frozen file

The complete tracked binary diff, all 18 then-modified/untracked files, their
SHA-256 manifest and git status were saved before changing anything, in:
`C:/Users/i/.codex/visualizations/2026/10/03/01a10045-8063-70d3-b492-5e9242f9ab36/formall0-operative-pre-isolation-20261008/`.
The saved original validation reports are also retained in this package under
`history/PRE_ISOLATION_VALIDATION.md` and `history/PRE_ISOLATION_VALIDATION.json`.
`history/formal_l0_pre_isolation.py.txt` preserves the entire previous implementation
as historical source evidence; it is not imported by production or by the main
operative witness. Only a test equivalence oracle executes that historical text.
Unrelated untracked materials are neither changed nor submitted.

The failed test was
`tests/test_live_evidence.py::LiveEvidenceTests::test_frozen_boundary_matches_exact_sources_and_keeps_debug_macros_separate`,
subtest `path='individual/formal_l0.py'`.
The freeze specifies SHA-256 of UTF-8 bytes with CRLF normalized to LF:

| Source | SHA-256 |
|---|---|
| Frozen expected | `1b6abea5d568c349bf7c181ecd771fc6f08cd0f1791fa49be7434c4acd354b62` |
| Previous modified source | `fe5d97ae4b203d4f2e487ae0a82e45775d66c9ac9f3afcff0ae3421007647718` |
| Restored production source | `1b6abea5d568c349bf7c181ecd771fc6f08cd0f1791fa49be7434c4acd354b62` |

All other frozen component hashes already matched before isolation. The prior full
suite had 527 passed / 113 subtests passed and exactly that one hash subtest failure.
There was no other recorded regression failure. The file was restored by writing
its exact HEAD blob after preserving the complete changed source. No reset, rebase,
checkout, frozen-list edit or old-test edit was used.

## Engine and copying scope

`experimental.formall0_operative.engine.TestOnlyFormalL0Engine` derives from the
unchanged production `FormalL0Engine`, using its constructor, caps, boundaries,
`FormalLimits` and `digest`, and the actual production `InternalState`, observation,
change detection, pattern, policy-recording and consequence utilities.
No production import/CLI/launcher path selects the experimental class.

The explicit constructor option remains boolean and default off. Disabled `advance`
delegates directly to frozen `FormalL0Engine.advance`, after rejecting marked
experimental state. Enabled `advance` calls its ordinary `_advance_operative`
transition. That transition does not call the frozen advance or a side executor.
It produces the actual state/frame/journal itself, with the operative read located
before the expected-outcome and comparison operands are computed.

The original base `FormalL0Engine.advance` is lines 57–293 (237 lines). The enabled
variant with the already validated hooks is the previous saved method at lines
130–384 (255 lines), now `engine.py` lines 111–365. The complete method was copied,
not only post-read processing: prefix, experience creation, operative read,
comparison, ordinary integration, feedback, subsequent edge formation, limits and
return share one state transition. Its method name changes from `advance` to
`_advance_operative`; the body and both operative hook methods are AST-identical
to the saved implementation. `BASE_ADVANCE_DIFF.txt` gives the explicit method
diff against base 0cd29715. FormalLimits/digest and the sampler are not copied.

## Exact semantic differences from frozen production

These are the previously registered opt-in differences, not new isolation changes:

1. Executable dependency edges in `l0_state.operative_test_only` connect ordinary
   relation references. Traversal collects every reached outcome identity.
2. At the original relation-read boundary, reached records supply actual expected
   outcomes. The existing membership calculation uses reachability of its current
   relation as prediction context. No audit provenance is read for execution.
3. The opt-in feedback preserves the original entry; subsequent calls do not query
   or select a specific S1.
4. After a previously absent relation is inserted by actual experience integration,
   all executed terminal relation operands connect to it. New edges execute only
   in later advances and retain the same experience/integration/frame supports.
5. Edge plus relation-record count shares the existing relation cap. New edge-batch
   capacity failure records a raw consequence, without eviction or cap changes.
6. A supplementary path trace records the actual operand read; it supplies no answer.

The two-line existing experimental-state rejection in Core is retained to prohibit
formal writeback. Normal Core constructors and their engine selection are unchanged.
No other production file changes; especially `formal_l0.py`, frozen components,
FROI, body, sampler/binder, caps and databases remain untouched.

## Why this still satisfies the original causal boundary

FA-T4: Both S0/S1 still have the identical reference-edge schema and one interpreter
loop, without provenance dispatch. FA-T5: later ordinary experimental-engine
advance reads the stored entry and persisted edge, with no special S1 request.
FA-T6: the re-executed S1-only ablation changes actual expected operands and outcome
comparison, with all other state held fixed. FA-T10: there is no independent graph
runtime, dedicated relation consumer, precomputed answer or post-advance attachment.
The interpreter is an explicitly scoped FormalL0-derived test realization, not a
claim that unmodified production FormalL0 now has operative adoption.

Migration checks compare the complete copied transition/hook AST and execute eight
rounds against the preserved pre-isolation implementation with equal UUID streams,
comparing full InternalState, ObservationFrame and journal. Default equivalence
also compares production/default/explicit-off engines with the immutable base.
Oracles test equivalence only; the operative witness executes the actual isolated
transition and obtains no result from them.

All causal controls, focused/related/full regression and the unmodified WORLD_ENTRY
hash test are run anew. Counts and final classification belong in `VALIDATION.*`.
No Minecraft, real A, existing database write, history migration or next phase occurs.
