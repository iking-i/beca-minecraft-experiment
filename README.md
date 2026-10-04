# BECA-V0：L0 持续递归与当前极限反馈实验

本仓库是 [beca-architecture](https://github.com/iking-i/beca-architecture) **Perfect Recursion / BER v0.8** 的独立 Minecraft 实验实现。发布时核对的理论 `main` 提交为 [`45d8869245fb210202a7e7982486d7f723bc6680`](https://github.com/iking-i/beca-architecture/commit/45d8869245fb210202a7e7982486d7f723bc6680)（2026-10-04）。现有实现及本地同步的实验文档原先依据 [`867e1f192f7f21298450a553a4a733ec8f15a999`](https://github.com/iking-i/beca-architecture/commit/867e1f192f7f21298450a553a4a733ec8f15a999)；后续理论增加的阶段完美结构和层间非对称兼容性并未因此自动获得实现或验证。来源机器可读记录见 [THEORY_REFERENCE.json](THEORY_REFERENCE.json)。

当前范围是 **L0 层内持续递归和当前有效极限反馈**，不声称已经验证向上递归、L1 或无限递归。仓库整理不改变实验行为。真实 A 的数据库、本机配置、凭据和运行日志保留在本地，不上传；完整清单见 [REPOSITORY_CONTENTS.md](REPOSITORY_CONTENTS.md)。

## 新克隆的首次安装

需要 Python 3.11 或更新版本、Node.js 22 或更新版本，以及与锁定 Mineflayer 版本兼容的 Minecraft Java 世界。现有测试使用 Java 26.1。

在克隆后的仓库根目录运行（Windows PowerShell）：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm --prefix minecraft ci
Copy-Item minecraft/config.example.json minecraft/config.json
```

编辑生成的 `minecraft/config.json`，填写服务器地址、局域网当前端口和独立身体账号。模板的 `25565` 是常见服务器示例端口，不是当前电脑的运行端口。

**仅在新克隆尚无个体时**，显式创建自己的 A，然后启动：

```powershell
.\.venv\Scripts\python.exe -m individual.lifetime initialize --label "首次本地实验"
.\.venv\Scripts\python.exe main.py
```

初始化会生成 `individual/lifetime.json` 和 `storage/individuals/A-<uuid>/`。`individual/lifetime.example.json` 只说明格式，**不要复制成运行身份**。已有 A 的电脑正常重启只执行 `main.py`，不要为每次 Session 重新初始化。Linux/macOS 使用 `python3` 创建环境，并把后续 Python 路径改为 `.venv/bin/python`。

在第一、二阶段的身体接口、唯一实验身份、连续状态链、SQLite 和外部 Supervisor 上增加最小内部递归。正常运行路径不使用原来的固定前进脚本。没有引入 LLM、语言知识、Minecraft 攻略、高级任务、自我修改、自我复制或自主联网。

当前阶段允许始终只有一个 recursive process，不要求 upward recursion。目标是 L0 内的结果反馈、真实有限记忆后果进入递归，以及是否出现可追踪的 architecture-limit recognition candidate。正式路径已经禁用旧的固定分化、分辨率减半、淘汰和探索评分，能力接口保留。完整审计与能力边界见 [FORMAL_L0_EXPERIMENT.md](FORMAL_L0_EXPERIMENT.md)。

程序、进程、数据库、游戏角色都是承载或能力结构。`individual_id` 是工程标记；`A0 → A1 → A2` 表示同一个体的连续状态变化。数据库属于 A 的生命周期，Experiment Session 是其中一段运行记录。当前 A 的身份和数据库由 `individual/lifetime.json` 固定。

## 启动和验收

完成上述安装后，无需重复安装依赖或 Minecraft。在 Java 26.1 测试世界开放局域网，将当前端口写入 `minecraft/config.json`。局域网重新开放后端口可能改变。不要同时启动使用同一个身体账号的其他工具。

```powershell
# 在仓库根目录运行
.\.venv\Scripts\python.exe main.py
```

默认持续运行并记录完整历史，没有 1000 次状态变化的停止门槛。每个 A 的数据单独放在 `storage/individuals/A-<uuid>/`，同一 A 的多个 Session 共用该文件夹。当前路径由本地生成的 `individual/lifetime.json` 指定，结束 Session 或重启沿用同一身份和全局版本。本地目录索引为 `storage/index.json`，不随 GitHub 发布；说明见 [storage/README.md](storage/README.md)。

如果要从零开始测试另一个 A，先退出正在运行的项目，再执行以下命令。它创建新身份和独立文件夹，保留旧 A 的全部历史，不会覆盖或继承旧结构：

```powershell
.\.venv\Scripts\python.exe -m individual.lifetime initialize --label "新一轮测试"
.\.venv\Scripts\python.exe main.py
```

默认启动使用 formal_l0。只读审计本阶段证据：

```powershell
.\.venv\Scripts\python.exe -m individual.experiment_audit --session-id latest --sample
```

审计分别输出层内递归、真实容量失败、后果再次进入递归、外部策略影响、内部关系证据变化和架构识别候选。单过程的前次结果影响下次关系读取即可有层内递归；信息整合不算升层。当前解释器没有组织层问题表示生成器，因此原始失败不能让整个阶段自动通过。`--verify-loop` 已改为要求本轮全部目标证据，缺识别候选时不会自动结束；不要用长时间运行假装补齐缺失能力。

| 命令 | 作用 |
| --- | --- |
| `pause` | 停止新动作，观察、核心运行和记录继续 |
| `resume` | 恢复当前实验的动作调度，ID 不变 |
| `status` | 查看状态、CPU、RAM 和存活情况 |
| `end_session` / `begin_session` | 在同一 Core 内结束或开启 Session，内部结构保留 |
| `new_session` | 切换到下一 Session，Core、个体 ID 和全局版本持续 |
| `terminate` / `exit` / Ctrl+C | 结束当前 Session 并关闭载体；下次仍读取此生命周期 |

正常退出先停止新动作，追加 SESSION_ENDED 并保留内部结构与递归过程，随后关闭 Bridge 和 Core。`--duration` 是实验者设定的 Session 时间限制，默认 0（无限制）。`--verify-loop` 只检查当前 Session 的证据，不拿以前的闭环直接验收新 Session。`--smoke-policy` 才会使用第二阶段的调试脚本；其余路径不加载该策略。

## A0 的最小结构

`AState` 保留第二阶段所有字段，并新增 `observation_frame`、`internal_state`。A0 中单元、关系、过程、经历窗口为空，只有初始解释机制需要的少量参数和动作试探状态。

```text
AState
  individual_id / state_version / started_at / last_update_at
  session_id / carrier_epoch
  environment_sequence / status / continuity_required = true
  latest_observation / latest_action
  health / hunger / position / inventory_summary
  observation_frame
  internal_state
    units / relations / active_processes
    observation_history_window / action_history_window
    detected_changes / resource_state
    generation_parameters / exploration_state
    latest_integration / latest_feedback / latest_generation
    latest_structure_changes / continuity_incidents / process_archive
    policy_registry / parameter_sources / policy_migration_status / body_capabilities
```

原始 Mineflayer 观察和人工调试映射只供记录、检查；正常结构引擎收到的是数值帧，不读取原始对象名称。没有敌人、食物、房屋、夜晚等预设概念。

## ObservationFrame

```text
frame_id / sequence_id / timestamp
encoding_namespace / body_epoch
self_channels                 # 数值通道 ID → 数值
spatial_data                  # 位置、朝向数值
nearby_data                   # 对象 ID、类型编码、相对位置、数量
numeric_channels              # 全部数值通道
coverage                      # 未加载、截断等采样边界
 delta
   change_id / previous_frame_id / frame_id
   changes                    # 增加、减少、出现、消失或未观测到
   maintained_channels / cochanged_channels
   after_action_ids / sample_gap
```

通道 ID 来自固定编码布局，方块/物品/实体使用游戏协议的类型编号，协议版本作为编码命名空间。缺编号的兼容输入只在编码边界被转换为无意义符号，不解释名称含义。人类名称单独存入 `SENSOR_DEBUG_MAPPING` 事件，不进入递归的判断条件。名称改为“food”或“enemy”而编号不变时，测试中的帧、结构参数和动作选择完全一致。

视野来自 Mineflayer 的已加载世界数据，不是屏幕图像。身体采样半径、数量、空气过滤和协议编码仍是外部接口条件。存在采样截断时，缺失通道保守记录为“未观测到”，不冒充对象真实消失。重连/死亡造成的采样断层不用于建立连续动作因果关系。

## RecursiveProcess（旧调试路径；不作为正式分化策略）

正式实现见 `individual/formal_l0.py`：一个持久过程接收每次连续观察，读取前次整合返回的关系引用，并进行新的证据核对。容量不足拒绝写入，原记录保留，原始失败进入下一输入；不会依据新结果、稳定性或压力改变数量。下面保留旧引擎的数据说明，只有独立调试夹具或显式 `--legacy-policy-debug` 才使用它。正式历史禁止重新进入旧适应引擎。

```text
process_id / origin_state_version / input_pattern
question                      # 数值条件通道、当前分辨率、分支编号
hypothesis                    # 结果计数及条件区间内的结果计数
attempts / observations / output / status
last_information_sequence
```

变化模式尚不能被当前关系稳定描述时产生问题过程。每次收到与其问题相关的新经历，立即 `publish_partial_result()`，不等待最终答案。不同分支实际检查不同数值通道；分辨率用于计算条件区间，并进入条件证据，不能只改一个展示字段。

生命周期支持 `ACTIVE / PAUSED / MERGED / SUPERSEDED / TERMINATED`。充分的暂时信息、没有新信息、等价问题合并、条件变化、容量不足和外部结束都会形成事件。已暂时稳定的问题不因“需要永久递归”而无限重新启动，监测到反例则重新提出问题。

## 内部结构怎样变化（旧固定策略；正式路径禁用）

数值差异形成描述性单元，单元随重复观察强化，未重复的单元衰减，工作容量不足时归档。提供单元合并操作；当前自动整合记录候选关系条件、合并等价递归问题。`split` 操作标签本身不代表已经生成高层结构，不声称已经发现了跨模式的概念等价。

过程提出暂时的 `X + action_code → Y`。整合对同一经历去重：多个过程上传同一条经历只增加一次关系证据。重复结果强化证据；出现 `X → Z` 时保留 Y、Z，降低无条件关系的适用性，记录候选条件并保持 unresolved。关系容量不足时归档整个关系，连同罕见结果保留在事件历史中，不筛掉少数结果。

向下反馈修改当前 `default_quantity`、按模式的数量、条件分辨率。下一次生成从这些内部参数读取数量，并记录源整合 ID、源状态版本、请求数量和实际获配数量。实际数量还受外部容量制约，不能把配额不足造成的减少误认为内部策略变化。

正式 Minecraft 身体现提供 34 项基础操作，包括移动、视角、挖掘、放置、手持物、背包、方块/实体交互、容器与合成格。旧编码 0、1、2 保留原义；新增能力通过数字槽位和当前对象引用调用，全部标记 BODY_CAPABILITY，能力清单和底层对应见 [BODY_CAPABILITIES.md](BODY_CAPABILITIES.md)。选择仍参考当前关系的未解程度和尝试次数，平分时使用内部记录的随机序列。参数取样明确登记为 INITIAL_EXTERNAL_POLICY，不冒称为学习结果。没有对象名称规则、健康奖励、死亡扣分、配方查询或高级任务。

完整链路记录帧 ID、变化 ID、动作 ID、过程 ID、部分输出 ID、整合 ID、生成 ID、源状态版本。记录的是时序关联和候选条件，当前不自动宣称发现了因果定律。

## 实际日志和验证

第三阶段旧版曾在固定玻璃区域通过真实 Java 26.1 验收；历史数据与日志样例见 [VALIDATION_STAGE3.md](VALIDATION_STAGE3.md)，数据库为 `storage/individuals/A-2eb28d2a-d5f6-4ef3-9ade-91e24f803eab/stage3-final.db`。这些独立 ID 的旧实验保留，不合并成新 A 的过去。当前主线为新注册的 `storage/individuals/A-4369420c-26f2-49b1-bbde-dd2b55c6f1fe/individual.db`，后续 Session 在此生命周期继续。

```powershell
.\.venv\Scripts\python.exe -m individual.inspect --db storage/individuals/A-2eb28d2a-d5f6-4ef3-9ade-91e24f803eab/stage3-final.db --history --limit 40
.\.venv\Scripts\python.exe -m individual.experiment_audit --db storage/individuals/A-2eb28d2a-d5f6-4ef3-9ade-91e24f803eab/stage3-final.db --sample --output storage/individuals/A-2eb28d2a-d5f6-4ef3-9ade-91e24f803eab/reports/stage3-final-report.json
```

查看完整状态历史和某次整合的输入：

```sql
SELECT state_version, snapshot FROM states ORDER BY state_version;
SELECT event_sequence, state_version, event_type, payload
FROM events ORDER BY event_sequence;
SELECT state_version, payload FROM events
WHERE event_type IN ('RECURSIVE_PARTIAL_OUTPUT', 'INTEGRATION_COMPLETED',
                     'DOWNWARD_FEEDBACK_UPDATED', 'RECURSION_GENERATED',
                     'COUNTEREXAMPLE_RETAINED')
ORDER BY event_sequence;
```

每次对外可见状态更新均在同一 SQLite 事务中追加状态、原因事件、各子事件和 `STATE_UPDATED`。事务失败不会让内存状态越过已提交历史。三个历史表禁止更新和删除。运行中的检查使用同一只读事务，避免将两个时间点的数据混成一个结果。

## 外部固定机制与 A 的可变结构（旧实现审计）

| 分类 | 实际内容 |
| --- | --- |
| CORE_MECHANISM | 身份记录、事件循环、Bridge、动作执行器、数值编码、差异检测、问题解释器、证据去重、SQLite |
| ENVIRONMENT_CONSTRAINT | 身体采样、可用接口、最大工作容量、测得资源、Supervisor 权限与人工停止 |
| INITIAL_EXTERNAL_POLICY | 探索评分、选择方式、暂时稳定判据、数量/分辨率更新规则、通道排序、资源使用与淘汰、强度更新与归档顺序 |
| 经历形成的可变数据 | 单元、关系、证据、候选条件、问题假设、尝试次数、当前数量与分辨率及其历史来源 |
| INTERNAL_VARIABLE_POLICY | 当前尚无已验证的来源迁移；固定规则改变参数不能算作自主策略形成 |

部分参数（例如窗口和暂时稳定阈值）已经作为数据保存，但本阶段没有实现它们全部自动改写。不要把“存成数据”说成“已经发生递归修改”。数量、条件分辨率和问题选择的变化已经接入真实执行路径。

默认物理工作上限：8 个过程、64 个单元、96 个关系、每关系 64 种结果、6 帧工作窗口、4 条近期证据引用、16 个数值条件通道。完整观察和输出留在日志中，这些数目不是理论上限，也不是 A 从一开始就知道了所有环境限制。

Supervisor 不属于 A。它单向送入实际 CPU/RAM 样本，A 仅获得数值资源压力；Core 输出只能作为遥测，不能修改外部限额。仍使用监测与超限终止，不是 OS 硬配额/容器隔离。

## 连续性和当前 TODO

`Continuity(A) != 0` 保留为个体级实验约束，不转换为普通奖励函数。记录身体死亡、连接中断与近期观察/动作的关联，标记为局部承载事件，不自动等同于 A 死亡。

SQLite 保存 A 的全生命周期状态链，Session 重启读取已提交的当前状态，不重建身份。完整载体停止造成的间隙会记录为中断；数据库标记本身不证明物理连续。保存历史快照与复制分支均可执行，分支必须标记为不同身份、不是原始主线。详情与操作见 [LIFETIME_STORAGE.md](LIFETIME_STORAGE.md)。

实际运行中完整 JSON 快照的磁盘开销较大：第一轮 647 个状态版本约占 389 MiB。当前没有压缩/长期归档，默认持续运行会继续增长。保留历史同时降低冗余写入、长期磁盘管理、更多物理条件下的反例检验、自动发现单元等价仍是后续工程工作。本阶段没有继续增加语言、长期知识、高级游戏行为或自我修改。

## 项目结构和检查

```text
main.py / requirements.txt / README.md
STAGE2.md / VALIDATION.md / VALIDATION_STAGE3.md
individual/
  identity.py / state.py / events.py / core.py / bridge.py / lifetime.py / lifetime.json
  observation.py / change_detection.py / internal_state.py
  formal_l0.py / l0_audit.py / experiment.json（当前正式路径）
  recursion.py / integration.py / structure.py / actions.py / action_space.py / policies.py
  inspect.py / experiment_audit.py / policy_audit.py / policy.py（调试兼容导入）
debug/
  smoke_policy.py / run_fixture.py
  world_probe.mjs / prepare_arena.mjs
supervisor/
  supervisor.py / limits.yaml
bridge/
  server.js / package.json
minecraft/
  action-space.json / src/capabilities.js（新增正式动作；既有接口保留）
storage/
  index.json / individuals/A-<uuid>/（此 A 的数据库、监控和 reports/）
  environments/（共享环境记录） / admin/（整理与校验记录）
tests/
  test_core.py / test_supervisor.py / test_structure.py / test_policies.py / test_lifetime.py / test_action_space.py / fixtures/
```

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
npm --prefix minecraft test
```

生命周期修正时 Python 61 项、Node 15 项测试通过。身体扩展的测试与能力边界见 [BODY_CAPABILITIES.md](BODY_CAPABILITIES.md)。数值模拟和 Node 测试适配器只作为测试证据；真实游戏验收单独标明，未用模拟结果替代游戏运行。

## 外部策略边界修正

本轮新增 PolicyRegistry、参数来源和 policy_migration_status；将初始策略复制到 A0，由当前 InternalState 提供运行参数，分别记录动作评分四部分和递归数量的资源/状态/初始策略三项来源。

真实 Java 26.1 联调使用端口 53335 和独立配置 `storage/environments/legacy/policy-boundary.minecraft.json`，保留原 Minecraft 配置。`storage/individuals/A-ee858dbd-002b-4cdb-a8ff-c1de059614f9/policy-boundary-live-002.db` 记录 A0→A64；A45 的数量 2→3 被 A48 读取并实际用于创建三个过程。共 5 次参数变化、0 次策略来源迁移；固定更新规则仍标为 INITIAL_EXTERNAL_POLICY。

完整策略清单、逐事件实例、局限和运行方法见 [POLICY_BOUNDARIES.md](POLICY_BOUNDARIES.md)。查看本轮证据：

```powershell
.\.venv\Scripts\python.exe -m individual.policy_audit --db storage/individuals/A-ee858dbd-002b-4cdb-a8ff-c1de059614f9/policy-boundary-live-002.db
```

本轮没有实现新策略的自主生成与采纳，没有据此宣布理论结构升阶。

