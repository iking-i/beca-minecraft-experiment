import { Vec3 } from 'vec3'
import { fileURLToPath } from 'node:url'
import { validateConfig } from './config.js'
import { BodyError, integer, requireObject } from './errors.js'
import { createCapabilities } from './capabilities.js'
import { controls, setInput, endDig } from './native_inputs.js'

const position = p => ({ x: p.x, y: p.y, z: p.z })
const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z)
const itemData = item => ({ name: item.name, type: item.type, count: item.count, slot: item.slot, displayName: item.displayName })
const blockData = block => ({ name: block.name, type: block.type, position: position(block.position), diggable: block.diggable })

function coordinates(value, name) {
  requireObject(value, name)
  for (const axis of ['x', 'y', 'z']) integer(value[axis], `${name}.${axis}`, -30000000, 30000000)
  return new Vec3(value.x, value.y, value.z)
}

function readableError(error) {
  if (error.code === 'UNSUPPORTED_VERSION') return `当前 Mineflayer 不支持服务器协议：${error.message}。请使用受支持版本的测试世界。`
  if (error.code === 'ECONNREFUSED') return '连接被拒绝：请确认 Minecraft Java 服务器已启动，地址和端口正确。'
  if (error.code === 'ENOTFOUND') return '无法解析服务器地址，请检查 host。'
  if (['ETIMEDOUT', 'CONNECT_TIMEOUT'].includes(error.code)) return '连接超时：请检查服务器、版本、网络，或完成 Microsoft 登录。'
  return error.message ?? String(error)
}

