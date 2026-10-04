import { createInterface } from 'node:readline'
import { loadConfig, createMinecraftBody } from './index.js'

const help = `命令：
  status / observe
  move forward|back|left|right|jump [毫秒]
  move stop
  dig x y z
  place x y z 物品名 [面x 面y 面z]
  activate x y z
  chat 消息
  perform 动作ID 参数JSON（例如 perform SELECT_HOTBAR_SLOT {"slot":0}）
  help / exit`

async function execute(body, line) {
  const [command, ...args] = line.trim().split(/\s+/)
  const target = () => ({ x: Number(args[0]), y: Number(args[1]), z: Number(args[2]) })
  switch (command) {
    case 'status': return body.status()
    case 'observe': return body.observe()
    case 'move': return body.move({ direction: args[0], durationMs: args[1] === undefined ? 500 : Number(args[1]) })
    case 'dig': case 'activate':
      if (args.length !== 3) throw new Error(`用法：${command} x y z`)
      return body.interact({ type: command, position: target() })
    case 'place':
      if (![4, 7].includes(args.length)) throw new Error('用法：place x y z 物品名 [面x 面y 面z]')
      return body.interact({ type: 'place', position: target(), item: args[3],
        ...(args.length === 7 ? { face: { x: Number(args[4]), y: Number(args[5]), z: Number(args[6]) } } : {}) })
    case 'chat': return body.chat(line.trim().slice(command.length).trim())
    case 'perform': {
      const match = line.trim().match(/^perform\s+(\S+)(?:\s+(.+))?$/)
      if (!match) throw new Error('用法：perform 动作ID 参数JSON')
      return body.perform({ action_id: match[1], parameters: match[2] ? JSON.parse(match[2]) : {} })
    }
    case 'help': return help
    default: throw new Error('未知命令；输入 help 查看用法。')
  }
}

try {
  const args = process.argv.slice(2)
  if (args.length && (args.length !== 2 || args[0] !== '--config')) throw new Error('用法：node src/cli.js [--config config.local.json]')
  const logger = Object.fromEntries(['info', 'warn', 'error'].map(level => [level, message => console.error(`${new Date().toISOString()} ${level.toUpperCase()} ${message}`)]))
  const body = createMinecraftBody(await loadConfig(args[1]), { logger })
  const input = createInterface({ input: process.stdin, terminal: false })
  let closing = false
  const shutdown = () => {
    if (closing) return
    closing = true
    body.stop()
    input.close()
  }
  process.on('SIGINT', shutdown)
  process.on('SIGTERM', shutdown)
  input.on('close', shutdown)
  input.on('line', line => {
    if (!line.trim() || closing) return
    if (line.trim() === 'exit') { shutdown(); return }
    // Observations and movement cancellation remain available during an action.
    void execute(body, line).then(result => {
      if (!process.stdout.destroyed) console.log(typeof result === 'string' ? result : JSON.stringify(result, null, 2))
    }).catch(error => console.error(`${error.code ?? 'ERROR'}: ${error.message}`))
  })
  process.stdout.on('error', error => {
    shutdown()
    if (error.code !== 'EPIPE') { console.error(error.message); process.exitCode = 1 }
  })
  body.start()
  logger.info('身体接口已启动，等待进入世界。输入 help 查看命令；exit 或 Ctrl+C 退出。')
} catch (error) {
  console.error(`启动失败：${error.message}`)
  process.exitCode = 1
}
