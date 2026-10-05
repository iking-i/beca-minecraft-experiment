# GSC-2 — Organization-Local Role Formation Specification

日期：2026-10-05。本轮是表示设计、候选规则审计和纸面 fixture 推导，不是实现或实测验收。

冻结：GSC-0 `8801ca88093e5c66fa11ba6eb4c084608a1bd690`；GSC-1 `716d2d905feedaa0d565e297cb5b2985a9222149`；GSC-2 audit `4fcc1bd54f1586110c76a036ec40a003a4238b0a`。

**GSC2_ROLE_FORMATION = UNRESOLVED。最终判定：UNRESOLVED。**

组织局部角色和区分 topology 的 identity 已有可讨论的表示方案；但没有找到同时满足本轮全部条件、能首次形成新 member→指定 slot 连接的干净规则。不会把下面被拒绝或仅用于重新表示的候选变成 runtime。GSC-0/GSC-1 的冻结通过结论不改变。

## 1. 表示的范围与禁止项

`Role(K,X,S)` 表示成员 X 在组织 K 的局部 slot S 上具有 incidence。它不表示 X 和 S 是全局同一对象，也不自动表示向外输出一个值。

必须分开：成员 identity、slot identity、organization configuration identity、Role 的输入根/直接支持。角色事实的名字、proof 次序、生成时刻和 UUID 不参与路由。Opaque identity 可用于 exact 引用和去重，**不能用其字面内容、固定编号或排序决定谁承担角色**。否则要求定义 identity 本身就会与禁止 routing 混淆。

fixture 允许声明有限成员、slot 的机械类型及组织作用域；不允许输入 Role、Eq(member,slot)、Reference(target=slot)、指定 member→slot 的表，或只换名字的 Assignment/Incidence 预接线。这里的 slot 声明只表达一个空位置存在，不附带成员、值、优先级或动作意义。

## 2. Organization-local 表示候选

引入以下**纸面**区分，不确定最终代码格式：

- B：稳定的组织作用域/载体锚点，来自合法有限条件；不是生成次序，也不暗含成员配对。
- M：组织成员的 exact identity 集合。
- E：实际结构材料及其原有 ordered port/incidence facts；保留原 occurrence identity。
- D：有限 slot declarations。每个 d 包含所属 B、opaque anchor 和机械 slot type；没有 member target。
- G：组织局部的 incidence topology，边是 `(member_key, slot_declaration_key)` 等明确声明的 typed 拓扑项。当前设计没有生产这些新边的已接受规则。

候选 configuration key：

```text
K = CanonicalOrganization(B, M, E, D, G)
LocalSlot(K,d) = ("LocalSlot", K.key, d.key)
Role(K,X,LocalSlot(K,d))
```

`K.key` 规范编码 B/M/E/D/G 的完整内容。Role 的编码是 K 的投影：K 的 G 使用 **d.key**，不使用含 K.key 的 LocalSlot；K 定义完成后才构造 LocalSlot/Role 的外层引用。这避免 `K 包含 Role(K,...)` 的递归自引用和无限 key 展开。

此处 Canonical 指 typed 集合的无歧义编码、exact 去重和完整内容相等；可以对集合键排序做序列化，但不能保留排在前面的成员。不能只信 hash，也不能为了消除名字差异而把不同 exact 成员 quotient 成同一对象。

| 必须回答的问题 | 本表示候选 |
|---|---|
| K 的 identity | 完整 configuration：B/M/E/D/G；不是单独 flat member set，也不是新 UUID |
| X 的 identity | 原有 exact Node/Variable identity 不变；角色不重命名或替换 X |
| S 的 identity | `LocalSlot(K,d)`；d 是有限、无目标的 slot declaration，S 是在 K 内的实例 |
| Role 有效范围 | 只在它指向的 K configuration 内；不能外推到其他组织 |
| 同一个 X 多个角色 | 可以在 K1 的 d0 与 K2 的 d1 上分别出现；没有跨组织统一规则 |
| 同成员不同 topology | G 不同则 configuration key 不同；旧 configuration 保留 |
| 同 topology 不同顺序 | 同 B/M/E/D/G 的任意构造顺序均得到同一 key；新支持并入原事实 |
| 继续参与 Closure | 表示上可作为有限 typed facts，理论上有此能力；但目前 GSC-0 不接受这些签名，本轮不添加 consumer/规则，因此尚未实现或证明 role closure |