// Internal dependency injection for transport/lifecycle tests; not a package export.
export function createBody(input, { createBot, logger = console }) {
  const config = validateConfig(input)
  let running = false
  let current = null
  let reconnectTimer = null
  let attempt = 0
  let retryDelay = config.reconnect.initialDelayMs
  let state = 'stopped'
  let lastError = null
  let busy = null

  function log(level, message) {
    logger[level]?.(`[Minecraft] ${message}`)
  }

  function status() {
    return { state, connected: state === 'ready', attempt, username: config.username,
      host: config.host, port: config.port, lastError: lastError ? { ...lastError } : null }
  }

  function clearControls(session, preserveModes = false) {
    try { session.bot.clearControlStates?.() } catch { /* A closed connection may have no controls. */ }
    if (preserveModes) {
      for (const [mode, value] of Object.entries(session.modes ?? {})) session.bot.setControlState(mode, value)
    } else session.modes = {}
    if (!preserveModes) {
      try { if ((session.useHand ?? -1) >= 0 || session.bot.usingHeldItem) session.bot.deactivateItem() } catch { /* Retired body. */ }
      session.useHand = -1
    }
  }

  function retire(session, reason) {
    clearTimeout(session.timer)
    session.abort.abort(new BodyError('DISCONNECTED', reason))
    try { if (session.dig) endDig(session, false) } catch { /* Retired transport. */ }
    clearControls(session)
    try { session.bot.stopDigging?.() } catch { /* Digging may already have ended. */ }
    try { session.bot.end(reason) } catch { /* Already disconnected. */ }
    // Protocol initialization can fail before its stream chain is usable.
    // Close the owned socket as well, rather than waiting for its 30s fallback.
    try { session.bot._client?.socket?.destroy() } catch { /* Already closed. */ }
  }

  function scheduleReconnect() {
    if (!running || reconnectTimer) return
    if (!config.reconnect.enabled) { state = 'disconnected'; return }
    state = 'reconnecting'
    const delay = retryDelay
    retryDelay = Math.min(retryDelay * 2, config.reconnect.maxDelayMs)
    log('info', `${delay}ms 后重新连接。`)
    reconnectTimer = setTimeout(() => { reconnectTimer = null; connect() }, delay)
  }

  function fail(session, error) {
    if (current !== session) return
    if (/No data available for version|unsupported protocol version|Unsupported protocol version|Server version .*not supported/.test(error.message)) {
      error = new BodyError('UNSUPPORTED_VERSION', error.message)
    }
    current = null
    lastError = { code: error.code ?? 'CONNECTION_FAILED', message: readableError(error) }
    log('error', lastError.message)
    retire(session, lastError.message)
    if (lastError.code === 'UNSUPPORTED_VERSION') state = 'disconnected'
    else scheduleReconnect()
  }

  function connect() {
    if (!running || current) return
    state = 'connecting'
    attempt++
    log('info', `连接 ${config.host}:${config.port}，第 ${attempt} 次尝试。`)
    try {
      const bot = createBot({ host: config.host, port: config.port, username: config.username,
        auth: config.auth, version: config.version, logErrors: false, respawn: false,
        profilesFolder: fileURLToPath(new URL('../.auth', import.meta.url)),
        onMsaCode: data => log('info', `Microsoft 登录：${data.verification_uri}，代码 ${data.user_code}`) })
      const session = { bot, abort: new AbortController(), timer: null, useHand: -1 }
      current = session
      session.inventoryServerSequence = 0
      for (const packet of ['window_items', 'set_slot', 'set_player_inventory', 'set_cursor_item']) {
        bot._client?.on?.(packet, () => { session.inventoryServerSequence++ })
      }
      session.timer = setTimeout(() => fail(session, new BodyError('CONNECT_TIMEOUT', '连接超时')), config.connectTimeoutMs)
      bot.on('error', error => fail(session, error))
      bot.on('kicked', reason => fail(session, new BodyError('KICKED', `被服务器断开：${typeof reason === 'string' ? reason : JSON.stringify(reason)}`)))
      bot.on('end', reason => fail(session, new BodyError('DISCONNECTED', `连接已关闭：${reason ?? 'unknown'}`)))
      bot.on('login', () => { if (current !== session) bot.end('stale connection') })
      bot.on('spawn', () => {
        if (current !== session || !running) { bot.end('stale connection'); return }
        clearTimeout(session.timer)
        session.referenceEpoch = (session.referenceEpoch ?? 0) + 1
        if (session.abort.signal.aborted) session.abort = new AbortController()
        state = 'ready'
        lastError = null
        retryDelay = config.reconnect.initialDelayMs
        log('info', `已进入世界：${bot.username}，坐标 ${JSON.stringify(position(bot.entity.position))}`)
      })
      bot.on('death', () => {
        if (current !== session) return
        state = 'dead'
        session.abort.abort(new BodyError('DEAD', '游戏角色死亡，等待服务器重生。'))
        clearControls(session)
        clearTimeout(session.timer)
        session.dig = null
        log('warn', '游戏角色死亡；等待明确的重生输入，不自动请求重生。')
      })
      bot.on('respawn', () => {
        if (current !== session) return
        state = 'spawning'
        session.abort.abort(new BodyError('RESPAWNING', '世界或维度切换，等待重新生成。'))
        clearControls(session)
        try { bot.stopDigging?.() } catch { /* World may already be unloaded. */ }
        session.dig = null
        clearTimeout(session.timer)
        session.timer = setTimeout(() => fail(session, new BodyError('CONNECT_TIMEOUT', '重新生成超时')), config.connectTimeoutMs)
      })
    } catch (error) {
      if (current) fail(current, error)
      else {
        lastError = { code: error.code ?? 'CONNECTION_FAILED', message: readableError(error) }
        log('error', lastError.message)
        scheduleReconnect()
      }
    }
  }

  function ready() {
    if (!current || state !== 'ready' || !current.bot.entity) throw new BodyError('NOT_READY', `机器人尚未进入可操作状态：${state}`)
    return current
  }

  function observable() {
    if (!current || !['ready', 'dead'].includes(state) || !current.bot.entity) throw new BodyError('NOT_READY', 'No observable world body')
    return current
  }

  function respawn() {
    const session = observable()
    if (state !== 'dead') throw new BodyError('INVALID_STATE', 'Respawn input requires a dead body')
    session.bot.respawn()
    return { confirmation: 'sent; verify by subsequent observation' }
  }

  function ensureSession(session, signal) {
    if (signal.aborted) throw signal.reason
    if (current !== session || state !== 'ready') throw new BodyError('DISCONNECTED', '动作所属连接已失效')
  }

  async function action(kind, operation) {
    const session = ready()
    if (busy) throw new BodyError('BUSY', `正在执行 ${busy.kind}，请等待完成`)
    const token = { kind, cancelRequested: false, cancel: null }
    busy = token
    const signal = session.abort.signal
    let timer
    let onAbort
    try {
      return await Promise.race([
        Promise.resolve().then(() => { ensureSession(session, signal); return operation(session, signal, token) }),
        new Promise((resolve, reject) => {
          onAbort = () => reject(signal.reason)
          signal.addEventListener('abort', onAbort, { once: true })
          timer = setTimeout(() => {
            const error = new BodyError('ACTION_TIMEOUT', '动作超时；关闭当前连接以停止未完成动作，动作不会自动重放。')
            reject(error)
            fail(session, error)
          }, config.actionTimeoutMs)
        })
      ])
    } catch (error) {
      if (error instanceof BodyError) throw error
      throw new BodyError('ACTION_FAILED', error.message ?? String(error))
    } finally {
      clearTimeout(timer)
      signal.removeEventListener('abort', onAbort)
      if (busy === token) busy = null
    }
  }

  function observe(options = {}) {
    requireObject(options, 'observe options')
    const session = observable()
    const { bot } = session
    const defaults = config.observation
    const blockRadius = integer(options.blockRadius ?? defaults.blockRadius, 'blockRadius', 1, 8)
    const entityRadius = integer(options.entityRadius ?? defaults.entityRadius, 'entityRadius', 1, 64)
    const maxBlocks = integer(options.maxBlocks ?? defaults.maxBlocks, 'maxBlocks', 1, 512)
    const maxEntities = integer(options.maxEntities ?? defaults.maxEntities, 'maxEntities', 1, 512)
    const origin = bot.entity.position
    const center = new Vec3(Math.floor(origin.x), Math.floor(origin.y), Math.floor(origin.z))
    const blocks = []
    let unloadedBlocks = 0
    for (let x = -blockRadius; x <= blockRadius; x++) {
      for (let y = -blockRadius; y <= blockRadius; y++) {
        for (let z = -blockRadius; z <= blockRadius; z++) {
          if (x * x + y * y + z * z > blockRadius * blockRadius) continue
          const block = bot.blockAt(center.offset(x, y, z))
          if (!block) { unloadedBlocks++; continue }
          if (!['air', 'cave_air', 'void_air'].includes(block.name)) {
            blocks.push({ ...blockData(block), distance: distance(origin, block.position) })
          }
        }
      }
    }
    blocks.sort((a, b) => a.distance - b.distance)
    const entities = Object.values(bot.entities).filter(e => e.id !== bot.entity.id && e.position && distance(origin, e.position) <= entityRadius)
      .map(e => ({ id: e.id, type: e.type, type_id: e.entityType ?? bot.registry?.entitiesByName?.[e.name]?.id ?? null, name: e.name ?? null, username: e.username ?? null,
        position: position(e.position), distance: distance(origin, e.position) }))
      .sort((a, b) => a.distance - b.distance)
    return capabilities.describe(session, { timestamp: new Date().toISOString(), encoding: { protocol_version: bot.version ?? null }, position: position(origin),
      orientation: { yaw: bot.entity.yaw, pitch: bot.entity.pitch }, bodyState: state === 'dead' ? 0 : 1,
      health: bot.health ?? null, hunger: bot.food ?? null,
      time: { timeOfDay: bot.time?.timeOfDay ?? null, day: bot.time?.day ?? null, isDay: bot.time?.isDay ?? null },
      dimension: bot.game?.dimension ?? null,
      nearbyEntities: entities.slice(0, maxEntities), nearbyBlocks: blocks.slice(0, maxBlocks),
      inventory: bot.inventory.items().map(itemData),
      coverage: { blockRadius, entityRadius, unloadedBlocks, blocksTruncated: blocks.length > maxBlocks, entitiesTruncated: entities.length > maxEntities } })
  }

  async function move(options) {
    requireObject(options, 'move options')
    const { direction, jump = false } = options
    if (!['forward', 'back', 'left', 'right', 'jump', 'stop'].includes(direction)) {
      throw new BodyError('INVALID_ARGUMENT', 'direction 必须为 forward/back/left/right/jump/stop')
    }
    if (typeof jump !== 'boolean') throw new BodyError('INVALID_ARGUMENT', 'jump 必须为布尔值')
    if (direction === 'stop') {
      const session = ready()
      // Cancels a timed movement without affecting a block interaction.
      if (busy?.kind === 'move') {
        busy.cancelRequested = true
        busy.cancel?.()
      }
      clearControls(session)
      return { stopped: true }
    }
    const durationMs = integer(options.durationMs ?? 500, 'durationMs', 1, 10000)
    return action('move', async (session, signal, token) => {
      const bot = session.bot
      if (token.cancelRequested) return { direction, stopped: true, position: position(bot.entity.position) }
      let timer
      let onAbort
      let finish
      let stopped = false
      try {
        const prior = { ...session.modes }
        token.priorControls = prior
        setInput(session, controls.indexOf(direction), 1)
        if (jump && direction !== 'jump') setInput(session, 4, 1)
        await new Promise((resolve, reject) => {
          finish = () => { stopped = true; resolve() }
          token.cancel = finish
          onAbort = () => reject(signal.reason)
          signal.addEventListener('abort', onAbort, { once: true })
          timer = setTimeout(resolve, durationMs)
        })
        ensureSession(session, signal)
        return { direction, stopped, position: position(bot.entity.position) }
      } finally {
        clearTimeout(timer)
        if (onAbort) signal.removeEventListener('abort', onAbort)
        token.cancel = null
        if (current !== session || state !== 'ready' || stopped) clearControls(session)
        else for (const key of [direction, ...(jump && direction !== 'jump' ? ['jump'] : [])]) setInput(session, controls.indexOf(key), Number(!!token.priorControls?.[key]))
      }
    })
  }

  // DEBUG_ONLY legacy semantic convenience interface; never dispatched by formal A actions.
  async function interact(options) {
    requireObject(options, 'interact options')
    const { type } = options
    if (!['dig', 'place', 'activate'].includes(type)) throw new BodyError('INVALID_ARGUMENT', 'type 必须为 dig/place/activate')
    const target = coordinates(options.position, 'position')
    let face
    if (type === 'place') {
      face = coordinates(options.face ?? { x: 0, y: 1, z: 0 }, 'face')
      if (Math.abs(face.x) + Math.abs(face.y) + Math.abs(face.z) !== 1) throw new BodyError('INVALID_ARGUMENT', 'face 必须是六个相邻面的单位向量')
      if (typeof options.item !== 'string' || !options.item.trim()) throw new BodyError('INVALID_ARGUMENT', 'place 需要背包物品名称 item')
    }
    return action(type, async (session, signal) => {
      const bot = session.bot
      const block = bot.blockAt(target)
      if (!block) throw new BodyError('BLOCK_UNLOADED', '目标方块所在区块尚未加载')
      if (['air', 'cave_air', 'void_air'].includes(block.name)) throw new BodyError('INVALID_TARGET', '目标必须是实际方块；放置时指定支撑方块')
      const eye = bot.entity.position.offset(0, bot.entity.eyeHeight ?? 1.62, 0)
      if (distance(eye, target.offset(0.5, 0.5, 0.5)) > 5) throw new BodyError('OUT_OF_REACH', '目标超出当前接口的 5 格交互距离')
      if (type === 'dig') {
        if (!bot.canDigBlock(block)) throw new BodyError('CANNOT_DIG', '当前无法挖掘此方块（距离或方块属性）')
        await bot.dig(block)
      } else if (type === 'place') {
        if (!bot.blockAt(target.plus(face))) throw new BodyError('BLOCK_UNLOADED', '待放置位置尚未加载')
        const item = bot.inventory.items().find(i => i.name === options.item)
        if (!item) throw new BodyError('ITEM_NOT_FOUND', `背包中没有 ${options.item}`)
        if (!bot.registry.blocksByName[item.name]) throw new BodyError('NOT_A_BLOCK', '当前放置接口只支持方块物品')
        await bot.equip(item, 'hand')
        ensureSession(session, signal)
        await bot.placeBlock(block, face)
      } else {
        await bot.activateBlock(block)
      }
      ensureSession(session, signal)
      return { type, position: position(target), ...(face ? { placedPosition: position(target.plus(face)) } : {}),
        confirmation: type === 'activate' ? 'sent' : 'completed' }
    })
  }

  function chat(message) {
    if (typeof message !== 'string' || !message.trim() || message.length > 256 || /[\r\n\u0000]/.test(message)) {
      throw new BodyError('INVALID_ARGUMENT', '消息必须是 1–256 字符的非空单行文本')
    }
    ready().bot.chat(message)
    return { sent: true }
  }

  const capabilities = createCapabilities({ action, ready, ensureSession, move, observe, respawn })
  return Object.freeze({
    start() {
      if (!running) { running = true; connect() }
      else if (!current && !reconnectTimer) connect()
      return status()
    },
    stop() {
      running = false
      clearTimeout(reconnectTimer)
      reconnectTimer = null
      const previous = current
      current = null
      state = 'stopped'
      if (previous) retire(previous, 'Body stopped')
      return status()
    },
    status, observe, move, interact, chat, perform: capabilities.perform
  })
}
