# BECA-V0 Minecraft 身体接口

本阶段用 Node.js + Mineflayer 实现连接、观察、移动、方块交互和聊天。只负责游戏身体，不包含 AI、递归、自我修改、记忆或自动任务。这个身体是后续 A Core 的环境接口，不把程序、连接或游戏角色等同于 A。

身体扩展保留上述接口和手动命令，另外提供正式 `perform({action_id, parameters})` 接口，包含 34 项基础能力。完整清单、槽位定义和边界说明见 [BODY_CAPABILITIES.md](../BODY_CAPABILITIES.md)。新增能力不会自动选工具、规划路线或解决失败；按请求指定槽位拿取物品属于执行请求。

## 安装与运行

需要 Node.js 22 或更新版本，以及 Mineflayer 支持的 Minecraft **Java 版**世界。已有游戏客户端就可以使用单人世界的“对局域网开放”，无需另装服务器。

本项目固定使用 Mineflayer 4.39.0 和 minecraft-data 3.117.0，支持列表最高为 **Java 26.1**。实测 Java 26.3 会返回 `UNSUPPORTED_VERSION`；请在受支持版本中新建测试世界。

在 PowerShell 中运行：

```powershell
cd minecraft
npm ci
Copy-Item config.example.json config.json
# 编辑 config.json，填写当前服务器和端口
npm start
```

已经安装并配置的电脑直接 `npm start` 即可。成功后显示 `已进入世界：BECA_Body` 和坐标。启动时角色不自动采取行动。

地址、端口、用户名在本地 `config.json` 中配置；上传的配置模板为 [config.example.json](config.example.json)：

```json
{
  "host": "127.0.0.1",
  "port": 25565,
  "username": "BECA_Body",
  "auth": "offline",
  "version": false
}
```

这是配置的必要字段示例；实际文件还包含连接超时、动作超时、重连和观察采样设置。`version: false` 自动检测服务器版本。每次重新开放世界后核对端口。

`BECA_Body` 是与玩家不同的离线测试身份，不会创建正版账号。如果服务器要求正版验证，将 `auth` 改为 `microsoft`，使用独立且拥有 Java 版授权的账号，按照终端提示登录。首次登录可以增大 `connectTimeoutMs`。登录缓存位于 `.auth/`，已忽略提交。

可以另存本地配置，然后运行 `npm start -- --config config.local.json`。

## 手动操作

进入世界后，在机器人终端输入简单命令，每行一条：

```text
status
observe
move forward 500
move back 500
move left 500
move right 500
move jump 200
move stop
chat hello
help
exit
```

方块命令示例（先用 `observe` 查询实际坐标并替换）：

```text
dig 1 64 0
place 1 63 0 dirt
activate 1 64 0
```

新接口也可以在身体终端手动测试：

```text
perform SELECT_HOTBAR_SLOT {"slot":0}
perform OPEN_CRAFTING_INTERFACE {}
perform MOVE_ITEM_TO_CRAFT_SLOT {"source_slot":10,"target_slot":1,"amount":1}
perform CLOSE_CRAFTING_INTERFACE {}
```

目标引用从本次 `observe` 的 `block_ref` / `entity_ref` 读取，不填写物品或方块名称。此终端是人工调试入口，不是 A 的决策来源。

放置的坐标指支撑方块，默认在它上方放置背包里的 `dirt`。也可指定六个相邻面的单位向量，例如 `place 1 63 0 dirt 1 0 0`。身体不会自动寻找材料、工具或接近目标。

输入 `exit` 或按 `Ctrl+C` 停止机器人。终端输入流关闭也会停止。用自己的游戏角色可以在同一世界观察 `BECA_Body`。

## 后续程序如何调用

公开入口为 [src/index.js](src/index.js)，只返回封装接口。Mineflayer 对象保存在内部，不开放 `.bot`、原始事件或任意方法转发。

```javascript
import { createMinecraftBody, loadConfig } from './src/index.js'

const body = createMinecraftBody(await loadConfig())
body.start()

// 等待连接；只有 ready 时才能调用观察和动作。
while (!body.status().connected) {
  if (body.status().state === 'disconnected') {
    body.stop()
    throw new Error(body.status().lastError?.message ?? '连接失败')
  }
  await new Promise(resolve => setTimeout(resolve, 100))
}

try {
  console.log(body.observe())
  await body.move({ direction: 'forward', durationMs: 500 })
  body.chat('hello')
} finally {
  body.stop()
}
```

| 接口 | 内容 |
| --- | --- |
| `observe(options = {})` | 坐标、朝向、生命值、饥饿值、时间、附近实体/方块、背包、采样范围 |
| `move({ direction, durationMs = 500, jump = false })` | 前后左右、跳跃、停止；可以组合移动和跳跃 |
| `interact({ type: 'dig', position })` | 挖掘指定方块，使用当前手持物品 |
| `interact({ type: 'place', position, item, face })` | 装备指定背包方块，在支撑方块的指定面放置 |
| `interact({ type: 'activate', position })` | 与按钮、拉杆、门等方块交互 |
| `chat(message)` | 发送单行游戏消息 |
| `start()` / `stop()` / `status()` | 管理和查询身体连接 |

观察返回全新的普通数据，来源为客户端已加载的世界数据，可能包含被遮挡的方块，**不是屏幕视觉识别**。默认方块半径 4、实体半径 16，各最多 64 条；可在配置或 `observe` 参数中调整。`coverage` 标明未加载和截断情况，空数组不代表世界中不存在相应对象。

移动相对于当前朝向，持续时间范围 1–10000 毫秒，结束或停止时释放按键，不保证固定移动距离。本版不提供寻路或转向。方块交互限已加载目标，眼部到方块中心距离不超过 5 格；服务器仍决定是否接受。普通方块激活返回 `confirmation: 'sent'`，需再次观察实际结果。

## 错误和重连

服务器未启动、端口错误、连接超时或掉线时会输出错误，默认从 1 秒开始重连，最多间隔 30 秒。进入世界后恢复初始间隔。不支持的版本明确报错并停止重试，需要更换受支持的世界。

未就绪返回 `NOT_READY`；动作冲突返回 `BUSY`；掉线取消当前动作，动作超时关闭当前连接。两种情况都不会自动重放动作。手动停止清除按键并取消重连。死亡或维度切换时等待游戏生成流程完成。

这些设置是当前身体接口的工程配置，不定义后续 A 的递归规则或个体连续性。

## 验证与结构

```powershell
npm run check
npm test
npm run smoke
```

`smoke` 连接当前配置的世界，读取一次观察后退出。测试覆盖数据封装、移动停止、方块操作、断线重连、超时、死亡/重生，以及真实协议的关闭端口和不支持版本处理。真实世界中的动作效果需要入场联调确认。

```text
minecraft/
├─ README.md
├─ config.json
├─ package.json
├─ package-lock.json
├─ .npmrc
├─ src/
│  ├─ index.js        # 公开接口
│  ├─ body.js         # 身体、动作、重连
│  ├─ config.js       # 配置
│  ├─ errors.js       # 错误
│  └─ cli.js          # 手动操作终端
├─ scripts/
│  └─ smoke.js        # 世界连接检查
└─ test/
   ├─ body.test.js
   └─ transport.test.js
```

依据：[Mineflayer API](https://github.com/PrismarineJS/mineflayer/blob/master/docs/api.md)、[官方版本支持列表](https://github.com/PrismarineJS/mineflayer/blob/master/lib/version.js)。
