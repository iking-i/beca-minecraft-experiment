# Generative Structural Closure Model — TEST_ONLY specification

日期：2026-10-05（Asia/Shanghai）。设计基准：实验仓库 `a88c89b0ca00f70a28e3462d74030b83ebc1b8be`。

本轮只定义并审计规格，没有实现原型，没有修改 FormalL0，没有连接 Minecraft，没有动作、behavior expression 或 Effect port。旧审计、配置、测试、WORLD_ENTRY_FREEZE 和个体历史不变。

## 1. 模型范围与结论

模型取名 **GSC-0**。输入是有限、有类型、已有身份的结构事实；输出是这些事实的精确同一性、绑定传播、连接组合及冲突的**全部结构后果**。历史是材料，不是候选答案。

生成内容不是预先列出的完整答案，但生成规律是实验者明确给定的固定机制。这里不声称 A 自己发明了闭包规则，也不声称已经解决一般创造、行为作者权或 v0.9 的 upward recursion。

在下述有限域、单调规则、完整穷尽、无截断成功条件下，可证明：

- 完成的 closure 与遍历顺序无关。
- 完成的 closure 幂等。
- 输入增加时结构事实只增加；冲突不会造成任意推论。
- 不存在从多个合法变化中择一的 selector。
- 新 Composite 可以由此前不存在的成员组织形成，而不引入语义传递律。

**足够进入独立 TEST_ONLY 原型实现**，限于本规格的有限闭包；本轮不实现。资源中断结果不是完成 closure，不能享有“任意中断队列前缀相同”的保证。

## 2. 有限实验条件与符号

一个测试条件预先声明：

```text
Σ = (namespace, scopes, node declarations, finite value domain,
     relation signatures, exact reference declarations,
     finite input envelope, resource ceilings, rule version)
```

这是能力与资源边界，不规定哪个事实“更好”。条件内不自动生成新 Node 身份、Variable、值、关系类型或函数项；它们必须由合法输入/已有材料声明。闭包可以构造新绑定、端口绑定、equality 后果、Conflict 和 Composite。

每个关系类型只规定固定元数、各端口的机械类型，以及端口是 Node/Reference/Value 中哪一种。类型 ID 是 opaque 编号，不能解释为 Minecraft 概念。端口次序是输入关系的内容，不能因为组合可交换就交换关系内部的两个端口。

不同观测时刻的可变字段使用不同 observation scope。例如 `position.x@t0` 与 `position.x@t1` 是不同变量；时间变化不应自动制造同一变量的数值冲突。要跨时刻认定相同变量或同一对象，需要相应合法身份声明或 explicit equality，不能靠名字相似。

有限 input envelope 是此独立条件可接受的总输入时刻/记录范围，**不是删除旧记录的滑动窗口**。达到上限报告 RESOURCE_LIMIT，不能保留最近窗口继续冒称同一单调闭包。

## 3. 编码、相等与 lineage 的共同约定

所有键使用带类型标签、版本、长度界限的无歧义规范编码；排序只用于集合序列化/去重，不用于选保留项或择优。结构相等检查规范内容，不只信任 hash；若实现用 digest 索引，必须核对内容防碰撞。

第一版 Value 采用声明的有限精确域，例如有类型整数及枚举；不使用浮点近似相等、NaN、容差或隐式数值类型转换。`Int(1)` 与其他类型中的同名值不是同一 Value。两个不同 Node 绑定相同 Value 不证明两个 Node 相同。

对象结构 identity 与生产 lineage 分离：同一规范结构有一个逻辑键，但可以有多个生产支持。新 UUID、时间戳、证明路径、输入顺序不进入派生结构的逻辑键，否则循环会不断生成伪新对象。

lineage 表示有限的 immediate justification graph：`(rule_id, premise_keys, conclusion_key, input-source refs)`。保存所有不同的直接支持，不无限展开所有推导路径。循环传播可能产生环，允许以 SCC/图表示；每个实际生成对象必须有通往输入/旧结构根的有限生产见证。空的循环不能凭自支持生成事实。

## 4. 最小 typed structure 对象

