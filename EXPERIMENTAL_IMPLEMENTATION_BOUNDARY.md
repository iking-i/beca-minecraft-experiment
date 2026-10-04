# Experimental Implementation Boundary — v0.8

## World-entry audit update (2026-10-04)

See [WORLD_ENTRY_AUDIT.md](WORLD_ENTRY_AUDIT.md) and [BODY_CAPABILITIES.md](BODY_CAPABILITIES.md). Java 26.1 / protocol 775 is the audited carrier. ActionSpace v2 retains 47 entries; 39 use the formal low-level path and eight multi-click conveniences remain debug-only. Formal frames/provisioning use numeric codes and numeric requirement IDs, not action names or use descriptions.

Held controls, both hands, explicit item release, dig start/cancel/finish, manual respawn, dismount, wake and supported raw slot modes are external fixed mechanisms. Placement never implicitly equips; target inputs check current view/face. Formal dig/place send native packets without fabricated world edits. Slot prediction is labeled carrier feedback, not server acknowledgment.

No recursive engine, resource capacity, higher layer, architecture recognition, reward, goal or selection algorithm is changed. Death remains observable through the existing explicit action channel; no survival rule is installed. Complete vehicle physics, editors, specialized GUI feedback and unsupported slot modes remain carrier limitations.

The user explicitly allowed independent new test databases for this phase. The acceptance runner uses a separate selection file and per-individual directory; the original canonical selection/history remain unchanged. Reports identify the test individual and TEST_ONLY authorship; they never claim a new A continues the original A.

## 当前 BECA-V0 阶段范围（2026-10-04）

