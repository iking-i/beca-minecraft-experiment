# GSC-1 Prototype Validation

日期：2026-10-05。冻结 GSC-0 基准：`8801ca88093e5c66fa11ba6eb4c084608a1bd690`。

**GSC1_PROTOTYPE = passed**。独立 TEST_ONLY consumer；本次不修改 GSC-0 或正式运行系统。

## 实际执行结果

`python -m experimental.gsc1.validate` 实际运行 GSC-1 **21 项**和冻结 GSC-0 回归 **23 项**。
GSC-1 failures/errors：0/0；GSC-0 failures/errors：0/0。未跳过测试。

History_A = (A0, B0, C0); History_B = (A1, B0, C1)。两个结果均 COMPLETE_GROUNDED，历史 closure 端口均 UNRESOLVED。

## 条件与因果

三个类型、六个普通变量、六个有限枚举值和 schema 完全相同。两个历史共用相同 CurrentInput tuple：Eq(h0,p0)、Eq(h1,p1)、Eq(h2,p2)，來源 D0/D1/D2。历史唯一差异是 H0、H2 的变量—值 Binding 内容；H1 不变。

初始历史只有 h0/h1/h2 的三个独立 Bind，不含任何 p0/p1/p2 Bind 或完整 outward。当前 explicit equality 使 GSC-0 PROP-ALIAS 产生输出绑定；每个新绑定都有对应 Hi、Di 输入根和全部直接支持。原 closure 还形成包含历史 Bind、当前 Eq、新 Bind 的 Composite；不会为了 GSC-1 删去其他组合。

checker 扫描整个 COMPLETE closure。对每个端口精确去重后的值集合，0→UNRESOLVED、1→GROUNDED、>=2→CONFLICT。全部 singleton 才逐项解包形成完整 tuple。schema 固定字段身份、类型和顺序，不提供值；包装不增加推理、分数、候选、规则、动作或 GSC-0 事实。

## 核心验收

| 检查 | 实际测试内容 |
|---|---|
| 唯一完整 grounding | A/B 得到两个不同完整 tuple，历史中尚无输出端口绑定 |
| Paired-history causality | 相同实际 input/source/Condition/schema；交换历史可复现另一结果 |
| History ablation | 两个历史各删除三个关键历史 Bind，六次全部重建 closure；对应端口缺失 |
| Current-input ablation | 两个历史各删除三个 Eq，六次全部重建 closure；对应端口缺失 |
| Conflict | B0/B1 全部传播，输出保留两值证据，不构造完整 tuple；独立三值测试也全部保留 |
| Mixed failure | 缺失与冲突端口同时保留；overall CONFLICT 不解决任何值 |
| Order independence | 两个历史 × 三种 seed 顺序 × 三种 queue/rule 顺序；18 次 COMPLETE closure 和完整 GroundingResult 按内容相等 |
| Idempotence | 两个 COMPLETE closure 重新闭包、重新 grounding 后全部内容相同 |
| Upstream resource rejection | 小 cap 的 working state 已有所有端口 Bind，仍 RESOURCE_LIMIT；GSC-1 不接纳成成功 |
| No default / old value filling | 缺失返回 outward=None；新 scope 不复用同名旧变量；先完整再缺失也不缓存旧 tuple |
| Lineage | 所有派生对象有有限根；逐端口保存所有直接支持和所有输入根，含 Hi/Di/PROP-ALIAS |
| Invalid input | 错 schema、域、类型或非法 upstream 明确 INVALID，不丢弃问题绑定后冒称成功 |
| Isolation | 双向 import 边界检查；checker 只读，包装不插入原 closure |

核心检查最终状态见机器报告，表中的测试内容不取代实际执行结果。

## 作者权审计

实现位置：`experimental/gsc1/grounding.py::check_grounding`。输出值提取只使用 `(unique_value,) = port.values`，位于所有端口已判 singleton 的路径。机械包装没有 choose/prefer/fallback/repair 或 normalize-by-preference；没有 selector，也没有 NO_OP。

EXTERNAL_FIXED_MECHANISM：GSC-0 固定规则、schema、精确值数量条件和包装机制。EXPLICIT_FIXTURE_INPUT：人工历史 Bind 与当前 Eq。具体派生输出由历史和当前输入共同决定。此结果证明条件下的结构确定性，**不证明新值创造、schema/equality 的自主发现、一般智能、主体连续性或 L1**。

规范 identity 与 provenance 分离；JSON 保存每个端口完整 direct-support 集合与有限 input roots，closure digest 指向原有全部 immediate graph/COMPOSE 无损索引。没有 first-proof 取舍或无限展开循环 proof tree。

## 冻结边界与文件

验证前后核对 **123 个基线 tracked 文件**字节 hash：全部相同。冻结 GSC-0 文件 hash 单列在 JSON。本次没有调用 GSC-0 validate，没有写旧报告，没有连接游戏、数据库或正式 A。

- [规格](GSC1_DETERMINATE_GROUNDING_SPEC.md)
- [原型与运行说明](experimental/gsc1/README.md)
- [源码](experimental/gsc1/grounding.py)、[测试](experimental/gsc1/tests.py)
- [机器报告与完整端口来源](GSC1_PROTOTYPE_VALIDATION.json)

```powershell
.\.venv\Scripts\python.exe -m unittest experimental.gsc1.tests -v
.\.venv\Scripts\python.exe -m experimental.gsc1.validate
```

GSC-1 是 frozen GSC-0 的 consumer。现有 API 足以完成本轮；未发现必须修改上游的接口缺口。未继续接入正式 runtime 或实现真实输出。