Node 与 Variable 共享节点身份系统；Variable 是 Node 的一个机械角色。Reference 只是引用项，不单独发明对象。Binding 的两个形式包括普通变量绑定与关系端口上的显式绑定。无需另设 candidate、score 或 active-answer。

| 对象 | identity | content / type | lineage | equality / canonicalization |
|---|---|---|---|---|
| Node | `(namespace, scope, node_kind, stable_id)` | 固定声明的节点角色/类型；属性是独立事实，不覆盖 Node | 输入/历史声明引用 | 完整键 exact 相同；不同键只能由合法 explicit equality 连接，不能重写旧键 |
| Variable | Node 键 + 声明的 value type | 可出现于关系端口的变量节点；没有 preferred value | Variable 声明来源 | 相同作用域及完整键；类型必须精确兼容 |
| Value | `(value_type, exact_encoding)` | 精确不可变值，必须属于有限域 | 值出现的输入/旧事实来源 | 相同类型及编码；不比较优劣、距离 |
| Reference | `(issuer_namespace, reference_scope/epoch, exact_token, declared_target_key)` | 不解析 token 含义；仅合法声明的 target | 原引用声明/输入 | 完整引用身份相同且目标声明一致才视为同一引用；不同引用不因 target type 相同而相等 |
| Relation | 输入发生身份 `(source, scope, occurrence_id)` | opaque type ID + ordered typed ports；各 port 指明 Node/Reference/Value | 原关系输入/历史来源 | 同一发生身份必须有相同内容；两次发生即使形状相同也保留两个输入支持，不统计频次投票 |
| Composite | `("Composite", sorted set of non-Composite leaf keys)` | 成员集合 + 可增添的 shared-incidence witnesses；不产生新的语义 relation type | 所有 COMPOSE 直接支持及成员来源 | 平坦集合相同即同一 Composite；嵌套/次序/重复成员不创建新对象 |
| Binding | `("Bind", variable_key, value_key)`；或 `("PortBind", relation_key, port_index, variable_key, value_key)` | 类型正确的值绑定事实；多个值可同时存在 | 输入 Bind 或传播规则/前提 | 完整 tuple 相同去重；不能覆盖另一个值 |
| Conflict | `("Conflict", variable_key, sorted unordered pair of distinct value_keys)` | 同一变量拥有两种不同绑定的事实；没有解决结果 | 两个 Bind + CONFLICT 规则 | 无序值对去重；三个值产生三对冲突，不选代表值 |

Equality、Difference、字段事实均用保留的结构 Relation/事实签名表达，避免新增含行为语义的对象种类。`Eq(a,b)` 是结构身份关系；`PortBind` 是派生 Binding，不是替宿主执行原动作的参数。

同发生 identity 却给出不同 Relation 内容、同 Node identity 却给出不兼容声明、同 Reference identity 却指向不同 target，属于 INVALID_INPUT/encoding conflict。不能选一个声明或 silently overwrite。保留输入审计事实，整个调用不给 successful closure；这种接口错误不同于合法 Bind 数值冲突。

## 5. Difference：只记录现实差异

“Reality”在此指 fixture 通过合法输入接口给出的有限精确观察，不是宿主的全知状态。观察需携带 identity、scope、coverage 与输入 occurrence refs。

`Difference_t = Diff(Observation_(t-1), Observation_t)`，只按同一来源的精确键比较：

| 可证实的变化 | 输出材料 | 不允许的解释 |
|---|---|---|
| 当前首次观察某字段/事实 | `Observed/Appeared`，当前 typed 值/关系，输入支持 | “新颖所以优先使用” |
| 同一稳定对象字段的前后精确值不同 | `Changed(object, field, old-scope/value, new-scope/value)` + 当前事实 | “数值变坏，所以避开” |
| 在明确完整 coverage 下证实原事实不再存在 | `ObservedAbsent/Removed` 的观测事实 | 从 closure 删除旧事实 |
| coverage 不足，不能确认消失 | `Unobserved`/coverage 事实 | 把未观察当 false 或否定旧事实 |
| 观察到一个新增 explicit equality/关系声明 | 保留该当前发生及来源 | 凭 type、距离、数值相同发明 equality |

