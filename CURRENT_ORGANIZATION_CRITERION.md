# Current Organization — Working Acceptance Criterion

> **CURRENT STATUS NOTICE (2026-10-05):** CO-WAC-1 itself remains the frozen working criterion. However, the mechanism-level matrix and the "共同最早未解决项 C3" summary in §9 are **historical results from the original mixed-object audit**. `CURRENT_ORGANIZATION_SCOPE_AUDIT.md` later enforced same-object scope and supersedes that summary for current interpretation. In particular, O-G0-1 is currently C1–C5 PASS within its finite TEST_ONLY scope. Do not rewrite the frozen criterion or delete the historical matrix; use `RESEARCH_STATUS.md` for the current project state.

版本：CO-WAC-1。冻结日期：2026-10-05。适用仓库：beca-minecraft-experiment。

本文件冻结 **C1 Novelty、C2 Provenance、C3 Organization、C4 Causal efficacy、C5 Non-prescription** 五项实验工作标准。它们用于比较本仓库机制的证据范围，**不是 Perfect Recursion 的普遍公理、理论定义或充要条件**，不修改理论仓库，也不改变既有实验的原验收规格。

后续若调整标准，必须显式给出新版本；不能为了某个机制取得 PASS 临时降低判据。本轮审计使用本版本，[CURRENT_ORGANIZATION_AUDIT.md](CURRENT_ORGANIZATION_AUDIT.md) 给出证据与分项裁定。

## 1. 审计单位与四种状态

每个机制先明确：被测结构 O、生成前状态 H、当前输入 I、固定解释器/类型/环境约束 M，以及实际消费者。不能用某个叶事实的通过替代整个组织的通过，也不能用全系统标签否定已证明的局部作用。

| 状态 | 意义 |
|---|---|
| PASS | 在明确限定的对象/条件内，实际源码和已有可核对证据满足本项；不表示普遍成功 |
| PARTIAL | 有本项实质子证据，但主被测结构或完整范围尚未满足；必须指出成立与欠缺分别是什么 |
| FAIL | 代码/反事实给出与本项要求直接相反的行为或明确实现限制；不是仅因没测试就 FAIL |
| UNRESOLVED | 缺少可裁定的直接证据，既不能确认成立，也不能确认实现必然不成立 |

五项独立评分，不互相代替；特别是 C4 的关系实例效力可以得到限定 PASS，而 C3 的组织形成仍 FAIL。整体“新因果有效组织”至少需要同一被测对象在 C1—C5 的相应范围同时满足，不能拼接五个不同对象的局部 PASS。

证据区分：实际读取的源码、既有测试的具体断言、既有机器记录的具体值、本轮静态推导。旧 README/审计/报告的 overall PASS 不是本标准的评分依据。仅存在一段测试代码不等于本轮执行过；已有报告可以证明其记录的执行范围，不能补全未断言的性质。

## 2. 五种“新”的层次

| 层次 | 定义 | 不能自动推出 |
|---|---|---|
| 新记录 | 新事件、时间戳、UUID、计数或同内容的额外来源记录 | 新关系、新组织 |
| 新关系实例 | 此前不存在的有内容的绑定、依赖、关联或约束实例；可使用固定通用签名 | 新的组织方式、理论升层 |
| 新 Composite/集合包装 | 新成员集合、连接支持集合或固定 schema tuple | 组织自身已有后续因果效力 |
| 新的因果有效组织 | 成员之间的组织关系有明确内容、来源，其组织本身参与后续处理并产生可定位效力 | 已改变解释器或形成更高层 |
| 新的组织方式 | 组织关系、协调/表示/处理方法本身出现可追溯变化；不是只换成员/填参数 | 自动等于 L1、维度变化或 Perfect Recursion 已被验证 |

这是证据分类，不要求每个实验都做到最后一层；但必须说清在哪一层成立。实例新颖性、组织形成、组织方式改变分别报告。

## 3. C1 — Novelty

**问题：O 的规范内容是否此前不存在，而非只是新的记录身份？**

PASS 需要生成前后可比较的实质内容，忽略运行 UUID、时刻、日志计数；旧原子材料可以组成新实例，不要求创造新 primitive value。固定通用语法所允许的未预存实例可以满足 C1；能满足 C1 不代表满足 C3/C5。

原样复制/重放完整答案、只增加计数或同结构不同 UUID 不满足。重复来源是 provenance 的增加，不自动算结构新颖。只比较 hash 没有核对内容时，限制必须列明。

证据：生成前不存在的具体关系/组织键及内容；测试对 before/after 的实际断言；已有轨迹里实质材料变化。反事实/消融可以支持 novelty 的依赖性，但不是 C1 唯一证明形式。

## 4. C2 — Provenance

**问题：O 的内容为何成立，能否沿实际生产支持追到历史、当前输入和固定/外部贡献？**

PASS 需要保留规范内容与生产 lineage 的区别、有限输入根见证和实际不同的直接支持。循环支持不无限展开，也不从空循环生成对象。全部直接支持可以用无损有限索引表示，不要求展开无限 proof tree。

固定机制、外部策略、具体 routing/input 的来源必须可辨认；放进 InternalState 不会改变作者权。仅附一个 integration ID、model hash 或 source 标签，不足以证明行为内容依赖于它。

对有界 active memory 与完整 journal 分开评价：active references 被容量阻止不等于历史日志已删除；但只展示计数/部分 refs，不能宣称已验证完整支持图。来源字段存在而没有完整核对时可为 PARTIAL，不能据此虚构 FAIL。

消融必须改变被说明的内容或依赖见证，并说明删除位置；不能删根材料后保留其派生 closure 再冒称来源无关。

