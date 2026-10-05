# GSC-0 Recursive Result Dependence — TEST_ONLY Counterfactual

日期：2026-10-05。运行输入基线：`559e356d77c69a5c0f3fa8ea58905c6ca943f77b`。

**实际分类：DERIVED_RESULT_NOT_CAUSALLY_NECESSARY。** 在下述两个有限域案例中，A_FULL_PREVIOUS、B_DERIVED_ABLATION、C_FRESH_RECOMPUTE 全部 COMPLETE，实际结构/来源比较得到 A=B=C。前轮派生结果可从保留的原始输入重新推导；它不是这两组下一轮新图形成的独立必要条件。

该结论只针对本轮固定 Condition/H/I/cap 的对照，不是任意 GSC-0 输入/资源预算的普遍证明，也不表示派生图不会被计算消费者读取。未修改 CO-WAC-1 或任何已有组织/连续性审计结论；未修复任何能力。

## 1. 交付与边界

- 独立入口：[experimental/gsc0_result_dependence.py](experimental/gsc0_result_dependence.py)。只导入标准库和冻结的 GSC-0 engine/model，不导入 FormalL0、A、Minecraft 或 SQLite。
- 本次机器记录：[GSC0_RECURSIVE_RESULT_DEPENDENCE_VALIDATION.json](GSC0_RECURSIVE_RESULT_DEPENDENCE_VALIDATION.json)。没有覆盖既有 GSC 验证报告或实验历史。
- 实际运行 2 个 H→COMPLETE，再分别运行 A/B/C，共 8 次 closure 调用；最终 **8 项自动控制/记录完整性测试全部通过**。控制测试不预设最终分类。
- 运行前后核对 139 个既有 tracked 文件字节 SHA-256，全部未变；包括 engine/model、现有 tests、三个审计/标准文件、连续性审计和所有已追踪历史报告。

运行入口（项目根目录，使用现有 Python）：

```powershell
.\.venv\Scripts\python.exe -m experimental.gsc0_result_dependence
```

入口只写本次独立 JSON；再次执行会重写这个本次验证文件，不会修改旧实验记录。本文报告最终执行结果，不把测试声明当作运行证据。

## 2. 精确定义材料与 ablation

不能用“事实类型是 Bind/Eq”判定它是派生结果：同一 canonical fact 可以既是原始输入，又有后续机械推导支持。

| 类别 | 本实验的识别依据 | B 的处理 |
|---|---|---|
| declaration | 同一 Condition 的 nodes/values/references；原 `DECL:` 根及对应 INPUT 支持 | 原事实、支持和根保留 |
| original INPUT / OBSERVED / DIFF seed material | 同一 H 的 Seed 与 `S_t.input_records=(fact.key,sources,rule)` 精确一致；在 S_t.proofs 找到相应输入直接支持 | 原事实及其全部外部输入支持保留，包括 Change notices、Relation、原始 Bind/Eq |
| derived O-G0-1 | 非上述原始事实的 Equality/Binding/PortBinding/Conflict/Witness；以及输入事实上的派生支持贡献 | 纯派生事实移除；双重来源事实保留本体，但仅去掉派生支持 |
| Composite / other derived material | Composite 与完整 COMPOSE 索引属于依赖图的辅助 materialized cache；不属于本 O | B 清理所有 Composite/cache，避免引用被删 leaves；原始 input Change 不删 |

代码先从同一 COMPLETE S_t 克隆隔离副本，再按这些已核对的记录/声明设置 facts/proofs，不另造 H。必须同时满足：

1. input_records 恰好等于同一个 H 的记录集合；
2. 每个声明/原始 seed 在 S_t 中内容完全一致，原始 Support 确实存在；
3. 全部外部输入根恰好解释 S_t.roots，不删除任何根或 input_record；
4. 非输入剩余事实只属于已定义的派生图类型或 Composite；
5. Condition 不变；未来 I 是同一组不可变 Seed。

不满足任何一项即 `ABLATION_NOT_WELL_DEFINED`，停止该对照，不改 engine。本轮两例均明确成立，不靠臆测“所有没有 INPUT 标签的东西都可删”。同 key 同内容有多种输入来源时，所有原始支持保留；不能只留 first input。

### Composite 清理的混杂边界

B 同时去掉 dependent Composite cache，因为保留它们可能留下已移除 leaf 的成员引用或旧索引。这个清理明确列为辅助干预，不把 Composite 的性质归给 O-G0-1。

