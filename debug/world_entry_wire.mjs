// TEST_ONLY passive protocol evidence. Never imported by the formal bridge or A.
import { appendFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { createRequire } from 'node:module'
import { createBody } from '../minecraft/src/body.js'
import { loadConfig } from '../minecraft/src/config.js'
import { serveBody } from '../bridge/server.js'

const require = createRequire(new URL('../minecraft/package.json', import.meta.url))
const mineflayer = require('mineflayer')
const names = new Set(['block_change', 'multi_block_change', 'acknowledge_player_digging', 'block_changed_ack',
  'window_items', 'set_slot', 'set_player_inventory', 'set_cursor_item', 'open_window', 'close_window',
  'spawn_entity', 'entity_destroy', 'entity_status', 'entity_metadata', 'entity_velocity',
  'rel_entity_move', 'entity_move_look', 'entity_teleport', 'update_health', 'position', 'system_chat'])
const inputs = new Set(['block_dig', 'block_place', 'use_item', 'use_entity', 'attack', 'window_click',
  'close_window', 'held_item_slot', 'look', 'player_input', 'entity_action'])
let sequence = 0, adapter
const output = join(dirname(process.argv[2]), 'wire-events.jsonl')
function record(direction, name, data, normalized = null) {
  appendFileSync(output, JSON.stringify({ wire_sequence: ++sequence, timestamp: new Date().toISOString(),
    source: 'TEST_ONLY_PASSIVE_WIRE', direction, name, data, normalized },
  (_, value) => typeof value === 'bigint' ? value.toString() : value) + '\n')
}
function normalize(bot, name, data) {
  const Item = require('prismarine-item')(bot.registry)
  const item = (value, slot) => {
    const v = Item.fromNotch(value)
    return { slot, item_type_id: v?.type ?? null, count: v?.count ?? 0 }
  }
  if (name === 'window_items') return { window_id: data.windowId,
    slots: data.items.map((v, i) => item(v, i)) }
  if (name === 'set_slot') return { window_id: data.windowId, slot: item(data.item, data.slot) }
  if (name === 'set_player_inventory') {
    const s = data.slotId, slot = s <= 8 ? s + 36 : s >= 36 && s <= 39 ? 44 - s : s === 40 ? 45 : s
    return { window_id: 0, slot: item(data.contents, slot) }
  }
  const block = (position, state) => ({ position, state_id: state,
    block_type_id: bot.registry.blocksByStateId[state]?.id ?? null })
  if (name === 'block_change') return { blocks: [block(data.location, data.type)] }
  if (name === 'multi_block_change') return { blocks: data.records.map(r => {
    const v = Number(r), c = data.chunkCoordinates
    return block({ x: c.x * 16 + ((v >> 8) & 15), y: c.y * 16 + (v & 15), z: c.z * 16 + ((v >> 4) & 15) }, v >> 12)
  }) }
  return null
}
const logger = Object.fromEntries(['info', 'warn', 'error'].map(level => [level, message => {
  process.stderr.write(`${message}\n`); adapter?.statusChanged()
}]))
const body = createBody(await loadConfig(process.argv[2], { port: Number(process.argv[3]) }), { logger,
  createBot(options) {
    const bot = mineflayer.createBot(options), write = bot._client.write.bind(bot._client)
    bot._client.write = (name, data) => {
      const value = write(name, data)
      if (inputs.has(name)) record('OUT', name, data)
      return value
    }
    bot._client.on('packet', (data, meta) => {
      if (!names.has(meta.name)) return
      let normalized = null
      try { normalized = normalize(bot, meta.name, data) } catch (error) { normalized = { decode_error: error.message } }
      record('IN', meta.name, data, normalized)
    })
    return bot
  }
})
adapter = serveBody(body)
process.on('SIGINT', adapter.shutdown)
process.on('SIGTERM', adapter.shutdown)
