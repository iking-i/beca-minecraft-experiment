# BECA-V0 正式 L0：V0-A / V0-B 基线

本轮基线版本 `formal_l0_v0_ab_2`。理论仍为 Perfect Recursion / BER v0.8；理论来源提交见 THEORY_REFERENCE.json。本轮只修正实验边界和 provenance，不修改理论、游戏能力、递归组织算法或已有生命周期历史。

当前是外部初始化的 single-process L0 baseline：k_actual=1，process capacity=N。不是 A 自主选择不分化。当前没有内生 create_process 能力，不进入 V0-C，不实现 architecture-limit recognition 或 L1。

## 1. 容量锁

首个正式 Session 在一个事务中追加以下内容到 `states.snapshot.internal_state.l0_state`，并追加 FORMAL_CAPS_LOCKED 事件：

- locked_caps：processes、units、relations、history、evidence_window、condition_channels、outcomes_per_relation。
- locked_resource_caps：正常 Supervisor 启动的 max_core_ram_mb、max_bridge_ram_mb、max_total_cpu_percent、max_lifetime_storage_mb，以及 body_observation_caps 中 blockRadius、entityRadius、maxBlocks、maxEntities。
- formal_condition_id：外部条件标记 C-<uuid>，不是新个体身份。
- baseline_version：formal_l0_v0_ab_2。

第一次观察之前就封存，因此停止在等待 spawn 阶段也不能通过重启更换容量。七项逻辑默认值依次为 8 / 64 / 96 / 6 / 4 / 16 / 64；四项采样默认值 4 / 16 / 64 / 64，缺字段按现有 Mineflayer 配置默认值规范化。独立、没有外部资源监测器的数值夹具使用明确的空 locked_resource_caps，不能把它说成 OS 资源约束验证。

启动先读 latest snapshot 比较，成功才申请写入租约；取得租约后再读一次，开启 Session 的事务中再次检查。Supervisor 在自己的审计数据库创建前也检查；Core 核对 Supervisor 提供的采样上限与实际配置一致。每次正式推进检查锁；SQLite BEFORE INSERT 触发器禁止后续状态改变或移除已保存的四个边界字段。

配置不同会明确报错并拒绝；不追加 Session、中断恢复、A 状态或事件。已 checkpoint 的数据库使用 immutable 只读检查，连 WAL/SHM 临时文件也不新建；有未 checkpoint WAL 时使用普通只读 SQLite，必须读取 WAL 中最新锁，不能忽略它。活跃 WAL 的 SQLite 读者可能使用 SHM 读锁协调，不改主数据库、WAL 中的状态或事件。

同条件重启保持 individual_id、全局版本、关系、过程 lineage 和 provenance；Session 标签、端口改变不能绕过锁。CPU/RAM/磁盘仍为外部采样监控阈值，逻辑槽上限严格执行；这不构成 OS 硬配额或新沙箱。观测间隔、端口、连接地址和人工运行时长不是本轮新增的容量字段，不以它们自动更改锁。

没有 A 的容量修改、申请扩容或解锁接口。不同条件须由实验者明确安排；当前不提供同一主线解锁条件的运行 API。旧正式历史没有新锁时明确拒绝自动升级，不从旧 physical_caps 推断或回填新基线，不修改或删除历史，也不自动创建替代 A。恢复旧条件或另设条件是实验者的显式安排，本轮不改主线选择。快照分支继承来源容量锁，且仍是独立身份，不是原 A 主线或 L1。

## 2. 后果的两个视图

外部 CURRENT_LIMIT_ENCOUNTER 事件只含包装字段：limit_id、a_facing_payload、auditor_metadata。

A-facing payload 精确十个字段：

```text
limit_id
resource_port_id        # 稳定数字端口，映射不由语义标签计算
operation_id           # 稳定数字操作地址
used
capacity
requested
operation_performed    # false
object_refs            # 编码单元、帧、关系或通道引用；无架构解释
source_state_version
frame_id
```

外部 auditor_metadata 精确七个字段：

```text
semantic_code
resource_name
operation_name
organization_ref
representation_name
classification
source                 # ENVIRONMENT_CONSTRAINT
```

语义代码、资源名称、L0.*、bounded_keyed_records_v1 只在审计包装中。pending_consequences、ObservationFrame.internal_observations、experience.limit_consequences 和 partial 的实际输入只复制 raw payload。验证器拒绝额外字段；不存在通过提醒调用者忽略几个字段来维持边界的路径。相同 limit_id 关联完整外部记录与实际输入；审计检查二者逐字段一致，并支持跨 Session 的来源查找。