Diff 不生成 action、goal、适应方向或“应该做什么”。不必计算差值数值；保留 old/new 即可，避免引入未声明值域。普通当前变量赋值只在它自己的 scope 内成为 Bind，旧 scope 的 Bind 保留。

Removed 是新的历史观察材料，不是 retract 规则。此模型只累积观测及结构后果，不声称累积的旧观测都同时是现实当前真相。

输入相同的观察不生成伪差异；新出现的来源支持与结构键分别处理。Difference 是本次有限输入的材料，不是答案。

## 6. Alignment / Unification：精确同一性饱和

允许的同一性来源只有：

1. exact stable Node identity；
2. exact opaque Reference identity 及已声明的目标；
3. 已在输入/历史中明确存在、类型兼容的 `Eq(a,b)`。

引用解析仅依合法声明，未声明 target 不推测；失效/新 epoch 不自动重绑定。same kind、名字、位置、同一绑定值或相似外观不产生 Eq。

对兼容 Node 生成以下全部有限后果：

```text
ALIGN-REFL: Declared(a)                         → Eq(a,a)
ALIGN-SYM:  Eq(a,b)                            → Eq(b,a)
ALIGN-TRANS: Eq(a,b) ∧ Eq(b,c)                  → Eq(a,c)
```

这些只定义 equality 自身的结构性质，**不是给任意 relation 加传递律**。不同角色/类型/值作用域不满足统一条件时拒绝该不合法 equality 声明，不用类型修补它。

逻辑上相同对象形成同一 identity class，可合并读取其全部事实；但物理存储保留原 Node 键和所有 Eq witness，不把类中某个键选作唯一新真值。新增 Eq 只新增事实，不重命名、删除或替换既有结构。

若实现用 union-find 加速，可有内部索引代表，但语义输出、canonical keys、lineage 不能依赖代表选择/插入顺序。规范对象键保持不变；不得为了方便实现 quotient 而破坏单调性。

## 7. Propagation：全部显式绑定边，不作择一替换

第一版采用显式绑定边，**不复制整条 Relation 为多个无条件真断言**，不把变量含义强行解释为某一数值。

```text
PROP-ALIAS:
    Bind(x,v) ∧ Eq(x,y) ∧ CompatibleVariable(y,v)
    → Bind(y,v)

PROP-PORT:
    Relation r 的 port i 明确引用变量 x ∧ Bind(x,v)
    → PortBind(r,i,x,v)
```

固定签名/类型检查属于机制。CompatibleVariable 只查 exact type/作用域声明，不查偏好、无冲突或“哪个值正确”。Reference 端口须先按合法 Reference 声明确切落到 x；这不是 target 搜索。

因此 `Bind(X,3), R1(X,A), R2(B,X)` 保留原 R1/R2，并产生两个端口上的 3 绑定边。发生 `Bind(X,1)` 与 `Bind(X,2)` 时，两个值都传播到每个合法使用位置；不是一个值被选中，也不声称关系已获得唯一一致解释。

派生 Binding/PortBind 是新 canonical 事实；保留 Bind、Eq、原 Relation 和端口索引的全部直接支持。同 tuple 去重，新支持并入 lineage。传播不删除原变量，不改写历史关系，不自动合成所有参数完备的行为。

## 8. Conflict：正向记录，不爆炸推理

```text
CONFLICT:
    Bind(x,v1) ∧ Bind(x,v2) ∧ exact(v1) != exact(v2)
    → Conflict(x,{v1,v2})
```

规则不要求“没有 conflict”才能传播或组合。Eq 使绑定传播到兼容别名后，也可在每个别名形成冲突；不选择一个 canonical winner 变量。

Conflict 以 x 为结构 incidence 节点，成为可参与组合的材料。它不推出任意值/任意关系，不产生新的 equality，不撤销绑定，不改问题优先级。后续输入可使含该 Conflict 的更大结构形成，但本轮没有冲突解决规则。

## 9. Composition：连通支持集合，不推出语义捷径

### 9.1 Leaf 与 incidence

Non-Composite leaf 是有限 canonical 事实：原 Relation、Difference 事实、Eq、Bind、PortBind、Conflict 等。每种签名声明它有哪些 Node incidence 端口：普通关系按原 Node/Reference target 端口；Bind/Conflict 关联其变量；PortBind 关联原变量；Value 本身**不是**共享 Node。

