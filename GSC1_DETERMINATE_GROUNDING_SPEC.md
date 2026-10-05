# GSC-1 — Determinate Grounding Specification

日期：2026-10-05。冻结上游：`8801ca88093e5c66fa11ba6eb4c084608a1bd690`。

本实验是独立 TEST_ONLY 的 GSC-0 consumer。GSC-0 源码、测试、规格和报告不修改；正式 A、FormalL0、Minecraft、数据库和冻结验收不接入。标准库实现，不新增推理规则或能力。

## 1. 输入与普通结构端口

`OutwardSchema(name, ports)` 固定非空 required-port 列表。每个 port 包含唯一名称、普通 GSC-0 Variable 的完整身份和精确 value type。schema 不含值、默认值、任务或优先级。声明顺序是字段序列化顺序。

端口使用 GSC-0 原有的 Alignment、Propagation、Composition 和完整 Closure。checker 不查找近似变量、不跨 scope 补值、不自行跟踪 alias；读取上游实际派生的普通 Bind。端口须精确存在于同一 Condition 声明和事实中，类型必须一致。

## 2. 唯一性协议

对每个端口收集 **所有** exact-variable、exact-type、有限声明域内的普通 Bind，以精确 Value key 去重。多个 proof/source 不算多个值。

| 不同合法值数 | port 状态 | 完整 outward |
|---:|---|---|
| 0 | UNRESOLVED | 不构造 |
| 1 | GROUNDED | 仅在所有端口都是 singleton 时构造 |
| >=2 | CONFLICT | 不构造；全部值及证据保留 |

完整结果 `GroundedOutwardStructure` 的逻辑键只含 schema 完整键和逐端口的精确值键，不含时间、proof 次序或 UUID。它是 **unique bindings → mechanical packaging**，不加入 GSC-0 closure，也没有行为执行。

任何 CONFLICT 时总体为 CONFLICT；否则若有缺失则 UNRESOLVED；否则 COMPLETE_GROUNDED。混合失败只汇总状态，不解决冲突：每个端口的缺失/冲突仍完整保留。失败时 `outward=None`，不生成 NO_OP。

上游必须是 GSC-0 的 COMPLETE Result。RESOURCE_LIMIT 直接拒绝，即使已提交工作前缀看似拥有所有输出绑定。非 Result、非法状态、非法 schema、非法 upstream binding 或无输入根来源的绑定为 INVALID，不能悄悄忽略并报告成功。调用方需提供真实 GSC-0 Result；checker 不是对任意伪造状态重算 closure 的安全验证器。

## 3. Paired-history fixture

同一 q scope、同一 gsc1 namespace。普通历史变量 h0/h1/h2 和普通输出变量 p0/p1/p2，类型分别为 TypeA/TypeB/TypeC。有限域为各类型的两个 opaque 枚举值 A0/A1、B0/B1、C0/C1；没有业务语义。

| 来源 | History_A | History_B |
|---|---|---|
| H0 | Bind(h0,A0) | Bind(h0,A1) |
| H1 | Bind(h1,B0) | Bind(h1,B0) |
| H2 | Bind(h2,C0) | Bind(h2,C1) |

这里关键历史关系是 **Binding 的变量—值关系**，不是新增业务 Relation。两个历史各只有三个独立绑定；没有输出端口绑定、完整 outward tuple 或对应完整输出对象。

两者严格共享同一个 CurrentInput tuple、Condition 和 OutwardSchema：

```text
D0 = Eq(h0,p0)
D1 = Eq(h1,p1)
D2 = Eq(h2,p2)
```

这是当前 explicit input，而不是系统自行发现同一性。输入数量、来源标签、事实内容完全相同，无按历史分支构造 current input 的代码。

运行顺序是 `Closure(history)`，再 `Closure(previous ∪ CurrentInput)`。第一次 closure 的三个输出端口都未绑定。第二次 closure 原有 PROP-ALIAS 生成 p0/p1/p2 的绑定；ALIGN 和 COMPOSE 等均穷尽执行，每组还形成含历史 Bind、当前 Eq 和新输出 Bind 的此前不存在的 Composite。三个 typed 分量可互不连通；GSC-1 不凭包装把它们发明成新的 GSC-0 业务关系。

期望结果分别为 `(A0,B0,C0)` 与 `(A1,B0,C1)`。每个输出绑定的根必须含相应 Hi、Di，直接支持含原 GSC-0 PROP-ALIAS。整个 outward 的包装前提是所有端口的 singleton 绑定；全部证据保存，不择一 proof。

## 4. 因果与失败验收

对两个历史逐项删除 Hi，重新从原 seed 闭包，对应端口 UNRESOLVED；逐项删除 Di，重建闭包，同样不得保留原完整结果。不能删除输入却沿用已经包含其派生绑定的旧 closure 冒称消融。

加入 Bind(h1,B1) 时，B0/B1 均传播，Conflict 保留，checker 不构造完整 outward。另外验证三个值、相同名称不同 scope、重复来源不增加值数、混合缺失/冲突、非法类型拒绝、checker 只读且不缓存旧输出。

两个历史各运行三种 seed 顺序 × 三种 queue/rule 顺序，比较 closure 实际规范内容、全部普通支持及 COMPOSE 无损索引，并比较整个 GroundingResult。重新闭包与重新 grounding 必须幂等。

## 5. 作者权与证明边界

schema、singleton 条件、包装机制、GSC-0 规则由实验者提供：EXTERNAL_FIXED_MECHANISM。历史绑定与当前 equality 来自人工 fixture 输入。派生输出绑定和 Composite 的具体内容由输入与固定结构规则共同决定。

包装仅解包已证明 singleton；不允许 selector、ranking、latest、majority、random、weight、reward、utility、fallback、填默认值、修补或冲突解决。canonical 排序只序列化全部来源，不用于保留最先/最优项。

每个 port 保存 binding key、全部直接支持、全部有限输入根。结果关联 upstream canonical digest，原 closure 保留完整 immediate graph 和 COMPOSE 索引；不无限展开 proof tree，也不只保存 first proof。

本实验可以验证 **在这些历史和当前输入下，递归闭包形成的结构足以唯一确定一个完整 typed 输出**。不证明系统创造新 primitive value、发现 schema/equality、产生行动、学会规则、保持主体连续性或形成 L1。读取三个单例并包装本身不是新的推理能力。

## 6. 判定与边界保护

全部核心检查实际执行通过才能标记 `GSC1_PROTOTYPE = passed`。新增代码全部位于 experimental/gsc1，正式 runtime 不导入它。验证器核对既有 tracked 文件字节 hash，单独记录 GSC-0 冻结文件；运行 GSC-0 原有 unit tests，但不调用它的报告生成器。既有源码、规格、报告、配置和正式历史都保持不变。
