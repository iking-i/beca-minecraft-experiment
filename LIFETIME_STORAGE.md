# 个体连续生命周期存储约束

从本次修正起，数据库属于 Individual Lifetime，Experiment Session 是其中的一段运行记录。常规启动、Minecraft 重启、参数调整和环境切换不创建新 A、不清空 InternalState、不把 state_version 归零。

## 当前 A 主线

- individual_id：`A-4369420c-26f2-49b1-bbde-dd2b55c6f1fe`。
- 生命周期数据库：`storage/individuals/A-4369420c-26f2-49b1-bbde-dd2b55c6f1fe/individual.db`。本次按用户要求注册新生命周期，不迁移旧实验。
- 主线登记：`individual/lifetime.json`，同时固定数据库路径和身份。
- 首次登记保存了 A0，后续状态持续追加；当前版本以数据库为准，登记报告是历史记录。
- 一次性注册记录见 `storage/individuals/A-4369420c-26f2-49b1-bbde-dd2b55c6f1fe/reports/lifetime-initialization-report.json`；重复初始化同一文件会拒绝。
- 首次正常启动开启第一个 Session，追加 A1；此后始终沿用该 ID 和 started_at，版本全局递增。

用户明确选择重新开始，因此旧数据库没有作为新 A 的历史。此前对旧数据库添加的迁移元数据已撤回，原 65 个状态和 392 条事件的内容校验一致，撤回记录保留在 `storage/individuals/A-ee858dbd-002b-4cdb-a8ff-c1de059614f9/reports/lifetime-migration-report.json`。其他旧数据库也保留，不伪造或合并成新 A 的过去。不要删除当前生命周期数据库，也不要通过换一个空文件来继续后续 Session。

## 启动与 Session

每个 A 的数据库、监控与报告存入 `storage/individuals/<individual_id>/`。同一 A 的 Session 共用一个文件夹；独立旧实验与快照分支分别存放。当前目录由 `individual/lifetime.json` 选择，索引见 [storage/index.json](storage/index.json)。当前已有数据已校验内容后整体移动，没有重写状态或重新生成身份。

如果明确要从零测试另一个 A，先正常退出，再执行 `python -m individual.lifetime initialize --label "新一轮测试"`（使用项目虚拟环境）。此入口创建新身份和新文件夹并更新运行选择，保留旧历史；它不是同一 A 的 Session 重启。常规启动不会调用此入口。

在 Java 26.1 中开放局域网，将当前端口写入 `minecraft/config.json`，然后使用固定命令：

```powershell
cd "D:\codex\project\我的世界"
.\.venv\Scripts\python.exe main.py
```

也可指定 Minecraft 配置和 Session 名称，数据库仍是同一份：

```powershell
.\.venv\Scripts\python.exe main.py --minecraft-config storage/environments/legacy/policy-boundary.minecraft.json --session-label "参数调整后的世界"
```

局域网端口可能改变，请更新选用的配置文件。本次生命周期注册没有启动机器人，也没有修改 Minecraft 配置。

常规 `main.py` 和 `individual.core` 入口拒绝另一个 `--db` 路径；主线文件缺失或 ID 不符时拒绝启动，不自动生成替代身份。ACore 的常规构造也要求已提交的生命周期历史。仅测试夹具或第一次显式初始化可使用 `initialize_lifetime=True`；正常运行入口不提供这个选项。

旧数据库已经缺失而选择文件仍存在时，默认 `initialize` 也拒绝。实验者若明确要另建新的 A，可执行 `python -m individual.lifetime initialize --replace-missing-selection --label "新一轮测试"`。旧选择文件原样保存在新目录的 `previous-selection.json`；初始化报告标记 previous_database_missing=true、original_individual_resumed=false。该入口不删除原目录其他文件，不绕过已有数据库的身份校验或活动租约，也不表示旧 A 连续恢复。此选项只存在于外部初始化命令，正常 Core / Supervisor 不自动调用。