相同 Value 不把不同对象连起来。Reference 身份也不靠 token 子串解释。关系 occurrence、端口身份和全部成员都保留，不能因为一次 equality 连接就把端点关系压成新的业务 relation。

两个 leaf/已形成 Composite 可组合，当且仅当：

- 各自的展开成员集合是非空的、在当前 Eq 下连通的支持集合；单 leaf 是大小 1 的退化支持；
- 两个支持之间有至少一对 Node incidence 满足当前已导出的 Eq（包括 exact identity 的反身情形）；
- 联集有至少两个不同 leaf；
- 联集内容与声明类型合法，处于同一有限实验条件。

枚举**所有**满足条件的支持对，产生：

```text
COMPOSE:
    Support(S) ∧ Support(T) ∧ SharedIncidence(S,T)
    → Composite(S ∪ T)
```

结果只组织原成员；`R1(A,B), R2(B,C)` 得到包含 R1/R2 和共享 B 证据的 Composite。**不产生 `R3(A,C)`**，不隐式投影、路径压缩、对象用途解释或语义传递。

### 9.2 多关系与 canonicalization

Composite 的成员是展开后的 leaf-key 集合，按规范键排序编码。已有 Composite 不成为新的嵌套 leaf；组合时总是 flatten。只依此支持集合生成 identity，不依“先组合哪两个”、UUID 或 proof tree。

同一 Composite 的 `shared` 内容表示成员端口之间全部已知 Eq incidence witnesses。新增 Eq 可以追加 witness，不改变成员 ID；witness 的键也去重。不得只记录遍历先遇到的共享节点。共享声明是组织关系，不是使用其意义作判断。

交换性：`S∪T = T∪S`。在每一步均有合法共享前提时，结合的成员结果一致：`(S∪T)∪U = S∪(T∪U)`。**可用性是偏运算**：例如链状 R1/R2/R3 的 R1 与 R3 未必能直接组合，不能声称所有括号的中间步骤都合法。公平闭包枚举所有连通支持，不依赖某个非法括号顺序。

同成员再次组合不创造新对象；不同合法生成路径是同一对象的不同 lineage。平坦有限集合阻止 `Composite(Composite(...))` 造成无限包壳，代价是第一版不表达嵌套层次差异；这是真实表示能力限制，不是隐式高层生成。

## 10. Recursive closure 的严格定义

令 UΣ 为在声明域中可能出现的全部事实/Composite/witness/有限直接支持的宇宙。它是有限的：无新自由变量、无新函数项、无新 relation type、无无限 lineage 展开；leaf 数量有限，Composite 至多是其有限幂集中的连通部分。

设 `S0 = C_t ∪ Difference_t`。对象声明/输入根支持也属于 S0。定义：

```text
TΣ(S) = S ∪ 所有当前前提成立的 ALIGN/PROP/CONFLICT/COMPOSE 后果
           ∪ 所有这些规则的直接 lineage/shared witnesses

S_(k+1) = TΣ(S_k)
ClosureΣ(S0) = 达到有限不动点的 S*
C_(t+1) = ClosureΣ(C_t ∪ Difference_t)  （仅当状态为 COMPLETE）
```

闭包检查同时包括事实、shared witnesses 和 immediate justification graph；仅“没有新对象 ID”但仍漏证据，不能报告 provenance complete。对循环支持保存有限图，不追求无限 proof-tree 枚举。

新 Bind/Eq/Conflict/Composite 再参与下一轮传播与组合。没有 prune、best match、最新优先、权重或语义条件。规则的 opcode 由满足的结构前提自动实例化，**不是另一个 operation selector 选出的调用**。

### 10.1 性质与证明边界