若 A 与 B 结构不同，入口另有 aux-only 控制路径：仅清理 Composite/cache，保留全部图事实/普通支持，使用相同 I。只有该控制仍与 A 相同，才允许将 A/B 差异判为 `PRIOR_DERIVED_RESULT_CAUSALLY_RELEVANT`；否则停在 UNRESOLVED。本轮 A=B，**没有触发或执行这条额外控制路径**。

A=B=C 已经说明：连同辅助物化缓存一起移除的前轮派生结果，并非当前结果的必要条件。不能从本轮推断单独持有 Composite 或单独持有某个图节点的效力。

## 3. 两个固定域案例

### 3.1 conflict_and_difference

Condition：一个 ordinary Variable X，namespace=`rrd-single`；预声明 Value(1/2/3)；signature p(node)。全部使用默认冻结 Caps。

H：

- INPUT Relation R:p(X)；
- INPUT Bind(X,1)；
- OBSERVED 再观察同一 Bind(X,1)，新根 H-observed；
- Difference(H0,H1) 带入 Bind(X,2) 与 Appeared notice。

H 完整闭包已形成 Eq(X,X)、两个 PortBind、Conflict(X,{1,2})、Shared 图。未来 I 是同一 Difference(I0,I1)：从已记录的 Bind(X,2) 到 Bind(X,3)，保留原 H-2 根并新增 I-3 根。没有替换/撤销旧绑定；本轮使用现有累积语义，不修订它。

### 3.2 alias_and_future_relation

Condition：两个 ordinary Variable X/Y，namespace=`rrd-alias`；Value(1)；signature p(node)。全部使用默认冻结 Caps。

H：INPUT R:p(X)、Eq(Y,X)、Bind(Y,1)。历史 closure 派生新的 Bind(X,1)、反向/反身 Eq、PortBind 及 Shared 图。

未来 I 是 Difference(I0,I1) 新出现的 R-future:p(Y)，根 I-R。预声明域及 signature 完全不变。后续产生新的对应 PortBind/Shared；新业务 Relation 是本轮输入，不冒称由 engine 发明。

第二例确保消融确实去掉了**派生 Binding**，不是只删除索引或 Shared；第一例则覆盖历史 Conflict 和 INPUT/OBSERVED/DIFF 的双重来源处理。它们是独立实验 fixture，不改旧 fixture。

## 4. A/B/C 操作

| 组 | 起始承载状态 | 本轮输入 |
|---|---|---|
| A FULL_PREVIOUS | 同一 H→COMPLETE 的完整 S_t，经 Engine 的 previous.clone | identical I |
| B DERIVED_ABLATION | 上述 S_t 的 input-only 隔离副本；保留所有声明/原始输入/根/记录，移除派生贡献及 dependent cache | identical I |
| C FRESH_RECOMPUTE | 不传 previous；相同 Condition 下从相同 H+I 执行 | 相同 H 中的每个 seed 和 identical I |

每组独立 Engine 对象，不共享被修改容器；Condition/H/I/cap 相同。A、B 完成后原 S_t digest 仍相同，同时输入内容未变。digest 只用于这个不可变性控制，**不用于代替结果结构比较**。

## 5. 实际删除量

| 案例 | 派生 Eq | 派生 Bind | PortBind | Conflict | Shared | Composite cache | 删除的普通派生支持 | 双重来源 key |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| conflict_and_difference | 1 | 0 | 2 | 1 | 36 | 120 | 44 | 2 |
| alias_and_future_relation | 3 | 1 | 1 | 0 | 78 | 247 | 130 | 2 |

原始 Eq(Y,X) 和原始 Bind 必须保留，即使饱和结果又包含它们的派生支持。input_records 和 roots 完全相同；不是把源历史删掉，再把恢复困难当作前轮组织的独立作用。

## 6. 比较方法和实际结果

`full_compare` 在内存中比较 actual dataclass fact contents 和支持集合，逐项包括：

- canonical relevant facts：所有非 Composite 事实；Relation 的 ports/type 等完整内容也比较，不仅比较 key；
- O-G0-1 图投影；
- 全部 explicit direct supports；
- lossless COMPOSE support index 的实际 leaves/masks/Witness 内容，用完整有限谓词索引证明支持一致，不展开巨大循环 proof tree；
- 所有 root_witnesses、input roots、input_records；
- 全部 auxiliary facts；
- 相对于**同一个完整 S_t** 的 newly formed relevant/graph facts，及包含 future-exclusive input roots 的归因集合。

