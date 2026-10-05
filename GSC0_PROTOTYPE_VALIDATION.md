# GSC-0 Prototype Validation

日期：2026-10-05。基准：`6491e8588795e44eba9e1da5161fe0eaed391b1f`。

**GSC0_PROTOTYPE = passed / PROTOTYPE_PASSED**，仅限独立 TEST_ONLY GSC-0 规格验证。正式 FormalL0、Minecraft、A、冻结验收和行为闭合结果未改。

## 实际执行

`python -m experimental.gsc0.validate` 实际运行 **23 项测试，全部通过**。原型只依赖标准库及自己的目录；源码 AST 检查确认没有正式 runtime 导入依赖，正式 runtime 也不导入它。验证前后核对 113 个既有 tracked 文件字节 hash，全部相同；没有打开 SQLite、启动 A 或接触游戏。

源码：[model.py](experimental/gsc0/model.py)、[engine.py](experimental/gsc0/engine.py)、[fixtures.py](experimental/gsc0/fixtures.py)、[tests.py](experimental/gsc0/tests.py)、[validate.py](experimental/gsc0/validate.py)。小型机器报告：[GSC0_PROTOTYPE_VALIDATION.json](GSC0_PROTOTYPE_VALIDATION.json)。

## 核心结果

- R4 真实形成，初始闭包中不存在。成员为 R1/R2/R3/Bind(X,3)，可追溯到 R1/R2/R3/D1/D2；保存 138 种 COMPOSE 直接支持。
- 去掉 R2、D1 或 D2 后，重建 seed closure，指定 R4 均不形成。
- 3 种 seed 顺序 × 3 种 queue/rule 顺序：9 次 COMPLETE 结果的事实、全部普通支持、根输入和 COMPOSE 支持索引按实际内容精确相等，不只比较 hash。
- 重复 closure 的全部规范内容与直接支持相同。
- 独立双变量/双端口冲突 fixture：Y 的 2/3 均传播到 X 和所有合法端口，保留 X/Y 的 Conflict，未生成 1；Conflict 参与组合。该较小条件是独立完整实验，不是裁剪核心 fixture 的工作前缀。
- 新业务 Relation 数量为 0；结构相连不生成语义捷径。
- 小结构 cap、workspace cap、operation cap、round cap、provenance cap、累计输入 cap 返回 RESOURCE_LIMIT/closure_complete=false；失败 batch 不部分采用，历史与 pending 输入保留，不 eviction/top-k/fallback。
- 所有派生对象都有有限根见证。循环使用有限直接支持图；普通规则全部适用支持已饱和。独立小型全端口/全支持对 oracle 检查 COMPOSE 支持集合及数量；另一递归支持联集 oracle 检查连通子集，没有漏项。

## 完整来源保存的表示边界

核心闭包有 16 个 leaf、5368 个 Composite，逻辑饱和支持图含 788693218 个规则实例、2365844080 条 premise edges。**这些数字是完整有限支持图的精确逻辑基数，不是声称逐条执行了这些次数。** 实际扫描/规则检查次数为 66054。

逐条展开如此大的 COMPOSE 图会掩盖原型本身。实现保存全部 connected-support masks 与全部 incidence witnesses，形成 lossless finite join index；`State.direct_supports(key)` 可完整展开任一 Composite 的全部直接支持。对任意支持 S/T，满足 sharing 的 witness 全部有效；索引没有 preferred proof、first proof、pruning、排序保留或随机抽样。

COMPOSE 的一条直接支持为 canonical 的两个 operand support keys 加一个 shared witness key，允许重叠/自支持；重复 premise 按集合去重。`CompositionIndex.counts()` 精确计算逻辑实例和 premise edge 数，并用独立显式小图验证。普通支持显式存集合；Composite.shared 是完整 witness 投影，不只留一个共享节点。索引基数/普通支持计入 provenance 存储上限；未把逻辑边数冒充实际存储条目。

最终闭包可以分层计算：ALIGN/PROP/CONFLICT 达到不动点后，构造全部 incidence witnesses，再按支持大小穷尽所有连通子集。COMPOSE 不能产生新的 Eq/Bind/业务 Relation，因此该计算是同一最小不动点的依赖分层，不是规则优先级或丢弃任何适用变化。已有 Composite 可再次参与 COMPOSE，全部对应直接支持仍保存于索引。

## 组合增长诊断

输入为同一个类型的链状 seed Relation。节点和 Value/引用域固定声明于各独立条件，所有规模使用相同 cap：structures=10000、provenance index entries=10000、workspace items=30000；无 pruning、无升 cap 救援。

| seed Relation 数量 | 状态 | leaf | Composite | 逻辑规则实例 | 逻辑 lineage edges | rounds |
|---|---|---|---|---|---|---|
| 1 | COMPLETE | 3 | 3 | 113 | 277 | 6 |
| 2 | COMPLETE | 5 | 14 | 1402 | 3988 | 8 |
| 3 | COMPLETE | 7 | 41 | 12275 | 36131 | 10 |
| 4 | COMPLETE | 9 | 100 | 85460 | 254362 | 12 |
| 5 | COMPLETE | 11 | 223 | 515477 | 1540977 | 14 |
| 6 | COMPLETE | 13 | 474 | 2831670 | 8481064 | 16 |
| 7 | COMPLETE | 15 | 981 | 14595287 | 43751647 | 18 |
| 8 | COMPLETE | 17 | 2000 | 71914744 | 215662870 | 20 |
| 9 | COMPLETE | 19 | 4043 | 342873881 | 1028432717 | 22 |
| 10 | COMPLETE | 21 | 8134 | 1594842938 | 4784098180 | 24 |
| 11 | RESOURCE_LIMIT | 23 | 8205 | 1367469519 | 4102025403 | 16 |
| 12 | RESOURCE_LIMIT | 25 | 5499 | 462312385 | 1386718935 | 14 |

RESOURCE_LIMIT 行显示的是完整已提交阶段/支持大小 batch 的工作状态，**不是该规模的全部 closure 数量**；不能拿这些前缀作为增长总量。failed batch 和 pending 输入不会变成新的完成结果。运行秒数与具体 limit 在 JSON 中。

结构和直接支持图增长明显；压平 Composite 阻止无限嵌套树，但不能消除有限连通支持的指数增长。无新语义/值/类型生产，也没有普遍无限生成或正式 A 的组织改造。

## 运行

```powershell
.\.venv\Scripts\python.exe -m unittest experimental.gsc0.tests -v
.\.venv\Scripts\python.exe -m experimental.gsc0.validate
```

本次判定基于实际执行的核心条件；增长资源中断与正确的 incomplete 行为是单列诊断，不被改称 COMPLETE。原型没有接 FormalL0/Minecraft，没有行为输出、Effect/action/selector/reward/semantic inference/L1。
