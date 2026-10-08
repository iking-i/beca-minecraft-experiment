# Formal A Continuous Operative Reentry — TEST_ONLY closeout

Date: 2026-10-08. Branch: `codex/operative-connection-correction`.

```makefile
FORMAL_A_CONTINUOUS_OPERATIVE_REENTRY = PASS / COMPLETED / FROZEN
IMPLEMENTATION_COMMIT = 1e28a00a401681efb304ec518ed672a12cea901f
CR_T1..CR_T10 = ALL PASS
CURRENT_STATE_AUTHORITATIVE = YES
S1_PERSISTED = YES
S1_REFORMED_AFTER_RESTART = NO
NORMAL_ACORE_REENTRY = PASS
EDGE_ABLATION = PASS
FROZEN_HASH = MATCH
```

Closeout anchor: the separate documentation commit containing this file and
`FORMAL_A_CONTINUOUS_OPERATIVE_REENTRY_CONVERSATION_HANDOFF.md`; its exact SHA is reported after commit and remote verification.
This avoids a circular self-hash. No implementation/evidence file is changed here.

## Frozen object, representation and scope

The preregistration is [the stage spec](FORMAL_A_CONTINUOUS_OPERATIVE_REENTRY_SPEC.md).
The evidence anchor is `1e28a00a401681efb304ec518ed672a12cea901f`. The reused derived engine/formation mechanism
remains frozen at `8b33097b746931b788ab5e72de66dd483af18edc`.
This phase uses explicitly enabled independent TEST_ONLY ACore lifecycles,
synthetic raw observations and FakeBridge. It does not create or migrate a formal
mainline A, alter the selected individual, or call Minecraft/body perform.

Both S0 and S1 use `InternalState.l0_state.operative_test_only.edges`, connecting
ordinary relation references. A single versioned experimental interpreter reads
them before actual expected-outcome operands and comparison are calculated.
The separately recorded provenance/support evidence does not dispatch execution.
`operative_core_test_only` metadata binds TEST_ONLY mode, engine version,
resolved database path and individual identity. Default Core rejects this state;
the explicit exception is guarded rather than a general weakening of rejection.

S0 is supplied only at origin. S1 forms from post-startup actual test experiences
and integration under the already frozen candidate formation rule. This is
executed synthetic-history evidence, not real-world causal-law evidence.

## Strongest accepted claim

在独立 TEST_ONLY ACore 生命周期中，同一个 A 的合成输入实际经历形成了 operative structure S1；S1 被原子写入权威 Current State，跨真实进程恢复后无需重新形成，即可在正常 ACore 状态转换中成为实际运行依赖。S0 与 S1 使用相同表示和执行机制；S1-only ablation 改变实际计算，来源标签不赋予执行特权，完整回归通过。

The scope is one individual per witness, not one individual shared across two
recording-mode runs. Identity continuity is verifiable database/state lineage;
it is not philosophical consciousness continuity. The necessary persistent
structure is distinct from optional external Full Audit History.

## Actual lifecycle evidence

```text
ACore / explicit TEST_ONLY version
  -> S0 in authoritative Current State
  -> ordinary synthetic observations and actual experience/integration
  -> newly formed S1 committed, not executed in formation round
  -> normal shutdown / lease release / OS process exit
  -> new Core process / same database / same individual / same engine version
  -> authoritative Current State restores the identical S1 and supports
  -> ordinary accept_observation and later advance use S1
  -> actual expected-outcome operands/comparison depend on S1
```

| Mode | Individual | Create / restart PID | State chain | Recorded states / events |
|---|---|---|---|---|
| ON | A-6d7863ca-15e6-4139-b79c-eb019b9fef18 | 3568 / 31852 | origin A1; S1 A3; shutdown A4; restart A5; shutdown A9 | 10 / 58 |
| OFF | A-9936dfcc-503f-4bb3-bcd4-ff0441f572ee | 2828 / 6552 | origin A1; S1 A3; shutdown A4; restart A5; shutdown A9 | 0 / 0 |

