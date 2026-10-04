# BECA — Testable Predictions and Failure Conditions for Perfect Recursion v0.8

## 当前 BECA-V0 阶段范围（2026-10-04）

本地实验阶段说明；以下范围限制实验目标，不改变 Perfect Recursion / BER v0.8 的核心定义。本文基于 [仓库提交 867e1f1](https://github.com/iking-i/beca-architecture/commit/867e1f192f7f21298450a553a4a733ec8f15a999) 同步，远端主分支尚未修改。

- 本阶段允许不分化；默认一个持续的 recursive process，物理 process capacity 固定且有限。新结果、未解释差异或 novelty 均不自动增加过程数量。
- 本阶段不要求 upward recursion，也不预建 L1。唯一 active recursive layer 为 L0。
- 本阶段目标是观察 architecture-limit recognition：先验证 previous recursive result 影响后续处理，再验证真实 current effective limit 的原始后果进入后续递归；识别候选需要独立、可追踪的问题表示与来源证据。
- 固定物理资源不允许自行扩展。活动记忆、关系与过程槽容量由外部配置给定；资源不足不得自动触发淘汰、压缩、分化、升层或资源申请。
- 极限只产生问题，不预设解决方案。正式路径采用容量写入拒绝，保留原记录；失败以 operation、used、capacity、requested、object references 与 provenance 进入观察和 canonical lifetime history。
- information integration != upward recursion。structure_revision 只表示状态/证据版本变化。新增记录、分支、进程、数据库大小或资源变化均不算升层。
- 旧固定分化、固定分辨率调整、固定压力减预算、固定淘汰与动作评分仅在显式 legacy_policy_debug 路径可执行，不能通过本阶段验收。
- 本地实现的当前边界：已有单过程递归与极限反馈通路，但数值解释器尚无由内部经历生成组织层问题表示的机制。原始失败或关系计数不能代替 architecture-limit recognition；无候选时必须报告 not_observed，不得宣布本阶段整体成功。

具体能力、固定策略审计、测试与判据见本地 [FORMAL_L0_EXPERIMENT.md](FORMAL_L0_EXPERIMENT.md)。以下原有 v0.8 内容保留；其中向上递归、层持续及 L0→L1→L2 是后续阶段目标，不是本轮自动验收条件。

---


This document defines observations that would support, narrow, or contradict the current architecture.

## 1. Within-layer recursive continuation

Prediction: a recursive layer can continue producing causally connected later states rather than behaving as a one-pass controller.

Support pattern:

```text
L0:
R0 -> R1 -> R2 -> R3 -> ...
```

with later states measurably conditioned by prior recursive outcomes.

## 2. Persistent lower-layer operation

Prediction: formation of a higher recursive layer does not require the lower layer to stop.

```text
L0 ---------------------> continues
      |
      `-> L1 -----------> continues
```

If higher-layer formation necessarily replaces or destroys all lower operation, the persistence claim must be narrowed.

## 3. Upward recursion criterion

Prediction: a genuine upward transition makes the lower layer itself recursively manipulable from a newly formed higher layer.

Support pattern:

```text
L0 organization / limits / generator
        ↓ becomes recursive object
L1
        ↓
changes later L0 organization / generation
```

The following alone do not satisfy the prediction:

```text
new branch
new process
new role
new world
new recursive origin
```

## 4. New origin versus higher layer

Prediction: the architecture can distinguish a same-layer recursive origin from a higher-layer origin.

Test at least:

```text
A. same-layer branch with independent recursion
B. replay branch
C. newly instantiated local origin
D. origin that recursively operates on the organization of its generating layer
```

Only `D` should count as upward recursion.

## 5. Current effective limit can become recursive information

Prediction: when a resource/organizational limit becomes behaviorally relevant, the system can represent its consequences and reconstruct its organization in response.

Candidate limits:

- storage;
- compute;
- communication;
- representation;
- perception;
- coordination.

The experiment must not pre-code the adaptation.

## 6. Limit does not prescribe answer

Prediction: reaching the same class of limit need not always produce one externally predetermined response.

Invalid experimental proof:

```text
if storage_full:
    create_L1()
```

A stronger result is that the limit becomes information and the resulting reconstruction is causally formed from the running system.

## 7. Same-layer reconstruction versus upward transition

Test whether the system can distinguish:

```text
Case A:
storage full -> existing compression mechanism -> continue in L0

Case B:
storage organization itself becomes recursive object -> L1 forms
```

If every large internal change is post-hoc labeled upward recursion, the theory is not falsifiable enough.

## 8. Repeatability of layer ascent

Prediction: a formed higher layer can itself continue downward recursion and may later encounter its own current limit.

Support pattern:

```text
L0 -> possible L1
L1 -> possible L2
```

A finite experiment does not prove infinity. It tests whether the mechanism is recursively repeatable without a built-in final layer.

## 9. Contradictory outcomes remain informative

Prediction: rare but reproducible outcomes can force higher-resolution reconstruction rather than being discarded by majority vote.

```text
A A A A B
```

A conforming architecture should be able to preserve `B` when it reveals a real missing condition.

## 10. Quantity-quality reciprocity

Prediction: accumulated variation can expose structural insufficiency and qualitative reconstruction can alter the generator of later variation.

Compare:

```text
quantity only
vs
quantity -> reconstruction -> changed generator -> new quantity
```

## 11. Recursive perception

Prediction: if two relevant real conditions are encoded identically but later effects diverge, representation itself can become a reconstruction target.

If sensing vocabulary is permanently protected from revision, the strong form must be narrowed.

## 12. Recursive capacity

Prediction: current capacity organization can itself become recursively reconstructable rather than remaining permanently external.

A finite implementation may still have hard physical/safety ceilings.

## 13. Local loss and cessation

Prediction: one process may fail, disappear, terminate, or lose information without necessarily collapsing all recursion.

The theory does not predict zero information loss or immortal local branches.

## 14. Subject continuity is distinct from layer persistence

Test separately:

```text
subject continuity:
A0 -> A1 -> A2

layer persistence:
L0 continues while L1 exists
```

Database persistence alone must not be treated as evidence of higher-layer recursion.

## 15. Process/origin/layer/subject classification test

For every generated structure, require classification as:

```text
recursive process?
recursive origin?
recursive layer?
new subject?
```

The architecture predicts these classifications need not coincide.

## 16. Replay is not automatically upward recursion

Prediction: a replayed historical branch can be a new recursive origin while remaining inside the same recursive layer.

If the present branch remains and an earlier-like branch is generated, classify it as replay/branch generation unless an independent higher-layer criterion is satisfied.

## 17. Subject continuity test

A continuing subject may satisfy:

```text
subject(a0) = subject(a1) = ... = subject(a_n)
state(a0) != state(a1) != ... != state(a_n)
```

without requiring earlier states to remain parallel current selves.

## 18. Session/lifetime test

Prediction: ordinary program or Minecraft session boundaries need not create a new experimental subject if the latest lawful canonical state continues.

A fresh database per run would erase long-horizon structural evidence and should not be the default experiment design.

## 19. Capability–knowledge test

Prediction: a body may possess an action channel without possessing strategy for using it.

Failure to learn an action that has no physical execution channel is not evidence against recursion.

## 20. External-policy audit

For each behavior-affecting rule, classify whether it is:

- environment constraint;
- fixed mechanism;
- fixed policy;
- internally formed structure.

If the claimed emergent response is actually produced by a fixed adaptation rule, the emergence claim fails.

## 21. Layer notation boundary

Prediction/discipline:

```text
L_n = recursive layer
D_n = dimensional-hypothesis structure
```

Observed `L0 -> L1` does not establish physical dimensional ascent.

## 22. Provenance/replay/reversal tests

The existing distinctions remain:

- theoretical reconstruction models an earlier state;
- replay generates a new branch;
- true reversal would return the active state itself;
- subject continuation preserves one subject through state change.

Retained internal later-state evidence falsifies a claim of complete reversal for the defined reversed domain.

## 23. Strong counterexample targets

The v0.8 strong form should be narrowed if formal analysis establishes any of the following as unavoidable:

1. a higher recursive layer can exist only by terminating the lower layer;
2. current limits can never become recursive information;
3. layer organization can never itself become a recursive object;
4. every new recursive origin is necessarily identical to a higher-layer transition;
5. information direction cannot be distinguished from recursive direction;
6. recursive process/origin/layer/subject identity cannot be meaningfully separated;
7. a unique final recursive layer is logically required;
8. higher-layer formation can only occur through a fixed externally supplied rule rather than recursively formed reconstruction;
9. perception/capacity/control must remain permanently fixed outside recursion.

## 24. Falsifiability discipline

Perfect Recursion must not protect itself by relabeling every structural change as a higher layer.

Before evaluation, specify enough of the current layer and its organizational variables to distinguish:

```text
same-layer modification
from
layer transition
```

and enough provenance to distinguish internal formation from external policy.

## 25. Current status

Perfect Recursion remains a conceptual architecture with experimentally testable structural claims, not an established universal law.

Its strongest current experimental challenge is to demonstrate a real current limit entering recursion and, without a hard-coded ascent rule, observe whether reconstruction remains within the current layer or creates a higher recursive layer that can recursively operate on the lower one.

