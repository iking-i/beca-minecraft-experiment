# BECA-V0 第二阶段：最小连续个体核心

历史阶段文档：当前已采用个体生命周期数据库，启动与 Session 规则以 [LIFETIME_STORAGE.md](LIFETIME_STORAGE.md) 为准，后续 Session 不新建 A 数据库。

在已有 [Minecraft 身体接口](minecraft/README.md) 上增加 Python A Core、连续状态记录和独立 Supervisor。当前只做可追踪的环境交互闭环，不包含 LLM、递归、学习、自我修改、自我复制或长期语义记忆。

程序、进程、数据库和游戏角色是承载与交互结构，不把其中任何一个直接等同于 A。`individual_id` 是工程标记，`A0 → A1 → A2` 是同一个实验个体的状态序列。

## 启动

当前电脑的 Node 依赖、Python 虚拟环境和 Python 依赖均已安装。在 PowerShell 中：

```powershell
cd "D:\codex\project\我的世界"
.\.venv\Scripts\python.exe main.py
```

先进入 Java 26.1 测试世界并“对局域网开放”，将端口写入 [minecraft/config.json](minecraft/config.json)。当前为 `62227`；重新开放后可能变化。不要同时启动第一阶段机器人或另一个使用相同身体账号的程序。

首次正常运行创建 `storage/beca.db`。已有实验历史时，程序拒绝直接重新启动这个数据库。完全停止后开始另一次实验，请明确选择新文件：

```powershell
.\.venv\Scripts\python.exe main.py --db storage/experiment-002.db
```

已有验收数据库保留审计用途，不占用默认 `beca.db`。添加 `--duration 10` 可以限定本次时间；默认持续运行。

新机器的安装步骤（Python 3.10+，Node.js 22+）：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm --prefix minecraft ci
.\.venv\Scripts\python.exe main.py
```

## 运行行为和控制

启动顺序：Supervisor → 唯一 A Core 与 A0 → Bridge 进程 → Minecraft 连接/spawn → 观察、状态更新和行动反馈。

策略与核心分离在 [individual/policy.py](individual/policy.py)：首次有效观察后等待 1 秒，前进 200 毫秒，停止，再观察。探测循环只执行一次；随后持续观察，不反复自动前进。这是验收策略，不是智能决策、固定价值观或生存策略。

可以用 `--observe-interval 1`、`--policy-wait 1`、`--move-ms 200` 调整采样和探测参数。

运行终端每行输入一个命令：

| 命令 | 行为 |
| --- | --- |
| `pause` | 停止新的策略动作并释放移动；核心、心跳、观察与状态记录继续 |
| `resume` | 恢复当前运行中的策略调度；不更换 ID |
| `status` | 查看 Core/Bridge 存活信息、版本和 CPU/RAM |
| `terminate` / `exit` / Ctrl+C | 人工终止本次实验 |

pause 不冻结 Minecraft 世界，也不是从完全停止状态恢复主体。正常退出先停止新动作，提交最后事件与状态，再关闭 Bridge、日志连接并释放 Core 实例锁。Core 不响应时 Supervisor 会在宽限期后独立终止 Core 和所属 Bridge；强制终止不能保证写出最后事件，保留此前已提交的历史。

## 状态和事件

`individual/state.py` 的 `AState` 包含：

```text
individual_id / state_version
started_at / last_update_at
latest_observation / latest_action
health / hunger / position / inventory_summary
environment_sequence / status
continuity_required = true
```

没有加入人格、目标或固定价值观字段。`continuity_required` 只记录实验定义，不驱动生存策略。

每次有效观察递增 `environment_sequence`，并产生新状态版本。动作请求/结果、暂停/恢复、Bridge 状态和身体死亡/重生也各自形成明确状态转移。

SQLite 的三个表：

| 表 | 内容 |
| --- | --- |
| `experiment` | 一次实验唯一 ID、开始时间和实验定义 |
| `states` | A0、A1、A2…每个版本的完整 JSON 快照 |
| `events` | 按 event_sequence 排序；包含 event_id、timestamp、individual_id、state_version、event_type、payload |

每次更新在同一事务中插入快照、原因事件和 `STATE_UPDATED`，提交成功后才更新内存状态。版本从 0 逐一增长，历史行禁止 UPDATE/DELETE。数据库不是防管理员篡改的安全存储。

跨进程文件锁确保同一个实验数据库只有一个活跃 Core。死亡、重生、断线和正常重连不重新生成 ID。公开 A 动作只允许 `move/interact/chat`；没有修改 Supervisor、宿主文件或访问原始 Mineflayer 对象的接口。

## 验证连续状态链

以下命令只读检查 ID 一致、版本连续、事件与快照一致、有效输入递增环境序列，也可以在运行期间使用：

```powershell
.\.venv\Scripts\python.exe -m individual.inspect --db storage/beca.db --history
```

`valid_state_chain: true` 表示工程记录通过检查，不证明完全停止后的主体连续性。

查看已经成功完成的真实闭环验收：

```powershell
.\.venv\Scripts\python.exe -m individual.inspect --db storage/individuals/A-033b3758-d7a1-450d-b911-2f2db2dadf9a/stage2-live.db --history --limit 40
```

该记录为 `A0 → … → A18`，包含 10 次环境输入、前进/停止和后续观察，详见 [VALIDATION.md](VALIDATION.md)。

## 用 SQLite 查看历史

不必另装工具，可用 Python 自带入口：

```powershell
.\.venv\Scripts\python.exe -m sqlite3 storage/beca.db 'SELECT individual_id,started_at FROM experiment;'
.\.venv\Scripts\python.exe -m sqlite3 storage/beca.db 'SELECT state_version,event_type,timestamp FROM events ORDER BY event_sequence;'
.\.venv\Scripts\python.exe -m sqlite3 storage/beca.db 'SELECT state_version,snapshot FROM states ORDER BY state_version;'
```

查询某个版本的事件：

```sql
SELECT event_sequence, event_id, timestamp, individual_id,
       state_version, event_type, payload