S0 is `opaque:origin -> opaque:operand`; S1 is
`opaque:operand -> U-cdb3852bc0eebc2503db:-1`. Committed shutdown state equals the
authoritative snapshot. Exact operative collection and formation evidence are
restored at restart; the next state version increases. Session identity may change
without creating a new individual. Both database integrity checks are `ok`.
The OFF run has an explicit audit gap and no states/events history to replay.
SQL tracing verifies no full audit/history SELECT in restore/reentry.

E3 after restart follows existing carrier-epoch gap handling: it records
`TEMPORAL_LINK_UNRESOLVED`, not a successful partial. E4/E5 in that same process
actually consume S1. The gap and frozen observation sequence are unchanged.
S1-only controls execute ordinary ACore processing and stop before commit;
no canonical history is altered and no alternate consumer supplies an answer.
Normal comparison is True; masking only S1 gives None. Reinsertion restores exact
input equality. Provenance removal, swapping and unification preserve operands.

## CR-T1 through CR-T10 evidence audit

| Criterion | Frozen result | Evidence |
|---|---|---|
| CR-T1 | PASS | Explicit TEST_ONLY mode, read-only admission, default rejection and validated writeback exception; no silent database conversion. |
| CR-T2 | PASS | Each ON/OFF witness retains one individual_id and consecutive committed versions across distinct OS processes. |
| CR-T3 | PASS | S1 is absent at origin; actual E2 experience/integration forms it, with no S1 execution in its formation round. |
| CR-T4 | PASS | S1 and lifecycle/version metadata are committed atomically in authoritative Current State; transaction-failure control rolls back. |
| CR-T5 | PASS | New Core process opens the same database/version and recovers the identical collection and S1/supports, without resupplying S0. |
| CR-T6 | PASS | Ordinary ACore.accept_observation uses recovered S1 through the same experimental advance, not a specialized consumer. |
| CR-T7 | PASS | Only S1 is masked while other state/input/supports stay fixed; actual expected outcomes and comparison change True -> None. |
| CR-T8 | PASS | Removed/swapped/unified provenance leaves actual operands unchanged; origin labels grant no execution privilege. |
| CR-T9 | PASS | Mode/version/path/identity/lease/caps/structure failures reject safely, without repair, fallback, history replay or replacement A. |
| CR-T10 | PASS | Original full collection passes, including Monitor; all 13 WORLD_ENTRY hashes match; original tests and old evidence are preserved. |

Evidence and code: `experimental/formall0_continuous/VALIDATION.md`,
`VALIDATION.json`, `channel.py`, `runner.py`, `validation.py`, and
`tests/test_formal_continuous_operative.py`. Full machine snapshots, post-commit
journals, formation supports, raw test observations and causal pairs agree.
No detached graph executor, specialized consumer, replay or precomputed answer
stands in for actual Core/Current State/ordinary experimental advance.

## Recorded verification and preserved failures

| Recorded implementation verification | Result |
|---|---|
| Dedicated lifecycle and independent negative controls | 28 passed |
| Related regression | 161 passed / 23 subtests passed |
| Complete original Python collection; no exclusions | 560 passed / 114 subtests passed; 0 failures |
| Original-environment diagnostic complete regression | 560 passed / 114 subtests passed; 0 failures |
| Original frozen WORLD_ENTRY guard | 1 passed / 13 subtests passed |

These are audited recorded results, not new closeout test/experiment runs.
Closeout performs JSON parsing, evidence/log/hash consistency, index consistency,
protected-file/untracked preservation and git diff checks only.

The original **NOT_TESTABLE** reports remain unchanged at
`experimental/formall0_continuous/history/tk_not_testable_original/VALIDATION.md`
and `VALIDATION.json`: CR-T10 NOT_TESTABLE, 559 passed / 114 subtests / 1 Monitor
failure. The exact test failed inside `tk.Tk()` before Monitor/Core construction,
while Tcl/Tk sourced `ttk/utils.tcl`. The immediate script-read failure is recorded;
the specific triggering cause is **NOT_ESTABLISHED**, not diagnosed as permanent
missing files, DLL damage or a demonstrated code regression.