| 性质 | 成立原因与条件 |
|---|---|
| Inflationary | TΣ 包含原 S；不会删除旧事实/绑定/冲突 |
| Monotone | S⊆S' 时每个原正向前提和 exact 不等式仍成立，因此 TΣ(S)⊆TΣ(S')。不使用“无冲突/不存在另一值/最新”这类非单调条件 |
| Termination | 有限 UΣ 上每轮只新增 canonical 项或有限直接支持，最终无新增；可能非常昂贵，不等于任意预算可完成 |
| Least closure | 从输入根开始逐轮闭包，得到包含输入且对全部规则闭合的最小集合；不是选最少结构的优化任务 |
| Idempotence | 完成 S* 满足 TΣ(S*)=S*，再次闭包无新事实或支持。要求 Σ/规则版本及输入根支持相同，不制造新的 RUN UUID 来源 |
| Order independence | 任意公平、无遗漏、无删除的穷尽执行最终达到同一最小不动点；调度次序不进入 canonical keys。lineage 须最终补齐所有直接支持，不只保留第一个证明 |
| Input monotonicity | 同一 Σ 下 C⊆C' 则 ClosureΣ(C)⊆ClosureΣ(C')；保留旧节点键而不是不断换 quotient 代表是这一保证的必要设计 |

公平性意味着每个已满足规则实例最终处理；scheduler 可以不同，但不能通过饥饿/有限 top-K 使合法实例永久缺失。幂等结论只对**完成的闭包**成立，输入变化/新作用域/改规则/资源中断不是反例或通过证据。

## 11. 资源边界：不能把前缀当闭包

固定 node/value/type/input-envelope 上限之外，声明 total canonical structures、provenance/witness storage、rule-instance workspace 和计算预算上限。lineage 与共享证据也计资源，不能在事实数看似正常时耗尽无界审计内存。

成功结果必须 COMPLETE。达到任一上限返回：

```text
RESOURCE_LIMIT {
  condition/rule_version,
  phase/round,
  resource_port,
  used, capacity,
  requested 或 lower_bound（明确是否已穷尽计数）,
  closure_complete: false,
  pending_input/source refs
}
```

不删除 oldest、不留 strongest/useful，不随机 eviction，不压缩成“最有用 Composite”。不返回排好序的前 N 项作为成功结果；按字典序截取也是内容取舍。

第一版推荐同步 round 的事务性边界：穷尽本轮所有后果，构成整批 Δk；检查整批资源，能容纳才全部提交。不能容纳就整批不采用，保持上一完成 round 的工作状态；上一个已完成的 C_t 与本次全部输入支持保留。本次不能推进成 COMPLETE 的 C_(t+1)。这不是删除已采用事实，而是不部分采用一个失败事务。

若 workspace/计算预算甚至不足以穷尽 Δk，立即停止并报告 incomplete；中途生成项只能是明确标记的审计工作前缀，不得作为新 canonical closure 或在下轮假装完整状态。pending 输入也不能默默丢弃；连输入都装不下时由调用者保留完整输入/旧状态，报告未接纳及资源原因。

**部分前缀、触发时间和遍历顺序可能不同；完成 closure 的唯一性不能被误用为资源中断的唯一性。** 原型比较中必须分开 COMPLETE 结果与 RESOURCE_LIMIT。同步 round 在完整 round 可计算时使提交边界确定，但不能保证任何资源环境下完整计算。

## 12. 无 selector 与五项作者权审计

| 规则族 | operation vocabulary author | operation instance author | operand author | result author | result adoption author |
|---|---|---|---|---|---|
| Difference | 外部 exact 编码/变化协议，EXTERNAL_FIXED_MECHANISM | 合法前后观察的实际差异穷尽实例化；EXTERNAL_FIXED_MECHANISM | 实际输入事实/覆盖，ENVIRONMENT_CONSTRAINT | 变化记录由输入确定，记录机制外部 | 合法输入全部接纳；资源失败整体报告，不择优 |
| Alignment | 外部精确身份/equality 结构规则，EXTERNAL_FIXED_MECHANISM | 所有 exact/Eq 前提均实例化，无 best match | 输入 identity、explicit Eq 或既有内部结构；来源分别记录 | 派生同一性依赖这些实际前提；不能称系统发明 identity 规则 | 全部 canonical 后果并入 |
| Propagation | 外部绑定规则，EXTERNAL_FIXED_MECHANISM | 所有合法共享变量端口均实例化，无值选择 | Bind/Eq/Relation 的实际历史内容，可属 INTERNAL_VARIABLE_STRUCTURE | 新绑定连接由具体前提与固定规则共同决定 | 所有值保留，Conflict 不删除它们 |
| Composition | 外部平坦连通支持规则，EXTERNAL_FIXED_MECHANISM | 所有共享 incidence 的支持对，穷尽产生 | 历史关系及新输入/派生事实 | 新组织成员内容随历史改变，可作为 INTERNAL_VARIABLE_STRUCTURE；固定组合律仍外部 | 全部 canonical Composite；不挑一个 R4 作为答案 |
| Conflict | 外部 exact 不同绑定记录规则，EXTERNAL_FIXED_MECHANISM | 每个合法不同值对自动实例化 | 输入/派生的两条 Bind | 显式冲突事实，不决定谁正确 | 全部保留，无冲突解决政策 |

