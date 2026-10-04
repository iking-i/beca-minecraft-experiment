import test from 'node:test'
import assert from 'node:assert/strict'
import { EventEmitter } from 'node:events'
import { Vec3 } from 'vec3'
import { createBody } from '../src/body.js'
import { validateConfig } from '../src/config.js'

const logger = { info() {}, warn() {}, error() {} }
const baseConfig = {
  host: '127.0.0.1', port: 25565, username: 'TestBody', auth: 'offline',
  connectTimeoutMs: 100, actionTimeoutMs: 500,
  reconnect: { enabled: true, initialDelayMs: 10, maxDelayMs: 20 }
}

class FakeBot extends EventEmitter {
  constructor() {
    super()
    this.username = 'TestBody'
    this.entity = { id: 1, position: new Vec3(0, 64, 0), height: 1.62, yaw: 0, pitch: 0 }
    this.entities = { 1: this.entity, 2: { id: 2, type: 'player', username: 'Observer', position: new Vec3(2, 64, 0) } }
    this.health = 20
    this.food = 18
    this.time = { timeOfDay: 6000, day: 1, isDay: true }
    this.game = { dimension: 'overworld' }
    this.items = [{ name: 'dirt', displayName: 'Dirt', type: 10, count: 16, slot: 36 }]
    this.inventory = { items: () => this.items }
    this.registry = { blocksByName: { dirt: {} } }
    this.blocks = new Map()
    this.blocks.set('1,64,0', { name: 'stone', type: 1, position: new Vec3(1, 64, 0), diggable: true })
    this.controls = {}
    this.calls = []
    this.endCount = 0
  }
  blockAt(p) { return this.blocks.get(`${p.x},${p.y},${p.z}`) ?? { name: 'air', type: 0, position: p, diggable: false } }
  clearControlStates() { this.controls = {} }
  setControlState(key, value) { this.controls[key] = value }
  canDigBlock() { return true }
  async dig(block) { this.calls.push(['dig', block.name]) }
  async equip(item, destination) { this.calls.push(['equip', item.name, destination]) }
  async placeBlock(block, face) { this.calls.push(['place', block.name, { ...face }]) }
  async activateBlock(block) { this.calls.push(['activate', block.name]) }
  chat(text) { this.calls.push(['chat', text]) }
  end(reason) { this.endCount++; this.emit('end', reason) }
}

function fixture(t, overrides = {}) {
  const bots = []
  const options = []
  const body = createBody({ ...baseConfig, ...overrides }, { logger, createBot: value => {
    options.push(value)
    const bot = new FakeBot()
    bots.push(bot)
    return bot
  } })
  t.after(() => body.stop())
  body.start()
  return { body, bots, options, spawn: () => bots.at(-1).emit('spawn') }
}

async function until(predicate, timeout = 1000) {
  const deadline = Date.now() + timeout
  while (!predicate()) {
    if (Date.now() > deadline) throw new Error('test wait timed out')
    await new Promise(resolve => setTimeout(resolve, 5))
  }
}

test('not ready before spawn; facade and observations never expose mutable Mineflayer objects', t => {
  const { body, bots, options, spawn } = fixture(t)
  assert.throws(() => body.observe(), { code: 'NOT_READY' })
  assert.equal(body.start().attempt, 1)
  assert.equal(options[0].host, baseConfig.host)
  spawn()
  const snapshot = body.observe()
  assert.equal(body.status().state, 'ready')
  assert.equal(snapshot.health, 20)
  assert.equal(snapshot.hunger, 18)
  assert.equal(snapshot.nearbyBlocks[0].name, 'stone')
  assert.equal(snapshot.nearbyEntities[0].username, 'Observer')
  snapshot.position.x = 900
  snapshot.inventory[0].count = 999
  snapshot.nearbyBlocks[0].position.x = 999
  snapshot.nearbyEntities[0].position.x = 999
  assert.equal(bots[0].entity.position.x, 0)
  assert.equal(bots[0].items[0].count, 16)
  assert.equal(bots[0].entities[2].position.x, 2)
  assert.equal(bots[0].blocks.get('1,64,0').position.x, 1)
  assert.deepEqual(Object.keys(body).sort(), ['chat', 'interact', 'move', 'observe', 'perform', 'start', 'status', 'stop'])
  assert.equal(Object.isFrozen(body), true)
  assert.doesNotThrow(() => JSON.stringify(snapshot))
})