新 evidence 只增加 lineage，不改变内容 identity。真正增加/改变 topology 则形成新的 configuration，不覆盖旧 G。B 是共同历史作用域，K 是不可变结构内容；不能把“同一个 B”与“同一个配置 K”混为一谈。

M/E/G 不是每轮覆盖的可变字段。未来若枚举可证明的有限材料支持，旧支持对应的全部配置必须保留；不能只构造“包含当前全部材料”的一个 K，再在输入增加时丢掉旧 K。表示方案只说明如何命名配置，不规定选择哪个支持或哪个配置。

## 3. 同成员、不同角色 topology

下列是**可表示结果的例子，不是输入 Role 的 fixture**。固定 B、M、E、D，其中 M 包含 X/Y，D 包含 d0/d1：

```text
G_A = {(X,d0), (Y,d1)}
G_B = {(X,d1), (Y,d0)}
K_A = CanonicalOrganization(B,M,E,D,G_A)
K_B = CanonicalOrganization(B,M,E,D,G_B)
```

在 X/Y/d0/d1 的 exact 身份保持固定时，`K_A != K_B`。交换边的生成顺序不改变 K_A。原材料、成员集合都相同，但组织内角色关联不同。

这解决的是表示区分；没有回答 G_A/G_B 的首次生成。同一个 X 可有 `Role(K1,X,LocalSlot(K1,d0))` 和 `Role(K2,X,LocalSlot(K2,d1))`，不得推出 Eq(X,S0)、Eq(X,S1) 或 Eq(S0,S1)。成员和位置是不同机械对象种类，Role 也不加入成员 equality 系统。

两个配置可能在忽略原身份的无标号图意义下同构，但不能因此把它们自动合并：配置 identity 必须保留 anchored member 和 slot correspondence。另一方面，对完整输入做一致重命名时，结果应按该重命名对应变换。这两个要求并不冲突。

## 4. 候选 first-generation 规则审计

### R-REIFY：把现成 incidence 显式化

纸面规则：

```text
Premises:
  Carrier(B,M,E)
  r 是 E 中的合法 relation occurrence
  r 的原机械 port i 的 exact target 是 X
  X 是合法成员
Conclusion:
  Role(K_occ, X, LocalSlot(K_occ, OccurrenceSlot(r,i)))
```

K_occ 的 topology 是全部原 relation ports 的 incidence 投影；OccurrenceSlot(r,i) 的身份由合法 occurrence 和原机械端口位置给出。原有 ordered port index 是关系结构的一部分，不是按成员名字排序所得的 routing 编号。Reference 若参与，只读其已合法声明的 target，不能新指向 S。

这里的 E 是某个不可变的、具有输入见证的材料支持，不是动态“最新全量 E”。记录支持的扩展可形成新 K_occ，旧 K_occ 不删除。若未来候选在同一步构造新 G 和 K，再投影 Role，其证明前提只能来自已成立材料，不能反过来用尚未生成的 Role(K,...) 证明自身；消除 key 自引用并不自动消除循环生产见证。

为什么前提足够：若此 Role 被**定义为现有 relation port 的 incidence 显式记录**，结论机械重述已经存在的结构，不查名字、不比较值、不选一个 proof。它可以是内容无关的表示机制。

为什么没有解决本轮问题：它不把 X 指派给此前独立声明的 d0/d1，也不形成此前不存在的成员—位置连接。它产生的是由 r/i 新标识的记录位置，连接内容已在 r 的原 port 中。把该 occurrence slot 再映射到指定 outward slot，会重新引入尚未解决的路由边。

**裁定：REPRESENTATION_ONLY，不是新 linkage 的合格 first-generation rule。** 输入已有关系不等于预输入 Role，但把已有端口重述为 Role，也不等于重构新角色拓扑。

### R-ALL：同域内全部成员与 slot 关联