规则前提可以精确列出操作实例，所以对**此有限结构闭包**已经不需要回答“谁选 compose(R1,R2)”：所有共享对都生成。程序员提供的是全部可用的纯结构规律，具体 operands 与结果由实际输入/历史组成决定，结果采用是集合并入。不存在多个合法变化只保留一个的步骤。

这缩小了上一轮 producer 的缺口，不能扩大为“任意新值/控制/行为内容已形成”。本模型不产生未声明值，不解释世界意义，不生成动作，也不声称这些规则自己被递归创造。

以下若实现中出现，必须标记 EXTERNAL_FIXED_POLICY 并判不符合本规格：best/nearest、按次数或最新排列保留、最高权重、随机选择、只应用一条相容规则、遇到冲突停传某个值、资源满时选择留下部分结果。排序编码、规则表编号、索引和公平工作队列不属于这种择一；但它们不能改变最终结果。

## 13. 最小独立 TEST_ONLY fixture 设计

以下是纸面输入与可核验期望，**未执行测试**，不借用 Minecraft 或正式 A 的 history。

### 13.1 条件与初始材料

一个作用域 q；exact Node 键 A/B/C；同 value type 的变量 X/Y；有限 Value 域 `{Int(1),Int(2),Int(3)}`。声明三个 opaque 二端口关系类型 p1/p2/p3，不给传递含义。

```text
R1 = p1(A,Y)
R2 = p2(X,B)
R3 = p3(B,C)

Observation_0：尚未观察到 Bind(Y,3) 和 explicit Eq(Y,X)。
C0 = Closure({上述声明，R1，R2，R3})。
```

既有 C0 可有 R2/R3 的 Composite，但没有 Y/X 的别名连接，也没有 3 的绑定；不能把 R1 与 R2 凭“都是变量”组合。

### 13.2 两个真实 fixture 差异

在 fixture 的 Observation_1 中实际出现：

```text
D1：精确变量 Y 的当前声明范围内，首次观察 Bind(Y,Int(3))。
D2：实际输入显式 equality 声明 Eq(Y,X)。
```

Difference 记录两条 Appeared 及源输入，并提供对应 Bind/Eq 材料。D2 是 fixture 人工提供的 explicit equality 输入，不是系统发现对象相同，也不能冒充 Minecraft 感知。值/关系种类在 Σ 内，scope 没有发生偷换。

### 13.3 可手工追踪的 R4

```text
D2 → ALIGN → Eq(X,Y) 及已有 reflexive 同一性
D1 + Eq(Y,X) → PROP-ALIAS → Bind(X,Int(3))
Bind(Y,3) + R1.port1 → PortBind(R1,1,Y,3)
Bind(X,3) + R2.port0 → PortBind(R2,0,X,3)

R1 与 R2 的 Y/X 共节点 witness → K12 = Composite({R1,R2})
K12 与 R3 共 B → K123 = Composite({R1,R2,R3})
K123 与 Bind(X,3) 共 X（R2.port0）
    → R4 := Composite({R1,R2,R3,Bind(X,3)})
```

R4 是审计别名，不是一个新增业务关系类型。它保留三个旧关系、新绑定及全部共享 incidence，包括 R1/R2 的 Eq 证据、R2/R3 的 B、R2/Bind 的 X。端口传播事实也会形成其他合法 Composite；它们同样成立，不仅保留这个展示的 R4。

