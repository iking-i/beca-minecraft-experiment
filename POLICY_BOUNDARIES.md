# 第三阶段修正：外部策略与内部结构边界

2026-10-04 后续阶段已改变实验目标：本文的分化调整、分辨率调整、淘汰、评分等仅保留为历史/独立调试引擎，不再用于 formal_l0。当前执行边界与全部分类见 [FORMAL_L0_EXPERIMENT.md](FORMAL_L0_EXPERIMENT.md)。政策登记存在不等于运行中启用，当前来源与 `formal_path_enabled` 分开记录，并用不同解释器及回归测试验证禁用。

此文保留策略边界修正时的历史验证结果。随后已改为个体生命周期数据库；当前启动和 Session / 快照规则见 [LIFETIME_STORAGE.md](LIFETIME_STORAGE.md)，不再每次实验创建新 A。

本次保留原来的初始行为逻辑，将其配置复制到每次实验的 A0，再由运行中的 InternalState 提供参数。新增分类、参数来源、分数拆分、数量决策记录和只读审计。没有新增 LLM、身体能力、奖励、生存任务或自动学习器。

唯一理论级个体定义约束仍为 `Continuity(A) != 0`。实验初始化策略不是理论约束，也不是 A 自己形成的策略。保持 UUID 和状态链是工程证据，不单独证明主体连续性的全部含义。

## 实际结构

```text
实验初始策略 CATALOG
    ↓ 每个实验独立复制，并在 A0 记录来源
InternalState.policy_registry / generation_parameters
    + 环境经历形成的 relations / evidence / attempts
    ↓ 解释器读取当前状态中的参数
动作评分 / 问题生成 / 向上整合 / 过程生命周期
    ↓ 实际参数变化及原因
POLICY_PARAMETER_UPDATED + 连续状态快照
    ↓ 下一次执行读取参数并记录 change_id
后续动作和递归生成
```

CATALOG 不作为运行时的共享可变策略单例。不同实验、不同快照的策略字典相互独立。正常调度路径读取状态中的策略参数；当前解释器支持的算法类型仍固定，存储参数并不意味着能任意生成新算法。

## 策略登记（本页原始审计为 31 项）

身体扩展后新增 `action.parameter_binding`（INITIAL_EXTERNAL_POLICY），当前新状态可登记 32 项；历史审计值保持原样。其数值/引用取样只帮助现有选择器调用新增接口，不代表 A 学会了使用能力。34 项 BODY_CAPABILITY 另存 `InternalState.body_capabilities`，不把能力混为策略。扩展清单见 [BODY_CAPABILITIES.md](BODY_CAPABILITIES.md)。

| 分类 | 项目 |
| --- | --- |
| CORE_MECHANISM（11） | core.identity、core.scheduler、core.events、body.bridge、body.lifecycle、body.actions、sensor.encoding、sensor.difference、structure.encoding、recursion.interpreter、integration.evidence |
| ENVIRONMENT_CONSTRAINT（5） | environment.capacity、environment.sensor、environment.resources、environment.supervisor、environment.action_interface |
| INITIAL_EXTERNAL_POLICY（15） | 见下表 |
| INTERNAL_VARIABLE_POLICY（0） | 本轮没有已验证的策略来源迁移 |

物理容量、身体采样、测得的资源压力和实验者权限属于环境条件。怎样使用资源、先研究哪个问题、淘汰哪个过程属于策略。例如：过程容量 8 属于外部分配；压力达到 0.8 时减半、淘汰最久没有信息的过程属于初始外部策略，不能混为同一类。