隔离反事实测试保持代码、历史和输入相同，分别保留、删除、重命名 auditor_metadata；实际下一状态、帧及除外部标签事件以外的全部递归日志完全相同。真实写入失败、数量和 opaque refs 仍保留，不以隐藏语义为由删除后果。

## 3. 动作归属

`decision_authorship(selection)` 读取 source/category、实际 sampling/selection/scoring 策略引用和 parameter_binding 来源。data_source 是经历数据依赖，不能替代决策作者：

| 选择/参数来源 | initiator | 整体来源 |
| --- | --- | --- |
| TEST_ONLY | capability_test | TEST_ONLY |
| EXTERNAL_FIXED_POLICY / INITIAL_EXTERNAL_POLICY | external_fixed_policy | EXTERNAL_FIXED_POLICY |
| 内部选择 + 外部参数绑定 | mixed_policy | MIXED_POLICY |
| 内部选择、没有外部决定参数 | internal_structure | INTERNAL_VARIABLE_STRUCTURE |
| 未能追溯来源 | unattributed | UNATTRIBUTED |

现有正式采样及参数绑定均为外部作者。请求、执行、失败事件沿用同一来源；provenance.decision_authorship 单独记录选择、参数和整体来源。EXTERNAL_POLICY_EFFECT 只针对实际外部或混合来源。experiment_audit / policy_audit 都核对来源与 initiator，外部行为不得被统计为内部策略形成。未来的内部标签仍需要真实生产与评估 provenance；派生函数本身不证明学习发生。

## 3. 正式路径审计：固定策略、机制与可变结构

下表来自执行函数，非 README 名称推断。旧策略的实现保留，生产调用已经隔离到 StructuralEngine，仅显式 legacy_policy_debug 可运行。

| 规则或内容 | 实际位置 | 分类 | 正式路径状态 |
| --- | --- | --- | --- |
| 新结果增加数量（floor3、increment1） | integration.integrate；generation.quantity | EXTERNAL_FIXED_POLICY | 禁用，正式路径不调用 integrate |
| 稳定阈值3→数量1及停止 | integration.integrate；generation.stability、recursion.retirement | EXTERNAL_FIXED_POLICY | 禁用 |
| 分辨率固定减半、最小1e-5 | integration.integrate；generation.resolution | EXTERNAL_FIXED_POLICY | 禁用 |
| 压力≥0.8→预算减半 | recursion.generate_processes；recursion.allocation | EXTERNAL_FIXED_POLICY | 禁用；压力只保留为外部测量 |
| 过程槽满→终止最旧信息过程 | recursion.generate_processes | EXTERNAL_FIXED_POLICY | 禁用；槽满拒绝创建，不终止已有过程 |
| 单元/关系满→淘汰最旧；结果满→整关系归档 | structure.StructuralEngine.advance、integration.integrate | EXTERNAL_FIXED_POLICY | 禁用；拒绝新记录，原记录保留 |
| 固定滑动窗口、删除最早条件桶/尝试次数 | structure.advance、RecursiveProcess.publish_partial_result、actions.select_action | EXTERNAL_FIXED_POLICY | 禁用；正式保留记忆不滚动，不调用旧发布或评分器 |
| 强度+1及衰减0.98 | structure.StructuralEngine.advance；structure.strength | EXTERNAL_FIXED_POLICY | 禁用；证据次数记录不等于该强弱适应策略 |
| 少尝试/未解决加动作分数 | actions.select_action；action.scoring | EXTERNAL_FIXED_POLICY | 禁用，无 novelty/exploration bonus |
| 最大评分后LCG平分选择 | actions.select_action；action.selection | EXTERNAL_FIXED_POLICY | 禁用，正式采样不读 scores/attempts/unresolved |
| 新问题生成门控、通道候选优先、停滞淘汰、同签名合并 | recursion.generate_processes/advance_processes、integration.integrate | EXTERNAL_FIXED_POLICY | 禁用，单一过程持续处理流，不按这些规则生成或终止 |
| 初始化一个过程 | formal_l0.advance；formal.process_initialization | EXTERNAL_FIXED_POLICY | 保留，明确是实验初始化；之后不自动改变数量 |
| 从当前可用动作中固定伪随机采样 | formal_l0.select_uniform_action；formal.action_sampling | EXTERNAL_FIXED_POLICY | 保留，缺少内部动作策略时的初始采样，不冒称自主策略 |
| 数值/引用参数域采样 | action_space.bind_parameters；action.parameter_binding | EXTERNAL_FIXED_POLICY | 保留，来源单独记录，不注入攻略/配方/最佳工具答案 |
| 数值编码、固定传感器序列与读取宽度 | FrameEncoder、FormalL0Engine.advance | EXTERNAL_FIXED_MECHANISM | 保留，表示能力本身有限且布局固定；不称作内部形成 |
| 单过程反复执行、前次反馈决定实际关系读取 | FormalL0Engine.advance | EXTERNAL_FIXED_MECHANISM | 保留；执行算法作者是程序员，被读取的数据因经历变化 |
| 历史形成的关系、结果证据及后次预期 | InternalState.relations、l0_state.feedback | INTERNAL_VARIABLE_STRUCTURE | 保留且可反事实检查；当前只证明证据/数据变化，不证明组织方式变化 |
| 活动单元、关系、保留记录、证据引用、通道、过程槽上限 | FormalLimits；experiment.json | ENVIRONMENT_CONSTRAINT | 固定只读运行配置；超限真实拒绝，无适应答案 |
| RAM/CPU/生命周期数据库族阈值与人工停止 | Supervisor._collect/_enforce；limits.yaml | ENVIRONMENT_CONSTRAINT | A没有修改接口；超限外部停止，不扩大预算或删除历史 |
| SQLite事务、单写入租约、连续版本、Bridge动作执行器 | EventStore、ExperimentLease、MinecraftBridge | EXTERNAL_FIXED_MECHANISM | 保留 |

