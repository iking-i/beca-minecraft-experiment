# 最小完整身体表达与真实闭环验证 — 当前结果

**REAL_MINIMAL_EXPRESSION_LOOP = NOT_READY**。
基线：0dc73536cb5a6b5422e651c06724ce2efeee769c。
理论 v0.9，未修改。没有启动 Minecraft、没有发送真实 perform、没有提交或推送。

## 实际最早阻塞：完整真实输入的准入容量

现有原生 body describe 返回 47 个能力。冻结 `typed_inputs` 对完整目录生成
47 NativePort + 58 ParameterSlot + 13 ParameterDomain = **118 个节点**。
这是依照当前 catalog/代码计算的静态下界，**不是一次真实观察测量**；不包含
观察值、引用、已有 Units 或 Pair。共享 Unit/content 上限仍为 64。
`NativeEngine.advance` 全批准入检查会在实际 formation 前拒绝。
因此本次单端口小材料离线验证不能证明完整真实观察可进入该实验 Core。
没有截断目录、改 sensor、提高 cap 或改写 NBO。原正式 ACore 的既有身体运行路径
不受此结论否定：这个缺口属于当前 TEST_ONLY Native/Binding operative 实验路径。

## 已完成的最小机械部分

新增隔离 reader 读取权威状态里的 **最新普通构造 Pair**、两个 UnitRef 端点、
对应 canonical DirectedConnection 和实际执行支持。不是重新扫描 raw receipt 求答案。
端口和槽身份来自既有 catalog；参数字段名仅用于已给定槽的协议编码，不选择值。
完整 schema 和当前能力 availability 校验只拒绝，不补缺、排序或仲裁。

固定外部测量端口为 catalog v2 code 16，必需参数为 integer slot ∈ [0,8]。
这是实验者指定的测量对象，**不是 A 自主选择**。没有换成免参动作绕过问题。
固定离线小材料输入为 0→1→1、外部 synthetic receipt 槽→0；同一独立测试 A/DB。
真实执行预算最多一次，门控不满足则零次；没有自动重试或候选替换。

普通构造提供的内容可机械解码为两个合法完整候选：

```json
{"code":16,"parameters":{"slot":0}}
{"code":16,"parameters":{"slot":1}}
```

槽→0 的端点由外部 synthetic receipt 给出；槽→1 的新端点由实际合成经历
0→1 形成的连接与外部通用组合规则共同决定。两者均保留，没有用来源标签
剔除原始候选以强迫唯一。没有参数 sampler/binder、value-to-action mapping 或 fallback。
**完整候选可被机械解码，不等于 A 已在普通构造中创建一个完整原生 expression 对象，
也不等于已形成表达采用权。** 此次 reader 是外部机械投影，不被改称新的内部构造器。

## 小材料范围内的执行阻塞与消融

Pair products 经实际普通 advance 构造；reader 不给它们重新形成端点。
消融新槽→1 连接后，实际普通构造/候选集从 {0,1} 变为 {0}；重新插入恢复 {0,1}。
保持 canonical 检查点不变。单候选 {0} 仍是外部 receipt 前提，不是内部新值作者权。
provenance、顺序和 disconnected 材料控制仍为歧义 {0,1}。

**当前没有内部采用关系决定采用哪一个完整候选。** 对实际测量 witness，门控返回
AMBIGUOUS / NOT_READY，perform 次数 **0**，Core 状态不变，没有 body/world 变化。
不能取首项、最小值、最新值或仅取 EXPERIENCE_INTEGRATED 候选来伪造采用。

## 一次性身体尾链：仅离线测试

`OneAttempt` 只允许独立 BindingCore；只有完整且唯一的读出结果可进入调用。
先独占建立外部持久 ledger，再使用原有 `_bridge.call('perform', expression)`。
回执必须与请求 code/parameters 精确匹配，包含原 native 执行 trace；错配为 FAIL，
传输不确定为 NOT_TESTABLE，均不重试。请求/执行记录沿现有 Core transition 提交，
新的 observe 再经同一 Core `accept_observation` 进入权威 Current State。
观察失败不会把已经完成的执行误写成动作失败。关闭监控/工具不会自行切换 A。

FakeBridge 测试采用唯一外部前提槽→0，只验证机械 transport、回执检查、一次预算
及同 A 重入的接线；**不作为内部参数新值形成或真实世界 PASS**。
未复用 BPC-R2 固定 witness/外部 query 条件，未重新执行 BPC-R2 或任何真实动作。

## 证据与验证

SPEC.md：实现前固定测量端口、拒绝歧义、最多一次请求、作者权与结果等级。
VALIDATION.json：新的离线历史、Current State、Pair/支持来源、消融/恢复与零执行门控。
VALIDATION_INITIAL_CAPTURE.json：保留最初采集和当时源码哈希。
TEST_RECORDS_PRE_RECEIPT_CLASSIFICATION_FIX.json：保留第一遍有效测试记录。
TEST_RECORDS.json：最终专项、相关及完整回归的实际命令、返回码、stdout/stderr 和哈希。
回执错配分类从 NOT_TESTABLE 修正为预注册 FAIL，不改变成功标准或冻结机制。

最终测试计数及冻结/保存检查在机器记录完成后附于下方。

## 分层结果与 nonclaims

- 完整表达候选：可机械解码；普通递归中的完整原生 expression 对象未证实。
- code 作者：外部实验者指定测量端口；身份来自环境 catalog。
- 新参数候选内容：经历连接 + 外部通用组合；初始值前提来自 synthetic receipt。
- 表达采用：NOT_ESTABLISHED，两个候选不静默择一。
- 原生真实接口进入 / Minecraft 执行 / 实际效果 / 新真实观察回流：均未发生。
- 连续运行双向真实闭环：NOT_ESTABLISHED，不宣称行为因果闭合。

另外，冻结 ReceiptEncoder/BindingEngine 只接受 external synthetic typed incidence；
真实 ACTION_EXECUTED 回执不会自动转成该输入。本次未把真实回执伪标为 synthetic，
也未实施 real receipt 适配。原有 body perform→receipt→observe 与 Core 世界重入
基础设施仍在；它们存在不证明本次闭环已经发生。

所有旧冻结源码/判据/证据、数据库、body、sampler/binder、caps、理论和 unrelated
untracked 保持原样。停止，不设计采用策略、不另开研究阶段、不自动提交或推送。

## 最终验证记录

- 专项：15 passed，6.65 s。
- 相关：92 passed，38.78 s。
- 完整 Python 回归：664 passed / 114 subtests passed，398.35 s。
- 原 13 项冻结哈希 MATCH，SPEC / 最终源码 / stdout 哈希核对通过。
- JSON / git diff --check PASS；原有 383 个 tracked/untracked 文件字节全部不变。
- 所有新增文件未暂存、未提交、未推送，tracked 工作树干净。
- 真实执行 0 次；结果仍为 NOT_READY，不将测试全绿升级为真实闭环 PASS。
