# FROI-1 Implementation and Regression Report

日期：2026-10-05。GitHub main 基线：`e87f73b7e6f04656431c3aa6335e597b86d499a5`。

开始前已读取 `00_DISCUSSION_CONSTRAINTS.md`、`RESEARCH_STATUS.md` 与完整 [FROI-1](FORMAL_RECURSIVE_ORGANIZATION_INTEGRATION_SPEC.md)。本地实现源码与该 main 的 blob 对齐；main 中更新过的研究文档用于当前解释，旧审计正文及结果不在本轮改写。Git 命令行认证不可用，因此使用现有 GitHub 连接读取、核对 main。

## 1. 本轮结论

| 项目 | 结果 | 范围 |
|---|---|---|
| implementation status | IMPLEMENTED | 四个接口及正式运行选项已接入 |
| regression status | PASSED | 208 项 Python/GSC 控制 + 42 项身体接口回归；全部通过 |
| T1 | NOT_EXECUTED | 缺真实 Minecraft 完整观察/历史及来源核对 |
| T2 | NOT_EXECUTED | 缺两个真实历史、固定真实读取 checkpoint 与相同当前整帧 |
| T3 | NOT_EXECUTED | 缺上述真实输入形成的 COMPLETE graph 与正式 detached 对照 |
| T4 | NOT_EXECUTED | 缺真实读取后再进入的下一帧 |
| T5 | NOT_EXECUTED | 缺整套正式 T1–T4 的完整性/污染控制上下文 |
| final FROI-1 classification | READY_FOR_LIVE_FROI_VALIDATION | 不能写 FROI-1 已通过 |

本地 `storage/` 没有 `.db` 生命周期数据库。本轮未连接真实 Minecraft、创建正式 A 或修改历史数据库。所有新增控制测试使用 TEST_ONLY FakeBridge；它们验证实现边界，不冒充正式 T1–T5。

## 2. 四个接口与实际执行路径

### Observation/history → GSC input

[integration/froi.py](integration/froi.py) 的 `history_from_store` 从已提交事件读取完整原始输入：WORLD_OBSERVATION、OBSERVATION_FRAME、EXPERIENCE_FORMED、partial/action 记录。它不从有界 active-memory window 取代完整历史，不删除或挑选部分 experience。

`History.material` 核对每条历史 experience 的原始帧、顺序、namespace/epoch、antecedent/outcome unit ref 和既有 temporal root。`History.origin` 沿真实 feedback.partial_id 找到引用来源；找不到或不唯一就 INVALID，不选 nearest/first。

`encode_input` 实现冻结的两种语法：历史 `Relation(root-node, record-variable)` 和实际 `Relation(read-root-node)`，以及每个历史字段实际观察值的 Bind。Variable/Value 使用 `UnitRef` 类型；所有 Node/record/read identity 按 A 与原始 namespace/epoch 隔离。每个已完成记录都进入 seeds；当前未完成 experience 不进入自身历史。无人工 Eq、答案映射或动作映射。

### Organization identity/state boundary

`produce` 对机械收集的有限 Condition 使用未改动的 `experimental/gsc0/engine.py` 和 `model.py`。COMPLETE 是发布可消费图的前提；RESOURCE_LIMIT、INVALID 不提供成功空答案或部分成功。完整 GSC 所有阶段照常执行，消费者不借用 Composite 的性质。

冻结 `OrganizationHandle` 保存版本、A 身份、历史截止线、当前整帧/引用、Condition、规范 typed graph 内容、全部直接支持、有限根见证和输入 registry。实际内容可比较，digest 仅作索引。无需沿用前轮 materialized closure。

FROI capacities 在首次进入该 profile 时随状态记录；恢复前校验相同 profile/caps，不能恢复到旧读表路径。capacity 配置是实验环境边界，不是 A 的新目标或答案。

### GSC organization → actual FormalL0 internal consumer

[ACore.accept_observation](individual/core.py) 在显式 FROI 模式中创建输入 session，调用 [FormalFROIEngine.advance](individual/formal_froi.py)。后者是 `FormalL0Engine` 的独立接入 profile，保留原观察/过程/经验/整合顺序，在真实 relation-read 步骤替换数据来源。

`consume` 只读取 handle 的 Shared witnesses 与 PortBinding：恢复本次精确读取锚点连接的全部历史字段值，保留所有支持、根与 Conflict。消费者没有 raw history 参数；也不调用 producer、旧关系表或其他 fallback。原关系表只继续既有记录/写入用途。

读取结果实际进入 `read_succeeded`、expected_outcomes、same-context/membership 检查。不可读取会执行原 raw-consequence 机制，进入 frame/experience 与 pending_consequences，并在后续轮实际重新处理，不只写组织摘要。