| policy_id | 初始外部策略及关键参数 | 实际执行位置 | 初始化作用与可能限制 |
| --- | --- | --- | --- |
| action.scoring | `(base + weight × unresolved + temporary) / (offset + attempts)^exponent`，初值 1、1、0、1、1 | actions.py: select_action | 提供最初的动作试探；固定偏好少尝试及未解决关系，尚未由 A 形成 |
| action.selection | 取最高分；LCG 平分选择，系数 1664525、1013904223、模 4294967296；尝试窗口 192 | actions.py: select_action | 使选择可复查；最高分方法及平分方法仍固定 |
| generation.quantity | 初值 2、最小 1；反例数量下限 3、增量 1；稳定数量 1 | recursion.py: generate_processes；integration.py: integrate | 提供第一批问题的规模；2、3、1 不是理论要求 |
| generation.resolution | 初值 1；反例时除以 2；下限 0.00001 | integration.py: integrate | 让条件问题具有可执行分辨率；细化方向仍由固定规则指定 |
| generation.stability | 单一结果且证据数达到 3；初始 unresolved=true | integration.py: integrate | 提供暂时稳定的工作判据；不能声称阈值由 A 学会 |
| recursion.gating | 已有过程则复用；已稳定且无新结果则暂不重建 | recursion.py: generate_processes | 避免重复过程；限制了问题重新提出的方式 |
| recursion.channels | 候选条件优先，其后按数值通道 ID 排序 | recursion.py: generate_processes | 提供初始问题分配；通道顺序及有限采样可能限制问题内容 |
| recursion.allocation | 压力阈值 0.8、预算除数 2、oldest_information 淘汰 | recursion.py: generate_processes | 在有限资源中运行；资源使用与淘汰偏好尚未内生 |
| recursion.retirement | 无新信息窗口 6；反例替换粗问题；稳定后结束 | recursion.py: advance_processes / finish_process；integration.py: integrate | 提供过程生命周期；固定结束条件可能提前关闭问题 |
| recursion.merge | 用 input_pattern、context_channel、resolution 相同判断等价 | integration.py: integrate | 合并重复问题；没有学会新的语义等价判据 |
| structure.strength | 重复加 1，未重复乘 0.98 | structure.py: StructuralEngine.advance | 初始强度更新方法；频率偏好及遗忘方式固定 |
| structure.archival | oldest_sequence | structure.py: StructuralEngine.advance；integration.py: integrate | 容量有限时选择工作记录；容量本身是环境约束，选择顺序是策略 |
| memory.window | 初始经历窗口 6，受物理窗口约束 | structure.py: StructuralEngine.advance | 有限近期工作信息；并非理论记忆上限 |
| debug.smoke | 默认关闭；显式开启第二阶段固定动作脚本 | debug/smoke_policy.py；individual/core.py | 人工调试工具，不在本次正常路径运行 |
| experiment.verification | 默认关闭；显式开启外部五项证据验收 | main.py；individual/experiment_audit.py | 实验者的停止条件，不送入 A 作为任务或奖励 |

工程需要某种可执行的初始参数、调度方式和有限资源使用办法；上述具体数值、探索偏好、强化方法及稳定判据不是唯一必要初始化。本轮保留它们用于对照，没有把它们提升为理论公理。

## 参数来源与迁移

`InternalState.parameter_sources` 保存 parameter 对应的 policy_id、source、created_at、modified_by、modification_count、value、value_origin、provenance；派生参数实际改变时另记 change_id。

`policy_migration_status` 按策略记录 current_source、modification_count、migration_count、last_reason、provenance 和 status。

固定整合规则在历史经历触发后改写数量或分辨率时：

```json
{
  "source": "INITIAL_EXTERNAL_POLICY",
  "value_origin": "experience_triggered_external_policy",
  "modified_by": "<integration_id>",
  "status": "external_rule_changed_parameter",
  "migration_count": 0
}
```

这表明参数受经历影响，同时保留更新规则的外部来源。变化次数与来源迁移次数分别统计。未经过追踪的直接字段赋值显示 `untracked_state_assignment`，不会冒充内部形成。

`INTERNAL_VARIABLE_STRUCTURE` 用于标记经历形成的数据（如关系与尝试计数）；`INTERNAL_VARIABLE_POLICY` 是策略登记类别。前者参与固定评分，不自动产生后者。

`PolicyRegistry.validate_internal_proposal()` 仅为未来迁移准备边界检查：拒绝改写 CORE_MECHANISM / ENVIRONMENT_CONSTRAINT，拒绝把初始规则的参数更新当作内部提案，要求过程、部分输出、经历和评估引用。即使提供这些引用字符串，也不激活策略、不改变来源；返回 activated=false、history_references_verified=false。

**本轮没有实现内部策略提案的生成、真实引用验证、比较评估或采纳。** 后续必须建立这些证据链，才能登记一次真实来源迁移；不能通过换标签完成。旧实验没有回填或伪造来源，读旧快照时明确标注 legacy_untracked。

