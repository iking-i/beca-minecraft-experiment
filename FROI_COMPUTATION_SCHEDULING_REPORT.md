# FROI-1 Live Computation Scheduling Isolation

日期：2026-10-05。当前问题：CURRENT_IMPLEMENTATION_BUG / LIVE COMPUTATION SCHEDULING BLOCKER。

## 基线与范围

GitHub main：`12bd2c326a15772576a762119d672f7348a66416`，标题 `Integrate FROI-1 formed organization into formal internal reads`。开始时 main 没有额外变更。本地 HEAD 为 `7bfdfb9e957598e1eff8b8ba153e766c02f677dd`；其 runtime、integration、Supervisor、GSC、身体、tests、debug 及本轮指定文档的所有 blob 与该远程基线一致。两个提交的历史父链不同，不把本地 SHA 冒称远程 SHA。

开始前读取完整讨论约束、研究状态、FROI-1、上一轮实现报告与相关执行源码。本轮不改理论、不改组织生成规律、不解决移动倾向、不运行 Minecraft 或正式 A、不执行 live T1–T5。

保留的真实历史：`storage/individuals/A-43959494-6cca-4edc-8400-520e94ee5776/` 中的两次 session 及其 Supervisor 数据。此前观察到 operations 133 → 2290 → 66054 → 2098049 → 20000001、Composition 阶段 RESOURCE_LIMIT 与 core_unresponsive 强制终止。本轮不改写这些历史证据；这种终止是宿主调度失败，不冒称 A 自主退出、GSC 要求生命周期结束或理论连续性验收失败。

## 变更文件

- `integration/froi_worker.py`：immutable JobSpec、结果 envelope、task-scoped subprocess、身份核对、取消与资源遥测。
- `individual/formal_froi.py`：在原真实 relation-read 位置 yield checkpoint；原消费者与后续处理不变。同步兼容入口和异步运行入口驱动同一个 continuation，没有第二套 FROI 语义。
- `individual/core.py`：正式 CLI FROI 路径启用 worker；冻结 checkpoint、poll、精确校验、恢复 consumer、人工取消。
- `supervisor/supervisor.py`：分别统计 Core、Bridge、worker，并在原资源预算内监控；向 Core 传递宿主终止分类。
- `tests/test_froi_scheduling.py`：13 项新增工程验证。
- `tests/fixtures/froi_worker_hook.py`：隔离测试中的慢任务、crash、损坏输出控制。
- `tests/fixtures/froi_scheduling_core.py`：实际 Core.main / Supervisor 配合惰性假身体的进程测试；仅 fixture 临时数据库。
- 本报告及 `FROI_COMPUTATION_SCHEDULING_VALIDATION.json`。

## Worker 架构与输入身份

```text
真实 FormalFROI read checkpoint（continuation 暂停，未提交本轮状态）
  → immutable JobSpec
  → 单一 task-scoped worker
  → 原 produce() / 原 GSC-0 全部阶段
  → typed result envelope
  → A 精确校验来源与 Condition
  → 原 consume(Shared / PortBind)
  → 恢复同一 continuation，提交正式观察与处理日志
```

worker 每个 job 启动一个进程，结果返回后退出。只接受父进程私有管道中的完整 immutable 输入，不读写 EventStore、不拥有策略或历史、不跨任务保持状态、不创建 A、layer 或 agent。线程仅承担父子管道 I/O，不执行 closure。Windows venv launcher 及真实 Python 子进程一起取消、回收。

JobSpec 固定：individual_id、session_id、source_state_version、history.state_version、完整 event_cutoff/history events、当前完整 frame、feedback/q_t、实际 reference origin、codec/FROI version 与原 GSC Caps。完整材料可无歧义重建 Condition 和全部 seeds；不截取历史。稳定 job_id 是完整规范输入的摘要；校验同时比较完整输入 identity，不只比较摘要。父端进一步校验返回 handle 的 frame、version、reference、origin、cutoff 与按原 codec 重建的 Condition。

`source_state_version` 保留原 FROI 含义：该读取待提交的目标版本；Core 还固定并核对读取前的 base_version、session 与完整内部状态。任何来源不匹配成为 STALE_RESULT；不自动改绑、重试、fallback 或消费旧图。

同步 `advance()` 与直接 ACore API 的同步兼容方式保留，供已有控制测试和 detached 工具使用；正式 `main.py --froi` 的 Core CLI 明确传入 `froi_async=True`，使用隔离调度。兼容调用不是本轮声称隔离的正式启动路径。

## Freeze / wait 语义

同一时刻最多一个 job。等待期间不采集新的正式 observation，不写新 WORLD_OBSERVATION，不推进 FormalFROI、环境序号或动作。已开始的当前观察在 continuation 中等待，原 pending actions 不被丢弃。

Core 继续 tick、heartbeat、Bridge lifecycle 处理、Supervisor 控制和 worker 监测。资源采样只在递归状态之外保留当前监测值；人工 pause/resume 使用宿主控制标志，审计事件随结果提交或取消保存，不改变冻结的递归 checkpoint。等待不是 A 自己选择的策略，而是 EXTERNAL_FIXED_MECHANISM / experiment scheduling condition。没有原始观察缓冲合并或异步 state merge。

