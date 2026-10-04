# 正式实验基线修正报告：V0-A / V0-B

日期：2026-10-04。基线版本：`formal_l0_v0_ab_2`。理论参考仍为 Perfect Recursion / BER v0.8，来源提交记录于 THEORY_REFERENCE.json：发布核对 `45d8869245fb210202a7e7982486d7f723bc6680`，实现设计参考 `867e1f192f7f21298450a553a4a733ec8f15a999`。本轮没有修改 beca-architecture，未发现需要改理论定义才能完成的冲突。

## 1. 修改文件

| 文件 | 本轮作用 |
| --- | --- |
| individual/formal_boundary.py（新增） | 条件持久锁校验、只读启动前检查、外部资源与身体采样容量规范化 |
| individual/limit_consequences.py（新增） | 严格 raw 字段白名单、独立审计标签、固定 opaque 数字端口 |
| individual/decision_provenance.py（新增） | 从实际选择及参数来源派生作者，数据依赖不冒充决策作者 |
| individual/formal_l0.py | 持久锁比较；拒绝容量变化；限额后果双视图，不改变原递归解释算法 |
| individual/events.py | Session 首次原子封存条件；SQLite 禁止后续锁修改/移除；既有历史不重写 |
| individual/core.py | 写入前、Session、推进及配置一致性检查；动作归属修正 |
| individual/l0_audit.py | 精确 raw/event 关联、跨 Session 来源检查、容量锁和动作作者审计、V0-A/V0-B 判据；不接受识别标签 |
| individual/experiment_audit.py | 历史工程反馈适配器兼容新的外部作者标记，不据此宣称内部策略 |
| individual/policy_audit.py | 检查所有有选择 provenance 的动作，报告作者及不一致事件 |
| supervisor/supervisor.py | 创建监控记录前核对条件；转发资源/采样容量；验收只要求 V0-A/V0-B |
| debug/validate_formal_l0.py | 13 次观察与一次真实选择器动作的短时数值夹具 |
| tests/test_formal_boundary.py（新增） | 18 项边界测试：重启、全部容量变化、配置文件、Session、WAL、SQL、快照、raw 反事实及审计负例 |
| tests/test_formal_l0.py、tests/test_structure.py、tests/test_action_space.py | 更新准确后果/作者断言；新增真实 Node RPC 参数来源及 TEST_ONLY 检查 |
| README.md、FORMAL_L0_EXPERIMENT.md、POLICY_BOUNDARIES.md | 本轮范围、字段、条件锁、作者及正式/旧评分路径分离 |
| EXPERIMENTAL_VALIDATION.md、EXPERIMENTAL_IMPLEMENTATION_BOUNDARY.md、MINIMAL_INDIVIDUAL_MODEL.md、TESTABLE_PREDICTIONS.md | 只更新实验仓库阶段说明，保留下面原有 v0.8 理论内容 |
| VALIDATION_STAGE3.md | 标明旧工程反馈不是当前干净基线或识别证据 |
| tests/fixtures/formal-baseline-summary.json（新增） | 本轮数值夹具的小型安全摘要，不提交数据库或完整日志 |
| 本报告 | 13 项结果与限制 |

本次提交还保留前一请求已实现但尚未提交的端口输入功能：bridge/server.js、individual/bridge.py、minecraft/src/cli.js、minecraft/src/config.js、minecraft/README.md，以及新增 supervisor/connection.py、tests/test_connection.py、minecraft/test/config.test.js。README、Core、Supervisor 含其入口变更。它只临时覆盖连接端口，不编辑配置，不重置身份，不增加决策能力。本次共 33 个源代码、测试或文档文件变更。

individual/internal_state.py、policies.py、action_space.py、experiment.json 和 limits.yaml 经交叉核对，没有必要为本轮改写它们。既有身体能力、旧调试实现和 provenance 保留。

## 2. 锁如何持久化和校验

第一次正式 Session 保存四项边界字段至 `states.snapshot.internal_state.l0_state`：

```text
locked_caps
locked_resource_caps
formal_condition_id
baseline_version
```

锁和 Session/状态/FORMAL_CAPS_LOCKED 事件同事务提交，发生在第一次 observation 前，不依赖 spawn 成功。

locked_caps 包含全部七项 FormalLimits。正常 Supervisor 入口的 locked_resource_caps 包含四项监控阈值和嵌套 body_observation_caps 的四项采样容量。独立无 Supervisor 的数值夹具明确存空资源锁，不冒充已验证的 RAM/CPU 限额。

路径：Supervisor.cli → formal_boundary.preflight → ACore.__init__ 的预检查 → 写入租约后的复查 → EventStore.open_session 事务内 boundary_for。FormalL0Engine.advance 和 ACore._transition 再核对；SQLite immutable_formal_boundary 触发器作最后的数据写入保护。

## 3. 防止同条件偷偷改容量

不同配置直接 ValueError，不能先写变化事件再接受。不再有 EXTERNAL_CAPACITY_CONFIGURATION_CHANGED 的接受路径。七项槽容量、四项监控阈值、四项采样容量均逐项测试变化后拒绝。