R4 此前不在 C0，不是过去完整结构复制，不是随机值或 selector 选出的候选。新形成的 K12/K123 再参与组合，展示 recursive closure；lineage 的一条完整输入见证是 R1/R2/R3/D1/D2，规则见证为 ALIGN、PROP、COMPOSE。

完整 lineage 还保存其他合法生成路径，例如先组合 R2 与 Bind，再与其他关系连接。展示一条路径不允许实现只留第一条来源。R4 identity 只由 leaf 集合决定；shared/lineage witnesses 分别规范去重。

### 13.4 消融与性质检查计划

| 测试 | 隔离操作与期望 |
|---|---|
| 历史结构消融 | 从原始 fixture seed 去掉 R2，**重新闭包**；R4 不形成，X 与 B 的原组织边消失。不能只删 R2 却保留包含 R2 的旧 Composite 再说消融无效 |
| 差异消融 | 去掉 D1 的材料，Bind(X,3) 与 R4 不形成；去掉 D2 的材料，Y 不同于 X，R1 与 R2 无共享同一性，指定 R4 不形成 |
| Order independence | 枚举种子排列及 rule/work-queue 顺序，在相同 Σ 下运行至 COMPLETE；比较全部规范事实/shared witnesses/直接支持集合，忽略运行计时与调试队列轨迹 |
| Idempotence | 将完成的 closure 与原根支持再次交给同版本闭包；不产生新结构或新直接支持。不因新 run ID 生成额外 lineage |
| 冲突保留 | 加入合法同 scope 的 Bind(Y,Int(2)) 事实，与 3 冲突；生成 Y/X 的两值传播与 Conflict 对，两种端口绑定均保留，不推出任意额外值 |
| 资源限制 | 比较能容纳结果的大 cap 与小 cap；小 cap 为 RESOURCE_LIMIT/closure_complete=false，旧状态和输入保留，不删除或择优；失败 round 不部分采用 |
| Lineage completeness | 对每一派生键校验有限根见证和所有直接规则支持；共享节点/别名 witness 可解析，循环不独立作为输入根 |
| 无伪语义关系 | 断言不会仅因 p1/p2 连通就出现新的 p3(A,B) 或任何未输入的业务 Relation；只能新增此规格允许的结构事实/Composite |

最后一项中的“新业务 Relation”包括任意未经输入声明的端点捷径，不局限例子的标签。fixture 证明的是结构构造机制与历史依赖，不是智能、行为闭合、主体连续性或 L1。

## 14. 数学与实现风险、进入原型的条件

最大风险是**组合及 provenance 的指数级爆炸**：即使输入很小，连通支持集合可接近全部子集；直接支持组合也可能巨大。有限性只证明最终可终止，不保证现实配额能完成。

其他需在原型严格守住的风险：

- equality 类改变时重写键会破坏单调性、去重与引用；保持原键和 Eq 饱和事实。
- 同值误认同对象、跨 epoch/scope 自动统一，会制造假连接和假冲突。
- 扁平化舍弃嵌套组织区别，第一版生成能力有限；不能把集合包裹称作一般组织重构。
- 仅保留首次 proof 导致 lineage 依赖顺序；无限展开循环证明又无法终止，须保存有限直接支持图。
- 资源中断的工作前缀依赖队列；只能报告未完成，不能评为不同闭包答案。
- 非单调的删除、冲突择一、当前真值替换都在本版范围外；累积旧事实不等于所有旧现实同时成立。

本规格足以定义一个独立、有限、内容无关、无 selector 的闭包原型及验收条件。原型实现前需把规范编码、有限域上限、签名 incidence 和 RESOURCE_LIMIT 协议固化为测试条件；这属于规格落实，不是新增 semantic policy。原型完成后才能用实测报告替换本文件的纸面推导。

不需要新增 selector、行为模块或 Minecraft API。正式 FormalL0 仍未具有本规格的闭包操作；将来若接入它要另行审计，不把当前文档当 runtime 已修正。此处结构内容生产路径已明确到规则前提穷尽实例化，但不推导动作或一般高阶规则生产能力。

## 15. 本轮交付

仅新增本规格文档。未新增机器规格、原型、测试执行记录或数据；未运行 closure、FormalL0、Minecraft；未修改已有文件/数据库/冻结 manifest。理论与实验的既有通过/失败结论均不改变。
