# Current Organization Scope Consistency Audit

日期：2026-10-05。读取基线：`d53e6b19b5b99660570a38eda0a95e58a9c617a3`。

标准：[CURRENT_ORGANIZATION_CRITERION.md](CURRENT_ORGANIZATION_CRITERION.md)，冻结的 CO-WAC-1。被复核文本：[CURRENT_ORGANIZATION_AUDIT.md](CURRENT_ORGANIZATION_AUDIT.md)。本文件不修改这两份文件，也不将工作标准升级为 Perfect Recursion 公理。

本轮仅新增本文。没有运行测试、closure 或新实验，没有连接 Minecraft、读取 canonical SQLite、改动程序/原型/测试/历史数据/理论仓库。以下测试均是读取既有断言；JSON 是既有执行记录，不是本轮执行结果。不继承其 overall passed 标签，不审计其他 GSC 阶段，不设计机制或提出解决方案。

## 1. 对象边界及方法

先固定 O/H/I/M/P/K，再检查旧证据指向哪个 O，最后评分。第二部分的 SCOPE_MISMATCH 只判范围，不先指定新的分数。

源码支持保留六个对象，但必须校准两个名称：

- O-F2 是**已经部署的固定 formal 行为管线**，不是历史生成的某个动作记录或 relation。完整组织方式没有历史生产器；不能拿新 action UUID 替它通过 C1。
- O-G0-1 是 `State` 中 Eq/Bind/PortBind/Conflict 与 **Shared witnesses 所表达的派生结构图**，及其无损图索引；不是“所有新增记录”的无差别集合。其 C3/C4 只针对这一整体图的关系/连接表达，不给每个孤立 leaf 一份总体 PASS。
- O-G0-2 是 `Composite(members)` 的规范对象本身，包括其可查的 COMPOSE provenance；**不把外部 `Shared` 图改名为 Composite 的内容**。`composition.shared(composite.key)` 是按成员查询另一份图，不是 Composite 有一个新 topology 字段。
- O-G1-1 是派生的 `Binding(p_i,v)`，不是 `Eq(h_i,p_i)`、PortAssessment 或 tuple。
- O-G1-2 是 `GroundedOutwardStructure(schema_key,fields)`；其来源可从同次 `GroundingResult` 的 ports/evidence 与 schema_key 追踪，但这不把那些 Binding 变成 tuple 的后续消费者。

无需进一步合并：上述对象有不同的生产函数、身份键或消费者。结构图内部的不同事实生产规则分开列证据；不据某种事实的效力声称所有事实都能单独驱动传播。provenance 支持边也不等于执行依赖边。

### 1.1 O-F1 — history-formed temporal relation instance

