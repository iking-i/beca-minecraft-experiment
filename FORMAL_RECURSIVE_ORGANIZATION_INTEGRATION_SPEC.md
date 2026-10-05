# Formal Recursive Organization Integration Specification

版本：FROI-1。日期：2026-10-05。本地读取基线：`679a58b7c2d6dcc74d2a877dc9527cfa9294b59d`。

本文件只定义未来接入与验收，不实施、不运行实验，不改变既有代码、测试、审计、结果或理论。本轮固定候选能力：

```text
accumulated history + current structural input
→ 固定 GSC-0
→ O-G0-1 derived structural organization
→ FormalL0 后续内部处理
```

最小初始记忆条件是：**在有限实验容量内保留实验所需的原始历史输入。**它属于本版本实验初始化条件，不是 Perfect Recursion 普遍规律。不要求前轮 materialized closure 原样持久化；允许在每次读取前从完整保留材料重算组织。

目标仅为真实 ObservationFrame/history 经机械表示形成组织，并影响 FormalL0 的内部读取、检查或读取失败反馈。既有动作选择路径不接本接口，不据本实验宣称世界行为作者权。本文不扩展理论或生成规则。

## 1. 当前真实接入点与职责

现有 [ACore.accept_observation](individual/core.py#L115) 将真实 ObservationFrame 交给 `FormalL0Engine.advance`。后者已有以下处理：

1. 对实际观察作 `detect_changes`、计算既有 unit identity；
2. 从 `feedback.next_relation_ref` 获取实际待读引用；
3. [formal_l0.py:195—215](individual/formal_l0.py#L195) 读取关系、构造 expected_outcomes、执行 same-context 与 membership 检查；
4. 引用存在但读取失败时，[199—203](individual/formal_l0.py#L199) 形成 raw read consequence，放进 experience/frame；
5. [270—294](individual/formal_l0.py#L270) 保留 feedback/pending_consequences，使原始失败反馈能进入后续轮。

本规格的消费者定位在 **第 2—4 步**。未来接入 profile 在这里以组织读取替代原来的 `internal.relations.get(reference)` 数据来源；不另加一条只写日志的旁路。旧关系表可以保留其历史用途，但不得作为本接入路径的 fallback，否则组织消融可能完全无效。

表示适配器、组织读取器和 GSC 运行器均是外部提供的固定基础机制；本实验不称这些机制由 A 自己发明。需要观察的是机制处理真实经历所形成的组织内容以及该内容的实际内部作用。

## 2. 接口一：Observation/History → GSC input

### 2.1 输入与历史截止线

输入契约：

| 内容 | 来源与边界 |
|---|---|
| H_raw | 同一 A 保留的原始 ObservationFrame、真实顺序/编码 namespace/body_epoch、实际动作与引用记录；不取人工标注答案 |
| H_records | 已完成轮的实际 `EXPERIENCE_FORMED`：experience_id、root、antecedent/outcome 的既有 unit refs、frame_ids、action_ids 等；必须能回溯 H_raw |
| F_t | 本轮完整真实 ObservationFrame；不使用人类 debug 名称解释其含义 |
| q_t | 本次真实 `feedback.next_relation_ref` 与读取发生的 frame/state identity；来自现有 FormalL0，不能由适配器选目标 |

H_records 是原始经历的**机械时间关联记录**，不是给定的 expected_outcomes 或人工结论。其 `outcome` 是已经发生的历史观察 unit ref，[formal_l0.py:182](individual/formal_l0.py#L182) 明确只记录 temporal association。即使真实 action 来源外部，也必须保留该 provenance，不将 action 的外部来源改称组织自主决策。

本轮构建组织时只把 **读取开始前已经完成** 的历史经验作为历史记录。当前 F_t 可以提供实际 identity、变化描述和当前读取引用，但当前尚未完成的 experience 不得作为历史记录参与自身预测。其记录在本次消费完成后才能加入下一轮 H_records。这样不会因“当前观察已经被写成历史答案”制造 membership 恒真。

### 2.2 机械编码最小契约

只提供一个固定、无语义的内部记录表示：

| 原字段 | GSC 表示 | 允许的含义 |
|---|---|---|
| 历史 experience.root | 精确 opaque Node identity `G(root)` | 已发生记录的索引引用，不是新目标 |
| experience_id / 对应历史观察字段 | 唯一 Variable `V(record_id,field)` | 该条记录的存储字段身份，不与别的字段自行绑定 |
| 已观察的 unit ref | 带类型的 opaque Value | 复制实际存在的 token，不解释它意味着什么 |
| 该条已发生记录 | `Relation(record_id, record_signature, (G(root),V(record_id,field)))` | 实际 co-recorded 字段的结构包装 |
| 该字段实际内容 | `Bind(V(record_id,field), Value(actual_unit_ref))` | 已发生事实，不是应当得到的结论 |
| 本次现有 q_t | `Relation(read_id, read_signature, (G(q_t),))` | 既有精确内存引用的读取请求；不规定返回值 |

每个模板实例来自一条可核对的实际记录；对契约内所有合法历史记录统一编码，不挑 preferred record。不同记录的 Variable identity 不混同。单位 token 使用既有 [pattern_id](individual/structure.py#L16) 及真实字段；适配器不另做语义类别或推断。

固定类型声明为 `record_signature=(node,variable)`、`read_signature=(node)`；Variable 与对应 Value 使用同一字符串类型 `UnitRef`，不是默认整数类型。record 的第二字段固定复制该实际 experience 的 outcome unit ref。这个字段契约只描述已经发生的时间关联，不给当前观察填预测答案。`G(root)`、record/read identity 的命名与 scope 必须包含同一 A 和实际引用的编码/载体来源，且读请求沿其真实引用来源使用同一身份；不得用本轮 epoch 重新解释旧引用。无法取得引用来源时须显式不可解析。既有 unit ref 只标识 `pattern_id` 所编码的 channel/change-kind 形状，不代表原始完整帧或数值内容相同。

该表示是原始 Frame/history 的有限机械投影，不声称涵盖帧的每个数值或新的世界因果关系。原始完整帧仍保留供审计。真实 numeric channel/value/change/reference 若被编码，只能按固定类型序列化、精确身份引用；浮点值必须无损带类型编码，不能量化为业务类别。字段契约不能在运行时因“哪个有利于得到答案”而变更。

当前 frame 的 unit/change identity 可保留为本次输入来源与检查对象，**不得新增 `Bind(q_t, current_outcome)`**，也不得给历史记录补上人工 equality。跨 encoding namespace/body_epoch 的引用按已有真实 identity 隔离；不凭相似 token 合并。

### 2.3 有限 Condition 与拒绝条件

每次组织计算先机械收集本次全部 H_records/current-read 所用的精确 identities、已有值和固定 signatures，声明本次有限 Condition，再从对应 seeds 运行 GSC-0。这是一次完整输入声明与计算，不是更改 GSC 的生产规则；不依赖将旧 Condition 的 State 强行传入新 Condition。

不得选前 N 个输入、按距离/优先级筛选、随机挑一个 token 或偷偷补默认值以适应容量。声明或完整 closure 超出配置容量，返回明确未完成/不可表示状态；本次不能通过验收。初始容量是外部实验配置，不能把自动扩大容量当作本实验结果。

本接口没有 observation→具体答案、结论或行为的表。`G(q_t)` 只是已有读取引用的精确身份；读到什么由实际历史材料和 GSC 的通用规律决定。若实现需要手写“某种观察对应某个答案”才能运行，即违反本接口，不能以命名为 codec 隐藏。

## 3. 接口二：organization identity / state boundary

输出契约是一个只读 organization handle，至少包含：

```text
individual identity / source state version / history cutoff
current frame identity / actual requested reference
Condition identity and codec version
COMPLETE or explicit incomplete status
O-G0-1 graph projection
direct supports / finite input-root witnesses
exact input record registry
```

组织内容 identity 用规范 typed facts 与连接内容表达，去掉运行 UUID 后仍可比较；digest 可作索引，但不替代实际内容比较。运行 handle/state version 与图的规范 identity 分离。相同输入重算出同样组织是允许结果。

O-G0-1 包含 Eq/Bind/PortBind/Conflict/Shared-incidence；不把 Composite 当作组织读取结果。GSC 自己仍按既有固定规则完成全部阶段，只有 Result.COMPLETE 才发布 handle；RESOURCE_LIMIT 前缀不可伪装成完整组织。

handle 的来源版本、历史截止线和 current reference 必须匹配该次 FormalL0 读取。旧 graph 可以作缓存，但重新计算或验证相同输入所得 handle 才可使用；不要求其原物化对象连续保留。不得把不同历史的 graph 偷接到正式主线；反事实替换只存在于隔离测试。

同一个 A 的本次输入与 handle 都受其既有连续状态链管理；此接口不创建另一个个体，也不凭组织 identity 改变 A identity。

## 4. 接口三：GSC organization → FormalL0 internal consumer

### 4.1 读取算法的严格范围

消费者使用当前已有的 read-request Relation 作为精确读取锚点，执行以下全量、无择优操作：

1. 读取 **GSC 生成的 Shared witnesses**，找出实际连接本次 read Relation 与历史 record Relation 的端点；连接依据是精确相同的 root Node incidence。
2. 对这些历史 record Relation，读取 **GSC 生成的 PortBinding**，恢复该实际记录字段的所有 observed-unit Value。
3. 对相同 unit ref 作集合去重，保留全部候选和它们的全部直接支持/根；排序仅用于 canonical serialization，不取一个答案。
4. 返回与现有读取步骤兼容的只读结果：引用是否可解析、全部 expected-outcome unit refs、实际消费的结构 keys 及支持。未解析/未完成必须显式区分。

源码可支持这条边：[engine.py:300—312](experimental/gsc0/engine.py#L300) 生成历史字段的 PortBind；[377—391](experimental/gsc0/engine.py#L377) 依据 exact Eq/incidence 生成 Shared。read Relation 不断言一个值；与哪条实际记录共享引用由图规则计算。不存在人为指定的观察答案边。

必须读取 handle 中实际 Shared/PortBind 对象，不能绕过它们遍历原始 H_records 直接返回字段，也不能在读取器里重做一次 GSC 后掩盖组织效果消融。原始历史重算属于 handle 生产阶段，不属于消费者的 fallback。

Conflict 或同一字段有多个合法绑定时，所有值与 Conflict 信息保留；不投票、评分、选 first/best 或填默认结果。缺失结构与完整空查询不同，不能把 incomplete 当作“查无历史”。

### 4.2 哪个真实处理步骤发生变化

本接入 profile 在 [FormalL0.advance:195—215](individual/formal_l0.py#L195) 使用上述结果构造 `read_relation` / `expected_outcomes`，继续执行当前已有的引用/上下文/membership 检查。这里不是附加一条组织摘要日志。

沿用现有读取步骤的执行前提：有 previous frame、没有 sample gap、存在活动 process。不存在实际 q_t 时不制造读取目标，也不制造缺失引用失败；首帧或 sampling gap 不得由本接口补成连续时间经验。

有实际 q_t 但组织读取不可用或无法解析时，必须进入现有 **read failure→raw consequence→frame/experience.internal observations→下一轮 pending consequences** 的真实内部路径，而非只生成审计报告。读成功则以全部真实历史候选执行现有检查，不按观察值预填 expected_outcomes。

测试性读取屏蔽必须明确标为 TEST_ONLY 干预。它使这次读取效果不可用，不能谎报真实物理容量已满。未来接入应把原因来源保留在原始失败记录与审计元数据中；状态链能区分“真实读取失败”与“测试人为屏蔽”。

本规格只定义组织数据进入已有处理步骤；不规定某个 observed outcome 必须获强化、被删除或引起某动作。现有动作 sampler/binder 不接 handle、候选、Conflict 或读失败结果，本次验收不以动作变化作为证据。

## 5. 接口四：provenance / ablation boundary

### 5.1 完整来源链

每一次实际消费必须能追踪：

```text
原始真实帧 / 实际动作与引用记录
→ 已完成的机械 experience 与字段
→ codec seed / declaration roots
→ GSC Shared + PortBind 的全部直接支持
→ FormalL0 本次实际读取的结构 keys / expected set
→ 成功检查或读取失败的执行路径
→ 若失败：下一轮实际重新输入的 raw consequence
```

必须分别标明固定 codec、固定读取器、实际输入材料与派生事实的来源。仅加 integration_id、hash 或来源标签不足以证明结构被消费。对输入支持与派生支持并存的事实，保留两者，不能把“有派生证明”偷换成原始事实自主生成。

### 5.2 与已做的物化结果消融区分

本次未来组织效果消融，保持 **H、F_t、q_t、FormalL0 其他状态、Condition、完整组织生产结果** 一致，只屏蔽消费者访问本次图的 Shared/PortBind effect。它不是删除原始输入，也不是删除前轮物化闭包再允许生产器重推导。

这种屏蔽只在 detached TEST_ONLY 调用边界施加；原始历史、正式 graph 和输入根保持不变。屏蔽状态必须随本次调用显式标记，不写回正式 A。消费者不得从原始历史或旧关系表绕开它。

它检验的是 **formed organization→actual internal consumer** 边，不试图推翻已记录的“旧物化结果可重新计算”结论。若去掉 effect 后只改变报告/UUID、真实处理完全不变，这个消融不能通过。

## 6. 未来正式测试验收（本轮不执行）

### T1：真实输入与机械表示

使用正式接入路径取得真实 ObservationFrame 和已完成 history records，不人工修改数字、unit ref、root 或补期望值。验证所有 seed 能回溯真实材料；decoder/encoder identity 一致；没有语义名称分支或候选选择。

使用契约完整的短历史前缀以符合已配置有限容量，不能截取某些有利 channel/record。若完整输入与当前 cap 无法完成，就记录不可验收，而不是借人工答案缩小图。

### T2：核心历史反事实

固定一个实际 FormalL0 read checkpoint 的其他状态，包括 pid、state version、previous_frame/unit、feedback.next_relation_ref、pending actions、resource limits、编码/body epoch 和本次完整 F_t。读取引用须有真实来源，不由测试者选择“最能改变结果”的答案目标。

两个组织生产端分别接收真实 H_A / H_B；它们是已记录原始历史及其机械 records 的不同完整集合，不是手工填写两个 organization。除了这个历史输入，current structural read input 相同。Condition 采用两组材料所需精确声明的固定联合域；未出现于某组历史的声明不自动产生该组绑定或答案。

必须实际验证：

```text
H_A != H_B
同一当前 F_t / q_t / 其他 FormalL0 状态
→ 两份 COMPLETE O_A != O_B（内容，不仅来源 ID）
→ 实际读取的 Shared/PortBind 内容不同
→ FormalL0 后续检查内容或执行路径不同
```

对 expected set、membership 和读成败分别比较。不能只比较 experience UUID、组织 digest 或最终 partial 日志。最强路径见证是：一个历史存在可解析的实际引用记录，另一个没有，消费者因而走成功/读取失败两条分支，后者形成 raw consequence 并被下一轮输入实际消费。测试不能通过给 H_B 人为删除目标关系或写入 expected set 制造这条结果。

固定 checkpoint 的引用来自实际 FormalL0；这是 counterfactual 的受控读取条件，不声称两个不同历史各自天然演化到相同全部状态。历史替换与 checkpoint 的不一致须在 TEST_ONLY provenance 中明确记录，不能成为正式 A 的恢复/替换操作。

如果真实 H_A/H_B 未产生不同组织读取效果，只能记录未观察到该验收链，不能按预期结果修改 codec、引用、raw frame 或 graph。不同历史保留的无关旧事实不同，也不够证明目标消费改变。

### T3：组织效果消融

对同一 H、F_t、checkpoint、COMPLETE handle，比较正常 consumer 与 TEST_ONLY effect-screened consumer。

必须固定原始数据与 graph 生产，不允许即时重算绕过屏蔽。记录实际读取 keys、read_success/failure、expected set/检查结果、分支执行及后续 raw input。要求屏蔽导致**真实内部处理差异**；若只有来源记录或日志变化，不能通过。

### T4：不是只写日志的执行见证

对 read-failure 路径至少继续一个真实 FormalL0 内部处理轮，核对原始 consequence 被放入 pending_consequences，下一次输入保留原内容并被处理。不是仅声称未来可能消费；也不是生成一条报告便结束。

这项验收不以移动、跳跃、聊天或其他世界动作不同为成功条件。世界观察是真实输入来源，组织效力的被测消费者仍是 FormalL0 内部。

### T5：完整性与污染控制

- 所有用于验收的组织 COMPLETE；cap/validation failure 是明确未验收，不能当成功空集。
- counterfactual 固定当前整帧、读取引用和其他状态；比较内容时剔除仅审计 UUID 差异。
- raw history、当前帧、seed registry、roots 与正式状态在 detached 消融前后未被修改。
- 实际运行时没有 raw-history/旧关系表 fallback，也没有连接 action selector 作为因果证据。
- 同一个接口契约/codec 版本用于全部组，不为取得差异临时改变字段表示或查询对应。

以上是未来验收方法，不是本轮已通过结果。

## 7. 可实施性裁定

四个接口可以在现有通用语法/精确引用/PROP-PORT/Shared 计算和现有 FormalL0 读取失败反馈步骤之间定义清楚。没有要求 GSC 生产新业务推理规则，也没有要求人为写入观察的正确答案：历史值来自已发生的机械记录，查询锚点来自真实现有引用，消费者保留全部匹配结果。

尚需未来实现与实际验收的内容是适配器、COMPLETE handle、真实读取替换和 detached effect 屏蔽；当前代码尚未接通，不声称已证明目标闭环。容量可完成性和真实历史是否给出所需反事实差异也尚未实测。

本版本未发现必须借 external semantic routing 才能定义这四个接口的问题；未来若实现只能靠这种路由完成，则本规格不能作为其授权或通过依据。本轮只给实现就绪判定，不提出替代机制或行为方案。

READY_FOR_IMPLEMENTATION
