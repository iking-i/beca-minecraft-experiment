import test from 'node:test'
import assert from 'node:assert/strict'
import net from 'node:net'
import { once } from 'node:events'
import { createRequire } from 'node:module'
import { createMinecraftBody } from '../src/index.js'

const protocol = createRequire(import.meta.resolve('mineflayer'))('minecraft-protocol')

test('real Mineflayer reports a closed local server port without crashing', async t => {
  const reservation = net.createServer()
  reservation.listen(0, '127.0.0.1')
  await once(reservation, 'listening')
  const port = reservation.address().port
  await new Promise(resolve => reservation.close(resolve))
  const body = createMinecraftBody({ host: '127.0.0.1', port, username: 'TestBody',
    auth: 'offline', version: '1.21.1', connectTimeoutMs: 3000,
    reconnect: { enabled: false } }, { logger: { info() {}, warn() {}, error() {} } })
  t.after(() => body.stop())
  body.start()
  const deadline = Date.now() + 5000
  while (body.status().state !== 'disconnected') {
    assert.ok(Date.now() < deadline, 'expected disconnected state')
    await new Promise(resolve => setTimeout(resolve, 20))
  }
  assert.equal(body.status().lastError.code, 'ECONNREFUSED')
  assert.throws(() => body.observe(), { code: 'NOT_READY' })
})

test('unsupported advertised version is reported and all owned connections close', async t => {
  const server = protocol.createServer({ host: '127.0.0.1', port: 0, version: '1.21.1',
    'online-mode': false,
    beforePing: response => ({ ...response, version: { name: '26.3', protocol: 777 } }) })
  let body
  t.after(async () => {
    body?.stop()
    for (const client of Object.values(server.clients)) client.socket.destroy()
    const closed = once(server, 'close')
    server.close()
    await closed
  })
  await once(server, 'listening')
  body = createMinecraftBody({ host: '127.0.0.1', port: server.socketServer.address().port,
    username: 'TestBody', auth: 'offline', version: false, connectTimeoutMs: 3000,
    reconnect: { enabled: true, initialDelayMs: 10, maxDelayMs: 20 } },
  { logger: { info() {}, warn() {}, error() {} } })
  body.start()
  const deadline = Date.now() + 5000
  while (body.status().state !== 'disconnected' || Object.keys(server.clients).length) {
    assert.ok(Date.now() < deadline, 'unsupported connection must close promptly')
    await new Promise(resolve => setTimeout(resolve, 20))
  }
  assert.equal(body.status().lastError.code, 'UNSUPPORTED_VERSION')
  assert.match(body.status().lastError.message, /26\.3/)
  await new Promise(resolve => setTimeout(resolve, 50))
  assert.equal(body.status().attempt, 1)
})