本地实验阶段说明；以下范围限制实验目标，不改变 Perfect Recursion / BER v0.8 的核心定义。本文基于 [仓库提交 867e1f1](https://github.com/iking-i/beca-architecture/commit/867e1f192f7f21298450a553a4a733ec8f15a999) 同步，仅为实验仓库的本地阶段说明，不修改理论仓库。

- 本轮限定 V0-A / V0-B 单过程正式基线：外部初始化 k_actual=1，process capacity=N。当前没有内生 create_process 能力，因此不能称为 A 自主选择不分化。新结果或 novelty 不自动增加数量。
- 本阶段不要求 upward recursion，也不预建 L1。唯一 active recursive layer 为 L0。
- 本轮只验证 previous recursive result 对后续处理的作用、真实容量极限及其 raw 后果重入。architecture-limit recognition 固定报告 not_observed，不进入 V0-C，也不生成识别候选或 L1。
- 首次正式 Session 原子保存 locked_caps、locked_resource_caps、formal_condition_id 和 baseline_version。七项逻辑容量、正式启动的四项 Supervisor 容量及四项身体采样容量跨重启/Session 锁定；不一致时在任何 A 写入前拒绝。无自动迁移、扩缩容或解锁接口。
- 极限只提供原始后果，不预设解决方案。递归输入仅允许 limit_id、opaque resource_port_id / operation_id、used、capacity、requested、operation_performed=false、object_refs、source_state_version、frame_id。语义代码、资源名称及架构标签只保留在 auditor_metadata。
- information integration != upward recursion。structure_revision 只表示状态/证据版本变化。新增记录、分支、进程、数据库大小或资源变化均不算升层。
- 旧固定分化、固定分辨率调整、固定压力减预算、固定淘汰与动作评分仅在显式 legacy_policy_debug 路径可执行，不能通过本阶段验收。
- 本轮可验证 V0-A / V0-B 基线，不验证组织方式改变、自主策略、自主分化或升层。INTERNAL_VARIABLE_STRUCTURE_CHANGE 当前只是数据/关系证据变化；不得改称架构重构。两个基线通过不代表 v0.8 强形式整体通过。

具体能力、固定策略审计、测试与判据见本地 [FORMAL_L0_EXPERIMENT.md](FORMAL_L0_EXPERIMENT.md)。以下原有 v0.8 内容保留；其中向上递归、层持续及 L0→L1→L2 是后续阶段目标，不是本轮自动验收条件。

---


**Status:** current implementation boundary for BECA-V0 / Perfect Recursion experiments  
**Scope:** experimental realization, not a new core theoretical invariant

This document separates the individual, recursive layers, environment, implementation substrate, and experimenter-supplied policy so that engineering convenience is not mistaken for recursively formed structure.

## 1. One hard individual-level constraint

The current first-individual experiment gives `A` one hard individual-level condition:

```text
Continuity(A) != 0
```

This is an identity/existence condition, not a reward, survival bonus, fitness score, or ordinary preference weight.

## 2. Five implementation categories

Every fixed element that can affect behavior should be classified as one of:

### 2.1 CORE_IDENTITY_CONSTRAINT

Currently:

```text
Continuity(A) != 0
```

### 2.2 ENVIRONMENT_CONSTRAINT

Examples:

- finite RAM, CPU, storage, process count, or runtime;
- Minecraft physics/world rules;
- finite sensing range;
- unavailable host/network permissions;
- sandbox boundaries;
- integrity protection on canonical history.

An environment constraint defines what is available. It does not prescribe adaptation.

### 2.3 EXTERNAL_FIXED_MECHANISM

Infrastructure that exposes possibility, for example:

- Mineflayer bridge;
- event transport;
- observation capture;
- low-level action execution;
- append-only state recording;
- process creation;
- world/role allocation capability;
- serialization/database access.

A mechanism should not silently choose when or why the operation is used.

### 2.4 EXTERNAL_FIXED_POLICY

A programmer-supplied rule that prescribes choice/adaptation, for example:

```text
if memory_low: delete_oldest
if storage_full: create_higher_layer
if unexplained: increase_branch_count
prefer_unseen_actions
if blocked: jump
select_best_tool
```

These must not be reported as recursively formed behavior.

### 2.5 INTERNAL_VARIABLE_STRUCTURE

A relation, representation, control variable, or policy whose current form was created/modified through `A`'s causal history and can affect later recursion.

## 3. Recursive-layer classification is separate

The implementation must distinguish:

```text
recursive process
recursive origin
recursive layer
individual / subject
```

A new process, branch, world, role, or recursive origin is not automatically a higher recursive layer.

A candidate higher layer must satisfy the v0.8 criterion that the lower layer's own organization, limits, or generator become recursively manipulable from the higher layer.

## 4. Initial topology

The first experiment should begin with:

```text
one canonical subject A
one directly encountered environment/world realization
one active recursive layer L0
```

Infrastructure MAY expose the capability to create/allocate later worlds, roles, or processes, but those carriers should not be pre-created and labeled as higher recursion.

The intended causal order is:

```text
internal reconstruction forms a structure requiring a carrier
-> implementation mechanism allocates carrier
```

not:

```text
implementation allocates carrier
-> system is declared to have ascended
```

## 5. Current effective limits

A finite experimental envelope may impose:

```text
R_exp
```

including bounded storage, compute, process capacity, or other resources.

A resource ceiling is an environment condition. It becomes hidden policy only when the implementation also prescribes the response.

The experiment may deliberately select a reachable limit, such as storage capacity, to observe whether the limit enters recursion.

It MUST NOT define the theoretical outcome in advance.

## 6. Resource limit versus adaptation

Distinguish:

```text
storage <= N
```

from:

```text
if storage == N:
    compress()
```

or:

```text
if storage == N:
    create_L1()
```

The first is an environment constraint. The latter two are adaptation policies if externally fixed.

## 7. Recursive quantity

A real machine can enforce:

```text
k_actual <= k_capacity(R_exp)
```

`k_capacity` is a resource ceiling. `k_actual` should not be permanently dictated by an unexplained external strategy if recursive control is under study.

## 8. Individual lifetime is not session lifetime

```text
individual lifetime != experiment session
```

Minecraft restarts, bridge restarts, host reboots, pauses, or observation gaps do not automatically create a new subject.

Preserve:

- stable canonical `individual_id`;
- monotonic state/event lineage;
- current internal structure;
- relevant process/origin/layer provenance;
- session metadata separately.

Do not create a fresh database merely because a new run begins.

## 9. Canonical history

A normal continuation may look like:

```text
A0 -> A1 -> A2 -> pause -> A3 -> A4
```

The canonical store is part of the experimental substrate used to resume and audit lawful state.

It is not identical to the theoretical subject and does not by itself prove recursive-layer ascent.

## 10. History integrity

Ordinary execution should not permit silent historical rewriting.

Preferred properties include:

- append-only recording;
- monotonic sequence/version identifiers;
- hash chaining or equivalent integrity verification;
- separated permissions;
- no ordinary runtime API for rewriting canonical past events;
- explicit corruption/replacement detection.

## 11. Resume, replay, branch, and layer are different

### Canonical resume
Continue from latest lawful state.

### Historical replay
Execute an earlier-like reconstructed state after later history exists.

### New branch
Begin distinct branch-local causal provenance.

### Higher recursive layer
A structure from which the lower layer's organization/limits/generator are recursively manipulable.

A replay branch may be a recursive origin without being a higher layer.

## 12. Capability–knowledge separation

The Minecraft experiment follows:

> **Capability sufficiently complete; prior knowledge and strategy minimal.**

Ordinary low-level player affordances should be available where technically possible:

- movement, turning, looking, jumping, sprinting, sneaking;
- digging/breaking and placement;
- held-item use;
- hotbar and inventory manipulation;
- block/entity interaction and attack;
- container manipulation;
- low-level crafting-interface manipulation.

Capability is not knowledge.

## 13. No hidden semantic skill library

Avoid A-facing solved functions such as:

```text
mine_wood()
find_food()
craft_pickaxe()
build_shelter()
escape_enemy()
equip_best_tool()
pathfind_to_goal()
```

Human-readable debug labels may exist outside the formal A-facing representation.

## 14. Missing body ability is an experimental limitation

The experiment must not report:

```text
A failed to learn X
```

when:

```text
A had no physical action channel capable of X
```

## 15. Minecraft capability versus host capability

```text
A <-> Minecraft body/world

host OS/files/credentials/network/hardware
remain behind an independent safety boundary
```

Provide sufficient in-world bodily possibility while minimizing unnecessary host-facing capability.

## 16. Policy provenance

Behavior-affecting parameters should expose enough provenance to answer:

- where did this parameter originate?
- was it fixed externally?
- was it created by mechanism?
- was it changed through `A`'s causal history?
- what observations/limits/reconstructions caused the change?

## 17. Layer notation boundary

Use:

```text
L_n = recursive layer
D_n = dimensional-hypothesis structure
```

A detected `L0 -> L1` transition is not evidence of physical `D0 -> D1` dimensional ascent.

## 18. Long-horizon observation

No arbitrary transition count is a theoretical validation criterion.

Record the actual causal structure being claimed:

```text
current state / limit
-> recursive processing
-> reconstruction
-> changed later generator
-> new consequence
```

and, for upward recursion:

```text
L0 organization becomes recursive object
-> L1 forms
-> L1 affects later L0 organization
```

## 19. Compact rule set

```text
one hard subject condition:
    Continuity(A) != 0

initial topology:
    one A + one environment/world + L0 only

environment limits:
    finite and real; do not prescribe adaptation

fixed mechanisms:
    expose possibility, including optional future carrier allocation

fixed policy:
    explicitly labeled and excluded from emergence claims

higher layer:
    not inferred from branch/world/role creation alone

body capability:
    sufficiently complete low-level affordances

prior knowledge:
    minimal

host capability:
    least privilege and independently constrained
```

> **Do not confuse environmental limitation with hidden goal, mechanism with strategy, carrier creation with layer ascent, recursive origin with subject identity, body capability with knowledge, or session restart with individual replacement.**

