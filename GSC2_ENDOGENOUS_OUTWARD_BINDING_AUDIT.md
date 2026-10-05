# GSC-2 — Endogenous Outward Binding Design Audit

日期：2026-10-05。范围：设计审计，不实现、不运行新实验。

冻结基线：

- GSC-0：`8801ca88093e5c66fa11ba6eb4c084608a1bd690`。
- GSC-1：`716d2d905feedaa0d565e297cb5b2985a9222149`。

本轮只新增本文件。未修改两套原型、测试、规格、验收报告，也未修改 FormalL0、Minecraft、正式 A、配置或数据库。结论依据实际规则代码与既有 GSC-1 验收数据；未新增或运行 GSC-2 runtime prototype。

## 1. 核心结论

**CURRENT_GSC_CANNOT_ENDOGENOUSLY_FORM_OUTPUT_LINKAGE**

适用前提是：outward port 有独立的 exact Variable 身份；全部历史和当前合法输入中，没有连接其与内部绑定变量的 equality 路径，没有其直接 Bind，也没有通过相同身份、Reference target、schema 变量别名或预设 routing 偷带连接。

GSC-0 能闭合已有 identity/equality、传播已有值、记录冲突并生成连通材料的 Composite。它没有首次生成组织局部角色分配或新的跨分量连接的规则。GSC-1 只检查已完成 closure 的绑定数，不能补这个缺口。

**干净的 GSC-2 生成规则仍为 UNRESOLVED；目前不宜进入原型实现。** 这是对当前规则集的确定结论，以及对未来设计尚未解决的判断；不是对所有可能的纯结构系统作不可能性宣判。

## 2. 三个不同的问题

| 问题 | 所需因果解释 | 当前实际范围 |
|---|---|---|
| Value formation | 值或新绑定内容为什么出现 | GSC-0 的 primitive Value 来自声明有限域和输入；可形成新的 Bind/组织。GSC-1 的 A0/A1 等由历史 fixture 给出，不证明创造新 primitive value |
| Port grounding | 指定 p 是否恰有一个合法值 | GSC-1 已验证：COMPLETE closure 中 0/1/>=2 个值分别为 UNRESOLVED/GROUNDED/CONFLICT；所有端口 singleton 才包装 |
| Port linkage formation | 内部 X 为什么与指定 p 发生关系 | GSC-1 的当前输入直接提供 Eq(h_i,p_i)，没有验证这条连接的内生形成 |

因此，可以保留 GSC-1 已通过的“历史依赖的新输出绑定与唯一 grounding”，但不能把它解释为新 primitive value 的自主创造，或 internal-to-outward linkage 的自主形成。本审计不撤销冻结验收，只限定其证明范围。

## 3. 实际代码逐项审计

下列位置均指冻结源码；行号用于定位实际规则，不根据注释或目标替实现作结论。

