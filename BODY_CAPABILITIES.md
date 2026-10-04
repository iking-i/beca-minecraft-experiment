# 身体能力与知识边界

本轮目标是验证连续性和持续递归，不是验证最低限度下能否运行。保留现有身体能力，仅隔离会替 A 选择目标、判断用途或纠正失败的自动化。没有新增 LLM、目标、奖励、配方知识或学习算法，`Continuity(A) != 0` 的实现未改变。

## 正式 ActionSpace

唯一动作定义来源为 `minecraft/action-space.json`。实际运行时，每次观察携带 `actionSpace`，每项有 `action_id`、数字 `code`、`category=BODY_CAPABILITY`、`parameter_schema`、`currently_available`、`environment_requirements`。旧编码 0/1/2 的含义保留。

| 编码 | 正式动作 | Mineflayer / 协议接口 |
| --- | --- | --- |
| 0 | NO_OP | 有界等待 |
| 1 | MOVE_FORWARD_SHORT | setControlState(forward)，120ms 后释放方向键 |
| 2 | JUMP | setControlState(jump)，120ms 后释放 |
| 3 | MOVE_BACKWARD_SHORT | setControlState(back) |
| 4 | TURN_LEFT_SMALL | look(yaw + 0.15, pitch) |
| 5 | TURN_RIGHT_SMALL | look(yaw - 0.15, pitch) |
| 6 | STRAFE_LEFT_SHORT | setControlState(left) |
| 7 | STRAFE_RIGHT_SHORT | setControlState(right) |
| 8 | LOOK_DELTA(yaw_delta, pitch_delta) | look；单位为弧度，pitch 限于身体可用范围 |
| 9 | SPRINT_START | setControlState(sprint, true) |
| 10 | SPRINT_STOP | setControlState(sprint, false) |
| 11 | SNEAK_START | setControlState(sneak, true) |
| 12 | SNEAK_STOP | setControlState(sneak, false) |
| 13 | LOOK_AT(object_ref) | lookAt 请求指定的对象位置 |
| 14 | DIG(block_ref) | dig(block, 'ignore')；完整挖掘，不自动瞄准或换工具 |
| 15 | PLACE_BLOCK(inventory_slot, reference_block, face) | 精确槽位拿取 + _placeBlockWithOptions(forceLook='ignore') |
| 16 | SELECT_HOTBAR_SLOT(slot) | setQuickBarSlot；slot 为 0–8 |
| 17 | USE_HELD_ITEM(duration_ms 可选) | activateItem → 按指定时长保持 → deactivateItem |
| 18 | SWING_ARM | swingArm |
| 19 | DROP_ITEM(slot, amount) | clickWindow 指定槽位，mode=4，逐个丢弃指定数量 |
| 20 | MOVE_INVENTORY_ITEM(source_slot, target_slot, amount) | clickWindow；源槽左键、目标右键分配或左键整栈放置 |
| 21 | EQUIP_FROM_SLOT(source_slot, equipment_slot) | clickWindow 精确目标槽；手持槽使用 mode=2 数字键交换 |
| 22 | INTERACT_BLOCK(block_ref) | activateBlock 的版本协商 block_place 包格式，去掉自动 lookAt |
| 23 | INTERACT_ENTITY(entity_ref) | useOn；不调用会自动瞄准的 activateEntity |
| 24 | ATTACK_ENTITY(entity_ref) | attack |
| 25 | MOVE_CONTAINER_ITEM(container_id, source_slot, target_slot, amount) | clickWindow；窗口内精确槽位搬移 |
| 26 | TAKE_CONTAINER_ITEM(container_id, source_slot, target_slot, amount) | clickWindow；窗口容器区 → 窗口背包区 |
| 27 | PUT_CONTAINER_ITEM(container_id, source_slot, target_slot, amount) | clickWindow；窗口背包区 → 窗口容器区 |
| 28 | CLOSE_CONTAINER(container_id) | closeWindow |
| 29 | OPEN_CRAFTING_INTERFACE | 开启当前 2×2 或已打开工作台 3×3 槽位接口；不查询配方 |
| 30 | MOVE_ITEM_TO_CRAFT_SLOT(source_slot, target_slot, amount) | clickWindow；目标必须是当前合成输入槽 |
| 31 | TAKE_CRAFT_RESULT(target_slot) | clickWindow 取当前服务器提供的输出，再放入请求的背包槽 |
| 32 | CLOSE_CRAFTING_INTERFACE | 关闭本地个人合成接口；打开的工作台调用 closeWindow |
| 33 | CLICK_SLOT(container_id, slot, mouse_button) | clickWindow mode=0；显式左/右键，支持堆叠、交换和操作鼠标携带物 |