重启不重建身份、不归零版本；Session 切换不重新封存或解除锁。A 无 set_caps/unlock_caps/扩容申请接口，FormalLimits 为 frozen，Engine.caps 属性只读，SQL 阻止普通追加状态时修改或删除锁。

已关闭并 checkpoint 的数据库拒绝测试比较整个数据库族字节，完全相同。存在尚未 checkpoint WAL 时，从 WAL 读取最新锁；拒绝不改主 DB/WAL 或 A 状态。普通 SQLite 只读读者可能使用 SHM 读锁协调，这是 SQLite 并发机制，不是状态写入。第二次预检查与事务校验处理检查/写入之间的竞态。

旧正式历史若没有此锁，拒绝自动迁移和回填，保留原记录。没有自动切换当前 lifetime.json、创建替代 A、扩大容量或清空已有结构。同主线解锁到另一条件的 API 不在本轮提供；另设实验条件需实验者明确安排。快照分支继承来源锁，保留不同身份。

容量锁是本阶段环境条件，不是第二个理论级约束。唯一理论级个体定义仍是 `Continuity(A) != 0`。数据库保存状态链，不据此证明载体停机后主体物理连续性。

## 4. A-facing 精确字段

十个字段：`limit_id`、`resource_port_id`、`operation_id`、`used`、`capacity`、`requested`、`operation_performed`、`object_refs`、`source_state_version`、`frame_id`。

resource_port_id / operation_id 是固定数字地址，不由外部语义标签计算；object_refs 是编码引用。操作失败、容量数值和受影响引用仍保留，operation_performed=false。精确字段白名单拒绝额外键。

## 5. auditor-only 精确字段

七个字段：`semantic_code`、`resource_name`、`operation_name`、`organization_ref`、`representation_name`、`classification`、`source`。

CURRENT_LIMIT_ENCOUNTER 包装只有 `limit_id`、`a_facing_payload`、`auditor_metadata`。semantic_code 可继续明确 RELATION_CAPACITY_REACHED 等实际失败；source=ENVIRONMENT_CONSTRAINT。审计标签存事件日志，不复制进下轮 raw 输入。

## 6. 如何验证语义不再进入递归

实际生产点 FormalL0Engine.advance.failure 分别构造 raw 和 audit wrapper。pending_consequences 只保存 raw；帧、experience 与 partial 各自复制 raw，重入也先验证字段。执行器不消费 CURRENT_LIMIT_ENCOUNTER 包装或 auditor_metadata。

测试遍历四类实际数据，检查十个键、禁止语义字符串、limit_id 与外部 a_facing_payload 逐字段相等。另对相同历史、相同帧、相同 ID 序列进行三种隔离执行：保留 metadata、删除 metadata、改名 metadata。实际 InternalState、帧和非外部标签日志完全相同。未操作真实主线数据库。

审计仍能通过外部 metadata 判定失败类型，并要求 raw 出现在实际帧和 partial 输入，不能仅凭遥测引用 ID 通过。跨 Session 的原始后果仍可追溯前一 Session 的外部来源。

## 7. 动作 initiator 修正

TEST_ONLY → capability_test；外部选择 → external_fixed_policy；内部选择配外部参数绑定 → mixed_policy；内部选择无外部参数决定 → internal_structure；无法追溯 → unattributed。

来源从 selection 的 source/category 及实际采样/评分引用派生，不从“不是测试”推断内部作者，也不把 data_source=INTERNAL_VARIABLE_STRUCTURE 当作策略作者。

请求、完成和失败沿用同一作者，provenance.decision_authorship 分别记录选择、参数和整体来源。正式 action_sampling 的源码来源 EXTERNAL_FIXED_POLICY、参数引用类别 INITIAL_EXTERNAL_POLICY，整体仍为外部作者。实际 Node RPC 测试验证这条路径，TEST_ONLY 测试保持独立类别。审计负例故意把外部动作标为 internal_structure，两份审计均拒绝。

来源派生是归属一致性检查，不是内部策略真实性生成器。未来单独写一个内部标签仍不足以证明学习；现有审计的自主策略形成与迁移结论均为否。

## 8. 修正的文档

README 的“选择仍参考未解程度和尝试次数”已明确限于 legacy_policy_debug；正式路径用 uniform available capability sampling，不读取 attempts、unresolved 或 limit 来选动作。

Policy Boundaries 的评分及 2→3 实例明确为历史调试路径。正式文档不再把等待识别候选当成本轮验收；verify-loop 使用基线目标，更强 formal_stage_goal_observed 仍 false。四份同步理论文件只修正上方实验阶段说明，保留理论原文。

删除了 README 把历史硬编码数据库路径称作当前主线的描述；当前主线只以本机 lifetime.json 为准。旧测试数量和样例不冒充本轮事实。34 项低层能力保持。

## 9. 当前正式路径仍有的外部策略