```text
Premises:
  MemberOf(B,X)
  EmptySlotDeclaration(B,d)
  机械类型合法
Conclusion:
  Role(K_all, X, LocalSlot(K_all,d))  （所有合法组合）
```

前提只有共处一个 B 和类型合法，没有产生该 incidence 的实际组织原因。规则若把这些对作为实际 Role，会预设“同域/兼容就接线”；若只作为 RoleHypothesis，则仍未建立角色成立的证明。

**裁定：不是干净的实际角色生成方案。** 它虽没有 selector、可保持重命名等变性，仍不能用穷尽 broadcast 取代 linkage 作者权。若保留假设，必须完整保留，不能选一个配置输出。

### R-PATTERN：正向结构 motif 触发角色

用于检验的候选，**不接受为规则**：

```text
Premises:
  MemberOf(B,X)
  EmptySlotDeclaration(B,d)
  r: R(Z,X)
  t: T(Z,X)
Conclusion:
  Role(K_pattern, X, LocalSlot(K_pattern,d))
```

R/T 仅为 opaque relation signatures，Z/X 是变量，不是固定名字。匹配穷尽执行，可以不读名字、不排序候选，也无需“只剩一个”条件。

结构前提真正支持的结论是：X 参与这个 R/T motif；可以记录 PatternWitness(B,X,{r,t})。它们**没有说明这个 motif 为什么构成某个 d 的角色**。上式把 motif participation 变成 slot incidence 的那一步尚无依据。若只对固定 d0 触发，便把目标答案写进规则；若对全部 d 触发，则退回 pattern-gated broadcast。规定“这个 slot 的意义就是这个 motif”也必须审计该 role contract 是否预置了期望对应，而不能仅靠定义改名宣布内生。

**裁定：UNRESOLVED / NOT_ACCEPTED。** 这不是宣称所有 motif 规则必定污染，而是当前没有论证这些 premises 足以产生该 slot incidence。重命名等变性、D 依赖性和唯一匹配都不足以补上这一步。

### R-WIRE / R-UNIQUE：拒绝的捷径

```text
PrewiredIncidence(B,X,d) → Role(K,X,S(K,d))
唯一 compatible X → Role(K,X,S)
```

前者预输入了被禁止的 mapping；后者只回答候选数量，没有给出关联的生产依据。若唯一性依赖“不存在另一个候选”，还违反正向单调生成条件。first/latest/best、hash、固定编号、随机、语义用途和 reward 优化都不作为候选。

**本节没有被接受的新 member→指定 slot 生产规则。**

## 5. Fixture F 与重命名等变性

本节全部是纸面推导，无执行代码，无“测试已通过”的声明。

F 包含一个 B；同机械类型成员 X/Y/Z；独立空 slot declarations S0/S1；opaque values V0/V1。关系 R、T 的二元机械签名在条件中预声明，不含业务意义。

对称基础事实为两个 relation occurrences `r_x:R(Z,X)`、`r_y:R(Z,Y)`。X/Y 的历史、声明和来源支持成对同构；若加入值事实，用 Bind(X,V0)、Bind(Y,V0)，不以不同绑定值制造额外不对称。V1 可只在有限域声明。没有 Role、member-slot Eq、指向 slot 的 Reference 或 member→slot map。

一致重命名 ρ 示例：

```text
X→A, Y→B_member, Z→C
S0→Q7, S1→Q8
V0→W3, V1→W4
```

这里 B_member 是成员的新 opaque 标签，与组织 carrier B 不是同一身份。relation occurrence 和 source refs 也按同一全图置换规则对应变换；规则类型/机械 arity/type contract 保持对应。不能只改对象名却保留一个写死旧名的输入、support 或目标。

要求 `Rule(ρF)=ρ(Rule(F))`。opaque ID 置换是保持声明/type/关系结构的 bijection，不是交换机械类型或任意重排 relation 内部有序端口。