以上 **34 项全部是 BODY_CAPABILITY**。原来的 `move / interact / chat` 公开接口和人工 CLI 命令保留。单独运行身体不会自动决策。

## 参数与观察

正式调用为 `body.perform({action_id, parameters})`，不开放 bot、socket、任意方法转发。A Core 通过现有 Bridge 的白名单 `perform` 调用它。

块和实体携带当前观察的 `block_ref`、`entity_ref`。引用没有用途知识；在持续可观测期间稳定，离开采样范围后可以重新分配。死亡、重生、连接和身体进程切换会使旧引用失效。窗口还有独立 `container_id`；关闭或更换窗口后不能沿用旧引用。当前可感知范围仍是原有协议采样范围，并非屏幕视觉识别。

正式数值帧保留 `item_type_id / type_id`、槽位、数量、可用的 metadata 与 durability；原始名称仍供实验者调试。递归和参数选择层不读 stone、zombie、pickaxe 等名称。背包原来的按类型聚合观察仍保留，并新增逐槽位观察、当前快捷栏、手持物、鼠标携带物、控制模式与窗口结构。

控制模式记录的是当前输入的保持状态，不保证服务器实际允许冲刺等效果；实际移动仍从后续坐标变化观察。

`equipment_slot` 是载体位置编码：0=当前手持槽，1=头，2=胸，3=腿，4=脚，5=副手。`face` 是协议面编码：0=下，1=上，2=负 Z，3=正 Z，4=负 X，5=正 X。它们只描述身体和界面位置，不描述物品用途。

所有容器槽号都属于**当前窗口**；不同窗口的背包偏移不同。使用观察中的 `inventory_start / inventory_end`，后者不包含端点。不能把个人背包槽号直接当箱子窗口槽号使用。个人合成输入槽为 1–4；工作台输入槽为 1–9；输出槽来自协议窗口布局。炉子等其他输出槽不会被误认为工作台合成格。

`MOVE_*` 便利操作当前要求目标槽为空；如果要堆叠、交换或操作失败后留在鼠标上的物品，A 可以明确选择 `CLICK_SLOT`。没有自动整理、寻找空槽或清空鼠标。`CLICK_SLOT` 的 -999 表示点击窗口外；这是显式丢弃携带物的输入，不在当前默认参数取样范围中。

放置保留原身体“按明确指定的背包物品放置”的能力：如果请求的槽位不在手中，先把**这一槽**交换到当前手持槽；交换也记录在结果中。不寻找其他物品或最佳工具。挖掘不更换工具。

## 分类和选择来源

| 分类 | 保存位置 / 含义 |
| --- | --- |
| BODY_CAPABILITY | `InternalState.body_capabilities` 与观察的 ActionSpace；实验者提供的身体操作 |
| ENVIRONMENT_CONSTRAINT | 观察中的当前对象、物品、窗口、可用性，以及外部采样/资源限制 |
| LEARNED_STRUCTURE | 经历进入原有 units、relations、过程与 provenance；这里只指历史形成的内部数据，不把固定更新算法称为自主学会的策略 |

PolicyRegistry 的原有四类继续保留。新能力首次被观察时追加 `BODY_CAPABILITIES_PROVISIONED` 与必要的 `BODY_INTERFACE_PARAMETER_UPDATED`；不重置 identity、版本、关系、过程或历史。外部安装能力不会被记为策略来源迁移或学习成果。

