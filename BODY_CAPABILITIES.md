# 身体能力与知识边界

当前审计条件：Java 26.1 / protocol 775 / Mineflayer 4.39.0。身体安装属于 BODY_CAPABILITY / EXTERNAL_FIXED_MECHANISM，不是 A 学会了 Minecraft。完整矩阵与真实验收见 [WORLD_ENTRY_AUDIT.md](WORLD_ENTRY_AUDIT.md)。

## 正式表示

唯一动作定义源为 minecraft/action-space.json v2。共登记 47 项，其中 39 项可进入正式低层通道，8 项多步便利接口保留为调试兼容接口。可用性仍取决于当前身体、对象和窗口状态，不保证成功或安全。

正式调用为 perform({code, parameters})。FrameEncoder 与 InternalState 的能力清单不携带动作名称/用途；使用数字 code、数值参数、opaque ref、槽号、数值环境条件。正式按键状态也以数字表示。下面的名称仅供实验者阅读。

| code | 调试名称 / 输入 | 当前实现 |
|---|---|---|
| 0 | NO_OP | 有界等待 |
| 1–7 | 短移动、跳跃、左右转向 | 保留原编码；短移动只恢复涉及的按键，其他保持输入不被抹除 |
| 8 | LOOK_DELTA | 显式 yaw/pitch |
| 9–12 | SPRINT / SNEAK START/STOP | 保持/释放单个输入，现代协议发送完整掩码 |
| 13 | LOOK_AT | 明确请求的引用中心视角，不含接近或后续操作 |
| 14 | DIG | 原生开始、当前物理 digTime 等待、结束包；仅确认发送，不预测方块消失 |
| 15 | PLACE_BLOCK | 指定槽必须已在主手；否则 HELD_SLOT_MISMATCH。验证当前射线与面，不自动换物品 |
| 16–18 | 快捷栏、限时主手使用、挥手 | 独立输入，不解释物品用途 |
| 22–24 | 方块使用、实体使用、攻击 | 验证视线/遮挡和范围，不自动瞄准或接近 |
| 28–29、32 | 容器关闭、合成接口开启/关闭 | 实际窗口与个人 2×2/工作台 3×3 槽位，不查配方 |
| 33 | CLICK_SLOT | 原有 mode=0 左/右键输入 |
| 34 | CONTROL_INPUT(control, pressed) | 独立持续按住/释放一个键 |
| 35–36 | USE_START(hand) / USE_RELEASE | 主/副手使用保持与明确释放；请求按住与服务器使用状态分开 |
| 37–39 | DIG_START / DIG_CANCEL / DIG_FINISH | 三个独立输入，不替 A 选择结束时间，不自动切换挖掘目标 |
| 40 | RESPAWN | 仅死亡状态可用，关闭 Mineflayer 自动重生 |
| 41 | DISMOUNT | 仅骑乘时可用；发潜行输入，需另行释放，不伪造下坐骑结果 |
| 42 | WAKE | 仅实际睡眠时可用，发离床包 |
| 43 | SLOT_INPUT | 原生 mode 0/1/2/4：普通、shift、数字键、丢弃；3/5/6 返回 CARRIER_LIMITATION |
| 44 | BLOCK_INPUT | 明确主/副手、当前碰撞面与命中点，不纠正错误参数 |
| 45 | ENTITY_INPUT | 明确主/副手和实体相对位置，验证射线/边界，特殊形状仍有限制 |
| 46 | SWAP_HANDS | 原生换手包，等待后续服务器库存信息，不预测互换 |

code 19/20/21/25/26/27/30/31 的多步丢弃、装备和搬移能力仍在人工 action_id 调试路径。正式数字调用返回 MACRO_NOT_FORMAL。正式 A 可用单次槽位输入构成相同的基础作用，不由接口替它组织多个点击。

## 感知与后果

保留有界方块/实体、坐标、生命、饥饿、时间、数值物品 ID、槽位、鼠标携带物、窗口区间与合成布局。新增当前方块碰撞引用/面/局部坐标；保持按键、请求使用的手、服务器使用状态、死亡/骑乘/睡眠/挖掘输入状态分开记录。

实验者编码：control 0 前、1 后、2 左、3 右、4 跳、5 冲刺、6 潜行；hand 0 主手、1 副手；face 0 下、1 上、2 -Z、3 +Z、4 -X、5 +X。这些用途映射不以说明文字进入 A。

引用属于当前有界采样，重连、死亡/重生、离开采样及窗口更换会失效。死亡时仍可观察并发明确重生输入；没有增加生存策略。若服务器设置 immediate respawn，自行重生属于环境条件。

普通方块射线范围为 4.5 格，创造模式 5 格；实体射线为 3 格，创造模式 5 格，另保留旧桥实体中心距离 3 格保护。属性修改、模组与特殊形状未被完整验证，不能宣称全部原生距离保真。

窗口 inventory_start / inventory_end 属于当前窗口，end 不含端点。不同窗口槽号不能混用。空槽且空鼠标返回 NO_EFFECT，无替代点击、自动整理、清空鼠标或重试。

clickWindow 有本地槽位预测：slot_feedback_kind=0 表示载体当前视图，不是逐次服务器确认；inventory_server_sequence 是实际库存同步包计数。动作返回 sent; verify by subsequent observation；ACTION_EXECUTED 独自不能证明物品效果。正式挖掘/放置不调用会预测世界编辑的 convenience 接口，不制造方块/air 更新。

## 来源与边界

安装时追加 BODY_CAPABILITIES_PROVISIONED / BODY_INTERFACE_PARAMETER_UPDATED，learned=false。历史状态不改写，能力安装不记成 INTERNAL_VARIABLE_STRUCTURE。正式动作采样算法不变，仍标 EXTERNAL_FIXED_POLICY；参数取样仍标 INITIAL_EXTERNAL_POLICY，新接口只补数值域编码。

动作请求记录 code、参数、源状态/帧与归属，后续 ObservationFrame / ChangeSet / EXPERIENCE_FORMED 关联 action_id。失败返回实际 INVALID_REFERENCE、NOT_IN_VIEW、FACE_MISMATCH、HIT_MISMATCH、HELD_SLOT_MISMATCH、STALE_WINDOW 等原因，不更换目标。超时沿用关闭不确定连接、不重放机制。

## 尚未完整覆盖

完整载具/船只客户端物理；拖拽/双击归集；创造模式编辑/飞行；书/告示牌文字与编辑器状态；交易选择/报价、附魔按钮、铁砧名称；窗口专有属性/进度；特殊实体形状、属性修改后的交互距离。均为条件能力或载体限制，不能解释为 A 学不会或递归失败。床的进入由原生方块输入与服务器决定，不调用自动瞄准的 bot.sleep。

## 运行和实验者验收

正常启动 main.py 会询问 LAN 端口，也可传 --port；无需反复改配置。不要同时启动同名身体和正式 A。

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m debug.world_entry_validation --new-test --port 当前端口
```

后者属于实验者 TEST_ONLY 验收，非正式策略。--new-test 按本轮用户授权创建独立测试生命周期，原数据库与 individual/lifetime.json 保留不动。报告与历史各在所属个体目录；重复同一测试 A 可用 --selection storage/world-entry-selection.local.json，不加 --new-test。新测试 A 不是原 A 的延续。

完整测试与真实游戏验收范围见 WORLD_ENTRY_AUDIT.md；替身测试不能代替真实死亡、睡眠、骑乘、物品或 GUI 验收。