特别地，B 重推导回来的旧事实不算“未来新形成”：三组统一使用 FULL S_t 为 novelty 基线。Future roots 指 I.sources 中此前不存在的根，不把旧 H-2 根误当新增现实。

| 比较项 | conflict_and_difference | alias_and_future_relation |
|---|---|---|
| A/B/C 状态 | 全部 COMPLETE | 全部 COMPLETE |
| canonical relevant facts | A=B=C | A=B=C |
| 图投影 | A=B=C | A=B=C |
| ordinary direct supports | A=B=C | A=B=C |
| lossless COMPOSE 支持索引 | A=B=C | A=B=C |
| 全部 root witnesses / input roots / input_records | A=B=C | A=B=C |
| auxiliary facts | A=B=C | A=B=C |
| future-I-attributable 新图结构数量 | 三组各 46 | 三组各 28 |
| future-I-attributable 新图结构内容 | A=B=C | A=B=C |
| 首个结构差异 | 无 | 无 |
| 分类 | DERIVED_RESULT_NOT_CAUSALLY_NECESSARY | DERIVED_RESULT_NOT_CAUSALLY_NECESSARY |

第一例最终图包含 Equality=1、Binding=3、PortBinding=3、Conflict=3、Witness=78；第二例包含 Equality=4、Binding=2、PortBinding=2、Conflict=0、Witness=105。这里报告的是图类型计数，不用 Composite 个数代替图证据。

### 辅助工作量

| 案例 | A operations / rounds | B operations / rounds | C operations / rounds |
|---|---:|---:|---:|
| conflict_and_difference | 8280 / 15 | 8287 / 16 | 8287 / 16 |
| alias_and_future_relation | 2211 / 13 | 2218 / 14 | 2218 / 14 |

A 在这两例少 7 次 operations、少 1 轮，说明已有闭包减少了饱和检查工作；没有事实、支持、根或未来归因差异。本轮不以此判组织独立因果效力，不把执行次数误作物理运行时间/无限资源效率证明。

## 7. 自动控制测试与机器记录

最终入口实际执行的 8 项测试：三组 COMPLETE；原 S_t 不变；根/记录/Condition 保留；消融非空且删派生支持；原始输入支持完整保留；未来确实形成新图；分类符合实际逐项比较；机器编码可无损恢复事实/所有直接支持/根和归因集合。均通过，无 failures/errors。

JSON 为避免重复复制相同三份图，使用每例 key_table 对完整 canonical keys 无损编号；仅在内存实际内容/支持/根相等之后，B/C 的 evidence table 才引用 A。编码控制测试解码后逐项核对原始三组表；没有 sampling、top-k、截断或只留 digest。机器记录保留各组工作量、类型数量和归因 key IDs，所有 comparisons 布尔值来自实际内容比较。

COMPOSE 巨量逻辑支持采用 engine 已有无损索引比较，报告记录该比较结果与 stats；图和所有普通 relevant facts 的直接支持/根则实际导出。没有把 JSON 总标签当作这些未发生比较的替代。

## 8. 因果分类与精确限制

本轮结果回答的是**persisted derived result 的必要性**：固定 H、I、Condition、cap，清除已经派生的图及其辅助缓存后，由完整原始材料重推导能够达到相同 COMPLETE 图、新事实和来源。当前两个案例的 O_t 因此表现为可再计算的 materialized closure。

这不推出：

- 前轮派生图从未被读取、在任何计算路径都无用途；
- 历史 H 无关或现实 I 无关；
- 任意 cap/任意 Condition/无限时间实验都会 A=B=C；
- 新组织实例、来源完整性、组织图消费者等既有工作判定需要改写；
- 同一身份的时间修订、开放域输入或生成器可塑性已经验证。

本轮没有 RESOURCE_LIMIT，没有 A=B≠C，也没有 A≠B。因此没有 persisted non-derived 差异来源或首先造成差异的 derived 类型可报告；不能凭“旧 Shared 无直接再读取”预设结果。差异分支若触发，入口会保留差异 key/支持、辅助控制结果并区分 canonical 首差异与尚未建立的时间执行首差异；本轮没有执行这些分支，不声称已验收它们。

结论停在 **DERIVED_RESULT_NOT_CAUSALLY_NECESSARY（上述两个独立有限 fixture）**。保留既有审计原文，不提出修复或新生成机制。