原有动作评分及平分选择继续使用。它读取当前可用动作编码；新增动作不再停留在三个编码之外的人工入口。针对参数，`action.parameter_binding` 明确登记为 **INITIAL_EXTERNAL_POLICY**：从观察中数字槽位和对象引用域作 LCG 取样，记录取样域、前后种子及选值。视角取样初值 [-0.15, 0, 0.15]；使用时长初值 [120, 2000]ms。它没有“饥饿则吃”“看到石头就挖”等用途判断，也没有伪称自己已经学会参数选择。新参数选择器是可调用性初始化，后续由递归形成的使用结构仍待检验。

现有评分/关系键仍以动作编码为基础；参数进入经历与 provenance，本轮没有新增参数级使用策略学习。开放 DIG 或合成槽不代表已经学会挖矿或配方。

能力存在不代表当前动作一定成功。`currently_available` 只反映是否已有目标、物品、窗口或布局，不预测安全、收益或可达性。方块交互的桥接距离上限当前为 5 格，实体为 3 格；这属于接口边界，不是 A 形成的知识，服务器仍可能拒绝更近的操作。

## 失败与 provenance

失败只生成 `ACTION_FAILED` 和 `reason_code`，如 OUT_OF_REACH、EMPTY_SLOT、INVALID_REFERENCE、CURSOR_OCCUPIED、STALE_WINDOW、NO_CRAFTING_LAYOUT。不会自动走近、选择替代物、换工具或重新尝试。超时仍沿用原接口行为：关闭不确定连接，停止旧动作，不重放。

真实运行随后发现两类反复断线：A10505 对 entity_type_id=71 的掉落物执行 ATTACK_ENTITY，随后在 A10509 被服务器以 `multiplayer.disconnect.invalid_entity_attacked` 踢出；A10438 的空合成槽 CLICK_SLOT 则因等待没有产生的输出同步而超时。修正后，普通攻击接口对掉落物/经验球返回 `INVALID_ATTACK_TARGET`；空槽且空鼠标的点击返回 `NO_EFFECT`。两者注明 ENVIRONMENT_CONSTRAINT，不改目标、不取消攻击或点击能力、不伪造服务器更新。目标选择器仍可提出这些请求，失败继续进入 A 的经历。

