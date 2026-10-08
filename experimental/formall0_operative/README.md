# FormalL0 Operative Adoption — TEST_ONLY

Preregistration: `FORMALL0_OPERATIVE_ADOPTION_TEST_ONLY_SPEC.md` at repository root.
Final validation: PASS after authorized frozen-source isolation, all ten criteria
and full regression (532 passed / 114 subtests). The prior FAIL remains in `history/`.
This package supplies isolated in-memory inputs and validation, not an executor.
The opt-in interpreter is the FormalL0-derived `engine.TestOnlyFormalL0Engine`.
Production `individual/formal_l0.py` is restored to its exact frozen implementation.
`ISOLATION.md` and `BASE_ADVANCE_DIFF.txt` document copying scope and semantic differences.
Original source and failed pre-isolation reports remain in `history/`.

Explicit opt-in: `TestOnlyFormalL0Engine(test_only_operative_adoption=True)`.
There is no production CLI, launcher, Core or database migration enabling it.
Core rejects experimental state writeback. Normal constructors remain default off.

Both S0 and S1 are ordinary `{source, target}` relation-reference dependencies in
the real `InternalState.l0_state.operative_test_only.edges`. The interpreter reads
reachable relation operands before computing its existing expected outcomes and
comparison. Formation connects all executed terminal operands to this advance's
newly inserted experience relation; its edges first execute in a later advance.
This is the frozen scoped candidate law, not a universal recursive law.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_formall0_operative_adoption.py -q
.\.venv\Scripts\python.exe -m experimental.formall0_operative.validation
```

The isolated CLI prints newly executed focused evidence; it reports the separately
required full regression as NOT_ESTABLISHED. Final acceptance and actual complete
regression records are in `VALIDATION.*`; the CLI does not invent a full-suite PASS.

Validation writes no database and runs no Minecraft or real A. UUID controls in
the baseline-equivalence fixture isolate bookkeeping from semantic comparisons;
production UUID generation is unchanged. Saved evidence is in `VALIDATION.json`
and its human-readable explanation is in `VALIDATION.md`.

PASS is limited to this synthetic-input TEST_ONLY FormalL0/InternalState chain.
It establishes no production-A integration, body/action/parameter authorship,
autonomous goals, behavioral closure, L1 or universal Perfect Recursion.