Bridge 状态变化或 session 结束会明确取消当前 job，再按原生命周期路径处理，不把旧结果接到变化后的状态。人工 terminate 取消 worker、关闭 continuation、写取消来源，随后关闭 session / Bridge / Core；不发布未完成图。

读取完成后继续原 tick 中应执行的阶段：如果暂停发生在动作前，恢复动作阶段；如果发生在动作后观察，恢复下一轮的正常间隔。否则反复先开启观察会饿死原动作阶段。该处理只保存原执行顺序，没有改 sampler、参数 binder、动作概率或移动偏好。

## Supervisor 与结果分类

独立采样 Core、Bridge、worker CPU/RAM/alive。worker 由已发现的 Core 后代进程句柄确认，worker 子进程不再计入 Core 统计。已有 Core RAM 预算仍覆盖 Core + worker 总量（512 MB）；Bridge 1024 MB、总 CPU 200%、heartbeat 45 秒和其他原上限保持不变。没有新增免费 worker 资源额度。

原 GSC 返回分类：COMPLETE / RESOURCE_LIMIT / INVALID。原 produce()、consume()、codec、Caps、Composition、生产规则字节不变；RESOURCE_LIMIT 仍走已有读取失败/raw consequence 路径，不发布 partial graph、不自动终止 A。

宿主执行分类独立：WORKER_FAILED、WORKER_EXITED、CANCELLED、HOST_RESOURCE_LIMIT、STALE_RESULT。crash、管道异常、宿主 RAM/CPU 终止均不伪装为 GSC RESOURCE_LIMIT。worker host failure 被审计后按宿主终止路径停止，不伪造递归反馈或自动恢复。没有另行发明 worker wall-clock timeout / WORKER_UNRESPONSIVE；长合法计算依旧受原 GSC caps、宿主预算及人工终止限制。

## 实际验证

全部使用 TEST_ONLY fixture / `.test-tmp/`，没有连接真实 Minecraft。

| 回归组 | 数量 | 结果 |
|---|---:|---|
| 原 Python 回归 | 141 | 全通过 |
| 既有 FROI 接口控制 | 15 | 全通过 |
| 新调度控制 | 13 | 全通过 |
| 冻结 GSC-0 / GSC-1 | 44 | 全通过 |
| 既有 persisted-result 控制 | 8 | 全通过 |
| 身体 / world-entry Node 回归 | 42 | 全通过 |
| 合计 | 263 | 全通过 |

新增测试覆盖：one-in-flight；正式观察冻结；等待期间无动作；pause；COMPLETE 与同步原 producer 的 Shared/PortBind 消费一致；原 RESOURCE_LIMIT 不终止 Core 且真实失败再进入；INVALID 无旧表 fallback；所有身份字段与 Condition mismatch；STALE_RESULT 不消费；worker crash；损坏输出；取消整个 worker 进程树且无 partial；实际 Core.main 心跳/暂停/终止/三方资源统计；原动作阶段不被饿死；原宿主预算不扩大。一个 test 同时覆盖多个要求。

关键进程控制：worker 固定延迟 20 秒，隔离 fixture 的 heartbeat timeout 为 3 秒，等待观察 3.4 秒；期间至少三个真实 heartbeat，版本和环境序号保持一致，暂停标志可见，Supervisor 没有 core_unresponsive；随后人工终止，Core、假 Bridge 与 worker 退出，取消事件落盘。生产 timeout 仍是 45 秒，没有修改 limits.yaml。这个缩时控制验证调度独立性，不是新 live FROI 验收。

初次沙箱回归的 Python 部分通过，但两个原 Node 网络测试受到 EACCES / 超时限制。开放本机临时测试端口后完整重跑，263 项全部通过；未修改原测试断言，也未连接游戏。最后完整运行包含上述动作阶段恢复控制。

完整回归入口沿用：

```powershell
.\.venv\Scripts\python.exe -m debug.froi_validation --baseline 12bd2c326a15772576a762119d672f7348a66416 --output .test-tmp/新的回归报告.json
```

该旧入口的 FROI readiness 字段不能当作本轮 live 结果；本轮分类以新验证 JSON 为准。旧报告未覆盖。单独调度验证：`python -m unittest tests.test_froi_scheduling -v`。

## 保护与真实边界

60 个受保护文件（包含冻结 GSC、身体、原测试、原 FormalL0、原 FROI produce/consume/codec、规格与 limits）与执行前 SHA256 相同。29 个已有 storage 文件逐字节未改变，包括 live individual/supervisor DB、WAL、锁与历史记录。机器报告保存全部原始哈希及空变化列表。本轮不修改旧审计、旧结果或理论仓库。

组合增长问题没有解决，也没有规避。隔离后真实历史仍可能得到 RESOURCE_LIMIT 或触及原宿主资源预算；这些必须原样报告。没有证明 live COMPLETE、行为作者权、Perfect Recursion 或 L1。

```text
IMPLEMENTATION: PASSED
SCHEDULING ISOLATION: PASSED
CLASSIFICATION: FROI_COMPUTATION_SCHEDULING_ISOLATED
GSC-0 RULES: UNCHANGED
FROI-1 CRITERION: UNCHANGED
OLD LIVE DATA: UNCHANGED
LIVE FROI T1-T5: NOT_EXECUTED
NEXT: READY_FOR_LIVE_RETRY
```

正式重试仍使用已有 `main.py --froi` 入口及现有端口选择机制。本轮没有自动重启正式 A。