| 对象/候选 | 重命名的纸面结果 | 能否作为生成验收 |
|---|---|---|
| K/LocalSlot/Role 表示 | 集合内容整体对应重命名，边的 correspondence 不变；序列化顺序可变但不丢项 | 表示层等变性可由完整键定义推出，未实测 |
| R-REIFY | 原 r/i incidence 的对应记录整体重命名 | 可推导等变，但仅是既有 incidence 表示 |
| R-ALL | 全部 member/slot 对整体重命名 | 等变不等于干净，仍为未论证 broadcast |
| R-PATTERN | 正向 R/T 匹配 witnesses 随置换对应；没有 ID 常量 | 形式上等变；motif→slot 的生产依据仍未解决 |
| R-UNIQUE/lexical/hash/first 等 | 唯一性未说明生产；编码/顺序择一可被重命名反例破坏 | 不采用，不声称通过 |

不能要求“重命名后字节 hash 不变”。要求的是内容按照 ρ 对应，exact anchored key 正确改变；canonicalization 不得将重命名后的排序位置用于角色决定。

## 6. 完全对称 fixture

F 的自动同构 σ 交换 X/Y、r_x/r_y 以及成对的 source refs，固定 Z、S0/S1、类型和 V0；全部输入结构在该置换下保持不变。Slot 相对两者也没有区别性关系。

任何满足等变性的实际角色规则，如果产生 `Role(K,X,S)`，则相应结果必须也含 σ 对应的 `Role(σK,Y,σS)`。若 K 和 S 的配置本身在 σ 下固定，则必须同时产生 `Role(K,Y,S)`，不能单独指派 X。

若保留了两种不同配置 K_X/K_Y，σ 可以交换配置：必须完整保留其轨道，不能挑一个配置。不能把“结果分成多个 K”误写成同一个固定 K 下仍可破坏对称性的例外。

纸面结果：R-ALL 会允许两者；R-PATTERN 因尚无 T 关系不产生任何角色；R-REIFY 产生两条现成 relation occurrence 位置的对称记录，不产生目标 S0/S1 的角色。当前冻结 GSC-0 本身根本没有 Role 生产签名/规则。

没有给定 slot occupancy contract 时，“多个成员”只能先记为 role ambiguity/multiplicity，不能凭空宣布其中一个错误。若未来 slot 的机械契约要求一个 occupant，则违反契约的不同支持必须保留为 conflict；仍不得择一。多个相同值来源可能值 grounding 唯一，但不表示成员 role 唯一。

## 7. 结构不对称 D 与消融

从 F 只增加一条当前事实：`D = t_x:T(Z,X)`。它不含 slot，不含 Role，也不含 mapping。D 的意义仅是一个实际新增 relation occurrence；把 X 替换成 Y 构造对照输入时，结构条件应完全镜像。

这一一般输入族可写为 `T(Z,u)`，u 是实际 observation 中的成员；本纸面例子取 X 来检查结构响应，并不赋予 X 特殊规则常量。若真实输入改为 T(Z,Y)，R-PATTERN 的形式匹配应对应转为 Y；这只能排除写死 X 的实现，仍不能证明 motif→slot 的关联合理。

这使 X/Y 不再对称，但“结构不对称”不自动产生“X 应承担 S”的结论。

| 候选 | F | F∪{D} | 从原 seed 删除 D 后重建 | 裁定 |
|---|---|---|---|---|
| R-REIFY | 对称的原 incidence 记录，无目标 slot 角色 | 增加 t_x 的 occurrence-slot 记录；不是 X→指定 S | t_x 记录消失；其他原记录保持 | 真实历史依赖的表示变化，但不解决目标角色生成 |
| R-ALL | X/Y 对各 slot 的全部关联/假设 | 仍同时允许 X/Y；D 不撤销 Y | 恢复原集合 | 不满足 D 使角色独特成立的目标 |
| R-PATTERN | 没有 R/T 同时出现的匹配，故没有派生角色 | 候选规则可为 X 给出角色，对 Y 不给出；对所有空 slot 都如此 | 重建后无 T，候选派生角色消失 | motif witness 的 D 依赖成立；Role 结论的合理性未成立，不算干净通过 |
| 已接受的 clean role rule | 尚无 | 无可报告的干净生成结果 | 无实测结果 | UNRESOLVED |

