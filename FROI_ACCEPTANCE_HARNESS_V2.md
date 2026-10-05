# FROI-1 ACCEPTANCE HARNESS v2

EXPERIMENTER / AUDIT / TEST_ONLY measurement tooling. No runtime imports it.
The original v1 files, freeze, criteria and historical results remain unchanged.
Base acceptance commit: `550b4bc46647371ca34f9d94043c051cde42263e`.

## Scope

v2 replaces whole-session materialization with stable one-row event_sequence
pages, directed version/type/cutoff queries, incremental hashes and a small
database-locator manifest. It does not modify A, FormalL0/FROI/GSC, production,
consumption, resume, codec, caps, Condition, history semantics or acceptance.
The full source remains protected: every event and state participates in the
same v1 canonical logical digest, and the entire database file is hashed.
Nothing is pruned or sampled. Incomplete rounds remain visible.

`tools/froi_acceptance_v2/checks.py` retains v1 predicates and interpreter calls.
Only T1 source access, T4 material access and continuation source lookups differ.
T2/T3/T5 and UUID replay/processing-effect functions are AST-identical controls.
No new ignored semantic fields are introduced.

## Evidence boundary

The manifest stores no session dump or nested artifact JSON string. Every
locator binds database/source freeze, table, sequence/event/version, content
digest, object type, checkpoint digest and history cutoff. Loading regenerates
the complete required locator set from the real prefix; missing/extra/corrupt
references reject. An independent whole-session PRE read verifies the source
against EXPORT, and POST verifies it again. State/body epochs and actual query
origin remain fixed. Restoration never executes the prefix or closure.

The required complete History is materialized ONLY at the unchanged production
API boundary. For the explicitly selected early live checkpoints its size is
275,250 to 772,420 bytes. v2 cannot promise arbitrary future histories or GSC
jobs fit a fixed host budget; any measurement failure must remain a measurement
failure, never RESOURCE_LIMIT or COMPLETE fabricated by the harness.

SQLite uses query_only and read transactions. Immutable reads are used only
when WAL is absent/empty; outstanding WAL requires normal read-only SQLite,
whose sidecars are included in PRE/POST. Never ignore committed WAL contents.

## Frozen controls and regression

`FROI_ACCEPTANCE_FREEZE_V2.json` pins the v2 tool hashes separately, preserving
the original v1 source hash contract. The v2 directory is outside v1's protected
source enumeration; this is intentional version separation, not removing any
v1-protected file. v2 requires BOTH original v1 and new v2 contracts.

The 12 added fixture controls compare exact logical freeze, restored objects,
T1 evidence, T2 histories/outputs, T3 replay/ablation, T4 trace, T5 predicates,
continuation and final statuses. Fixture counterfactual UUID entropy is fixed
only for equality measurement; live code and the production UUID rule are not
patched. Negative controls cover missing/corrupt locators, source changes,
fixture rejection and whole-materializer prohibition.

Engineering validation: 270 existing Python tests, 12 v2 tests, 8 independent
result-dependence controls, 42 Minecraft interface tests. The last use isolated
local transport fixtures, not a Minecraft world. The initially denied sandbox
transport checks were rerun with authorized local transport access. The
result-dependence controls require their existing populated validation entry;
direct unittest invocation without that setup failed, then correct entry passed.

The 4,304,048,128-byte actual database streaming probe scanned 4,022 rows,
streamed 8,638,430,781 bytes and sampled peak RSS 166,670,336 bytes, below the
predeclared 512 MiB measurement budget. Its largest decoded event was
30,707,256 original payload bytes. The final live harness additionally measures
Windows OS peak working set (real executing Python, not a venv launcher), block
sizes, scans, stream bytes, output sizes and duration. Fixture validation and
this reading probe are not formal acceptance.

## Explicit real acceptance

```powershell
.\.venv\Scripts\python.exe -B -m tools.froi_acceptance_v2 `
  --database "storage/individuals/A-71bc612c-8f2c-4f70-8d4d-3d38bed52942/individual.db" `
  --session "S-09272552-fb87-4078-871b-1c752b1d4862" `
  --versions 16 20 22 25 --pair-versions 15 12 `
  --limit-id "c6809c75-69aa-41df-9099-6f228f4e2338" `
  --output "storage/acceptance/froi-v2-new-output"
```

Outputs are created exclusively, outside A history. No Minecraft or new formal
A is started. T1/T3 are independently reported for each supplied checkpoint;
T2 uses the original A16 pair only, not new favorable pair searches. T4 keeps the
original A27->A30 limit, exact trace and incomplete-organization rejection.
T5 preserves all_used_organizations_COMPLETE and covers the full source.
Reports inventory all 121 original organization results, including 117 limits.

The original run's Git SHA remains **MATERIAL_UNAVAILABLE**. The frozen
measurement commit is a different field and cannot repair that missing fact.
No implementation or fixture result predeclares the real T1-T5 outcomes.
