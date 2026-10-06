# Successor-0 — TEST_ONLY requirement-bounded formation

Independent prototype on branch `successor-0-requirement-bounded`, based on
`9dab7ebf4244fd3490291dfdb0e22c09c11547f6`. No formal runtime imports this module.
It imports only the Python standard library and its own sibling modules.

Scope: externally supplied `RequireBound`, unique producer on each expanded
unbound port, typed `Transfer`, finite acyclic fixture. Multiple producers are
rejected, never selected. Cyclic fixtures and incompatible declarations are
rejected. Different values remain conflicts; no arbitration is performed.

`form()` registers exact declarations and producer keys, validates the fixture,
then propagates only from the supplied requirement. Global declaration indexing
and acyclicity validation perform no binding propagation or composition.
All successful input bindings are externally supplied leaves, explicitly marked
`INPUT` in provenance. Activation, demand and derived binding supports are
recorded inside an immutable `ActivatedSupport`.

An organization identity hashes its complete canonical content; the canonical
content itself is retained. It excludes run IDs, timestamps and the full input
registry. Equal disconnected additions leave its content and identity unchanged.
`COMPLETE_LOCAL_SUPPORT` means the requested binding is supported, not a global
fixed-point closure. Missing producers yield `UNRESOLVED`; stack exhaustion is
reported `RESOURCE_LIMIT` rather than success.

The consumer receives only the organization and query endpoint. It verifies
existing direct-support edges; it cannot look up history or run formation.
Detached controls preserve the original organization and remove access to either
the handle or a necessary support edge in a separate immutable projection.

## Fixed validation

Before execution, `validation.py` fixes S0-T1–T10, A/B/C, D10/D100/D1000,
and both consumer ablations. The independent negative controls also cover
renaming, order independence, conflicts, multiple producers, cycles, invalid
types/scopes, incomplete handles and missing facts/supports.

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_successor0 -v
.\.venv\Scripts\python.exe -m experimental.successor0.validation
```

The accepted claim is only:

> Given an externally supplied opaque requirement, a fixed non-semantic local
> formation rule can form and causally expose a requirement-bounded organization
> without global exhaustive structural enumeration, within the unique-producer
> acyclic TEST_ONLY scope.

This does not establish internally formed goals, multiple-solution autonomy,
behavioral authorship, universal generative dynamics or Perfect Recursion as
validated. No Minecraft, real A, GSC-0, FROI or CEC-0 is executed by these commands.