R-PATTERN 只能演示一个可能通过形式重命名/消融检查的规则**仍可把路由藏在规则结论中**。不能为了期望 X 胜出而把 T 当成“胜出标记”；若 T 与 slot role 无结构性契约，增加 D 就指定 X 的角色是未经证明的外部决定。

“删除 D”是从原输入重建反事实 closure，不是在同一单调历史中删除 D 或其派生项。保留实际历史时，旧证据与配置不删除；反事实须有独立明确边界。本轮仅做这两种情形的纸面区分，没有操作数据库。

## 8. 单调性与“对称→唯一”的限制

若正向单调规则在 F 已产生 r_X 与 r_Y，则：

```text
F ⊆ F∪{D}
Closure(F) ⊆ Closure(F∪{D})
```

对**同一个 K、同一个 S**，新 D 不能让旧 r_Y 不成立。不能依靠“不存在另一候选”“当前只有一个”“第一个匹配”撤销它。

因此，有几种必须分开的情况：

1. F 原先无 Role；D 提供某个已证明正向生产前提，使 X 的角色首次出现。这在形式上可单调，但当前尚无这样的干净规则；R-PATTERN 的未论证结论不能替代它。
2. F 原先有全部假设；D 增添约束或 conflict 记录。原假设保留，不等于已完成唯一角色生成；若要剔除或采用配置，必须另审计 adoption 机制。
3. D 使组织结构形成新的 K_D。可以把它与 K_F 区分，但旧 K_F 及全部角色事实仍保留。只对 K_D 问一个明确的条件性问题，不等于系统自动选择 K_D；latest K、最少 conflict K、最优 K 都不能偷偷补进来。

把不相同 configuration 上的事实混成同一个“当前 K”再声称单调性通过，会掩盖删除、切换或 selection。相同成员集合的新 topology 值得有新 identity，但 identity 区分本身不是角色的生成或配置采用规则。

## 9. Closure 性质与风险

下面是未来规格必须满足的义务，不是已经实现的新 closure。

| 性质 | 表示/R-REIFY 可推导的部分 | 新 role generation 仍需解决 |
|---|---|---|
| Locality | 记录同组织内已给定 relation port，不扫描全域名字 | 指定 slot 缺局部结构生产依据；shared carrier 不自动授权 all-pairs 关联 |
| Monotonicity | 新事实只增加新记录/configuration/支持 | 不可用 absence/unique-so-far 作前提，不可撤销对称角色 |
| Confluence/order independence | 集合并入与 exact canonical 内容不取决于顺序 | 所有新合法角色后果/支持必须穷尽；等变性不证明 fixed-point 合流 |
| Idempotence | 同内容、同输入根再次记录不产生新项 | 不能每轮引入 run ID、无限新 K scope 或 slot 包壳 |
| Provenance completeness | 保留全部直接 occurrence/incidence 支持，不择一 proof | 新边必须有非循环的输入根生产见证；配置/proof identity 分离，所有合法支持保留 |
| Finite canonicalization | 固定 B/M/E/D、有限 G 边域时，至多有限个配置（若只有二元 member-slot 边，上界 2^(|M||D|)） | 还需声明其他拓扑项域、上下文生成界限；任意把 K 当新 member 递归嵌套会破坏这个有限性论证 |
| Conflict preservation | 区分不同角色配置、保留全部支持，不生成 Eq(member,slot) | occupant/value 契约须明确；不得用 conflict 来淘汰角色或选配置 |
| Resource limits | 未来不足必须 incomplete，不把有限性等同可计算性 | 不允许 pruning/top-k；新的 role/configuration/lineage 全计资源 |

组织成员声明及原事实可保留 stable identity，但 topology 内容变化必须形成不同配置。Scope、input envelope、slot declaration 域和 rule version 要在独立条件中固定；它们是资源/表示边界，不是 routing。

Role 若未来参与闭包，必须以新独立规格定义其合法规则，并保持跨配置 facts 的作用域。不能直接把 Role 作为 Eq 交给 GSC-0，也不能仅因在 K 中承担位置便写 Bind(外部端口,V)。组织内角色、port linkage 与 value grounding 仍是三个不同因果步骤。

## 10. Hidden-routing contamination audit

