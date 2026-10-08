# Operative Handoff TEST_ONLY Specification

**Date:** 2026-10-08  
**Status:** QUESTION_FROZEN / DESIGN_FROZEN / IMPLEMENTATION_NOT_STARTED / EXPERIMENT_NOT_STARTED  
**Scope:** TEST_ONLY structural-operativity handoff; no Minecraft run, no body expression, no behavioral authorship claim, no runtime replacement.

## 1. Current blocker

Current audit result:

```text
GENERIC_OPERATIVE_STRUCTURE_SEMANTICS = ABSENT
```

Preserved evidence:

```text
formed represented relation = established in scoped prior work
persistence = established
specialized later consumption = established
generic operative adoption into ordinary recursion = not established
```

The current blocker is therefore not formation itself. It is the absence of one
non-privileged execution path through which both origin-supplied runnable structure and
later internally formed structure can become ordinary recursive dependencies.

## 2. Frozen research question

> Can one creator-supplied initial operative structure S0 and one later internally formed
> structure S1, of the same operative structural kind, enter the same generic execution
> mechanism M such that ordinary later recursion causally depends on S1 without any
> provenance-specific branch, relation-specific consumer, or externally assigned semantic
> mapping?

This stage does **not** ask whether A can autonomously choose an action, form a complete
body expression, survive, create goals, or modify Minecraft.

## 3. Core handoff model

```text
Creator supplies S0
        ↓
M executes S0 as ordinary operative structure
        ↓
individual <-> environment recursion
        ↓
system forms S1
        ↓
M executes S1 through the same operative semantics
        ↓
ordinary later recursion changes because S1 is present
```

Required identity:

```text
execution_semantics(S0) = execution_semantics(S1)
```

Allowed difference:

```text
provenance(S0) = ORIGIN_SUPPLIED
provenance(S1) = INTERNALLY_FORMED
```

Provenance may remain auditable, but it MUST NOT choose the execution path.

## 4. Non-privilege requirement

```text
first structure != special privileged structure
```

The execution mechanism MUST NOT branch on:

- initialized_at_origin;
- creator_supplied;
- bootstrap;
- internally_formed;
- BPC/FROI stage identity;
- concrete domain labels such as C, O, BodyPort, Minecraft action;
- relation-specific type semantics added only for the witness.

Strong test:

> If provenance labels distinguishing S0 from S1 are removed from the execution input,
> M's operative behavior must remain unchanged.

This does not require provenance to be deleted from audit evidence. It requires provenance
to be non-operative for execution.

## 5. Minimum semantic boundary for M

M MAY provide only generic mechanical semantics necessary to execute the structural form
under test, such as generic dependency traversal, pointer/reference resolution, operand
routing, or equivalent substrate mechanics.

M MUST NOT provide:

- task-specific policy;
- action selection;
- value-to-action mapping;
- target selection;
- reward;
- preference;
- survival policy;
- relation-specific consumer logic;
- fallback/retry that supplies the missing meaning;
- a special route for S1.

The test is about whether structure determines the dependency while M only executes the
same structural rule.

## 6. Required witness shape

The TEST_ONLY fixture must contain:

1. a minimal runnable initial structure S0 supplied at initialization;
2. a lawful input/history path capable of forming S1 after startup;
3. S1 having the same operative structural type expected by M;
4. a later ordinary recursive advance in which S1 is an actual operand, dependency, or
   routing element;
5. no explicit "consume S1" test hook in that later advance.

S1 MUST NOT merely appear in metadata, provenance, lookup output, expected-outcome
attachment, debug output, or relation index.

## 7. Acceptance criteria

All criteria refer to the same S1 edge/object.

### OH-T1 — ORIGIN RUNNABILITY

S0 is creator-supplied and can causally affect ordinary TEST_ONLY recursive processing
through M.

PASS requires actual processing effect, not successful serialization.

### OH-T2 — INTERNAL FORMATION

S1 is absent before the declared formation boundary and is formed by the declared
individual/environment recursive history without directly injecting S1 as fixture data.

### OH-T3 — SAME MECHANISM

S0 and S1 enter the same code path / interpreter semantics in M.

No provenance-specific, origin-specific, or internally-formed-specific execution branch
may exist.

### OH-T4 — OPERATIVE ADOPTION

After S1 forms, it becomes an actual operand/dependency/routing element of ordinary later
recursive processing.

A relation record plus specialized lookup is insufficient.

### OH-T5 — NORMAL REENTRY

A normal later recursive advance uses S1 without a manually designated S1 query root or
relation-specific semantic consumer.

### OH-T6 — EDGE ABLATION

Hold fixed:

```text
nodes/endpoints
current input
other state
M
formation history evidence
```

and mask only S1.

The actual later recursive processing path or participating operand set must change in the
predicted structural way. Fewer query results alone are insufficient.

### OH-T7 — PROVENANCE NON-PRIVILEGE

Remove or neutralize the execution-visible distinction between:

```text
ORIGIN_SUPPLIED
INTERNALLY_FORMED
```

while preserving the structures themselves.

Execution semantics and result must remain determined by structure, not provenance.

### OH-T8 — STRUCTURAL REUSE

After first operative use, S1 remains part of the running TEST_ONLY structure and can be
used again under the same generic semantics unless ordinary recursion lawfully modifies
or removes it.

Re-deriving a descriptive record every time is insufficient.

## 8. Failure / non-pass classification

Use only:

```text
PASS
FAIL
NOT_ESTABLISHED
NOT_TESTABLE
```

Important distinctions:

- S1 formed but specialized consumer required -> OH-T4/OH-T5 FAIL.
- S1 only changes recorded output attachment -> OH-T4 FAIL.
- deleting S1 only changes query count -> OH-T6 NOT_ESTABLISHED or FAIL depending on
  whether ordinary processing was expected to change.
- M branches on provenance -> OH-T3/OH-T7 FAIL.
- fixture directly injects S1 -> OH-T2 FAIL.
- generic mechanism itself supplies task answer/policy -> witness invalid for this claim.

## 9. Explicit nonclaims

Even a complete PASS would NOT establish:

- behavioral causal closure;
- internally authored Minecraft action;
- action code authorship;
- parameter authorship;
- autonomous goal formation;
- survival objective;
- general learning;
- L1/upward recursion;
- universal Perfect Recursion generative dynamics;
- that all possible formed structures are executable.

The strongest allowed PASS claim would be:

> In a minimal TEST_ONLY fixture, a creator-supplied initial operative structure and a
> later internally formed structure of the same operative kind were executed by the same
> non-privileged generic structural mechanism, and the later formed structure became a
> causally necessary ordinary recursive dependency under edge ablation.

## 10. Execution boundary

Current status:

```text
QUESTION_FROZEN = YES
DESIGN_FROZEN = YES
IMPLEMENTATION_STARTED = NO
TESTS_ADDED = NO
MINECRAFT_RUN = NO
NEW_A_CREATED = NO
FORMAL_RUNTIME_CHANGED = NO
BODY_CHANGED = NO
SAMPLER_BINDER_CHANGED = NO
```

The next implementation, if authorized, should target only this minimal TEST_ONLY witness.
It must not connect to Minecraft or body expression until this structural handoff itself
has been discriminated.