| 控制命令 | 效果 |
| --- | --- |
| pause / resume | 暂停或恢复动作，保持当前 Session 和个体状态 |
| end_session | 结束当前 Session，Core 保持运行，停止该 Session 的观察与动作 |
| begin_session | 在同一 Core 中开启下一 Session，保持 ID、版本、内部结构与递归过程 |
| new_session | 在同一 Core 中结束当前 Session 并开启下一 Session |
| status | 查看当前 Session、个体状态版本和资源 |
| terminate / exit / Ctrl+C | 结束当前 Session、提交状态并关闭载体；下次启动仍读取此生命周期 |

服务器暂时断开时 Mineflayer 的连接机制仍适用。更换连接参数或环境可正常结束本次运行，修改配置，再用相同命令启动，不更换数据库。

## 保存什么

`experiment` 表保留为旧身份锚点以兼容原日志；新的 `individual_lifetime` 表记录生命周期角色和来源。新增表：

| 表 | 用途 |
| --- | --- |
| individual_lifetime | 生命周期唯一身份、创建时间、mainline / snapshot_branch 角色和来源 |
| states / events | 原来的全局连续状态及事件；不覆盖、不删除 |
| sessions | Session ID、开始版本、名称、环境配置、carrier_epoch 和来源 |
| session_ends | Session 结束版本、原因、时间与是否发生载体中断 |
| state_sessions | 全局版本与 Session 的关联；Session 之外的生命周期事件可无 Session |
| snapshots | 指定历史状态的完整内容、SHA-256、版本、名称和快照 ID |

所有上述历史表禁止更新和删除。结束 Session 与开启下一 Session 都以新版本和事件追加。同一数据库的跨进程租约防止两个 Core 同时承载此状态链；同一时刻最多一个未结束的 Session。

每次重启读取整个最近 AState，因此保留 InternalState、关系证据、数量和分辨率、策略来源、随机状态、尝试次数、活动过程及已有 provenance。正常 Session 结束不再批量终止所有 RecursiveProcess。

新 Session 的第一帧先获得新的 carrier_epoch，保留旧观察历史，但不把旧动作和新世界状态直接拼接成连续经验。相关过程在采样断层时暂停、保留 ID 和假设，之后可按现有机制继续处理。过程正常合并、替换或淘汰的完整历史仍在事件表中，Session 不重置 lineage。

未正常结束的运行再次启动时，先追加 SESSION_INTERRUPTED 和对应结束记录，再追加下一 SESSION_STARTED；全链 ID 与版本不变。中断原因明确记录，不把中断伪装成无间隙运行。

## 快照与实验分支

保存快照可在 Core 运行期间从另一个终端执行。快照是独立审计对象，插入由 SQLite 事务串行化，不重新创建 A、不改变其版本或执行轨迹：

```powershell
.\.venv\Scripts\python.exe -m individual.lifetime snapshot --label "当前已提交状态"
```

省略 --version 保存最新已提交状态，也可用 --version 指定某个已有全局版本。命令返回 SNAP- 开头的 snapshot_id；下一步替换为这个实际 ID。

从该快照复制实验分支：

```powershell
.\.venv\Scripts\python.exe -m individual.lifetime fork --snapshot-id "<上一步返回的 SNAP-ID>"
```

默认自动创建分支自己的身份文件夹，命令返回 branch_database；也可显式指定 --output 为一个新文件。拒绝覆盖原数据库或已有分支。分支具有新的 individual_id、role=snapshot_branch、original_mainline=false，并记录父身份、父状态版本、快照 ID 和校验哈希。

分支自己的版本从 0 开始，因为它是另一个明确标记的分支身份。父主线不被回滚或改名；父历史的版本保持原值。分支将截至快照的原始状态、事件和 Session 记录原样保存到 append-only 的 origin_history，保留原来的 process_id、experience_id、integration_id 等引用。嵌套分支也保留祖先历史。它们不会计入原始 A 的主线历史。

