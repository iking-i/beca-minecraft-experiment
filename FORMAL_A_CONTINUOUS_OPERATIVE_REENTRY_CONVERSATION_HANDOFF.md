# Formal A Continuous Operative Reentry — conversation handoff

Date: 2026-10-08. Branch: `codex/operative-connection-correction`.
Implementation/validation anchor: `1e28a00a401681efb304ec518ed672a12cea901f`.
Closeout anchor: the separate documentation commit containing this handoff and
`FORMAL_A_CONTINUOUS_OPERATIVE_REENTRY_CLOSEOUT.md`, reported after commit and checked against the remote branch.

```makefile
FORMAL_A_CONTINUOUS_OPERATIVE_REENTRY = PASS / COMPLETED / FROZEN
CR_T1..CR_T10 = ALL PASS
CURRENT_STATE_AUTHORITATIVE = YES
S1_PERSISTED = YES
S1_REFORMED_AFTER_RESTART = NO
NORMAL_ACORE_REENTRY = PASS
EDGE_ABLATION = PASS
FULL_REGRESSION = 560 passed / 114 subtests passed
FROZEN_HASH = MATCH
NEXT_QUESTION_FROZEN = YES
NEXT_DESIGN_STARTED = NO
NEXT_IMPLEMENTATION_STARTED = NO
NEXT_EXPERIMENT_STARTED = NO
MINECRAFT_RUN = NO
```

## Read first and known baseline

Read `00_DISCUSSION_CONSTRAINTS.md`, `OPERATIVE_CONNECTION_ERRATUM.md`,
`FORMAL_A_CONTINUOUS_OPERATIVE_REENTRY_CLOSEOUT.md`, the frozen stage spec, all
`experimental/formall0_continuous/` code/VALIDATION/TK_DIAGNOSIS records and
`history/tk_not_testable_original/`, plus `tests/test_formal_continuous_operative.py`.
Read prior FormalL0 adoption closeout/ISOLATION and Current State / Full Audit
History handoff before interpreting the new scope. Current indexes are
`RESEARCH_STATUS.md` / `RESEARCH_STATUS.json`; README summarizes them.
The local authoritative `THEORY_REFERENCE.json` records
`iking-i/beca-architecture/main@2e207806289269a1213f6fcc83fa14eb0984aab7`. It is not changed or remotely
revalidated by this closeout; no theory synchronization is performed here.

The closeout changes only its two new documents and the three current status
indexes. Experimental code, old reports/specs, hashes, tests, default runtime,
body, sampler/binder, caps, databases and unrelated untracked files are preserved.
Tracked worktree must be clean after commit; unrelated untracked material may remain
and is excluded. The push targets only this current research branch, not main.
The exact closeout HEAD and remote verification are reported after commit.

## What is established, with exact scope

在独立 TEST_ONLY ACore 生命周期中，同一个 A 的合成输入实际经历形成了 operative structure S1；S1 被原子写入权威 Current State，跨真实进程恢复后无需重新形成，即可在正常 ACore 状态转换中成为实际运行依赖。S0 与 S1 使用相同表示和执行机制；S1-only ablation 改变实际计算，来源标签不赋予执行特权，完整回归通过。

Scope: synthetic observations/FakeBridge, explicitly enabled TEST_ONLY Core path,
mechanism `FORMALL0-OPERATIVE-CORE-TEST_ONLY-1`, independent database, one individual
per ON/OFF witness. Actual OS processes exit/reopen; this is not a Python-state
handoff. S0 is ORIGIN_SUPPLIED only at initial creation; S1 is absent initially and
formed through ordinary experience/integration under the unchanged frozen engine.
S0/S1 use the same reference-edge representation and execution mechanism.

```text
ACore -> S0 / authoritative Current State
-> ordinary synthetic experiences -> internally formed S1 -> atomic commit
-> normal Core shutdown / lease release / process exit
-> new Core / same DB / same A / same mechanism version
-> exact S1/supports restored without replay or reformation
-> ordinary accept_observation / advance -> actual operative dependency
```

State chain in both mode witnesses: S0 A1; S1 formed A3; shutdown A4; restart A5;
shutdown A9. First restart E3 has the unchanged carrier gap; E4/E5 read persisted S1.
S1-only ablation changes actual expected operands/comparison True -> None; controls
stop before write. Removed/swapped/unified provenance leaves operands unchanged.
No special consumer or post-processing attachment supplies the result.
OFF has no recorded states/events and still recovers S1. Current State is
necessarily persistent; optional Full Audit History is observer evidence.

## Evidence, regression and original failure

CR-T1–CR-T10 PASS. Recorded dedicated tests 28 passed; related 161 passed / 23
subtests; full original collection 560 passed / 114 subtests, no exclusions;
WORLD_ENTRY guard 1 passed / 13 subtests. These were audited, not rerun at closeout.
Production FormalL0 LF-normalized hash:
`1b6abea5d568c349bf7c181ecd771fc6f08cd0f1791fa49be7434c4acd354b62`.
All 13 frozen hashes match. Default behavior and historical evidence are unchanged.

Keep the original CR-T10 NOT_TESTABLE and 559/114/one-Monitor-failure report and
raw Tcl/Tk traceback. Tcl reported failure reading `ttk/utils.tcl` during Tk
bootstrap, before Monitor/Core construction. The triggering cause remains
NOT_ESTABLISHED: passing later checks do not prove a permanent library defect,
DLL defect or a specific test-order regression. The independent byte-identical
Tcl/Tk verification environment supports real GUI/full regression; it does not
establish that an unknown transient cause has been diagnosed or permanently cured.
Original failures and earlier FA-T9 frozen-source conflict records remain failures.

## Nonclaims and remaining boundaries

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

Do not equate TEST_ONLY Core integration with default/mainline adoption or internal
body-expression authorship. The law, startup scaffold and test input source are
experimenter supplied and accurately attributed. Do not combine prior BPC scoped
results into a live operative body loop. No claim of consciousness continuity,
general parameter formation, universal generative dynamics or theoretical proof.

## Only the next question is frozen

**已经由同一个 A 的实际经历形成、持续保存并正常重入的内部 operative structure，能否进一步参与 A 对外表达内容的形成，并通过结构消融证明其因果作用？**

This does not require direct Minecraft execution. Before next-stage design, first
check:

- ACore 现有的身体表达准备路径。
- select_uniform_action 及外部固定策略。
- action code 与参数绑定机制。
- BPC-R2、BPC-LIVE-1 已冻结的身体接口结论及解释纠错边界。
- 内部 operative structure 能否成为实际表达操作数。

Do not encode a fixed S1-to-action map as internal authorship. A changed internal
computation is not evidence that action code or parameters are internally authored.
No next acceptance criteria, design, implementation, migration or experiment is
provided/authorized by this handoff. Next design/implementation/experiment remain
NOT_STARTED. Preserve the known baseline and stop after closeout remote verification.
