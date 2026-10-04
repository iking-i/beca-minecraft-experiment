# Experimental Validation Scope — v0.8

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


**Status:** current validation guidance for Perfect Recursion / Bidirectional Evolutionary Recursion (BER)

The experiment is not primarily a minimality test. It must make distinct causal claims observable rather than collapsing all recursion into one persistent state sequence.

## 1. Validation dimensions

The current experiment distinguishes:

1. **within-layer recursive continuation** — later recursion is causally conditioned by earlier recursion inside the same layer;
2. **subject continuity** — the experimental individual is not silently replaced by unrelated reinitialization;
3. **layer persistence** — a lower recursive layer can remain active after a higher one forms;
4. **upward recursion** — the current layer itself becomes a recursive object and a higher layer forms;
5. **repeatability of ascent** — a formed higher layer can continue its own downward recursion, encounter its own limits, and potentially become the object of a further higher layer.

These are related but not interchangeable.

## 2. Within-layer recursion

A useful causal chain is:

```text
state / observation
-> recursive processing
-> internal reconstruction
-> changed later generation/action
-> environment consequence
-> new information re-enters recursion
```

A single action or one-pass feedback loop is insufficient.

## 3. Subject continuity

The individual lifetime must be distinct from an experiment session:

```text
individual lifetime != experiment session
```

Ordinary Minecraft restart, bridge restart, host restart, or pause must not automatically create a new individual if the latest lawful state continues.

The canonical lineage should preserve stable identity, monotonic state/event lineage, current internal structure, relevant provenance, and explicit session IDs.

A fresh database should not be created for each normal run.

## 4. Continuity store is not the phenomenon by itself

Append-only or integrity-protected history is an experimental support mechanism. It helps determine whether later execution is causally connected to earlier execution.

It does **not** by itself prove Perfect Recursion.

The experiment must not report:

```text
database rows continue
=> upward/downward Perfect Recursion proven
```

Subject continuity is one condition. Recursive-layer formation is another.

## 5. Current-limit test

The environment should expose at least one real, reachable current effective limit, such as bounded storage or another finite organizational capacity.

The limit must be observable to the recursive system through consequences, but the adaptation must not be hard-coded.

Invalid pattern:

```text
if storage_full:
    create_higher_layer()
```

Valid experimental question:

```text
current organization reaches binding limit
-> limit becomes information
-> what reconstruction actually forms?
```

Possible results may include compression, re-encoding, redistribution, capacity expansion, changed representation, or higher-layer formation.

## 6. Upward-recursion criterion

A candidate higher layer `L1` must satisfy more than branch or role creation.

The experiment should establish that:

```text
L0 organization / limits / generator
become recursively processable from L1
```

and that `L1` can influence or reconstruct later `L0` organization.

The following alone are insufficient:

```text
new process
new branch
new Minecraft role
new world
new recursive origin
```

Those may all remain same-layer structures.

## 7. Lower-layer persistence criterion

If `L1` forms, test whether `L0` can continue operating rather than being replaced merely because the higher layer exists.

Support pattern:

```text
L0 ---------------------> continues
        |
        `-> L1 ---------> continues
```

If every candidate higher-layer formation necessarily destroys or replaces the lower layer, the persistent-layer claim must be narrowed.

## 8. Repeatability criterion

A finite experiment cannot prove literal infinity.

The stronger practical test is whether the same general relation can repeat:

```text
L0 downward recursion
-> current limit
-> possible L1 formation

L1 downward recursion
-> current limit
-> possible L2 formation
```

If `L1` can only exist because a one-off external rule names it higher but cannot itself participate in the same class of recursion, the result is weaker than the intended architecture.

## 9. Recursive origin is not automatically higher layer

Any new origin should be classified as one of:

```text
same-layer origin
replay branch origin
new local origin
higher-layer origin
```

Only the final classification supports upward recursion.

## 10. Process/origin/layer/subject audit

Every experimental claim should distinguish:

```text
recursive process
recursive origin
recursive layer
individual / subject
```

A new branch or recursive origin is not automatically a new subject. Subject identity requires a separate continuity criterion.

## 11. Failure is recursive information

Environment/interface failures should become structured observations where possible:

```text
attempt
-> failure / constraint / unexpected result
-> observation
-> integration
-> later recursive change
```

The interface should not silently solve the failure on behalf of the system.

## 12. Capability–knowledge separation

The Minecraft experiment adopts:

> **Capability sufficiently complete; prior knowledge minimal.**

Low-level movement, looking, digging, placement, item use, inventory/container manipulation, interaction, attack, and low-level crafting-interface manipulation should be available where technically possible.

High-level solved strategies such as `find_food()`, `craft_pickaxe()`, `build_shelter()`, or automatic path completion should not be mistaken for learned behavior.

## 13. Environment constraint versus hidden policy

Finite RAM, CPU, storage, process capacity, Minecraft physics, permission limits, and sandbox boundaries are environment constraints.

A hidden policy appears when the implementation prescribes the adaptation, for example:

```text
if memory_low: delete_oldest
if unexplained: add_branch
if blocked: jump
```

and then reports that response as internally formed.

## 14. Implementation categories

Behavior-affecting elements should be classified as:

- `CORE_IDENTITY_CONSTRAINT`;
- `ENVIRONMENT_CONSTRAINT`;
- `EXTERNAL_FIXED_MECHANISM`;
- `EXTERNAL_FIXED_POLICY`;
- `INTERNAL_VARIABLE_STRUCTURE`.

A field stored in `InternalState` is not automatically internally formed.

## 15. Layer notation boundary

Use:

```text
L_n = recursive layer
D_n = dimensional-hypothesis structure
```

A successful `L0 -> L1` experiment does not demonstrate physical dimensional ascent.

## 16. Validation summary

A strong BECA-V0 result should show, where technically reachable:

```text
same individual continues
AND
within-layer recursion is causally real
AND
real current limits enter recursion
AND
adaptation is not externally hard-coded
AND
if a higher layer forms, it recursively operates on the lower layer
AND
lower layer can persist
AND
higher layer can itself continue recursion
```

No arbitrary state-transition count is a theoretical success criterion.

## 17. Compact criterion

> **The v0.8 experiment should distinguish persistence from recursion, branch creation from layer ascent, recursive origins from subjects, and resource limits from hidden policy. The strongest evidence is not merely that one agent runs for a long time, but that a current recursive layer can encounter a real limit, recursively reconstruct it, and—without a hard-coded ascent rule—possibly become the object of a newly formed higher recursive layer while lower recursion continues.**