test('observe reports unloaded samples and truncation instead of inventing empty world data', t => {
  const { body, bots, spawn } = fixture(t)
  spawn()
  bots[0].blockAt = p => p.x === 0 ? null : { name: 'stone', type: 1, position: p, diggable: true }
  const snapshot = body.observe({ blockRadius: 1, maxBlocks: 1 })
  assert.equal(snapshot.nearbyBlocks.length, 1)
  assert.equal(snapshot.coverage.blocksTruncated, true)
  assert.ok(snapshot.coverage.unloadedBlocks > 0)
  assert.throws(() => body.observe({ blockRadius: Infinity }), { code: 'INVALID_ARGUMENT' })
})

test('movement presses direction/jump then releases all controls; explicit stop interrupts duration', async t => {
  const { body, bots, spawn } = fixture(t)
  spawn()
  const moving = body.move({ direction: 'forward', jump: true, durationMs: 400 })
  await Promise.resolve()
  assert.deepEqual(bots[0].controls, { forward: true, jump: true })
  await assert.rejects(body.move({ direction: 'left' }), { code: 'BUSY' })
  assert.equal((await body.move({ direction: 'stop' })).stopped, true)
  assert.equal((await moving).stopped, true)
  assert.ok(Object.values(bots[0].controls).every(v => !v))
  for (const direction of ['back', 'left', 'right', 'jump']) {
    const result = await body.move({ direction, durationMs: 1 })
    assert.equal(result.direction, direction)
    assert.ok(Object.values(bots[0].controls).every(v => !v))
  }
})

test('dig, place and activate use block coordinates and detached return values', async t => {
  const { body, bots, spawn } = fixture(t)
  spawn()
  const position = { x: 1, y: 64, z: 0 }
  await body.interact({ type: 'dig', position })
  const placed = await body.interact({ type: 'place', position, item: 'dirt' })
  assert.deepEqual(placed.placedPosition, { x: 1, y: 65, z: 0 })
  assert.equal((await body.interact({ type: 'activate', position })).confirmation, 'sent')
  assert.deepEqual(bots[0].calls.map(c => c[0]), ['dig', 'equip', 'place', 'activate'])
  await assert.rejects(body.interact({ type: 'place', position, item: 'diamond_block' }), { code: 'ITEM_NOT_FOUND' })
  await assert.rejects(body.interact({ type: 'place', position, item: 'dirt', face: { x: 1, y: 1, z: 0 } }), { code: 'INVALID_ARGUMENT' })
  await assert.rejects(body.interact({ type: 'dig', position: { x: 2, y: 64, z: 0 } }), { code: 'INVALID_TARGET' })
  bots[0].blocks.set('20,64,0', { name: 'stone', position: new Vec3(20, 64, 0) })
  await assert.rejects(body.interact({ type: 'activate', position: { x: 20, y: 64, z: 0 } }), { code: 'OUT_OF_REACH' })
})

test('stop immediately after move prevents a not-yet-started key press', async t => {
  const { body, bots, spawn } = fixture(t)
  spawn()
  const presses = []
  bots[0].setControlState = key => presses.push(key)
  const moving = body.move({ direction: 'forward', durationMs: 400 })
  await body.move({ direction: 'stop' })
  assert.equal((await moving).stopped, true)
  assert.deepEqual(presses, [])
})

test('error + kicked + end schedules one reconnect; stale spawn cannot replace the new session', async t => {
  const { body, bots, spawn } = fixture(t)
  bots[0].emit('error', Object.assign(new Error('refused'), { code: 'ECONNREFUSED' }))
  bots[0].emit('kicked', 'duplicate event')
  bots[0].emit('end', 'closed')
  assert.equal(body.status().state, 'reconnecting')
  assert.match(body.status().lastError.message, /服务器已启动/)
  await until(() => bots.length === 2)
  bots[0].emit('spawn')
  assert.equal(body.status().state, 'connecting')
  spawn()
  assert.equal(body.status().state, 'ready')
  assert.equal(body.status().attempt, 2)
})

