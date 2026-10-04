# 仓库内容与本地数据边界

本仓库发布 BECA-V0 Minecraft 实验实现。此次整理只增加忽略规则、配置模板和说明，不改变实验运行逻辑或当前 A 的数据。

## 纳入版本管理

- `individual/`、`bridge/`、`minecraft/src/`、`supervisor/` 和 `main.py`：完整运行代码，包含旧调试路径。
- `tests/`、`tests/fixtures/`、`minecraft/test/`、`minecraft/testing/`、`debug/`：测试、模拟身体、小型输入生成器和调试工具。
- `requirements.txt`、各 `package.json`、`minecraft/package-lock.json`：依赖声明与锁定版本。
- `minecraft/config.example.json`、`individual/lifetime.example.json`：不包含真实账号或本机身份的配置模板。
- `individual/experiment.json`、`supervisor/limits.yaml`、`minecraft/action-space.json`：实验配置与能力定义，保留当前值。
- 根目录和模块 README：实验文档、理论来源、历史验收结果与局限。
- `storage/admin/organize-20261004.ps1`、`storage/admin/split-legacy-archives.py`：原有一次性整理源码，保留原位置和内容。它们依赖本机历史计划及归档，**不是新克隆的初始化步骤，不要直接运行**。

小型测试数据以源码夹具和生成器保存，不需要随仓库分发 SQLite。`python -m unittest discover -v` 使用隔离的临时数据；`python -m debug.validate_formal_l0` 可生成单独标记为 `test_fixture` 的短期数值测试历史，不切换主线身份，也不代表真实 Minecraft 验收。

## 留在本地，不上传

- `minecraft/config.json`、`individual/lifetime.json`：本机服务器、账号配置和当前个体指针。
- `storage/individuals/`、`storage/index.json`、环境记录、管理报告：所有真实生命周期数据库、快照、lineage、provenance、审计导出和历史归档。
- `.env`、token、认证缓存、私钥和凭据文件。
- `.venv/`、`node_modules/`、缓存、运行日志、临时测试文件、压缩备份。

`.gitignore` 不删除这些内容，也不更改正在选中的 A。GitHub 中的源码副本不是原始 A 的连续主线。另一台机器新克隆后应显式初始化一个新个体，不能把身份模板或测试数据当作原 A。

历史文档引用的数据库路径仍作为历史出处保留；这些大文件不在仓库中，因此相应历史审计命令需要原始本地数据。已有摘要不能代替原始数据库重新证明结果。

## 后续同步

只提交经过检查的代码、模板、测试和文档。添加文件后先检查 `git status --short` 和 `git diff --cached --stat`，避免用强制添加把被忽略的凭据或生命周期数据纳入提交。敏感信息检查需要检查实际待提交内容，不能仅依赖 `.gitignore`。