目前正式路径仍保留的初始行为策略只有：单过程初始化、动作伪随机采样、参数域采样。策略类别沿用 Registry 的 INITIAL_EXTERNAL_POLICY；审计事实使用 EXTERNAL_FIXED_POLICY。二者都表示外部作者，不能因为参数在 AState 内就改称内部形成。

generation_parameters中的旧default_quantity、pattern_quantities、condition_resolution等作为兼容/历史字段保留，值可能仍为旧初始化值；formal_l0不读取它们决定数量、分辨率或适应行为。实际k_actual从新正式过程日志读取，初始化为1，之后不因新结果改变。首次登记策略列表也可能包括已禁用的旧策略；不能把“登记了”当成“仍驱动正式实验”。

## 4. 当前极限及证据

关系槽满时拒绝新增，整合仍返回尝试引用；下轮过程请求读取该引用却读不到，构成行为上绑定的关系极限。保留窗口、证据引用和条件宽度同样可失败，失败不指定压缩、淘汰、分化、扩容或升层。两个当前/前次输入寄存器与有限保留记忆分开；输入替换不是历史淘汰。

下轮读取的关系与结果因历史变化，执行算法仍由外部提供。关系证据插入和计数不是组织方式重构。固定通道布局、固定序列前 N 项取样、固定参数域和拒绝写入机制均须继续纳入研究者的实现边界分析。

## 5. 本轮审计判据

只支持六项事实：WITHIN_LAYER_RECURSION、CURRENT_LIMIT_ENCOUNTER、BEHAVIORALLY_BINDING_LIMIT、LIMIT_FEEDBACK_REENTERED_RECURSION、INTERNAL_VARIABLE_STRUCTURE_CHANGE、EXTERNAL_POLICY_EFFECT。数据变化不意味着组织变化。

baseline_goal_observed 要求层内递归、绑定极限和后果重入，并要求容量锁、raw 分离及作者检查有效。v0_a_baseline_observed 与 v0_b_baseline_observed 分开报告。`--verify-loop` 仅按此外部基线判据停止，不向 A 传入任务或奖励。

recognition_status 永远 not_observed；formal_stage_goal_observed=false 表示包含更强识别目标的阶段尚未验证。ARCHITECTURE_HYPOTHESIS_PROPOSED 标签若在历史或测试中出现，保留并列为本轮范围外未接受的声明。无识别生成器、无 current_organization 概念生成器、无架构修改、无自动分化、无 L1。

## 6. 运行和复核

```powershell
.\.venv\Scripts\python.exe main.py --port <游戏当前端口>
.\.venv\Scripts\python.exe -m unittest discover -q
npm --prefix minecraft test
.\.venv\Scripts\python.exe -m debug.validate_formal_l0
.\.venv\Scripts\python.exe -m individual.experiment_audit --db <夹具数据库> --sample
.\.venv\Scripts\python.exe -m individual.policy_audit --db <夹具数据库>
```

本轮只运行短时 TEST_ONLY 数值夹具与本机身体测试，不运行长时间 Minecraft，不把夹具当成真实游戏或当前主线。当前执行结果、准确文件清单和 13 项报告见 [BASELINE_CORRECTION_REPORT.md](BASELINE_CORRECTION_REPORT.md)；安全的小型数值摘要见 tests/fixtures/formal-baseline-summary.json。既有历史文档的旧数量和样例只作历史解释，不作为本轮事实。
