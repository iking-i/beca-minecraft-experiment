# 第二阶段验收记录

以下保留当时的验收结果。当前生命周期和重启规则见 [LIFETIME_STORAGE.md](LIFETIME_STORAGE.md)，旧版新建实验数据库的运行说明不再适用于后续 Session。

日期：2026-10-03，用户时区 Asia/Shanghai。事件时间使用带 `+00:00` 的 UTC 时间。

## 自动测试

`.venv\Scripts\python.exe -m unittest discover -s tests -v`：21 项通过。

覆盖：跨进程唯一实例锁、固定 ID、连续版本、观察与背包摘要、行动反馈、原子事件记录、历史禁止修改/删除、事务失败不执行动作、死亡/重生、断线/重连、暂停/恢复、失败动作不重放、旧数据库拒绝自动恢复、真实 Node 进程适配器、Supervisor 独立及强制终止、内存阈值、Bridge 退出检测、Core 遥测无法修改 Supervisor 配置。

## 真实 Minecraft 闭环

连接现有身体接口，地址 `127.0.0.1:62227`。记录在 `storage/individuals/A-033b3758-d7a1-450d-b911-2f2db2dadf9a/stage2-live.db`：

- ID：`A-033b3758-d7a1-450d-b911-2f2db2dadf9a`。
- `A0 → … → A18`，19 个状态、38 条事件、10 次有效环境输入。
- A6/A7：前进请求/执行。
- A8：新观察，坐标从 `(1.5, 112, 8.5)` 变为 `(1.5, 112, 8.7)`。
- A9/A10：停止请求/执行。
- A11 及后续：继续观察。
- A18：记录最后状态并正常关闭实验。

独立的 `storage/individuals/A-033b3758-d7a1-450d-b911-2f2db2dadf9a/stage2-live.supervisor.db` 包含 20 次 CPU/RAM 采样和正常终止记录。

## 真实人工控制与身体生命周期

`storage/individuals/A-fe7d6ef3-f8a6-4312-ba63-b5558d2891ef/stage2-controls.db` 验证暂停期间核心仍运行并接收观察，还记录了身体死亡/重生。53 个状态、106 条事件、43 次环境输入，ID 保持不变。

`storage/individuals/A-84ada684-0521-4635-a27c-dc317b46bada/stage2-manual.db` 验证完整人工控制：

- ID：`A-84ada684-0521-4635-a27c-dc317b46bada`。
- A13/A14、A31/A33：两次身体死亡/重生，ID 没有改变。
- A36：`SUPERVISOR_PAUSED`。
- A39：`SUPERVISOR_RESUMED`。
- A40：`EXPERIMENT_TERMINATED`。
- 41 个状态、82 条事件、27 次环境输入。
- 独立 Supervisor 日志确认三个命令和 Core 退出码 0。

以上数据库均通过只读状态链审计，进程均已退出。它们属于不同的实验，不把一次实验完全停止后另一次创建的 A 宣称为原主体的自动延续。

另保留 `storage/individuals/A-12403161-3ce8-481b-8609-5471562fddf5/stage2-validation.db`：之前的端口关闭时，验证了连接拒绝、重试、状态记录和正常结束；没有有效游戏观察，不计作闭环成功。

## 当前限制 / TODO

- 真实 Minecraft 掉线重连仍需专门联调；ID 保持和事件记录已通过自动测试。
- 资源限制采用定时采样和超限终止，尚未使用 Windows Job Object、容器或 OS 硬配额。
- 各进程当前使用同一 OS 用户。公开 API 无法修改 Supervisor，但本阶段没有抵御任意恶意代码的文件权限隔离。
- 长期运行需要磁盘容量告警、历史归档和 SQLite 增长策略；不能靠覆盖旧状态处理。
- 完全停止后的主体连续性、热迁移、持续冗余保持开放，没有实现 checkpoint 恢复为同一主体。
- 没有实现 LLM、递归、学习、自我修改、自我复制、自主联网或长期语义记忆，也没有开始下一阶段。
