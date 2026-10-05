# Windows 实验启动器实现报告

日期：2026-10-05。远程基线：`d07c3831dbd37ef60391cf96d463d84776c51819`。

本轮仅增加实验者启动管理 UI，不改变 FROI、GSC、FormalL0、Core、Supervisor、动作采样、能力、理论或实验判据。未启动真实 A、连接 Minecraft、执行 live FROI 验收或修改既有数据库。

## 文件与入口

修改：`main.py`、`individual/storage.py`、`.gitignore`、`README.md`。

新增：`launcher.py`、`tests/test_launcher.py`、本报告、`WINDOWS_LAUNCHER_VALIDATION.json`。

```powershell
.\.venv\Scripts\python.exe main.py
```

无参数启动显示中文 tkinter 窗口：可滚动的已有 A 列表、名称与完整身份、角色、数据库路径、创建时间、最新 state_version、Session 数、当前选择 ★，以及“新建个体 A”、端口、默认勾选的 FROI-1、“启动实验”和“取消”。当前选择区显示数据库路径。标准库 tkinter 可用（8.6），没有引入新依赖。

有任意显式命令行参数时完全跳过 GUI，调用原 `supervisor.cli()`；例如 `main.py --froi --port 51234`、`--use-config-port`、`--help`、原 `--branch-db` 行为保持。GUI 返回 LaunchConfig，在同一 main 进程关闭窗口后调用原 CLI，不再启动第二个 main.py。GUI 不传 `--db`，继续遵守 pinned lifetime。

无参数且 tkinter 不可用/无法打开显示窗口时，给出明确错误和显式 CLI 用法，退出码 1；取消或关闭窗口返回 0，不启动 Core。

## 发现与选择已有 A

`list_lifetimes()` 扫描 `storage/individuals/`，以各目录的 `lifetime.json` 为来源；`storage/index.json` 只补充名称，不能作为身份凭据。临时目录、损坏 manifest、缺失/损坏数据库、身份不一致、非 mainline / snapshot branch 均不列入可启动项。

`lifetime_entry()` 使用只读 SQLite 与原 `individual.inspect.verify()` / history 校验，检查完整状态链和 session 关联，并核对数据库与 manifest 的 identity/role。目录名必须匹配身份，数据库固定为该目录的 individual.db，不允许 manifest 路径绕出目录。无有效 WAL 时使用 immutable 只读连接；有 WAL 时尊重真实历史，不能忽略 WAL 读取旧状态。

`select_existing_lifetime()` 是明确的外部选择管理函数：

1. 限定目标位于选定 storage root，校验 mainline manifest 与历史。
2. 持有选择文件管理锁，使用原 ExperimentLease 校验目标与当前个体都未运行；有活动 lease 则拒绝。
3. 持锁后重新校验，比较旧指针字节，拒绝并发改绑。
4. 更新目录索引，以原 `write_json()` 的临时文件 replace 原子切换 `individual/lifetime.json`。索引写入失败不会先改变指针。
5. 释放管理锁；原 runtime 在正式启动时仍执行自己的 preflight 和 lease 检查。

没有 EventStore 写入、初始化、状态变化、身份重新生成、旧目录删除或数据库改写。可启动性检查与 runtime lease 是两道检查，不宣称 GUI 能永久预占将来的 Core lease。当前正在运行的 A 也不能被切换离开。

损坏的其他 catalog manifest 不再阻塞原 `update_index()` 管理操作；其损坏数据仍留在原目录。本轮未增加针对 A 的历史清理逻辑。

## 新建与缺失选择

“新建个体 A”完整复用 **未修改** 的 `individual.storage.create_lifetime()`，输入 label，分配新身份与独立目录，自动成为选中 A。旧 A、previous-selection.json、初始化报告与原审计规则保留。

若当前选择指向缺失数据库，窗口先提示，再单独要求确认。只有确认后才传 `replace_missing_selection=True`；默认拒绝，不把创建新 A 称作恢复原 A。取消名称输入/拒绝确认不会创建 A。若已经明确创建新 A，随后取消启动窗口仅取消启动，不删除这次明确创建的 A。

## 端口、FROI 和启动顺序

端口默认从 `minecraft/config.json` 读取。启动前复用 `parse_minecraft_port()`，合法范围 1–65535。本次值通过 `--port` 传入原 Supervisor，不修改 config。本版本没有保存默认端口复选框。

FROI-1 默认勾选，相当于 `--froi`；取消勾选则不传该选项。准备启动复用原 Formal 与 FROI preflight，包括正式容量、Supervisor 资源与身体感知容量检查。已锁定 FROI 的 A 不能用非 FROI 模式启动；错误显示在 messagebox，指针不切换。

启动顺序：验证目录/历史 → 验证端口 → 原 preflight → 安全选择已有 A → 关闭窗口 → 同一进程原 Supervisor CLI。任何准备失败保留窗口供修正，不启动 Core。理论和递归过程不参与 GUI 选择。

## 验证结果

机器报告：`WINDOWS_LAUNCHER_VALIDATION.json`。

| 组别 | 数量 | 结果 |
|---|---:|---|
| 原 Python（含 FROI 与调度隔离） | 169 | 全通过 |
| 新 launcher 控制 | 16 | 全通过 |
| 冻结 GSC-0 / GSC-1 | 44 | 全通过 |
| 既有 persisted-result 控制 | 8 | 全通过 |
| 身体 / world-entry Node 回归 | 42 | 全通过 |
| 合计 | 279 | 全通过 |

16 项新增测试覆盖枚举与元数据、损坏/不一致/非主线拒绝、指针与索引更新、数据库字节与版本不变、目标活动 lease、当前活动 lease、新建委托原函数及旧历史/previous-selection 保留、缺失选择明确确认、端口校验、原 preflight 与本次端口、显式 CLI 绕过、无参数 GUI、取消不启动、headless 错误、锁定 FROI 拒绝与指针不变、其他损坏 manifest、索引失败不改指针。测试仅使用 `.test-tmp/` fixture。

另外使用真实 tkinter 创建隐藏的 TEST_ONLY 窗口，检查中文控件树和关闭行为，结果通过。未打开正式实验、未模拟点击真实 A 的启动按钮。这是原生窗口构建 smoke，不冒称完整人工视觉验收。

完整回归沿用 `debug.froi_validation`，新输出位于 `.test-tmp/launcher-regression-2.json`，旧报告不覆盖。第一遍所有 suite 通过，但保护检查发现当时仍在编辑 README，因此固定后完整重跑；最终全部 suite 与保护检查均通过。远程 README 与本地旧版不同，本轮用规范换行的三方合并保留远程理论引用/研究说明，只叠加启动器说明；没有以本地旧 README 覆盖远程研究内容。

原 runtime、原测试、FROI/GSC 字节、实验判据、旧报告等受保护文件不变；既有 storage 文件与当前 lifetime selection 均与本轮执行前 SHA256 一致。最终机器报告保存哈希与空变化列表。GUI 以后经实验者明确操作可以更新 selection/index 或创建新 A；这些管理操作不属于 A 的自主行为，不写成内部决策。

```text
WINDOWS_LAUNCHER_IMPLEMENTATION: PASSED
REGRESSION: PASSED (279)
EXISTING_LIVE_DATABASES: UNCHANGED
FROI / GSC / FORMALL0 / ACTION / CRITERIA: UNCHANGED
LIVE_FROI_T1_T5: NOT_EXECUTED
```