test('disconnect cancels active motion; reconnect never replays the action', async t => {
  const { body, bots, spawn } = fixture(t)
  spawn()
  const moving = body.move({ direction: 'forward', durationMs: 400 })
  const rejected = assert.rejects(moving, { code: 'DISCONNECTED' })
  await Promise.resolve()
  bots[0].emit('end', 'network lost')
  await rejected
  assert.ok(Object.values(bots[0].controls).every(v => !v))
  await until(() => bots.length === 2)
  spawn()
  assert.deepEqual(bots[1].controls, {})
  assert.equal(body.status().state, 'ready')
})

test('late equip completion after disconnect cannot send a place command', async t => {
  const { body, bots, spawn } = fixture(t)
  spawn()
  let finishEquip
  bots[0].equip = () => new Promise(resolve => { finishEquip = resolve })
  const placement = body.interact({ type: 'place', position: { x: 1, y: 64, z: 0 }, item: 'dirt' })
  const rejected = assert.rejects(placement, { code: 'DISCONNECTED' })
  await Promise.resolve()
  bots[0].emit('end', 'network lost')
  await rejected
  finishEquip()
  await Promise.resolve()
  assert.equal(bots[0].calls.some(c => c[0] === 'place'), false)
})

test('action timeout releases controls and closes the uncertain connection', async t => {
  const { body, bots, spawn } = fixture(t, { actionTimeoutMs: 100, reconnect: { ...baseConfig.reconnect, enabled: false } })
  spawn()
  bots[0].dig = () => new Promise(() => {})
  await assert.rejects(body.interact({ type: 'dig', position: { x: 1, y: 64, z: 0 } }), { code: 'ACTION_TIMEOUT' })
  assert.equal(body.status().state, 'disconnected')
  assert.equal(bots[0].endCount, 1)
})

test('connection timeout is reported; manual stop cancels reconnect and pending movement', async t => {
  const { body, bots } = fixture(t, { reconnect: { enabled: true, initialDelayMs: 100, maxDelayMs: 100 } })
  await until(() => body.status().state === 'reconnecting')
  assert.equal(body.status().lastError.code, 'CONNECT_TIMEOUT')
  body.stop()
  await new Promise(resolve => setTimeout(resolve, 130))
  assert.equal(bots.length, 1)
  assert.equal(body.status().state, 'stopped')
  body.start()
  bots[1].emit('spawn')
  const moving = body.move({ direction: 'right', durationMs: 400 })
  const rejected = assert.rejects(moving, { code: 'DISCONNECTED' })
  body.stop()
  await rejected
})

test('death rejects motion and respawn restores the same facade', async t => {
  const { body, bots, spawn } = fixture(t)
  spawn()
  const moving = body.move({ direction: 'jump', durationMs: 400 })
  const rejected = assert.rejects(moving, { code: 'DEAD' })
  await Promise.resolve()
  bots[0].emit('death')
  await rejected
  assert.equal(body.observe().bodyState, 0)
  bots[0].emit('respawn')
  assert.equal(body.status().state, 'spawning')
  spawn()
  assert.equal(body.status().state, 'ready')
  await body.move({ direction: 'forward', durationMs: 1 })
})

test('unsupported server version closes the socket and does not retry indefinitely', async t => {
  const { body, bots, spawn } = fixture(t)
  let closed = false
  bots[0]._client = { socket: { destroy() { closed = true } } }
  bots[0].emit('error', new Error('No data available for version 26.3'))
  assert.equal(body.status().state, 'disconnected')
  assert.equal(body.status().lastError.code, 'UNSUPPORTED_VERSION')
  assert.equal(closed, true)
  await new Promise(resolve => setTimeout(resolve, 30))
  assert.equal(bots.length, 1)
  assert.throws(() => body.chat('hello'), { code: 'NOT_READY' })
  body.start()
  spawn()
  assert.equal(body.chat('hello').sent, true)
  assert.deepEqual(bots[1].calls.at(-1), ['chat', 'hello'])
  assert.throws(() => body.chat('a\nb'), { code: 'INVALID_ARGUMENT' })
})

test('configuration rejects invalid addresses/options without modifying caller configuration', () => {
  assert.throws(() => validateConfig({ ...baseConfig, port: 0 }))
  assert.throws(() => validateConfig({ ...baseConfig, username: '' }))
  assert.throws(() => validateConfig({ ...baseConfig, reconnect: { enabled: 'yes' } }))
  const input = { host: 'localhost', port: 25565, username: 'TestBody' }
  const validated = validateConfig(input)
  assert.equal(validated.observation.blockRadius, 4)
  assert.equal(input.observation, undefined)
})