| 检查项 | 本轮处理 |
|---|---|
| 对象名字、固定 ID、numeric/lexical order、hash、地址、filename | 仅 exact identity 可作引用；不作生产或 adoption 条件；来源路径只作审计 |
| source support 数量/频率、first/latest/best、随机 | 不用作角色证据或胜出机制，所有直接支持保留 |
| unique compatible object | 只证明数量与类型，未证明角色因果；拒绝当生成捷径 |
| Eq(X,S)、Reference(target=S)、预输入 Role/Assignment/Incidence | 不进入 fixture；禁止换包装预接线 |
| Slot 的 opaque 标签暗含语义/特定成员 | Slot declaration 不含 target、值、动作或意义解释 |
| motif→某个 slot | R-PATTERN 的关键未解决处；不能凭 rename/消融形式合格就宣布干净 |
| 新 Slot(r,i) 自动对应原有 S0/S1 | R-REIFY 没有这条 correspondence，不能由 decoder 私自补上 |
| 选择 K_D / 最佳配置 / 冲突最少配置 | 未提供机制，不隐含在 organization identity 或报告中 |
| 新增局部 Role→外部 action | 不定义、不实现；本轮没有 Minecraft、正式输出或行为意义 |

纯结构规则仍由实验者定义 vocabulary 与规则规律，这不自动等于 policy 污染。关键是该规律是否定义了有独立机械依据的关系，还是把任意结构特征直接当作指派目标的答案。本轮未能证明后者的缺口已经消除，也不把所有可能的纯结构生成规律一概判为不可能。

## 11. 最终结论与下一步

| 交付问题 | 结果 |
|---|---|
| organization-local role representation | 给出 Role/LocalSlot 与 member identity 分离的纸面方案 |
| organization identity | B/M/E/D/G 完整 configuration；解决相同成员不同 topology 的表示区分与自引用问题 |
| candidate first-generation rules | R-REIFY 仅重新表示；R-ALL 无关联依据；R-PATTERN 缺 motif→slot 因果依据；没有接受的新生成规则 |
| renaming equivariance | 表示及若干候选可按定义作等变推导；未执行测试，不能替代 routing 审计 |
| symmetric-input | 不允许单独破坏 X/Y 对称；完整保留对应 facts/configuration 轨道或不给唯一角色 |
| asymmetric-input | D 产生结构不对称，但无已接受规则能证明目标角色首次成立 |
| ablation | 被拒绝候选可有 D 依赖；没有干净生成结果可声称通过消融 |
| same members/different topology | 表示层能区分；不是生成成功 |
| monotonicity/confluence | 同 K/S 不能从保留双 Role 变成删除 Y；新配置、反事实重建与 adoption 必须分开；完整生成闭包尚未证明 |
| hidden routing | 主要缺口位于结构 motif/compatibility→指定 slot，以及配置 adoption；未用任何捷径补齐 |
| clean prototype justified | **否，本轮不进入原型** |
| final verdict | **GSC2_ROLE_FORMATION = UNRESOLVED** |

下一步应先给一个 **slot 的纯机械结构契约与其正向生成关系**：为什么某局部结构变化构成该 slot 的 incidence，而不只是筛出某个成员；其生成是否作用于固定配置还是产生新配置；完全对称时如何保存全部后果；新配置与旧配置如何共同存在。若契约本身已给成员 correspondence，仍属预接线，应继续停在 unresolved。

表示部分相对完整，但不将整体判为 READY_FOR_PROTOTYPE。只有具体干净生产前提、纸面反例、有限闭包义务和角色/外部接口边界都补齐，才有理由另开独立实验。

## 12. 本轮边界

只新增本文件。未新增 runtime、experimental/gsc2、fixture 代码或 tests；没有执行角色规则或 closure，没有重跑冻结原型验收，没有修改任何旧文档、源码、配置、数据库或正式 A/Minecraft。

重命名、对称、不对称与消融结果全部是标明范围的数学/规则审计，不是实测结果。提交前后核对 `4fcc1bd54f1586110c76a036ec40a003a4238b0a` 的 134 个既有 tracked 文件字节 hash，保持不变。commit SHA 在最终交付消息给出。
