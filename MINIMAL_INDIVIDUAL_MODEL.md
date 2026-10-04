# Minimal Experimental Individual Model — v0.8

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


**Status:** current experimental realization of Perfect Recursion / Bidirectional Evolutionary Recursion (BER)

This document defines the current first-individual experiment and its relation to recursive layers.

## 1. Initial experimental state

The experiment begins with one individual and one directly encountered environment:

```text
D0:
A <-> E
```

where:

- `A` is the only initial subject under study;
- `E` is the directly encountered environment;
- `A` and `E` begin in the same initial dimensional-hypothesis level `D0`;
- interaction alone does not create `D1`;
- no higher recursive layer is predeclared merely because `A` and `E` interact.

At the recursive-layer level, the clean initial condition is:

```text
L0 only
```

Any `L1` must arise through later recursive reconstruction rather than initialization.

## 2. Layer notation and dimensional notation

The experiment distinguishes:

```text
L_n = recursive layer
D_n = dimensional-hypothesis structure
```

Therefore:

```text
L0 -> L1
```

does not automatically imply:

```text
D0 -> D1
```

## 3. Individual identity and lifetime

Successive states may belong to the same continuing subject:

```text
A0 -> A1 -> A2 -> A3 -> ...
```

with one canonical subject identity under the experiment's adopted continuity criterion.

```text
individual lifetime != experiment session
```

A normal pause, host restart, bridge restart, or Minecraft restart must not automatically create a fresh `A`.

## 4. One hard individual-level condition

The current first-individual experiment gives `A` one hard individual-level condition:

```text
Continuity(A) != 0
```

This is an identity/existence condition, not a reward, fitness score, survival bonus, or ordinary preference weight.

The method used to preserve continuity may itself change recursively.

## 5. Canonical continuity store

The implementation preserves one lawful causal-state lineage across ordinary sessions.

Preferred properties include:

- stable `individual_id`;
- monotonic event/state lineage;
- append-only or equivalently integrity-protected history;
- explicit session metadata separate from lifetime identity;
- preservation of current internal structure and relevant provenance.

The experiment should not create a fresh database for each normal run.

The canonical store is an experimental carrier and audit mechanism, not the definition of the subject itself.

## 6. Continuity support is not proof of Perfect Recursion

A protected history chain can show that later execution is causally connected to earlier execution.

It cannot by itself prove recursive-layer ascent.

The experiment must distinguish:

```text
subject continuity
from
within-layer recursion
from
higher-layer formation
```

## 7. Environment coupling

`A` begins with real input and output paths:

```text
E -> A
A -> E
```

This is a structural birth condition, not an additional behavioral command such as `always explore` or `maximize novelty`.

## 8. Capability–knowledge separation

The Minecraft experiment follows:

> **Capability sufficiently complete; prior knowledge minimal.**

The body should expose ordinary low-level operations required for a normal player to affect the world, including where technically possible:

- movement, turning, looking, jumping, sprinting, sneaking;
- targeting currently perceivable blocks/entities;
- digging/breaking;
- block placement;
- hotbar selection and held-item use;
- inventory movement, equipping, dropping;
- block/entity interaction and attack;
- container-slot manipulation;
- low-level crafting-interface manipulation.

The experiment should not pre-supply solved high-level skills such as `craft_pickaxe()`, `build_shelter()`, `find_food()`, `equip_best_tool()`, or `pathfind_to_goal()` when those decisions are under study.

## 9. Within-layer differentiation

`A` may generate many local recursive processes inside `L0`:

```text
        A
     /  |  \
    b   c   d
```

This is **within-layer/internal differentiation**, not automatically downward-recursion terminology and not automatically higher-layer formation.

The individual count may remain one:

```text
individual count = 1
recursive-process count = many
```

## 10. Process termination

Local processes may continue, pause, merge, be replaced, fail, or terminate.

Failure, uncertainty, detected limits, resource cost, changed conditions, and supersession can all be informative.

```text
no successful answer != no information
no successful answer != mandatory infinite continuation
```

## 11. Recursive quantity and control

Recursive quantity, filtering/integration, continuation/termination, memory organization, perception, action strategy, allocation, and coordination may themselves become recursively revisable.

A physical ceiling remains possible:

```text
k_actual <= k_capacity(R_exp)
```

The capacity ceiling is an environment condition, not by itself a policy prescribing `k_actual` or how adaptation must occur.

## 12. Current-limit experimental condition

A useful first experiment should expose at least one real, reachable current effective limit, such as finite storage.

The system should be able to observe consequences of that limit, but the adaptation must not be externally hard-coded.

Invalid:

```text
if storage_full:
    create_L1()
```

Valid experimental question:

```text
L0 reaches a binding limit
-> limit enters recursion
-> what reconstruction forms?
```

Possible same-layer results include compression, re-encoding, redistribution, or another internal reorganization.

A genuine upward transition occurs only if `L0` itself becomes a recursive object and `L1` forms.

## 13. Initial world/role topology

The experiment should not pre-build the result it is supposed to observe.

A clean initial Minecraft realization begins with:

```text
1 active subject/body realization
1 active world/environment realization
1 active recursive layer L0
```

Infrastructure may support later allocation of additional worlds, roles, or processes, but those carriers do not count as higher recursion merely because they can be created.

The causal order should be:

```text
recursive reconstruction forms a structure that requires a new carrier
-> carrier is allocated
```

not:

```text
carrier is pre-created
-> carrier is declared a higher recursive layer
```

## 14. New world/role is implementation substrate, not theory result

A new Minecraft role or world may carry:

- a same-layer branch;
- a replay branch;
- another local recursive process;
- a higher-layer realization.

Its theoretical classification depends on causal role, not on the mere fact that it is separate.

## 15. Upward-recursion experimental criterion

A candidate `L1` must be able to recursively act on aspects of `L0` such as its organization, limits, or generative conditions.

Support pattern:

```text
L0 organization becomes object of recursion
        ↓
L1 forms
        ↓
L1 changes later organization/generation of L0
```

`L0` should be able to continue while `L1` exists if the persistent-layer claim is being tested.

## 16. Repeatability

If `L1` forms, it should itself be capable of downward recursion:

```text
L1_0 -> L1_1 -> L1_2 -> ...
```

and may later encounter its own current limit.

A finite experiment cannot prove infinity. It can test whether the layer-forming mechanism is repeatable without an explicit final-layer rule.

## 17. Implementation categories

The implementation must distinguish:

1. `CORE_IDENTITY_CONSTRAINT` — currently `Continuity(A) != 0`;
2. `ENVIRONMENT_CONSTRAINT` — finite resources, Minecraft physics, permissions, history integrity;
3. `EXTERNAL_FIXED_MECHANISM` — sensing/action/storage/process/world allocation plumbing;
4. `EXTERNAL_FIXED_POLICY` — programmer-supplied behavioral/adaptation rules;
5. `INTERNAL_VARIABLE_STRUCTURE` — structures formed or changed through `A`'s own causal history.

A mechanism may expose the physical possibility of allocating a world or role without prescribing when or why it should be used.

## 18. Host safety boundary

Minecraft is the intended directly exposed environment.

Host OS, files, credentials, network, hardware, and unrelated infrastructure remain behind an independent safety boundary.

The experiment should preserve sufficiently complete in-world bodily affordances while minimizing unnecessary host-facing capability.

## 19. Minimum experimental summary

```text
Initial recursive layer: L0 only
Initial subject:         one canonical A
Initial environment:     one E / one Minecraft world realization
Relation:                A <-> E
Hard subject condition:  Continuity(A) != 0
Lifetime:                crosses ordinary sessions
Canonical history:       integrity protected
Body capability:         sufficiently complete low-level affordances
Prior knowledge:         minimal
Current limits:          real and observable, adaptation not hard-coded
Higher-layer creation:   not pre-initialized
Host safety:             independently constrained
```

## 20. Compact formulation

> **The first BECA-V0 experiment begins with one subject, one directly encountered environment, and one recursive layer. It preserves subject continuity across sessions without treating database persistence as proof of Perfect Recursion. Real current limits may enter recursion, but their solutions are not prescribed. Additional worlds, roles, branches, or origins are implementation carriers whose theoretical meaning must be inferred from causal role. Upward recursion is established only when the current layer itself becomes a recursive object and a higher layer forms.**

