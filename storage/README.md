# 按个体连续历史存储

每个 `individual_id` 对应一个独立文件夹。同一个 A 的全部状态、递归 lineage、provenance 和多次 Experiment Session 留在该文件夹；Session 结束不创建新目录、不重置身份或版本。不同 A 的历史不合并。

```text
storage/
  index.json                      # 身份、标签与文件夹索引
  individuals/
    A-<uuid>/
      lifetime.json               # 此文件夹的身份与主线/分支/旧实验分类
      individual.db               # 全部状态、事件、Session 和内嵌快照
      individual.db-wal / -shm     # SQLite 配套文件（存在时）
      individual.db.lock
      individual.supervisor.db    # 外部监控，不属于 A
      reports/                    # 此个体的审计导出
      lifetime-initialization-report.json
    A-<另一个 uuid>/
      ...
  environments/legacy/            # 共享环境配置与外部布置记录
  admin/                          # 整理计划、内容校验和旧清理记录
```

旧实验按数据库中的真实身份归档，保留原数据库名。已经压缩的旧实验按身份拆为各自 `archive/run-00N.zip`，数据库、WAL、SHM、锁文件与监控数据一起保留。压缩归档不能直接作为运行数据库。

## 继续当前 A

```powershell
.\.venv\Scripts\python.exe main.py
```

当前文件夹由 `individual/lifetime.json` 指向。重启或切换 Session 仍读取此文件夹，全局版本继续递增。移动文件本身不证明物理连续性。

## 从零新建另一个 A

先正常退出正在运行的项目，再执行：

```powershell
.\.venv\Scripts\python.exe -m individual.lifetime initialize --label "新一轮测试"
.\.venv\Scripts\python.exe main.py
```

此操作明确创建新身份、新文件夹和 A0，并选择这个新 A。旧文件夹保留，不删除、覆盖或继承其历史。如果当前 Core 持有运行锁，拒绝切换。常规启动不会自动创建替代身份。

## 查看与导出

```powershell
.\.venv\Scripts\python.exe -m individual.lifetime history
.\.venv\Scripts\python.exe -m individual.inspect --history --limit 30
.\.venv\Scripts\python.exe -m individual.experiment_audit --session-id latest
.\.venv\Scripts\python.exe -m individual.policy_audit
```

默认读取当前 A；审计导出默认写入其 `reports/`，文件名包含时间，重复审计不覆盖先前导出。指定 `--db` 可以只读检查另一个 A，导出默认归入该数据库所在文件夹。显式 `--output` 保留为外部导出能力。

快照仍在所属数据库内。`individual.lifetime fork --snapshot-id ...` 省略 `--output` 时，快照分支自动获得单独文件夹、新身份和 `snapshot_branch` 标记，不改变原 A 的运行选择。

旧文件中的原始路径与报告数值保留为历史证据；整理前后路径和 SHA-256 对应见 `admin/storage-reorganization-report.json`。