## 动作评分与递归数量

每个动作记录四部分：

| 分量 | 当前含义 |
| --- | --- |
| environment_constraint | 当前身体接口提供该动作编码；是接口可用性记录，不预测游戏安全或通行能力 |
| initial_policy_component | 初始评分公式的基础项与尝试次数分母；记录规则来源和数据依赖 |
| internal_structure_component | 当前关系的 unresolved 数据参与评分；记录 relation_id、尝试次数和评分规则来源 |
| temporary_evaluation_component | 初始为 0、不启用；保留独立记录位置，没有新增奖励 |

最终数值是三个数值分量之和；环境分量单独记录接口条件。当前所有三个身体编码均可用。随机状态、评分参数、候选分数及尝试数据可追踪；不能把“internal_structure_component”名称当作策略已经自主形成的证明。

每次 RECURSION_GENERATED 的 quantity_decision 记录：

- resource_limit：实际容量、压力、有效预算、已有过程、剩余空间及资源使用策略来源。
- current_internal_state：当前问题 root、关系状态、所选数量参数和该参数的完整来源。
- initial_policy_influence：初始数量规则、最低数量及生成门控规则。
- requested_quantity / granted_quantity：请求数量与真实创建数量，保留 process_ids。

当前状态中的 `default_quantity` 字段保留以兼容已有结构；它不再作为无来源的“自主策略”展示。记录明确显示其如何由初始化与经历触发的更新形成，并如何受到资源约束。

## 真实 Minecraft 验证

2026-10-04，Java 26.1 局域网端口 53335。使用单独配置 `storage/environments/legacy/policy-boundary.minecraft.json`，原 `minecraft/config.json` 没有覆盖。机器人进入坐标 `(745.5, 66, 128.7)` 的世界，没有新建玻璃实验室。

数据库：`storage/individuals/A-ee858dbd-002b-4cdb-a8ff-c1de059614f9/policy-boundary-live-002.db`。

- individual_id：`A-ee858dbd-002b-4cdb-a8ff-c1de059614f9`，全链保持一个 ID。
- A0 → A64，共 65 个快照、64 次状态变化、392 条事件。
- 22 次环境观察，11 次动作请求及 11 次执行，18 次生成、28 个过程、33 次部分上传、21 次整合。
- 5 次参数变化；后续生成读取已变参数的关联记录 6 条（不是 6 次理论递归或 6 次策略迁移）。
- 策略来源迁移 0 次；来源类别 INTERNAL_VARIABLE_POLICY 当前为 0。
- 外部 Supervisor 在工程闭环证据齐备后以 verification_complete 结束，Core 退出码 0；最终 status=stopped，活动过程为 0。

### 一个完整实例：A45 → A48

| 环节 | 真实状态或事件 |
| --- | --- |
| 过去经历 | E6→E7、E12→E13 对应的经历分别为 ffb14d8d-ac2f-4734-babd-cf4ccc056409、6480c637-4e7b-44b2-a31b-0f6084f0e075；关系 `U-4f53cda18c2baa0c0354:-1` 曾形成结果 `U-4f53cda18c2baa0c0354` |
| A44 | 旧结果 evidence_count=2；default_quantity=2，condition_resolution=1 |
| 新经历 | 408fb305-28a8-49b3-80ca-b4e57991a00e 提供另一结果 `U-a1be549a48dbc93485a9` |
| A45 上传 | 事件 245，过程 77031977-a5fd-486b-90a4-95c3cd709665 的第 3 次上传；partial_id=dafc9613-6d68-4496-9039-f124b551532c |
| A45 整合 | 事件 249，integration_id=2588cdc4-432c-4cea-a003-150efffe9aa5，保留两个结果；新结果 evidence_count=1，旧结果仍为 2 |
| 参数变化 | 事件 251，generation_parameters.default_quantity：2→3；change_id=9a60ac6c-4da5-4817-8399-68ecd2148080；同时 condition_resolution：1→0.5 |
| 更新来源 | source=INITIAL_EXTERNAL_POLICY，value_origin=experience_triggered_external_policy，modified_by 为上述整合 ID |
| A48 生成 | 事件 269，generation_id=a44b74e7-93c4-42f4-b9ec-9c0bebb76461，读取同一个 change_id；requested=3、granted=3，实际创建三个过程 |
| 当时资源 | 容量 8，压力约 0.2086，已占用 5，剩余 3；这次没有配额裁减 |