The original HEAD/current single tests, pure Tk checks and later full runs pass.
The final full run used the same Python/DLLs and a 1265-file byte-identical complete
Tcl/Tk library copy, bound only through verification-process environment variables.
This is a usable independent validation environment, not proof of a permanent
repair or of the original transient cause. No skip, xfail, Tk mock, frozen hash,
old test or expected result was changed to obtain PASS.

`TK_DIAGNOSIS.json` / `TK_LIBRARY_MANIFEST.json` retain the boundary evidence.
`history/RAW_LOGS.json` preserves original raw failure/pass bytes losslessly as
base64 plus raw SHA-256 and UTF-8 text because *.log files are git-ignored.
Prior facility/related failures and prior FormalL0 FA-T9 source-hash FAIL remain
historical failures. Later PASS is not retroactively written into any earlier run.

## Frozen compatibility and nonclaims

FormalL0 LF-normalized SHA-256 remains
`1b6abea5d568c349bf7c181ecd771fc6f08cd0f1791fa49be7434c4acd354b62`.
All 13 WORLD_ENTRY component hashes match; WORLD_ENTRY_FREEZE is unchanged.
Default FormalL0/Core behavior is preserved. Adoption is demonstrated only through
an explicit versioned TEST_ONLY Core path, not the ordinary production selection.

```ini
DEFAULT_FORMALL0_ADOPTION = NOT_ESTABLISHED
REAL_MAINLINE_A_ADOPTION = NOT_ESTABLISHED
BODY_EXPRESSION_AUTHORSHIP = NOT_ESTABLISHED
AUTONOMOUS_ACTION_SELECTION = NOT_ESTABLISHED
AUTONOMOUS_GOAL_FORMATION = NOT_ESTABLISHED
L1_UPWARD_RECURSION = NOT_ESTABLISHED
BEHAVIORAL_CAUSAL_CLOSURE = NOT_ESTABLISHED
GENERAL_PARAMETER_FORMATION = NOT_ESTABLISHED
ARBITRARY_STRUCTURE_EXECUTION = NOT_ESTABLISHED
PHILOSOPHICAL_CONSCIOUSNESS_CONTINUITY = NOT_ESTABLISHED
UNIVERSAL_GENERATIVE_DYNAMICS = NOT_ESTABLISHED
```

No default/mainline migration, action/parameter authorship, goals, body policy,
capacity increase, theory update or world-facing execution is established.
The Current State / Full Audit History closeout retains its independent
infrastructure scope; full history remains optional observer evidence, not an
A-facing recursive memory or a prerequisite for restoration.
OH/BPC/FROI/GSC/CEC/Successor and prior FormalL0 results retain their frozen scopes.
BPC-R2 and BPC-LIVE-1 PASS are not concatenated into an operative behavioral loop.

## Next research question only — no design or implementation

**已经由同一个 A 的实际经历形成、持续保存并正常重入的内部 operative structure，能否进一步参与 A 对外表达内容的形成，并通过结构消融证明其因果作用？**

This is not a request to run Minecraft. Before any next design, the required
initial checks are only:

- ACore 现有的身体表达准备路径。
- select_uniform_action 及外部固定策略。
- action code 与参数绑定机制。
- BPC-R2、BPC-LIVE-1 已冻结的身体接口结论及解释纠错边界。
- 内部 operative structure 能否成为实际表达操作数。

Do not prewrite an S1-to-action mapping or infer action authorship from an internal
calculation effect. This closeout defines no next mechanism or acceptance test.

```ini
NEXT_QUESTION_FROZEN = YES
NEXT_DESIGN_STARTED = NO
NEXT_IMPLEMENTATION_STARTED = NO
NEXT_EXPERIMENT_STARTED = NO
MINECRAFT_RUN = NO
```

Stop after this separate closeout commit is pushed and its remote HEAD verified.
