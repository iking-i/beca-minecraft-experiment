import { serveBody } from '../../bridge/server.js'

let ready = false
let x = 0
const body = Object.freeze({
  start() { ready = true; return this.status() },
  stop() { ready = false; return this.status() },
  status() { return { state: ready ? 'ready' : 'stopped', connected: ready, attempt: 1, lastError: null } },
  observe() {
    if (!ready) throw new Error('not ready')
    return { timestamp: new Date().toISOString(), position: { x, y: 64, z: 0 },
      health: 20, hunger: 20, time: { timeOfDay: 100 }, inventory: [], nearbyBlocks: [], nearbyEntities: [] }
  },
  async move(args) { if (args.direction === 'forward') x += 0.25; return { position: { x, y: 64, z: 0 } } },
  async interact(args) { return { type: args.type } },
  chat(message) { return { sent: true, message } }
})
serveBody(body)