普通攻击的服务器拒绝条件可对照 [PaperMC 的服务器源补丁](https://github.com/PaperMC/Paper/blob/main/paper-server/patches/sources/net/minecraft/server/network/ServerGamePacketListenerImpl.java.patch)。此接口目前按普通实体攻击处理，不据此宣称覆盖特殊武器的全部攻击协议。Mineflayer 槽位等待问题另参见 [上游问题记录](https://github.com/PrismarineJS/mineflayer/issues/3906)；本轮修复依据本机实际空槽事件和安装版本的 `waitForWindowUpdate` 执行代码，未假定所有合成都失败。

上述修复由实验者修改身体接口完成，不记为 A 自主形成的策略。已通过 Node 完整 30 项测试及 Python 身体/RPC/来源追踪 11 项测试。未替用户停止、重启 A，未更改已有数据库；正在运行的 Node 进程会继续使用启动时加载的旧代码，修复在下一次启动加载。

每次请求记录 `provenance.internal_state_before_version`，可在不可改写的 `states` 中读取此前 InternalState。请求包含动作编码、参数、源帧、结构版本、选择评分与参数来源。Bridge 结果/失败详情记录开始和结束时间、目标、前后方块/槽位/界面状态。之后的正式观察产生 ObservationFrame 和 ChangeSet；`after_action_ids` 链接本次动作。EXPERIENCE_FORMED 保存 action_ids、action_parameters 和失败码，再进入原有 RecursiveProcess 与 Integration provenance。记录的是时序反馈，不能只凭相邻事件宣称因果已经被证明。

```sql
SELECT state_version, event_type, payload
FROM events
WHERE event_type IN ('BODY_CAPABILITIES_PROVISIONED', 'BODY_INTERFACE_PARAMETER_UPDATED',
  'ACTION_REQUESTED', 'ACTION_EXECUTED', 'ACTION_FAILED', 'OBSERVATION_FRAME',
  'CHANGE_DETECTED', 'EXPERIENCE_FORMED', 'RECURSIVE_PROCESS_CREATED',
  'RECURSIVE_PARTIAL_OUTPUT', 'INTEGRATION_COMPLETED')
ORDER BY event_sequence;
```

## 旧接口、自动化与未覆盖项

没有发现需要移除的自动采矿、建造、路径规划或生存任务函数，本轮没有删除现有能力。旧 `interact` 的物品名称入口和人工 CLI 保留为 DEBUG_ONLY 编码入口；正式 A 使用同一类能力的数字/引用接口。第二阶段固定动作脚本仍仅在显式 `--smoke-policy` 中作为 DEBUG_ONLY 运行；数值环境与新增身体环境替身为 TEST_ONLY。默认正式运行不会进入这些入口。

并非所有普通玩家输入都已暴露：骑乘后的载具方向控制、主动下坐骑、手动重生按钮、持续按住移动键、飞行切换、左右手分别使用、睡觉/离床、物品名称编辑、书籍/告示牌编辑、交易/附魔/铁砧等界面按钮和特殊选择包仍未提供完整正式接口。跳跃/移动在水中可能产生原生游泳效果，但没有专门的持续游泳控制。原有聊天接口保留为人工入口，正式数值选择器不生成自然语言聊天。

这些遗漏不能解释为 A 学不会，也不证明递归不足；仍是载体接口边界。没有为了“最小实验”禁止它们；本轮先实现用户列出的操作集合。

目前的真实底层限制：

- Mineflayer 的 `dig` 是带计时及协议完成动作的接口，本轮采用用户允许的完整 DIG，未开放逐包 START/STOP/CANCEL 三套挖掘控制。
- 个人背包没有“向服务器请求打开个人合成窗口”的独立包。OPEN_CRAFTING_INTERFACE 暴露已有 2×2 槽位；3×3 工作台先由 A 对对象执行 INTERACT_BLOCK，等世界返回窗口。它不自动寻找或打开工作台。
- Mineflayer 便利的 activateBlock/activateEntity 会调整视角，装备 hand 可能选择快捷栏位置。新目标引用接口只发送指定目标的底层输入；必要的私有协议辅助函数保持在 Body 内，并有固定版本和测试。旧接口不变。
- `clickWindow` 在新协议中带本地窗口预测和服务器同步，不是原始屏幕鼠标模拟；有些操作只确认“输入已发送”，实际效果需要随后观察确认。所有槽位结果均来自当前窗口或服务器更新，不调用 recipesFor、craft、recipe database。
- 距离、采样范围、交互面中心、协议版本、服务器权限及动作超时会影响成功。这些限制持续记录为环境/载体边界，不附带纠错策略。

## 运行与验证

原启动方式保留，不换生命周期数据库。先核对 `minecraft/config.json` 的局域网端口，再在项目根目录运行：

```powershell
.\.venv\Scripts\python.exe main.py
```

下一次接收真实 Minecraft 观察时会追加新能力登记；现有数据库本轮没有被自动启动、迁移或重置。不要同时运行单独身体 CLI 与正式 A，以免两个连接争用同一机器人账号。

测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
cd minecraft
npm test
```

验证覆盖真实 Python/Node RPC 和 Body facade，身体替身使用安装的 prismarine-windows 槽位实现。合成测试由环境替身给出任意输出，验证槽位操作及反馈，而不是宣称验证了真实配方。另有原有真实 Mineflayer 连接错误/不支持协议测试。**本轮未在真实游戏中验收全部新能力，也未新增一次理论递归成功的结论。**

本轮验证结果：Python 72 项、Node 28 项测试通过，JavaScript 语法检查通过。真实游戏的物品效果、服务器权限、配方与窗口同步仍待逐项验收。
