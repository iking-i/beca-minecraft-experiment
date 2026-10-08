# Implementation boundary

New version: GENERIC-OPERATIVE-CONTENT-TEST_ONLY-1. No body/expression path.
`ContentCore` subclasses actual ACore, reuses the existing guarded TEST_ONLY
operative lifecycle/Current State commit and initialization. It adds a distinct
content mode, version and database/individual binding. Restart supplies no origin.

The only production-source edit is a read-only foreign-content-mode admission
guard after the existing argument/cap preflights in ACore.__init__. It rejects
takeover by default or old operative modes before lease/schema/session writes.
It follows the existing nonempty-WAL/immutable read-only convention. Unmarked default state follows
the same engine and transitions as before. No default constructor is replaced.
Frozen FormalL0 and every prior experimental implementation remain unchanged.

`ContentEngine` derives from the already validated TestOnlyFormalL0Engine. It
does not copy its transition, run a detached graph, query a specialized consumer,
or attach content after advance. Dynamic dispatch at `_read_operative_operands`
first executes the identical old traversal, then the generic typed constructor.
Its returned actual outcome operand set is used by the old transition's existing
expected-outcome calculation. A scoped execution flag distinguishes an actual
advance from pure admission validation; try/finally resets it even on rejection.
S0 and S1 are never inspected by provenance or special identities.

Only typed content is stored in content_test_only.nodes; execution summaries and
evidence are separate. Pair identities and behavior do not read summaries or
evidence. The interpreter reads stored Pair references in later constructions.
Mechanical `evaluate` is a verification utility only; it is never called by the
engine to supply results. Alpha/order/provenance/distractor controls distinguish
reference-based product construction from a path report or selected answer.

Construction is an externally supplied fixed generic operation. No internally
authored operation choice is claimed. Its material operands depend on the actual
operative reachability and the current UnitRef, and all eligible operands are kept.
UnitRef refers to the frozen channel/kind pattern identity, not exact delta
magnitude. A magnitude-only historical difference may legitimately share identity.
Capacity is charged against the existing units cap, together with Unit records;
no independent enlarged resource pool is introduced. Invalid/excess batches abort
before persistence. This is not a limit-to-solution or automatic recovery rule.

Old frozen result scopes, source hashes, tests and historical failures are preserved.
No runtime policy/sampler/binder/body/cap/schema migration, selected A or theory
change. Synthetic observation inputs and independent temporary TEST_ONLY DBs only.
