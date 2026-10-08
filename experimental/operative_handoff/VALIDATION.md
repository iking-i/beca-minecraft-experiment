# Operative Handoff TEST_ONLY validation

Frozen specification/base: `41aceb5f0b74f7be6eb186dd5e2c0a34ba1b5d8d`.
Specification: `OPERATIVE_HANDOFF_TEST_ONLY_SPEC.md`, unchanged.

**OPERATIVE_HANDOFF_TEST_ONLY = PASS** for the isolated structural witness.
This report does not claim adoption into the existing formal A runtime.

## Fixture, formation, and execution boundary

Declarations: `Node(A), Node(B), Node(C)`; origin supplies only `Edge(A,B)`.
All names are opaque; renaming is tested. The first ordinary input activates A.
Later structural input observes C, not an edge or solution path.

The declared fixed TEST_ONLY formation law is temporal-frontier incidence:
all prior participating nodes without outgoing dependencies in the prior graph
are connected to all current observed nodes (excluding self/existing pairs).
For this fixture, prior participation A/B has frontier B, so later observation C
forms `Edge(B,C)`. Branching tests verify that every eligible pair is formed,
without first/best/nearest/priority selection. This law is not asserted to be a
Perfect Recursion universal formation rule.

S0 audit: `ORIGIN_SUPPLIED`, version 0, initial structural input.
S1 audit: `INTERNALLY_FORMED`, version 2, supports `processing:1` and
`observed:2:C`. The exact input and prior processing are retained in immutable
cycle history. S1 is absent initially and before formation; no fixture input
contains it. Formation does not invoke the executor.

The sole executor is `experimental/operative_handoff/mechanism.py:7`,
`Mechanism.advance(nodes, edges, active)`. It executes all outgoing dependencies
of participating nodes using one traversal loop. Sorting provides a reproducible
trace, not selection; every reachable dependency is processed. Audit/provenance
is not an argument. S0 and S1 are the same Edge type in the same `State.edges`.

`Runtime.advance` executes the committed graph, forms new edges, and assigns an
immutable next State. It does not execute newly formed edges during formation.
The next ordinary advance uses that same edge collection. No consumer/query,
raw history reconstruction, old stage import, body call, or specialized S1 path
is present. Commit here means the isolated runtime's state transition, not a
write to a formal individual's database.

## Actual processing traces

| Condition | Participating nodes | Actual dependencies |
|---|---|---|
| S0 first advance | A, B | A→B |
| Formation cycle, before S1 commit | A, B | A→B |
| Later ordinary advance | A, B, C | A→B, B→C |
| Mask only S1 | A, B | A→B |
| Remove audit/provenance | A, B, C | A→B, B→C |
| Unify provenance labels | A, B, C | A→B, B→C |
| Repeated ordinary reuse | A, B, C | A→B, B→C |

The edge-ablation projection changes only `State.edges`: nodes A/B/C, S0,
current input, prior processing, history and all audit supports remain identical.
C ceases to participate in actual execution, not merely in a query result.
Reuse tests prohibit formation calls during later ordinary inputs and verify
that the same edge/audit persists without rebuilding S1.

## Frozen criteria

| Criterion | Result | Evidence |
|---|---|---|
| OH-T1 ORIGIN RUNNABILITY | PASS | S0 makes B participate; removing S0 leaves only A |
| OH-T2 INTERNAL FORMATION | PASS | S1 absent before version 2; generated from prior processing and node observation |
| OH-T3 SAME MECHANISM | PASS | Same Edge collection/type and same observed Mechanism.advance calls |
| OH-T4 OPERATIVE ADOPTION | PASS | S1 is an executed dependency and makes C participate |
| OH-T5 NORMAL REENTRY | PASS | Ordinary subsequent input A uses S1 without a query/consumer |
| OH-T6 EDGE ABLATION | PASS | Mask only B→C; actual dependency path and participating node set change |
| OH-T7 PROVENANCE NON-PRIVILEGE | PASS | Removed/unified/swapped/malformed audit labels cannot change execution |
| OH-T8 STRUCTURAL REUSE | PASS | Repeated ordinary advance retains/executes S1 without reformation |

Static AST/source checks: one outgoing-edge execution loop; executor has no
audit/provenance/support/history access and no S0/S1, creator/internal,
bootstrap, BodyPort, Minecraft, reward, goal or survival branch.

## Executed verification

- Dedicated tests: **19 passed**; latest run 0.22 s.
- Frozen GSC-0 controls: **23 passed**, 4.17 s.
- Initial complete regression: **452 passed, 50 setup errors, 114 subtests passed**,
  333.80 s. All 50 errors were pytest tmp-path initialization failures:
  `could not create numbered dir with prefix pytest- ... after 10 tries`
  in the sandbox default temporary directory; affected test bodies did not run.
- Complete regression with a fresh writable external basetemp: **502 passed,
  114 subtests passed**, 315.02 s; exit code 0. No test assertions or fixture
  semantics were changed. `git diff --check` and JSON parse validation: PASS.

No frozen tests, runtime files, hashes, caps, specifications or historical reports
were changed to address the temporary-directory environment issue.
See `VALIDATION.json` for executed criterion results, traces, hashes and test records.

## Accepted claim and nonclaims

Within the frozen minimal TEST_ONLY scope, an origin-supplied operative edge and
a later internally formed edge of the same structural kind entered the same
non-privileged generic execution mechanism; the formed edge became an ordinary
recursive dependency, survived normal reentry, and was causally necessary under
edge ablation.

This does **not** establish behavioral causal closure, action/parameter/goal/
survival authorship, Minecraft behavior, L1/upward recursion, a universal
Perfect Recursion proof, executability of all possible formed structures, or
generic operative adoption in existing FormalL0/FROI/live A. No Minecraft,
formal A or new real-world experiment was run. This package is TEST_ONLY;
formal runtime, body, sampler/binder, caps and all old frozen evidence are unchanged.
No subsequent stage is designed or implemented by this result.