| 项 | 固定范围 |
|---|---|
| O | `internal.relations[root]` 的 antecedent/action_code/outcomes 与证据；被测实质是新 outcome 关联，不是计数或 UUID |
| H | 保留的 previous_frame/previous_unit、已有 relations、feedback、先前 action 记录 |
| I | 当前 ObservationFrame、pending_actions、前一轮原始 limit consequences |
| M | 编码/时间相邻规则、固定 relation schema、sample-gap 判定、容量拒绝机制 |
| P | `FormalL0Engine.advance`：形成 experience，再创建 root row/插入 observed outcome（[formal_l0.py:172](individual/formal_l0.py#L172)、[223](individual/formal_l0.py#L223)、[240](individual/formal_l0.py#L240)） |
| K | 下一次 `advance` 的 `internal.relations.get(reference)`，读取 outcomes 形成 partial.processing（[195](individual/formal_l0.py#L195)—[215](individual/formal_l0.py#L215)）；动作 sampler 不读该表来选动作 |

action 的外部来源必须披露：默认 formal 动作由 sampler/binder 生成，返回的实际 action 才进入 pending_actions。`pending_actions[-1]` 是记录最近实际动作的约定，不是把动作选择器嵌入 relation 生产器。context 截取影响 experience 的信息范围；relation 内容没有一个“把这个 context 映射成指定答案”的分支。

### 1.2 O-F2 — complete formal behavioral pipeline

| 项 | 固定范围 |
|---|---|
| O | 当前 formal profile 的执行管线：观察/编码→advance→状态持久化；另一路 available codes→LCG sampler→参数 binder→command→Bridge→新观察 |
| H | Individual 当前状态、关系记忆、随机状态、policy 参数、已有事件；不是另一份管线源码 |
| I | Bridge observation、当前可用动作域、tick/人工测试调用 |
| M | 固定 ACore 编排、FormalL0 解释器、动作 codec、公开 Bridge API、资源/类型约束 |
| P | 程序员提供管线和连接；实验运行实例化并执行它，没有由历史构建/替换该管线的函数 |
| K | core worker 调用 `core.tick()`（[core.py:507](individual/core.py#L507)）；管线输出由 Bridge 调用接口实际消费（[261](individual/core.py#L261)），随后新观察进入 ACore |

[core.py:115](individual/core.py#L115) 和 [209](individual/core.py#L209) 是两条实际入口，[333](individual/core.py#L333)—[360](individual/core.py#L360) 把它们编排进 tick。这里的 complete 指当前实现范围，不表示整个理论闭环已成立。显式 capability test 可绕过 sampler，但旧审计的默认 formal 路径实际启用 sampler/binder。

### 1.3 O-G0-1 — derived structural graph

| 项 | 固定范围 |
|---|---|
| O | 有类型的派生事实和 incidence 连接图：Eq/Bind/PortBind/Conflict，以及连接 leaf/port 的 Shared witnesses；保留支持/根索引 |
| H | R1/R2/R3 历史闭包及普通 Node/Variable/Value 声明 |
| I | Difference 带入 D1=Bind(Y,3)、D2=Eq(Y,X)；冲突测试另带 Bind(Y,2) |
| M | 有限类型/作用域域、全部 ALIGN/PROP/CONFLICT/SHARED 规则、COMPLETE 判定和 cap |
| P | `Engine.consequences`（[engine.py:282](experimental/gsc0/engine.py#L282)）；`Engine.run` 的 shared-incidence 段（[377](experimental/gsc0/engine.py#L377)—[391](experimental/gsc0/engine.py#L391)） |
| K | 后续 closure rounds 读取 Eq/Bind；shared 段读取 derived Eq；composition 段读取 Witness 的两个端点建立 adjacency，判定连通子集（[394](experimental/gsc0/engine.py#L394)—[420](experimental/gsc0/engine.py#L420)） |

Shared 是有端点、端口的明确结构（[model.py:225](experimental/gsc0/model.py#L225)），不只是字符串来源标签。Conflict/PortBind 不进入 `consequences` 的 Bind 列表；其 effect 在 incidence/Shared/组合侧，而非作为任意新 binding 推理前提。

### 1.4 O-G0-2 — Composite

| 项 | 固定范围 |
|---|---|
| O | canonical `Composite(members)`；主具体实例 R4={R1,R2,R3,Bind(X,3)} |
| H | 既有闭包和此前 Composite；其中不含指定 R4 |
| I | 本轮完成的派生图及其共享连接；D1/D2 是间接生产前提 |
| M | flatten/canonicalize、穷尽合法连通支持组合、无 ranking/pruning 的 COMPOSE 索引 |
| P | `Engine.run` 以连通 mask 生产 Composite（[420](experimental/gsc0/engine.py#L420)）；`Composite.__post_init__`（[model.py:127](experimental/gsc0/model.py#L127)） |
| K | 下一次 run 读取旧 Composite.members 初始化 masks（[engine.py:400](experimental/gsc0/engine.py#L400)）；`CompositionIndex.for_conclusion`/root/proof 查询消费其成员键；测试和报告读对象。无 Composite→Bind/Eq 生产器 |

其 key 仅是 flat leaf set。完整 Shared 信息可从图索引按该 key 查询；把这种上下文读取归到 O-G0-1，不能声称 O-G0-2 自身储存或重构了端点组织。

### 1.5 O-G1-1 — derived outward-port bindings

| 项 | 固定范围 |
|---|---|
| O | 三个 ordinary `Binding(p_i,v)` 的具体派生实例，保留每个实例的直接支持与根 |
| H | 独立历史 H_i=Bind(h_i,v_i) 的完整初始闭包；初始 p_i 未绑定 |
| I | 人工 CurrentInput D_i=Eq(h_i,p_i)，不是由内部图新生成的连接 |
| M | GSC-0 规则、相同 Condition/type/namespace/scope；outward 名称不改变 ordinary Variable 类型 |
| P | 上游 GSC-0 PROP-ALIAS；`close_history` 调用该生产器（[fixtures.py:34](experimental/gsc1/fixtures.py#L34)） |
| K | 后续 GSC-0 规则/组合；尤其 `check_grounding` 扫描实际 Binding，按 schema 的精确变量读取值及支持（[grounding.py:31](experimental/gsc1/grounding.py#L31)—[44](experimental/gsc1/grounding.py#L44)） |

路由的作者是 [fixtures.py:29](experimental/gsc1/fixtures.py#L29) 的 `zip(sources,outputs)`：逐对写 Eq(h_i,p_i)。这条边决定 O 的具体 target，不只是一个无关输入事实的外部来源。

### 1.6 O-G1-2 — GroundedOutwardStructure

| 项 | 固定范围 |
|---|---|
| O | 具体 `GroundedOutwardStructure(schema_key,fields)`；不是 upstream Binding 的别名 |
| H | 已完成的 closure 与固定 OutwardSchema；历史不含完整 tuple |
| I | checker 收到的 COMPLETE closure 和 schema；即本对象的直接输入，内部已经包含 O-G1-1 |
| M | 合法 schema/类型检查、各字段 binding cardinality 0/1/>=2、精确 singleton 解包；缺失/冲突拒绝完整结果 |
| P | `check_grounding` 第 54—57 行；`GroundedOutwardStructure` 构造/key（[model.py:43](experimental/gsc1/model.py#L43)） |
| K | tests 读 fields/key；`grounding_record` 将其序列化（[validate.py:33](experimental/gsc1/validate.py#L33)）。无进入后续 closure/grounding/body 的生产性消费者 |

schema 不仅有合法类型，还指定具体 field name→Variable identity；来源是 [fixtures.py:23](experimental/gsc1/fixtures.py#L23)。generic 包装代码与这个具体对应配置分开评判；不能仅因把配置列在 M 就免除 C5。

## 2. 旧审计十五项判定的对象对照（本节不重评分）

CONSISTENT 指主要证据和所声称的对象相符；CONSISTENT_WITH_LIMIT 指成立范围已明确限定。SCOPE_MISMATCH 包括把两个对象合并评分，或用另一个对象的局部成立支撑当前对象的分数；不表示所有原始事实错误。

| Mechanism | Criterion | Claimed verdict | Actual audited object（原文目标） | Evidence object（直接证据） | Scope consistent? |
|---|---|---|---|---|---|
| FormalL0 | C1 | PASS | relation instance；还提 unit | relation 内容差异是主证据，unit 是前提 | CONSISTENT_WITH_LIMIT：仅 O-F1 |
| FormalL0 | C2 | PARTIAL | relation/provenance | O-F1 的 refs/journal；行为链作为来源上下文 | CONSISTENT_WITH_LIMIT：未借动作效力补全来源 |
| FormalL0 | C3 | FAIL | relation row 及固定 evaluator | O-F1 的创建/更新路径 | CONSISTENT：需要重新依据内容而非标签确认 |
| FormalL0 | C4 | PASS | 关系记忆的后续读取 | O-F1 被真实 lookup；控制擦除 relations | CONSISTENT_WITH_LIMIT：不是 O-F2 的内生行动 |
| FormalL0 | C5 | FAIL | 机制汇总中与上述 relation 混用 | O-F2 的 sampler/binder；不是 O-F1 的答案生成规则 | **SCOPE_MISMATCH** |
| GSC-0 | C1 | PASS | 新事实 + R4 | O-G0-1 新绑定；O-G0-2 新成员集合 | **SCOPE_MISMATCH**：两对象合评分 |
| GSC-0 | C2 | PASS | closure 与 R4 | O-G0-1 basic proof saturation；O-G0-2 COMPOSE oracle | **SCOPE_MISMATCH**：可各自成立，不能视为单一 O |
| GSC-0 | C3 | PARTIAL | Composite 的组织 | Composite.members + O-G0-1 Shared 拓扑 | **SCOPE_MISMATCH**：拓扑子证据在另一对象 |
| GSC-0 | C4 | PARTIAL | 主要目标 Composite | 强证据来自 O-G0-1；另有 O-G0-2 masks/索引读路径 | **SCOPE_MISMATCH**：需独立检验剩余 Composite 证据 |
| GSC-0 | C5 | PASS | 通用 closure/COMPOSE | 两个对象各自生产规则均可直接检查 | CONSISTENT_WITH_LIMIT：共同机制事实可分别使用，不能合成组织总分 |
| GSC-1 | C1 | PASS | p Bind + tuple | O-G1-1 的新 binding 和 O-G1-2 的新 key/fields | **SCOPE_MISMATCH**：两种 novelty |
| GSC-1 | C2 | PASS | bindings 的 provenance + tuple | O-G1-1 全部支持；O-G1-2 有同次 evidence/schema 上下文 | **SCOPE_MISMATCH**：后者不能只用前者的 roots 代替包装来源 |
| GSC-1 | C3 | FAIL | tuple 自身 | O-G1-2 固定 schema、fields 构造 | CONSISTENT：上游 Composite 不补足 tuple |
| GSC-1 | C4 | PARTIAL | tuple 主对象 | O-G1-1 被 checker 读；tuple 无下一轮消费者 | **SCOPE_MISMATCH** |
| GSC-1 | C5 | FAIL | GSC-1 总体/tuple 混用 | 主要是 O-G1-1 生产前的 explicit Eq target linkage | **SCOPE_MISMATCH**：tuple 的具体 schema 对应还须独立检查 |

源码/测试位置及原判定见旧审计 [FormalL0 §§C1—C5](CURRENT_ORGANIZATION_AUDIT.md#2-formall0)、[GSC-0](CURRENT_ORGANIZATION_AUDIT.md#3-gsc-0)、[GSC-1](CURRENT_ORGANIZATION_AUDIT.md#4-gsc-1)。上述标记不以旧分数为新分数的前提。

## 3. 同一 O 的重新评分及直接证据

### 3.1 O-F1

| 标准 | 裁定 | 同对象的证据与限制 |
|---|---|---|
| C1 | PASS | root row/outcomes 出现此前未有的实质关联；[advance:223—240](individual/formal_l0.py#L223)。既有行为 JSON 的 substantive_relation_contents 显示同一 `U-ee9cd61aee438f8f69d4:-1` 下 outcome 内容不同，非仅 UUID/count |
| C2 | PARTIAL | experience→partial→integration→relation refs 可以追踪，action_code/action_ids 记录实际外部动作事实；evidence_window 满时 active ref 不再增加，但完整 journal 保留事件。没有覆盖所有 row 的完整支持 oracle；不能虚构日志丢失 |
| C3 | FAIL | O 是固定 antecedent/action→observed outcome 行及 refs；实际操作只 record_distinct_experience，没有在该对象内生成独立组织关系/协调约束。不是因为固定语法就 FAIL，也不要求解释器自改；而是此处只观察到记录模板的新实例。新关系、被读到均不能替代 C3 |
| C4 | PASS | 下一轮 actual lookup 读取 O.outcomes；[test_formal_l0.py:117](tests/test_formal_l0.py#L117) 固定其他状态仅擦除 relations，读成败和 expected 改变。只证明这个被索引实例的有限读效力，不证明每条 relation 均被读/引起行为变化 |
| C5 | PASS | 生产器记录实际 observed outcome，没有对 observation 写预定答案/target routing、挑最佳 outcome 或调用动作 selector 决定 relation 内容；保留全部容量允许的 outcome。固定时间关联/索引规则属于通用机制。上游 action 外部生成须披露于 C2，不能据此自动判本对象 FAIL |

C4 的四类比较：

1. 依赖路径是 `feedback.next_relation_ref`→`relations.get`→expected→partial.processing，而非仅附 integration ID。
2. 既有 `BEHAVIORAL_CAUSAL_CLOSURE.json.ablation` 同一 requested ref `U-0294313806f11063b38a:-1`，读前 expected=`[U-ee9cd61aee438f8f69d4,U-4f53cda18c2baa0c0354]`，擦除后 read=false/expected=[]。
3. 源码 [formal_l0.py:199](individual/formal_l0.py#L199) 的 read-failure 分支会形成 raw consequence；指定消融直接断言的是读字段，不是已验证整个后续组织空间。写关系的 schema/容量规则仍相同。
4. 既有 action_changed=false，两个 command 均 code=46/parameters={}。sampler 独立，所以不能把内部读取 PASS 扩大为行为作者权。

保留 FAIL 的理由来自实际记录结构，并非为了回应质疑而调到 PARTIAL。context first-N 属于外部截取范围，记录于 experience；本 O 的 outcome 字段不按它选一个具体答案。容量拒绝写入也不等于“从兼容答案取 first”。这些限制不能伪装成内部学会了关联/优先策略。

### 3.2 O-F2

| 标准 | 裁定 | 同对象的证据与限制 |
|---|---|---|
| C1 | FAIL | 本 O 的连接组织在代码/初始化已提供；历史运行没有产生新管线。新 command/row 不是新管线，不能借 O-F1 的 novelty |
| C2 | PARTIAL | [core.py:236](individual/core.py#L236) 记录 source state/frame/selection/decision authorship；实际 command 和 binder choices 可追。统一管线不是 GSC 式输入根支持图，且历史支持的完整性受 O-F1 refs 窗口限制；不宣称完整 provenance 已验证 |
| C3 | FAIL | 两路组织和连接由固定 core/engine/selector/binder/Bridge 调用提供；没有运行生成的新组织配置。仅有其 constituent 状态更新 |
| C4 | PASS | 限于已部署管线作为固定机制的实际执行效力：worker 调用 tick→execute_discrete_action→Bridge.call；既有 fixture-body RPC 记录 actual formal command，返回被 core 写成 ACTION_EXECUTED/FAILED 并进入 pending_actions。不是由历史生成的新组织效力 |
| C5 | FAIL | [select_uniform_action:296](individual/formal_l0.py#L296) 与 [bind_parameters:86](individual/action_space.py#L86) 在 O 内实际选择 code/具体 target/参数；LCG 不受 relation 内容决定。公开声明 external 并不免除此项 |

已有 [test_formal_l0.py:135](tests/test_formal_l0.py#L135) 实际调用 formal action 并检查外部 selection；[150](tests/test_formal_l0.py#L150) 同 seed 下不同 novelty/attempts/relations 得同选择。`debug/behavioral_validation.py` 通过 `tests/fixtures/capability_body.js` RPC 执行命令，JSON 明确 real_minecraft=false、fixture_body_rpc=true。这里没有把 FakeBridge 的观察断言升级成真实世界验收。

C4 检查四类范围：生产管线输出由 Bridge 和随后状态更新真正读取；命令参数进入调用路径，不只是报告文本；code/args 对应公开接口的可执行调用由外部 sampler/binder 决定；既有历史擦除只改变内部 relation read、不改变最终命令。没有管线组织替换实验，因此 C4 PASS **仅指固定实现的实际调用效力**，不指 H 创造了新行为组织，也不以此补全 C1/C3。

### 3.3 O-G0-1

| 标准 | 裁定 | 同对象的证据与限制 |
|---|---|---|
| C1 | PASS | initial 无 Bind(X,3)，D1+D2 后经 PROP-ALIAS 产生该 binding，继续产生对应 PortBind/Shared；冲突 fixture 产生两值及 Conflict。新的是图中 typed 实例/连接，不是 primitive value/新业务 Relation |
| C2 | PASS | [engine.py:69—101](experimental/gsc0/engine.py#L69) 的实际 supports/finite roots；[tests.py:135](experimental/gsc0/tests.py#L135)、[141](experimental/gsc0/tests.py#L141) 核对根和全部 basic immediate supports。Shared 有 SHARED(left_leaf,right_leaf,Eq) 支持，不用 Composite 的 138 种支持代替该图的证据 |
| C3 | PASS | 限定为有限派生图的组织实例：Shared 明确表达多个 leaf 的端点/端口连接，Eq/Bind/PortBind 表达类型约束与关联，不只是成员包含。生产器生成这些 inter-leaf 连接，并把图变成 adjacency；[engine.py:387—398](experimental/gsc0/engine.py#L387)、[model.py:225](experimental/gsc0/model.py#L225)。不是发现新组织方法/语法或自主生成初始 equality |
| C4 | PASS | closure rounds 真读派生 Eq/Bind；shared 阶段真读 Eq；composition 真读 Shared 两端建立 adjacency，约束哪些组合可形成。消费者读的是本图中的关系，而非未消费的 Composite 包装。有限具体 tests 同时核对传播事实与连通图结果 |
| C5 | PASS | 限定通用结构闭包：全部合法事实/冲突/共享连接保留，遍历顺序改变不择答案。人工输入 D1/D2 和 domain 的来源外部，必须披露；不因此声称输入作者权内生，也没有规定“采用 R4”或特定 outward target |

C3 不要求“新组织方式”，CO-WAC-1 第 5 节允许固定通用关系语法形成新的组织关系。这里的 PASS 指**新生成的显式连接图**，不是“某个旧 Relation 有 ports”或“包装包含四成员”。一个孤立 Eq/Bind 不能继承这一图级 PASS；新增 Shared 将关系材料的端点组织显式化，源码确实储存并使用它。

C4 四类比较和证据限制：

- 路径：新 Bind(X,3) 被 PROP-PORT 用来生产 PortBind(R2,0,X,3)；derived Eq 被 shared-incidence 用来生产 witnesses；Shared 被 composition 用来计算 adjacency。Conflict/PortBind 的消费者在 incidence/组合侧，不能声称它们会自己改 binding 规则。
- 读取：[tests.py:141](experimental/gsc0/tests.py#L141) 重新枚举 `consequences` 检查同一图确实已容纳所有适用结果/支持；[67](experimental/gsc0/tests.py#L67) 冲突案例断言 X/Y 的两个 Bind 和两端所有 PortBind，非单个 R4 布尔值。
- 可形成结构：[tests.py:152](experimental/gsc0/tests.py#L152) 的独立 all-pairs incidence oracle 核对由图给出的全部 COMPOSE 支持；[182](experimental/gsc0/tests.py#L182) 用 Shared 图作独立 union fixed-point，与实际 masks 完全比较。生产图的连接约束与下游结果吻合。去 R2/D1/D2 只证明生产材料必要，**不单独当成生成后图的干预证明**；实际消费者和独立 oracle 是另两类证据。
- 输出：下游 canonical closure/支持集合会受图约束；没有 action/body 输出。通用规则不变，原始业务 Relation 未新增，不声称“重写组织方式”。

这些是既有 COMPLETE 小域的实际断言和生产/消费路径，未执行移除一个派生图节点但保持全部输入的专项反事实。C4 PASS 的范围是已证明图关系被读取并决定合法生产结果，不能扩大成这种未做干预也已通过。GSC0 JSON 记录既有 23 项执行；不使用其总体标签给本项打分。

### 3.4 O-G0-2

| 标准 | 裁定 | 同对象的证据与限制 |
|---|---|---|
| C1 | PASS | [tests.py:33](experimental/gsc0/tests.py#L33) 初始 R4 absent、后续 present；既有 JSON 记录 canonical members；不是仅拿 Bind(X,3) 的新颖性替它通过 |
| C2 | PASS | R4 自身的 COMPOSE 全部直接支持和 finite roots 可查；独立 proof-graph oracle 核对索引。既有记录 direct_support_count=138、roots={R1,R2,R3,D1,D2}；是 Composite 的生产来源，不仅是某个 leaf 的根 |
| C3 | FAIL | 本 O 的规范内容只有 flatten 后的 members，没有自己的端点/组织内约束。其合法连通性由 O-G0-1 提供；不把查询得到的 Shared 图偷算为这个对象新生成的组织内容。FAIL 限于裸 Composite，不否认其处于有拓扑的闭包上下文 |
| C4 | PARTIAL | [engine.py:400](experimental/gsc0/engine.py#L400) 的确读取旧 Composite.members，索引/支持消费者也读取成员键。这是本 O 的直接读取子证据；但没有证明其组织身份在保持 leaf 图下改变后续实质结构，且 basic consequences 不消费 Composite |
| C5 | PASS | 全部合法连通集合被产生，固定通用 COMPOSE 语法/canonicalize 允许；R4 只是测试审计标识，不在生产器里被 rank/选择/设为目标 |

C4 四类比较：依赖路径限于 members→mask/support key；已有 idempotence 测试确实把含 Composite 的完整 state 再输入，old members 被读取，但不隔离单个 Composite；可形成 basic Eq/Bind 与 leaf adjacency 不由这个对象改变；不存在 action 输出。root 消融只说明 R4 的形成前提，不证明 R4 生成后的效力。

PARTIAL **不借用 Eq/Bind 的效力**：它来自本对象真实的 members 读取和有限 COMPOSE 支持使用。现有算法仍按图穷尽所有连通 subsets，未证明在同叶图下单独改变一个已生成 Composite 会改变最终 COMPLETE 可形成内容。查询图/生成 proof 是有限读取，不等于新的组织策略已驱动计算。

### 3.5 O-G1-1

| 标准 | 裁定 | 同对象的证据与限制 |
|---|---|---|
| C1 | PASS | history closure 中 p_i 无值；PROP-ALIAS 后出现新的 Binding(p_i,v)。[tests.py:39](experimental/gsc1/tests.py#L39) initial 的 exact port lookup 空，[145](experimental/gsc1/tests.py#L145) 核对派生 binding 的根/支持；不是借 tuple key 的 novelty |
| C2 | PASS | 每个 binding 的全部 direct supports、H_i/D_i/declaration roots 都保留；既有 A.p0 是 PROP-ALIAS(Bind(h0,A0),Eq(h0,p0))，另有已存在 binding 的 reflexive 循环支持；循环不是首次生产见证 |
| C3 | FAIL | 此 O 的新内容是已有 routing 下的单个/三个独立赋值关联，没有在 binding 对象间产生新组织关系。它的 Eq 路由是输入，不是由这些 bindings 组织形成的边；上游 Composite 不在此 O 内 |
| C4 | PASS | checker 实际按 exact variable 读取这些 Binding，决定 0/1/>=2 的端口状态以及 tuple 能否形成；不是仅拿删除 H/D 后对象不生成作证 |
| C5 | FAIL | D_i 明确规定内部 h_i 到目标 p_i 的对应，直接参与本 O 生产；源头是固定 zip mapping。这是对本对象具体 target 的规定，与上游动作只是被如实记录的情况不同 |

C4 四类比较：实际读路径为 Binding.variable/value→checker bindings map→cardinality→fields；相同 current/domain/schema 下 A/B 的 binding keys/value 和 roots 支持内容改变；逐 H_i 或 D_i 消融时只有对应 p_i.values 空，其余端口仍 GROUNDED（[tests.py:61](experimental/gsc1/tests.py#L61)、[71](experimental/gsc1/tests.py#L71)）；冲突保留两个值并不生成完整 tuple（[81](experimental/gsc1/tests.py#L81)）。可形成输出结构改变，但路由和消费者组织没有改变。读源码和 exact port 断言证明生成后的 Bind 确实被消费；root 消融本身仍仅证明生产依赖。

既有 A/B tuples=(A0,B0,C0)/(A1,B0,C1) 是该实际读取的下游结果，不能只凭这两个最终值判 C4。此 PASS 不等于行为作者权或 tuple 自己的后续效力。

### 3.6 O-G1-2

| 标准 | 裁定 | 同对象的证据与限制 |
|---|---|---|
| C1 | PASS | 前态无完整 tuple，checker 构造新的 schema_key+fields；[tests.py:33—45](experimental/gsc1/tests.py#L33) 核对实际完整对象/缺失对象。不能仅用新 p Bind 通过 |
| C2 | PASS | 限于同次 GroundingResult+schema/closure 上下文：tuple.schema_key 明确 field→Variable/type，对应 PortAssessment 的 exact binding_key/全部支持/roots 可回溯，构造器机械组装 singleton。包装来源包括外部 schema 与输入 binding，不能只列 H/D 根。仅导出 tuple 而丢弃伴随 evidence，不具有此完整证据范围 |
| C3 | FAIL | 固定 schema tuple，没有新成员间组织关系；名字/类型/字段对应事先给定。将上游的 Shared/Composite 组织性移到这里不合法 |
| C4 | FAIL | 在当前实现范围内没有生产性后续消费者：只被测试比较和报告序列化。checker 重算时读原 closure，而不是读上次 tuple；[tests.py:171](experimental/gsc1/tests.py#L171)、[179](experimental/gsc1/tests.py#L179)；纯审计读取/新日志不满足冻结 C4 |
| C5 | FAIL | 本对象的具体 field→Variable 对应由 fixture 的 OutwardSchema 预先配置，checker 按该对应填字段；属于冻结标准中的预设变量/slot 对应。不因为上游 Eq 外部就自动 FAIL，当前对象自身的具体字段寻址是独立证据 |

C4 四类比较：测试/`grounding_record` 的确读 tuple.fields/key，不能说“完全没有 reader”；这些只核对/输出审计。没有后续计算依赖路径读 tuple 生成新 Binding/Composite/问题，没有旧 tuple 保留后被读取，没有因 tuple 自身改变而变化的可形成结构或 body/action。历史/输入消融改变其生产是否成功，但不证明生产后的 O 有效。当前已知实现缺失这种消费者，因此本项 FAIL，不是因为没重跑就判 FAIL。

C5 要把两层路由分开：

1. O-G1-1 的 h_i→p_i 是 CurrentInput 指定的结构边。
2. O-G1-2 的 required field name→exact p_i Variable 是 [fixtures.py:23—24](experimental/gsc1/fixtures.py#L23)、[OutwardSchema.key](experimental/gsc1/model.py#L19) 提供的具体组织对应；[grounding.py:31](experimental/gsc1/grounding.py#L31) 和 [54](experimental/gsc1/grounding.py#L54) 将对应贯彻到 fields。合法类型/namespace、纯字段名字和 singleton 解包本身允许；**具体把哪个 Variable 放进哪个 required slot**不是仅有类型约束。

通用 `check_grounding` 不选兼容值、不 fallback，包装规则本身没有值 selector。审计对象却是此具体配置产生的 tuple，而不是只抽取通用 formatter；所以不能把 formatter 的干净机械行为拼成整个对象 C5 PASS。没有证明 tuple 发明了字段对应；它也没有自行引入新的 h→p 路由。该项保持 FAIL，理由与旧审计的主要证据不同，旧的对象混用仍须撤回。

## 4. Object-level matrices

每一行固定为上文同一 O。PASS 均受所列有限 fixture/生产/消费者范围限制；同机制不同 O 的分数不得拼成“新组织整体通过”。

| Object | C1 Novelty | C2 Provenance | C3 Organization | C4 Causal efficacy | C5 Non-prescription |
|---|---|---|---|---|---|
| O-F1 temporal relation instance | PASS | PARTIAL | FAIL | PASS | PASS |
| O-F2 deployed formal behavioral pipeline | FAIL | PARTIAL | FAIL | PASS | FAIL |
| O-G0-1 derived structural graph | PASS | PASS | PASS | PASS | PASS |
| O-G0-2 Composite | PASS | PASS | FAIL | PARTIAL | PASS |
| O-G1-1 outward-port bindings | PASS | PASS | FAIL | PASS | FAIL |
| O-G1-2 GroundedOutwardStructure | PASS | PASS | FAIL | FAIL | FAIL |

O-G0-1 的五项限定 PASS 不表示“新的组织方式”、完整 behavioral authorship、自主 linkage discovery 或 upward recursion；它证明的是由已声明输入经通用规律形成并实际使用的显式组织图实例。本轮不改变任何旧 prototype 验收标签。

## 5. Mechanism-level summary（不重新压成五格总分）

| 机制 | 各对象分别已经证明什么 | 没有证明什么 |
|---|---|---|
| FormalL0 | O-F1 形成新的 temporal association，后续确实读关系；其生产器未预写具体 outcome。O-F2 的固定管线确实执行动作，外部 sampler/binder 可追 | relation 的新组织形成；管线由历史生成；关系决定动作；完整 relation 支持图 |
| GSC-0 | O-G0-1 生成有明确连接/约束、来源、真实消费者的有限组织图实例；O-G0-2 新建 canonical 集合并保存完整 COMPOSE 来源，存在 members/索引读子证据 | 裸 Composite 自有新拓扑/组织约束；Composite 独立改变闭包规律；新组织方法；初始 Eq 作者权内生 |
| GSC-1 | O-G1-1 从 history+external Eq 形成新的 p Bind，被 checker 消费；O-G1-2 新 tuple 有可追溯的 singleton 包装内容 | target linkage 自主形成；tuple 自有新组织关系；tuple 驱动后续递归；具体字段对应由历史发现 |

这些对象没有一个统一的历史生产/消费边界，不能继续把每个机制压成一行五格并沿用旧“共同缺口”。这是范围校准，不是另一个总体 prototype 验收。

## 6. 对旧判定的处置与共同项

**可以原样保留，但只归到明确对象：** O-F1 的 C1 PASS、C2 PARTIAL、C3 FAIL、C4 PASS；O-G0-2 的 C1/C2/C5 PASS；O-G1-2 的 C1 PASS、C3 FAIL。原来的混合 C2 在分对象后可得到相同 PASS，但必须分别明确其支持图和伴随包装来源。上述相同分数不意味着十五格原表全都范围正确。

**必须撤回原混合判定或重新限定：**

- FormalL0 C5 FAIL 不能评价 O-F1；它仍适用于 O-F2。O-F1 本轮为 PASS，外部 action 来源仍明确记录。
- GSC-0 原 C3 PARTIAL 使用另一对象的 Shared 子证据；本轮显式图 O-G0-1 为 PASS，裸 Composite O-G0-2 为 FAIL。没有把“不能重写方法”当作图 C3 失败理由。
- GSC-0 原 C4 PARTIAL 不能混用图级强因果证据；O-G0-1 为 PASS；O-G0-2 仍 PARTIAL，但依据只剩本对象 members/索引的真实读路径及明确欠缺。
- GSC-1 原 C1/C2 的两对象合评分撤回为两行各自的限定 PASS；不能只追 Bind 的根就宣称包装来源完整。
- GSC-1 原 C4 PARTIAL 撤回：Bind O-G1-1 为 PASS；tuple O-G1-2 为 FAIL，不能借前者的消费者。
- GSC-1 原 C5 的 Eq routing 证据只直接判 O-G1-1 FAIL；O-G1-2 另依据具体 schema 字段寻址判 FAIL。**分数相同，不表示旧证据可原样移用。**

**对象一致后，旧的“共同最早未解决项”不再存在。** 冻结 CO-WAC-1 将它定义为三机制都非完整 PASS 的最早列；现在没有合法的统一三机制五格表，所以其原汇总前提已经失效。若仅作透明的对象级交集核对，六行中也不存在所有对象都非 PASS 的一列，因为有限范围的 O-G0-1 各项均 PASS。不能事后只挑 Composite/tuple 行，制造一个看似共同的 C3 缺口，也不能修改冻结标准把“任一行非 PASS”改成“共同”。

多个对象仍有 C3 缺口，不等于三个机制整体共享一个统一 C3 判定；这是不同命题。O-F1 的 C2 也仍未完整验证，O-G1 的具体路由和 tuple 的生产性消费者缺失各有独立证据。此处仅报告证据范围，不据评分设计机制或提出解决方案。