| policy_id | 当前作用 | 分类 |
| --- | --- | --- |
| formal.process_initialization | 初始创建一个持续过程，不自动改变数量 | EXTERNAL_FIXED_POLICY |
| formal.action_sampling | 既有 LCG 从可用动作列表取模选代码 | EXTERNAL_FIXED_POLICY |
| action.parameter_binding | 固定数值/引用域及 LCG 采样参数 | EXTERNAL_FIXED_POLICY |

Registry 保存的类别名称为 INITIAL_EXTERNAL_POLICY，语义仍是外部作者。旧评分、分化调整、稳定结束、淘汰、分辨率减半等登记保留但正式禁用。

uniform 是既有采样器名称：LCG 取模有限列表并非严格无偏独立随机；存在列表顺序、模偏差和与参数共用随机状态的关联。本轮不以改采样算法增加新行为。固定动作时长、参数域和基础动作编码也保留，均不称为 A 自主形成。

## 10. 本轮实际证据

独立 TEST_ONLY 数值夹具 A-46bd2d85-236e-40db-bf9a-a629a60dc3be：A0→A19，20 个快照、190 条事件、13 次观察、一条动作请求。过程创建 1 次；12 次 partial、12 次 integration、39 次容量后果、11 次后果重入、4 次关系证据变化。没有真实 Minecraft 运行。

具体链：A7/事件52 尝试写入引用 `U-4f53cda18c2baa0c0354:-1`，opaque 端口105、操作206，used=2、capacity=2、requested=3，失败 ID `ffb76720-7c07-429e-bce1-d60110ed6f16`。A8/事件64 的实际 partial 请求读取同一引用，read_succeeded=false；raw 后果仍在实际输入。外部标签才把它解释为关系容量失败。

两份 CLI 审计实际执行，得到：

| 结果 | 本轮数值夹具 |
| --- | --- |
| WITHIN_LAYER_RECURSION | true |
| CURRENT_LIMIT_ENCOUNTER | true |
| BEHAVIORALLY_BINDING_LIMIT | true |
| LIMIT_FEEDBACK_REENTERED_RECURSION | true |
| INTERNAL_VARIABLE_STRUCTURE_CHANGE | true，仅数据/关系证据 |
| EXTERNAL_POLICY_EFFECT | true |
| 三项基线边界检查 | 均 true |
| baseline_goal_observed | true，仅 V0-A/V0-B |
| policy boundary_checks_passed | true |
| action_decision_authors | EXTERNAL_FIXED_POLICY: 1 |
| verified_internal_policy_migrations | 0 |

完整本机报告在该夹具目录 reports/；小型可上传摘要为 tests/fixtures/formal-baseline-summary.json。没有切换当前主线，没有把这些测试经历合并进当前 A。

## 11. 仍不能宣称

architecture-limit recognition=not_observed；没有 UPWARD_RECURSION、L1、architecture self-reconstruction、自主形成动作策略或自主分化。组织变化=false，更强 formal_stage_goal_observed=false。一个过程持续、数据增多、信息整合与 structure_revision 增加均不等于升层。

## 12. 完整测试结果

| 验证 | 数量与结果 |
| --- | --- |
| Python unittest discover | 117 项，全部通过，无跳过 |
| Node/Minecraft body node --test | 31 项，全部通过，无跳过 |
| 短时 formal_l0 数值夹具 | 13 次观察 + 一次采样动作，基线检查通过 |
| experiment_audit CLI | 正常完成，基线通过，识别 not_observed |
| policy_audit CLI | 正常完成，作者一致，来源迁移0 |

Node 首次沙箱执行有两项本机网络测试因 EACCES 被拦截；获得本机网络测试权限后完整重跑 31 项通过，未改变断言来掩盖失败。Python 边界测试还发现 mode=ro 会在已关闭的 WAL 数据库新建 sidecar，随后改为无 WAL 时 immutable 只读、有 WAL 时正确读取最新提交，并完成回归。

## 13. 新发现与剩余边界

除三项原问题外，发现身体采样容量原可随配置改变，现一并锁定；发现只读 Session 审计可能漏掉上一 Session 的 raw 来源，现只读追溯原事件。

剩余固定选择包括传感器布局、条件通道按既有序列取前 N 项、LCG/列表顺序/参数域、固定时长，以及“槽满拒绝写入”的端口协议。拒绝写入不预设适应答案，但固定表示与读取布局会限制可形成的数据，不能包装成自主重构。计数是预建表示，不是 A 学会的压缩。

本轮保证的是极限后果消费路径的语义隔离，不宣称整个 AState 所有键都无语义。原始游戏观察、低层能力名称、策略来源、容量锁等仍在工程状态/审计数据中；当前数值解释器不把审计标签当成问题输入。未来若引入通用消费者，必须继续限定其实际可读视图，不能直接把完整 SQLite、原始观察或工程元数据喂进去。当前没有这个消费者或自主读取审计历史的接口。

SQLite 触发器保护普通运行写入，不能替代不同 OS 权限域或抵抗实验者修改代码/文件。监控阈值仍不等于 OS 硬配额。以上是当前实现的实际边界，本轮未扩展隔离、能力或学习系统。