## 5. C3 — Organization

**问题：O 是否具有新形成的组织关系，而非记录表的一行或固定 schema 的集合包装？**

PASS 需要明确的成员以及组织关系/约束/拓扑/依赖表达；组织内容不是仅由外部预设对应表填值得到；并能说明新形成的组织关系如何区别于单独材料和一般集合包含。使用通用关系语法、类型和机械组成规律本身允许，不要求新代码、自改解释器、角色机制或升层。

组织表达与因果效力分开：C3 检查组织关系本身，C4 检查其消费者。只有集合 membership 可为包装；带共享证据、连接结构的组合具有 C3 子证据，但不能未经核对就宣称组织方式改变。

既有 schema 内的新 relation row/outcome、flat support union、新字段 tuple，不自动满足完整 C3。保存了原有 incidence 不等于生成新的组织内关系；另一方面不能把保存了原关系/端口的 Composite 说成毫无拓扑信息。

“新的组织方式”是比组织实例更强的单列主张：必须指出什么组织规则/处理关系发生了变化；五项没有把这种变化强制等同理论 upward recursion。

## 6. C4 — Causal efficacy

**问题：被测 O 本身是否进入后续真实处理，使读取、依赖路径、约束或可形成结构有可定位变化？**

必须分别比较以下项目，而不是只比较最终输出：

1. **依赖路径：** 哪个执行函数实际读取 O 的哪个字段、键或组织关系？provenance 边与执行数据依赖不能混同。
2. **后续读取：** 固定当前输入/解释器/环境/初始化时，对 O 的替换、消融或对应历史变化是否影响 lookup 成败、读出的内容或处理分支？
3. **可形成结构：** 哪些绑定、连接、组合、过程状态或后续问题实际变得可形成/不可形成？哪些仍保持不变？
4. **输出：** 最终结果/动作是否变化？变化不能单独证明组织效力；不变化也不能否定已经观测到的内部读取效力。

限定 PASS 可以是明确读取/处理链的实例级效力，不要求所有项目都改变，也不要求一定改变动作。但必须检查并报告四类范围；对新包装只证明 constituent 的作用，主包装尚未作为组织被消费，整体可为 PARTIAL。

UUID 不同、hash 不同、单纯留下一条日志、资源占用变大、声明会影响行为，不足以满足 C4。拒绝运行的 RESOURCE_LIMIT 前缀不能当成 completed organization。仅移除输入前提使结果不出现，证明的是材料必要性；若要证明生成后的组织本身有效，必须有相应消费者证据，不能偷换对象。

## 7. C5 — Non-prescription

**问题：外部是否提前规定了具体答案、target correspondence 或采用哪种结果？**

允许：通用语法、精确身份引用、类型/作用域/资源约束、固定通用机械规律、无取舍的正向闭包、完整 canonicalization、singleton 检查、append-only 审计。固定解释器不自动等于外部策略。

必须标记外部规定：observation→具体答案的模板、固定 target routing、priority、reward、selector、fallback、nearest、first/latest/best、投票、随机选值/目标、hash-to-answer、预设变量/slot 对应、外部 planner。即使规则是确定性的、没有评分，固定对应仍属外部 routing。

普通外部观察/历史材料会影响生成内容，这不自动等于污染；要检查它是环境事实/通用身份材料，还是实验者已经填好的目标连接/答案。**explicit Eq(h,p) 若用于指定内部变量到 outward port 的对应，必须单列为外部 routing；唯一 grounding 不转移该边的作者权。**

按规范键排序保留全部项是编码；按该顺序只取一个是策略。hash 用于内容索引不等于 hash-to-answer；若未防碰撞，要报告表示限制而不是误判为 routing。缺失/冲突时拒绝完整输出不等于 fallback/NO_OP。

C5 PASS 仅指限定运行范围无这些外部答案/路由/采用规定；人工 fixture 的输入作者权仍须披露，不声称系统自主发现输入事实。已明确存在违规路由/selector 时 FAIL；核心机制干净而实际 pipeline 混入外部规定不能仅给核心 PASS 后掩盖总体限制。

## 8. 矩阵解释规则

矩阵顺序固定为 C1→C5。各机制的范围和局部限制必须在审计正文给出，矩阵不得替代证据。

“共同最早未解决的标准”定义为：在该顺序中，**三机制都尚未取得该项完整 PASS 的最早一列**。不是任意一个机制第一次非 PASS，也不是全体逻辑失败的证明。若不存在这种列，必须如实写不存在，不能调整判据制造共同结论。

本版本不据矩阵设计解决方案；标准与审计各自文件末尾给出同一个三机制×五标准矩阵和共同最早未解决项，评分依据在审计正文，不从原规格 passed 标签继承。

## 9. 本轮按 CO-WAC-1 得出的总矩阵

| 机制 | C1 Novelty | C2 Provenance | C3 Organization | C4 Causal efficacy | C5 Non-prescription |
|---|---|---|---|---|---|
| FormalL0 | PASS | PARTIAL | FAIL | PASS | FAIL |
| GSC-0 | PASS | PASS | PARTIAL | PARTIAL | PASS |
| GSC-1 | PASS | PASS | FAIL | PARTIAL | FAIL |

共同最早未解决的标准：**C3 Organization**。FormalL0 的 C4 PASS 限于关系记忆的真实读取效力；不能替代 C3，也不能拼接为整体新组织通过。此矩阵是 CO-WAC-1 的本轮工作审计结果，不是三套机制原验收的重新执行结果或 Perfect Recursion 理论结论；不据此提出解决方案。