如需运行分支，必须显式声明：

```powershell
.\.venv\Scripts\python.exe main.py --branch-db "<返回的 branch_database>" --minecraft-config minecraft/config.json
```

此命令运行快照分支，不是恢复原始 A 的主线。为主线和分支配置不同身体账号或分开运行，避免同一个 Mineflayer 身体账号相互挤下线。本次只在隔离测试中验证分支运行，没有为真实 Minecraft 启动额外个体。

## Lifetime 与 Session 报告

查看主线全生命周期及各 Session：

```powershell
.\.venv\Scripts\python.exe -m individual.lifetime history
.\.venv\Scripts\python.exe -m individual.inspect --db storage/individuals/A-4369420c-26f2-49b1-bbde-dd2b55c6f1fe/individual.db --history --limit 80
```

报告分别输出 `A_lifetime_history` 和 `Experiment_session_history`，包含主线/分支角色、全局版本与每段运行的起止版本、环境信息和事件计数。

工程闭环审计默认检查整个生命周期；单独检查最近 Session：

```powershell
.\.venv\Scripts\python.exe -m individual.experiment_audit --db storage/individuals/A-4369420c-26f2-49b1-bbde-dd2b55c6f1fe/individual.db --session-id latest
```

`--session-id` 也接受具体 Session ID。Supervisor 的 --verify-loop 只用当前 Session 的证据判断验收，不会因为过去已出现闭环而立即结束新 Session。验证门槛仍是外部实验工具，不变成 A 的目标。

SQLite 示例：

```sql
SELECT individual_id, role, origin FROM individual_lifetime;
SELECT state_version, individual_id, timestamp FROM states ORDER BY state_version;
SELECT s.session_id, s.start_version, e.end_version, s.label, e.reason
FROM sessions s LEFT JOIN session_ends e USING(session_id)
ORDER BY s.start_version;
SELECT e.event_sequence, e.state_version, ss.session_id, e.event_type, e.payload
FROM events e JOIN state_sessions ss USING(state_version)
ORDER BY e.event_sequence;
```

## 验证与连续性边界

Python 61 项测试通过，其中新增 15 项生命周期测试，覆盖一次性注册、重启、Session 切换、崩溃记录、跨进程互斥、快照、分支原始历史、嵌套来源、拒绝身份替换，以及真实 Node Bridge 接口跨两个 Session。Node 接口测试使用测试身体适配器，没有将其冒充真实游戏联调。

本次新生命周期只进行一次性 A0 注册，未运行真实游戏 Session。A0 注册是工程初始状态，不代表运行载体已经启动。旧实验迁移已按用户指示撤回；旧策略审计结论保留：固定规则导致的参数变化仍属于 INITIAL_EXTERNAL_POLICY。

本次实现的是个体生命周期的持久状态链，以及 Core 持续运行时的 Session 切换。`Continuity(A) != 0` 仍是个体定义条件。相同 UUID 或快照读取本身不证明载体完全停止期间也保持物理连续；相关停机和恢复会明确留痕，热迁移与冗余承载仍未实现。

完整状态与 provenance 长期追加会占用磁盘，本轮没有通过删除旧历史减少开销，也没有实现压缩。当前身体工作容量与初始外部策略保持原有逻辑。

## 本轮文件

新增：individual/lifetime.py、individual/lifetime.json、tests/test_lifetime.py、本文档、新生命周期数据库与注册报告。storage/individuals/A-ee858dbd-002b-4cdb-a8ff-c1de059614f9/reports/lifetime-migration-report.json 记录先前迁移已撤回。

修改：individual/state.py、events.py、identity.py、core.py、structure.py、inspect.py、experiment_audit.py、policy_audit.py；supervisor/supervisor.py；debug/run_fixture.py；相关测试与运行文档。

Minecraft 身体实现、连接配置、Supervisor 资源限额和旧独立历史没有重写。新生命周期与旧实验分开；后续 Session 持续追加到这一份数据库。
