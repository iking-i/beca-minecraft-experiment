// Process adapter around the existing public body API; no raw Mineflayer access.
import { createInterface } from 'node:readline'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
import { createMinecraftBody, loadConfig } from '../minecraft/src/index.js'

export function serveBody(body, { input = process.stdin, output = process.stdout, errors = process.stderr } = {}) {
  const lines = createInterface({ input, terminal: false })
  let closing = false
  let sequence = 0
  let signature = null
  let timer
  const send = message => {
    if (!output.destroyed) output.write(`${JSON.stringify(message)}\n`)
  }
  const statusChanged = () => {
    if (closing) return
    const status = body.status()
    const current = JSON.stringify(status)
    if (signature === current) return
    signature = current
    send({ kind: 'lifecycle', sequence: ++sequence, timestamp: new Date().toISOString(), status })
  }
  const shutdown = () => {
    if (closing) return
    closing = true
    clearInterval(timer)
    body.stop()
    lines.close()
  }
  const dispatch = async request => {
    const args = request.args ?? {}
    switch (request.method) {
      case 'start': return body.start()
      case 'status': return body.status()
      case 'observe': return body.observe(args)
      case 'perform': return body.perform(args)
      case 'move': return body.move(args)
      case 'interact': return body.interact(args)
      case 'chat': return body.chat(args.message)
      case 'close': shutdown(); return { closed: true }
      default: throw Object.assign(new Error('Unknown bridge method'), { code: 'UNKNOWN_METHOD' })
    }
  }
  lines.on('line', line => {
    let request
    try {
      request = JSON.parse(line)
      if (!request || typeof request !== 'object' || Array.isArray(request) || !Number.isSafeInteger(request.id)) throw new Error('Invalid bridge request')
      if (closing) throw new Error('Bridge is closing')
      void dispatch(request).then(result => {
        send({ kind: 'response', id: request.id, ok: true, result })
        statusChanged()
      }).catch(error => send({ kind: 'response', id: request.id, ok: false,
        error: { code: error.code ?? 'BRIDGE_ERROR', message: error.message, details: error.details ?? null } }))
    } catch (error) {
      send({ kind: 'response', id: Number.isSafeInteger(request?.id) ? request.id : null,
        ok: false, error: { code: 'INVALID_REQUEST', message: error.message } })
    }
  })
  lines.on('close', shutdown)
  output.on('error', error => { shutdown(); errors.write(`${error.message}\n`) })
  timer = setInterval(statusChanged, 50)
  // Logging happens synchronously after death/spawn state changes in the existing body.
  // Call this observer from its logger as well to retain short-lived death states.
  return { statusChanged, shutdown }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  let adapter
  try {
    const logger = Object.fromEntries(['info', 'warn', 'error'].map(level => [level, message => {
      process.stderr.write(`${message}\n`)
      adapter?.statusChanged()
    }]))
    const override = process.argv[3] === undefined ? {} : { port: Number(process.argv[3]) }
    const body = createMinecraftBody(await loadConfig(process.argv[2], override), { logger })
    adapter = serveBody(body)
    process.on('SIGINT', adapter.shutdown)
    process.on('SIGTERM', adapter.shutdown)
  } catch (error) {
    process.stderr.write(`${error.message}\n`)
    process.exitCode = 1
  }
}