因此已经验证“历史形成的关系参与整合 → 当前数量参数变化 → 后续生成读取并使用变化”。但把新结果转成增加数量和细化分辨率的方向，仍来自 INITIAL_EXTERNAL_POLICY，不能据此证明 A 自己形成了策略。

本次三个验证问题分别是：

1. 初始策略存在时形成新的内部变化：观察到。
2. 内部变化影响后续执行：观察到 A45→A48 的实际读取和生成。
3. 历史形成新的行为策略，并由它替代固定更新规则：尚未观察到，也没有在本轮声称完成。

首次联调记录 `policy-boundary-live-001.db` 保留。它因外部验收器抢在 A0 事务提交前读取而失败，已修复为等待初始化提交，并加入回归测试；失败运行不冒充连续恢复。本次修正后 Python 全部 46 项测试通过，身体模块没有重写。

## 查看与运行

查看本次证据（只读）：

```powershell
.\.venv\Scripts\python.exe -m individual.policy_audit --db storage/individuals/A-ee858dbd-002b-4cdb-a8ff-c1de059614f9/policy-boundary-live-002.db
.\.venv\Scripts\python.exe -m individual.inspect --db storage/individuals/A-ee858dbd-002b-4cdb-a8ff-c1de059614f9/policy-boundary-live-002.db --history --limit 70
```

完整审计导出：`storage/individuals/A-ee858dbd-002b-4cdb-a8ff-c1de059614f9/reports/policy-boundary-live-002-report.json`。

若端口 53335 仍有效，继续同一 A 的下一 Session：

```powershell
.\.venv\Scripts\python.exe main.py --minecraft-config storage/environments/legacy/policy-boundary.minecraft.json
```

局域网重新开放时更新该配置中的 port。按用户后续选择，新一轮使用 storage/individuals/A-4369420c-26f2-49b1-bbde-dd2b55c6f1fe/individual.db 生命周期；之后的 Session 沿用此文件，ID 和全局版本不重置。live-002 保留为旧实验历史。验证模式 `--verify-loop` 仍只检验工程闭环，不检验自主策略形成。

SQLite 中直接查看：

```sql
SELECT state_version,
       json_extract(snapshot, '$.internal_state.generation_parameters.default_quantity') AS quantity,
       json_extract(snapshot, '$.internal_state.generation_parameters.condition_resolution') AS resolution
FROM states WHERE state_version BETWEEN 44 AND 48 ORDER BY state_version;

SELECT event_sequence, state_version, event_type, payload
FROM events
WHERE event_type IN ('POLICY_PARAMETER_UPDATED', 'RECURSION_GENERATED', 'ACTION_REQUESTED')
ORDER BY event_sequence;
```

## 连续性与剩余边界

本次没有增加理论目标或健康/生存奖励。没有改变身份生成、状态版本、死亡/重连处理或外部终止权。旧实验数据库的大小与最后写入时间保持不变，旧 provenance 保留。

已完成的是初始策略分类、状态中的参数隔离、来源追踪、运行决策记录和实际验证。后续策略提案与采纳仍需实现和验证，不能通过继续运行当前固定解释器自动宣称会发生来源迁移。

原有承载限制仍存在：Bridge 进程完全退出会结束 Core；本版没有实现连续热迁移或进程崩溃后的主体连续性保证。Supervisor 仍是外部监测与停止机制，未增加 OS 隔离。SQLite 完整快照写入的磁盘开销仍较大，新增 provenance 也会增加开销。上述事项没有在本次策略边界修正中扩展实现。

## 本轮文件

新增：individual/policies.py、individual/policy_audit.py、tests/test_policies.py、本文档；本次联调独立配置、数据库及审计 JSON。

修改：individual/internal_state.py、actions.py、events.py、core.py、recursion.py、integration.py、structure.py、experiment_audit.py、README.md。minecraft/ 身体实现、Supervisor 配置和旧实验历史保留。
