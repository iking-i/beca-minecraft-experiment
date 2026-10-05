# GSC-1 — Determinate Grounding Prototype (TEST_ONLY)

GSC-1 is a read-only consumer of frozen `experimental/gsc0` at
`8801ca88093e5c66fa11ba6eb4c084608a1bd690`. It uses only the standard library
and GSC-0. No production runtime, Minecraft, database or output execution.

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest experimental.gsc1.tests -v
.\.venv\Scripts\python.exe -m experimental.gsc1.validate
```

The validation command runs GSC-1 tests plus frozen GSC-0 regression tests and
writes only `GSC1_PROTOTYPE_VALIDATION.md/.json`. It does not run GSC-0's report
generator or replace any GSC-0 validation file.

`check_grounding(complete_gsc0_result, schema)` reads exact ordinary-variable
Bindings. Zero distinct legal values means UNRESOLVED; one means GROUNDED;
two or more means CONFLICT. All ports must be singletons to package a tuple.
Otherwise `outward is None`. RESOURCE_LIMIT upstream is rejected even if its
unfinished working state already contains one binding for every port.

All listed schema ports are required. The schema fixes names, types, variable
identities and field order, but provides no values. Canonical sorting serializes
all evidence; it never discards bindings. A mixed missing/conflicting case keeps
both per-port statuses and reports CONFLICT overall. No complete tuple is made.

Binding evidence contains every direct support and all finite input roots;
the closure digest identifies the upstream finite graph, including GSC-0's
lossless COMPOSE support index. GSC-1 does not copy or expand infinite proof
trees, add facts to GSC-0, invent values or claim semantic understanding/L1.

Fixtures deliberately supply historical Bind relationships and current explicit
Eq inputs. The experiment proves history-dependent mechanical determinacy under
fixed rules, not autonomous discovery of those equality declarations.