| 能力 | 实现位置 | 实际产生内容 | 能否首次形成内部↔outward linkage |
|---|---|---|---|
| Difference | [gsc0/model.py:176](experimental/gsc0/model.py#L176)，`difference` | 精确比较输入记录，产生 Difference notice 和当前已有事实；新来源加入同一事实的支持 | 不能。若当前记录含 Eq/Bind/Reference 到 p，则连接已经由输入提供。Difference 不发明连接；notice 本身无 Node incidence |
| ALIGN-REFL | [gsc0/engine.py:288](experimental/gsc0/engine.py#L288)，`Engine.consequences` | Declared(a) → Eq(a,a) | 不能。声明 p 只产生 Eq(p,p)，不产生 Eq(X,p) |
| ALIGN-SYM | [gsc0/engine.py:292](experimental/gsc0/engine.py#L292)，`Engine.consequences` | 反转已有 Eq | 不能跨越此前不同的 equality 分量 |
| ALIGN-TRANS | [gsc0/engine.py:294](experimental/gsc0/engine.py#L294)，`Engine.consequences` | 串联已有 Eq(a,b)、Eq(b,c) | 可产生此前未存储的 Eq(a,c)，但两端已通过既有路径连接；不是首次连接两个分量 |
| PROP-ALIAS | [gsc0/engine.py:300](experimental/gsc0/engine.py#L300)，`Engine.consequences` | Bind(x,v) + Eq(x,y) → Bind(y,v) | 需要已经成立的 Eq；不能决定 y 应为哪个 outward port |
| PROP-PORT | [gsc0/engine.py:306](experimental/gsc0/engine.py#L306)，`Engine.consequences` | 在输入 Relation 已有变量/Reference target 端口上形成 PortBind | 不创建 Relation 端口，不把一个端口的值转到另一个不同变量，不产生 Bind(p,v) 的独立来源 |
| Conflict | [gsc0/engine.py:315](experimental/gsc0/engine.py#L315)，`Engine.consequences` | 同变量两种 Bind → Conflict | 不生产新的 Eq、角色或 routing；保留所有绑定，不解决冲突 |
| Shared incidence | [gsc0/engine.py:377](experimental/gsc0/engine.py#L377)，`Engine.run` | 检查已有 Eq，记录共享 leaf/端口 witness | 只有已有 Eq 前提满足才添加 witness；不会因为需要输出而发明 Eq |
| Composition | [gsc0/engine.py:393](experimental/gsc0/engine.py#L393)，`Engine.run`；[gsc0/model.py:127](experimental/gsc0/model.py#L127)，`Composite` | 全部合法连通 leaf 集合及全部直接 COMPOSE 支持 | 不能从 Composite 反向推出新 Eq、Bind、业务 Relation 或角色事实 |
| Closure | [gsc0/engine.py:320](experimental/gsc0/engine.py#L320)，`Engine.run` | 对这些规则完整饱和，资源不足明确 incomplete | 不增加规则表达能力。更多轮次、Composite、CPU 或容量不能补一个不存在的生产规则 |
| GSC-1 checker | [gsc1/grounding.py:8](experimental/gsc1/grounding.py#L8)，`check_grounding` | 读取 exact Variable 的 Bind，计数后包装 singleton | 不读取 Composite 来解释新角色；不会生成或搜索连接 |

Reference 按 [gsc0/model.py:51](experimental/gsc0/model.py#L51) 的声明 target 解析；[gsc0/model.py:203](experimental/gsc0/model.py#L203) 的 `incidence` 只读取原端口/target。用 Reference 包装 `target=p` 并不让 routing 变内生，它只是另一种外部连接表示。

## 4. 当前规则集的边界证明

设 E0 是全部合法 seed/历史/当前输入中的 compatible Eq 加 exact identity。E* 是其等价闭包。设 B0 是全部输入根中的普通 Bind。

1. ALIGN-REFL/SYM/TRANS 只计算 E*。它们可以补全已有分量内部的边，但不能合并原本不连通的 identity 分量。
2. 对任何派生普通 Bind(y,v)，都存在输入 Bind(x,v)∈B0，且 x E* y。归纳依据是 PROP-ALIAS；其余规则不产生普通 Bind。
3. 若 p 所在 E* 分量没有输入 Bind，则所有轮次都没有 Bind(p,v)。Eq(p,p) 和循环 proof 不构成无输入根的值生产见证。
4. PROP-PORT 依赖已有 Relation 和已有普通 Bind。它生成的是该现成变量端口的 PortBind；没有 PortBind→Bind 或 Relation 任意跨端口传值规则。
5. Shared/Composite 只记录已有 incidence 的组织，不进入 `Engine.consequences` 的 Bind/Eq 生产前提。饱和更多 Composite 不改变第 2 点。
6. GSC-1 看到 p 的 Bind 集为空，只能返回 UNRESOLVED；不能用 Component、相同 type、名字或历史值补齐。

这里必须检查 **完整路径**：没有一条直接 Eq(X,p)，不代表不存在 Eq(X,Z)、Eq(Z,p) 的绕行。若绕行存在，GSC-0 可以推出 Eq(X,p)，但 linkage 的路径早已来自输入，不能作为首次内生形成的证据。

一般 Relation(X,p) 也不自动等于 equality：它可提供一个输入的拓扑连接，使相关材料进入同一 Composite，但当前规则仍不会因此把 Bind(X,v) 复制给 p。结构相连、身份相同、值转移是不同机制。

在本轮更强的隔离条件下——没有 Eq 路径、p 的 Bind、含 p 的跨内部 Relation、指向内部/输出的预设 Reference 或同身份别名——跨边界首次连接没有生产规则。此结论由正向规则归纳得出，不依赖某次运行有没有偶然找到输出。本轮没有运行新闭包或声称获得 GSC-2 实测通过。

## 5. GSC-1 explicit routing 的作者权

[gsc1/fixtures.py:18](experimental/gsc1/fixtures.py#L18) 声明 h0/h1/h2 与 p0/p1/p2 为同 namespace/scope 下的普通 Variable，但身份分别独立。[第 29 行](experimental/gsc1/fixtures.py#L29) 明确执行：

```text
CurrentInput = {Eq(h0,p0), Eq(h1,p1), Eq(h2,p2)}
```

生成过程使用 `zip(sources, outputs)`，因此 **h_i→p_i 的 correspondence 由 fixture 作者固定提供**。这些值不是从 Composite 内部角色生成的。

既有 [GSC1_PROTOTYPE_VALIDATION.json](GSC1_PROTOTYPE_VALIDATION.json) 中，A 的 p0 记录为：

- 值：TypeA/A0；binding key：Bind(p0,A0)。
- 非声明输入根：H0 与 D0。
- 有生产能力的直接支持：PROP-ALIAS(Bind(h0,A0), Eq(h0,p0))。
- 另一个直接支持为自身 Bind(p0,A0) 与 Eq(p0,p0) 的循环传播。它保留了来源图，但不能替代 H0/D0 的有限生产见证。

GSC-1 的 `test_current_input_ablation_each_port_both_histories`（[tests.py:71](experimental/gsc1/tests.py#L71)）已在两个历史分别删除三个当前 Eq 后重建 closure；对应端口变 UNRESOLVED。既有报告记录其通过，本轮没有重跑或改写该报告。

| 项目 | 分类与解释 |
|---|---|
| ALIGN/PROP 固定规律 | EXTERNAL_FIXED_MECHANISM；对全部满足条件的前提运行 |
| fixture 里的具体 Eq(h_i,p_i) | EXTERNAL_STRUCTURAL_ROUTING；明确属于 EXPLICIT_FIXTURE_INPUT，不是内部生成连接 |
| 在 GSC-2 条件下沿用固定 h_i→p_i | EXTERNAL_FIXED_POLICY / external policy contamination；它预先决定了路由目标 |
| GSC-1 singleton checker | 机械基数检查与包装，不从多个值中择一 |

**Q1：是否必要？** 对当前 GSC-1 fixture，三条 Eq 是各输出值到达 p_i 的必要连接输入；“必要”是相对此 fixture，不是所有未来结构模型都必须使用 Eq。其他预接好的 alias/path 也可能传值，但不因此成为内生连接。

**Q2：是不是 selector？** 不是 GSC-1 运行中的值 selector：没有比较多个绑定、排序后取一个或淘汰冲突。它仍是外部 routing 决定，指定哪个内部变量属于哪个输出目标。因此“无值 selector”不能推出“连接作者权属于内部结构”。GSC-1 没有解决 endogenous behavioral authorship，也没有实际行为执行。

## 6. 缺失的因果边

当前实有链：

```text
历史 Bind(h,v) + 外部提供的 Eq(h,p)
→ 固定 PROP-ALIAS
→ 新 Bind(p,v)
→ 唯一性检查
→ outward tuple
```

缺失链是：

```text
历史与当前输入形成的新组织 K
→ 为什么 K 中某成员承担某个 outward port 的角色？
→ 可追溯的新 linkage
```

仅知道某值唯一，不回答它应属于哪个 p；仅知道 X 与 p 类型相容，也不回答二者为何新发生连接。把这个判断藏进 schema resolver、packer、Reference constructor、decoder 或 adapter，仍然是外部 routing。

## 7. Flat Composite 的准确限制

Composite 的 identity 是 `("Composite", sorted flat leaf-key set)`；`__post_init__` flatten、去重，`CompositionIndex.shared` 保留全部原 leaf 端口之间的 Eq incidence witnesses。

它能表达新的成员组织，保留原关系的 ordered ports、既有拓扑、alias 证据和所有生成支持；不能说它“完全没有内部 topology”。

但当前构造没有生成以下内容的字段或规则：

- 组织局部、具有 K scope 的成员角色。
- K 中新产生的 member→slot incidence。
- 保持 X 全局身份不变，同时让 X 在 K 中承担 outward.p0 的局部角色。
- 同一成员集合在两个组织里具有不同角色/拓扑配置的独立组织 identity。
- 可参与后续递归的嵌套组织边界；已有 Composite 总被 flatten。

在当前表示里，若两种角色配置的 leaf 集合完全相同，Composite identity 会合一；`shared` 的增加只记录已成立 Eq，不是任意新 role assignment。`Engine.consequences` 也不消费 Composite 来生成角色或新 topology。

**Q3：是否缺 role assignment / topology reconstruction？** 是，缺少新角色/新边的生产与组织局部表示；但已有 incidence/topology 的保留和新支持集合的组织能力确实存在。

这不是“任何 flat set 数学上都无法编码 topology”。如果有 Role/Incidence edge facts，它们可作为不同 leaf 进入集合。但当前规则没有生产这些事实；直接把它们作为输入放进去，仍是预建角色。仅扩充数据格式、添加字段或取消 flatten，也不会自动生成干净 linkage。

## 8. 最小缺失结构与候选研究方向

**Q4：最小缺失项至少有两层，不能只改一个容器字段：**

1. 表示能力：可追溯、组织局部的 typed member/role/slot incidence；能区分角色配置，不把“承担一个角色”强行写成全局身份 Eq。
2. 生成机制：哪些纯结构前提使这样的 incidence 首次成立，且不是预写 X→p mapping。其来源、有限域、canonical identity、局部性、冲突、饱和与资源中断语义必须可审计。

这只是缺口描述，不是已确定的新签名或可实现规则。固定 outward schema 的端口声明可以作为接口能力边界保留，但不能偷偷在声明中给出 member correspondence。新局部 slot 如何成为既定外部端口的一部分，仍是需要证明的因果边。

| 方向 | 可研究价值 | 尚未解决的问题与污染风险 |
|---|---|---|
| A. outward 与内部同质 | GSC-1 已将两者声明为普通 Variable；可避免另一个特殊推理模块 | 同类不等于同身份、不意味着相连。直接让 p 与 h 共用 identity，是把 mapping 移到声明处 |
| B. 内容无关、local、confluent 的结构规则 | 研究是否能由已有局部组织条件生成新的 incidence，且全部合法后果保留 | 尚无干净规则。same type/唯一 compatible 对象就转值仍可能是外部 routing；confluent 不证明作者权 |
| C. linkage 是组织内角色，而非 Eq | 可能保留 X 的身份和组织局部角色，避免角色承担与全局同一性混同 | 写入 Role(K,X,p) 只命名了答案；仍须解释该边的生产前提及与既定 p 的联系 |
| D. outward relation 作为普通递归材料 | 使 typed 端口及角色关系可被记录、组合、递归检查 | 把 Relation(...p...) 预输入会预接 topology。裸 schema 的接口声明与特定 X→p 连接必须分开；本轮隔离条件不能借此绕过 |
| E. 保留组织配置/局部 topology | 有机会表达相同成员的不同角色组织，区别于 flat membership | 仅增加嵌套或 richer identity 不决定角色；还须证明有限 canonical closure、来源完整、无外部择一 |

**Q5：能否不加 semantic inference/selector/reward/priority/optimization？** 当前不能确认一个满足全部条件的方案。新的纯结构规则可以在原则上研究；没有证据允许声称已找到或不可能找到。机制必须接受结构反例，而不能为期望 tuple 定做。

## 9. 对称性、局部性与唯一性的诊断

若 p 与内部材料没有任何已有局部关系，严格沿现成 incidence 执行的局部规则无法跨两个独立分量建立第一条边。让规则读取全域寻找 compatible 对象，是另一项机制；不能以“无比较分数”为由直接称其内生。

对纯内容无关的规则，应检查一致重命名 exact IDs 和 opaque 值标签后的等变性。在具有可交换内部材料的对称输入里，若不存在区别其与 p 关系的结构证据，单独指定一个来源可能打破该对称性。按编码、hash、名字、插入次序或类型编号打破对称性，就是隐藏 routing。

保留全部对称 linkage 假设也不自动成功：它可能给同一 outward port 带来多个不同值，正确结果仍为 CONFLICT；如果保留不同组织配置，decoder 不能挑一个配置输出。相同值的多个支持可计为一个值，但不能因此虚构产生这些 linkage 的规则。

这些是未来候选的检验条件，不是本轮新增算法或对全部系统的不可能性证明。环境/历史若提供真实的结构不对称性，仍需明确其与端口发生关系的规则，不能借“不对称”代替因果推导。

## 10. External policy contamination 清单

| 等价方案族 | 本轮判断 |
|---|---|
| nearest、first compatible、latest、most frequent、highest weight、random compatible、output candidate ranking | 直接择一；禁止 |
| same type → choose one | 类型只证明合法性，不授权指定对应；禁止 |
| same type → broadcast 全部值 | 虽未择一，但预定义向哪些输出转值；不能作为内生连接证明，还可能全部冲突 |
| hash(value)%port_count、history hash routing、canonical-first、stable-ID 排列 | 用编码/历史标识替代角色因果；确定性不等于内生；禁止 |
| fixed h0→p0/h1→p1、同编号/同名字段配对、单一类型为每对变量专设通道 | 外部固定 mapping，可隐藏在 schema、signature 或构造器中；禁止冒称生成 |
| position→move 等 semantic mapping | 提供业务解释和目的地；禁止 |
| learned Q/value/reward routing、utility/optimization | 学习形式不消除奖励/目标路由作者权；禁止 |
| external planner、LLM selector、matching historical action templates | 外部答案/目标选择；禁止 |
| Reference(target=p)、把 schema 直接指向已绑定 h、预置 Role/Relation(X,p) | 预接线或 identity alias；换表示不改变来源 |
| 枚举所有 role assignments 后挑唯一“可用”组织、packer 自动 normalize/repair | 可能把 selector/补值挪到 result adoption；除非唯一性本身有完整结构证明，否则不能通过 |
| 从 Composite.shared/lineage 里取第一条路径决定输出 | proof 选择不等于角色生产；来源顺序不能赋予角色 |

“类型兼容”“每端口已唯一”“闭包顺序无关”各有必要性，但都不能单独证明 linkage endogenous。全部规则可穷尽执行，也可能穷尽执行一个外部预设的 routing policy；必须审计规则的目标关系，而不只检查是否使用排名。

## 11. 最终裁定与下一步

| 要求 | 裁定 |
|---|---|
| Current GSC capability verdict | CURRENT_GSC_CANNOT_ENDOGENOUSLY_FORM_OUTPUT_LINKAGE；受第 1/4 节前提约束 |
| GSC-1 explicit routing classification | fixture 人工提供的 external structural routing；不是运行中的值 selector，在 GSC-2 目标下是 external policy contamination |
| Missing causal edge | 新组织 K → 组织局部成员承担指定 outward port 角色 → 新 linkage |
| Flat Composite limitation | 能组织并保留既有 incidence，不能生产新局部角色/边或区分同成员的角色重构 |
| Candidate structural directions | 同质端口、组织局部角色、可递归接口结构、richer topology；均为研究方向，不是已证明规则 |
| Clean prototype currently justified | **否。GSC2_DESIGN = UNRESOLVED；不标记 prototype passed，也不实现原型** |
| Recommended next step | 先做一个独立 role/incidence 表示与生成规则的纸面规格及污染审计，再决定是否值得实现 |

下一轮纸面设计至少应给出：组织局部角色的 identity/类型/支持、具体首次生成 linkage 的纯结构前提、接口角色与内部角色的边界、有限性/单调性/合流性依据，以及无法唯一确定时完整保留冲突的协议。必须用断连、对称双来源、重命名、同类型多变量、相同成员不同角色配置、历史/当前输入消融等反例检查，不预置期望 routing。

在这些问题解决前，**Q6 的答案是停在 unresolved**。不修改冻结 GSC-0/GSC-1，不把推测的 Role 字段、新的 Eq 或更多 Composite 数量当成已经找到的干净解决方案。

## 12. 本轮验证边界

本轮重新读取实际源码、GSC-1 规格和既有 JSON 中的具体支持。既有 JSON 的 21 项 GSC-1 与 23 项 GSC-0 回归通过是冻结结果，不是本轮新执行记录。

未运行 closure、测试、Minecraft 或正式 A；没有新增 experimental/gsc2、runtime、rule、fixture、数据库或配置。只新增本审计文档，并在提交前后核对 GSC-1 基线的 133 个既有 tracked 文件字节 hash。审计提交 SHA 在最终交付消息给出，避免将文档自身 commit 写入自身造成自引用。
