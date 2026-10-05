# TEST_ONLY GSC-0

独立标准库原型，依据根目录 `GENERATIVE_STRUCTURAL_CLOSURE_SPEC.md`。不导入或连接正式 A、FormalL0、Supervisor 或 Minecraft；不输出行为。

在项目根目录运行：

```powershell
.\.venv\Scripts\python.exe -m unittest experimental.gsc0.tests -v
.\.venv\Scripts\python.exe -m experimental.gsc0.validate
```

第二条命令运行测试与有限增长诊断，写小型 `GSC0_PROTOTYPE_VALIDATION.md/.json`，不写个体数据库。未配置第三方依赖。

`Engine.run(seeds, previous=None)` 返回 COMPLETE 或 RESOURCE_LIMIT。只有 `closure_complete=true` 才是完整闭包；非法类型/身份输入明确抛出 ValueError，不择一修补。

基础支持显式保存，全部 COMPOSE 直接支持用有限、无损的连接索引保存，可由 `State.direct_supports(composite_key)` 展开。报告的 logical support/edge 数与实际 index storage、计算次数分列，不能把前者当成物理分配或执行次数。

旧完成状态只读克隆；失败 round/支持大小 batch 不部分提交。所有合法连通成员集合都保留，Conflict 不解决，没有排名、择优或 pruning。