旧 [formal_l0.py](individual/formal_l0.py) 及其世界入口冻结哈希保持原状。独立解释器复制既有 advance 编排，替换该读步骤；不是动态改写、隐藏 import 或更新旧冻结清单。它不新增 sampler/binder，也不改变现有生成规律。复制代码的维护边界明确：不能把以后原 FormalL0 的改动无审计地自动引入本 profile。

### Provenance / detached effect screening

`FROI_ORGANIZATION_FORMED` 保存实际 graph、规范内容及全部支持/根/输入 registry；`FROI_ORGANIZATION_CONSUMED` 保存实际读取 keys、状态及支持链。

`advance_detached` 接收已经 COMPLETE 的同一 handle，复制 FormalL0 state/frame/actions，不再生产图。screening 只屏蔽消费者对图的访问，H/Condition/graph/provenance 不删改。测试引起的读取失败明确标 TEST_ONLY，不冒称物理容量已满。返回 state 被标为 detached，ACore 持久化边界拒绝写回正式 A。

## 3. 回归与新增控制

机器报告：[FROI_IMPLEMENTATION_VALIDATION.json](FROI_IMPLEMENTATION_VALIDATION.json)。可重跑入口：[debug/froi_validation.py](debug/froi_validation.py)；输出必须选择新文件，旧报告不被覆盖。

| Suite | 数量 | 最终结果 |
|---|---:|---|
| 原有 Python 回归 | 141 | 全部通过，测试文件未改 |
| 新增 FROI 接口控制 | 15 | 全部通过 |
| 冻结 GSC-0 / GSC-1 | 44 | 全部通过 |
| 既有 persisted-result 控制 | 8 | 全部通过，历史报告未重写 |
| Minecraft 身体回归 | 42 | 全部通过，身体与测试未改 |

[tests/test_froi.py](tests/test_froi.py) 实际检查：机械 seeds、所有历史记录和根、handle 不可变性、Shared/PortBind 的真实消费、无旧表/原始历史 fallback、相同 frame/Condition 的历史反事实、已形成图的效果屏蔽、detached state 写入拒绝、RESOURCE_LIMIT/INVALID、真实内部失败反馈再进入、active window 外输入保留、sample-gap/无引用守卫、引用原 epoch、恢复边界和 sampler 独立性。

历史反事实控制用两个完整的已记录 **测试载体**历史前缀，保留同一个 checkpoint/current frame/query/联合 Condition；没有手动删指定 target。图差异实际改变成功/失败读取路径。效果屏蔽控制对 producer 加禁止调用断言，检查屏蔽后的原始读取失败进入 pending_consequences。独立容量失败控制还执行下一轮并核对原始失败再输入。这些是实现控制；屏蔽后的真实游戏后续输入仍须正式 T4 验收。

早期执行中的问题与最终处理：

- 直接改动冻结 FormalL0 导致旧 source-hash 回归失败；最终恢复原文件，独立 profile 接入，未改测试或冻结 manifest。
- 两个 Node 网络测试在沙箱内出现 EACCES/超时；允许它们访问本机临时测试端口后，原 42 项测试全部通过，未连接真实游戏。
- persisted-result 控制不能裸导入运行，因为其测试需要先生成两组实验数据；使用原有实验入口初始化数据后 8 项通过，新报告写到 `.test-tmp/`，不写旧历史报告。

最后按原字节恢复 FormalL0 后，又执行 25 项 FROI/冻结入口检查，全部通过。未改变任何验收断言。完整回归期间的保护文件未变化；机器报告同时保留该次检查与最终字节恢复核对。

## 4. 启动与未来真实输入

已有明确选择的测试个体、完整配置和已开放 Java 测试世界时：

```powershell
.\.venv\Scripts\python.exe main.py --froi
```

沿用现有启动端口询问。需要本次直接指定端口可加 `--port 当前端口号`。新测试个体仍由现有 `individual.lifetime initialize --label "FROI-1 live"` 显式创建，不自动覆盖/替换已有个体或清除历史。

未传 `--froi` 时保留原 FormalL0；已经进入 FROI 的生命周期不能去掉该选项来绕开组织读取。`--froi-caps` 可在初始化前指定一个完整 GSC Caps JSON；未指定时使用冻结 GSC 已有容量。运行期间不得改容量或输入表示来追求 COMPLETE。

下一次正式验收仍按 FROI-1 原文 T1–T5：先取得真实完整观察历史、真实 reference/checkpoint 和后续帧，再执行规定的组织与内部处理反事实。不能用这里的 FakeBridge 数据补足缺失项。当前尚未观察正式结果，不据测试结果提出其他机制、理论要求或行为方案。

READY_FOR_LIVE_FROI_VALIDATION