FROM events
WHERE state_version = 8
ORDER BY event_sequence;
```

查看观察前后坐标：

```sql
SELECT state_version,
       json_extract(snapshot, '$.environment_sequence') AS environment_sequence,
       json_extract(snapshot, '$.position') AS position
FROM states
ORDER BY state_version;
```

## 外部 Supervisor

[supervisor/limits.yaml](supervisor/limits.yaml) 配置 RAM、总 CPU、采样间隔、超限次数、心跳超时和退出宽限期。CPU 100% 指一个逻辑 CPU 满载。当前采用定时检测、记录和超限终止，不是 OS 硬配额。

外部资源和控制日志保存在匹配的 `*.supervisor.db`，如 `beca.supervisor.db` 的 `supervisor_events` 表，不作为 A 的记忆或状态组成部分。

Core 的输出只作为遥测读取，不能修改资源限制或对 Supervisor 发出控制命令。本阶段没有不同 OS 用户、ACL 或容器隔离，不宣称抵御同一用户下的任意恶意程序。

## 停止、持久化与主体连续性

只保证正常实验运行期间状态转移在同一条活动链中按序记录。SQLite 快照用于调试、审计、崩溃分析，不是身份本身。

当所有连续承载完全停止后，读取快照是否仍是原主体，这个问题保持开放。当前没有自动恢复：重用已有实验历史会报错；另一次实验使用新数据库和新 ID。运行中的暂停/恢复与 Bridge 重连不会重建 Core 或更换 ID。

## 测试、结构与 TODO

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

21 项测试通过；真实 Minecraft 的观察、前进/停止、状态链、人工暂停/恢复/终止和身体死亡/重生已验证。真实掉线重连仍需专门联调。验收进程均已退出。

```text
main.py / requirements.txt
README.md / VALIDATION.md
individual/
  __init__.py / identity.py / state.py / events.py
  core.py / bridge.py / policy.py / inspect.py
bridge/
  package.json / server.js
supervisor/
  __init__.py / supervisor.py / limits.yaml
storage/
  README.md
  beca.db                         # 首次正常运行生成
  beca.supervisor.db              # 外部监控记录
  stage2-*.db                     # 验收记录
tests/
  __init__.py / test_core.py / test_supervisor.py
  fixtures/
minecraft/                        # 第一阶段代码保留，仅更新端口
```

TODO：真实网络重连验收、OS 硬配额和文件权限隔离、长期磁盘/历史归档。完全停止后的主体连续性、持续冗余或热迁移没有解决。递归引擎属于后续阶段，本次到这里停止。
