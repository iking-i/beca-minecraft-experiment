import test from 'node:test'
import assert from 'node:assert/strict'
import { Vec3 } from 'vec3'
import { createBody } from '../src/body.js'
import { CapabilityBot } from '../testing/capability_bot.js'

function fixture(t, options = {}) {
  const bot = new CapabilityBot()
  const body = createBody({ host: '127.0.0.1', port: 25565, username: 'TestBody', auth: 'offline',
    actionTimeoutMs: 3000, reconnect: { enabled: false }, ...options },
  { createBot: () => bot, logger: { info() {}, warn() {}, error() {} } })
  body.start(); bot.emit('spawn'); t.after(() => body.stop())
  const execute = (action_id, parameters = {}) => body.perform({ action_id, parameters })
  return { body, bot, execute, block: () => body.observe().nearbyBlocks[0].block_ref,
    entity: () => body.observe().nearbyEntities[0].entity_ref }
}

test('formal registry has 34 low-level capabilities with schemas and honest availability', async t => {
  const { body, execute } = fixture(t)
  const raw = body.observe(), actions = raw.actionSpace
  assert.equal(actions.length, 34)
  assert.ok(actions.every(a => a.category === 'BODY_CAPABILITY' && a.parameter_schema && Array.isArray(a.environment_requirements)))
  assert.equal(actions.find(a => a.action_id === 'TAKE_CONTAINER_ITEM').currently_available, false)
  assert.ok(raw.inventorySlots.some(s => s.slot === 36 && s.item_type_id === 1 && s.count === 8))
  await assert.rejects(execute('mine_wood'), { code: 'UNKNOWN_ACTION' })
  await assert.rejects(execute('DIG', { block_ref: 'stone' }), { code: 'INVALID_REFERENCE' })
  await assert.rejects(execute('LOOK_DELTA', { yaw_delta: Infinity, pitch_delta: 0 }), { code: 'INVALID_ARGUMENT' })
  await assert.rejects(execute('DIG', { block_ref: raw.nearbyBlocks[0].block_ref, recipe: 'tool' }), { code: 'INVALID_ARGUMENT' })
})

test('returned references and registry schemas are detached from the owned body state', async t => {
  const { body, bot, execute } = fixture(t)
  const raw = body.observe()
  const ref = raw.nearbyBlocks[0].block_ref
  raw.nearbyBlocks[0].position.x = 999
  raw.actionSpace.find(a => a.action_id === 'DIG').parameter_schema.properties.block_ref.type = 'number'
  raw.actionSpace.find(a => a.action_id === 'DIG').environment_requirements.push('fake_requirement')
  const next = body.observe()
  assert.equal(next.actionSpace.find(a => a.action_id === 'DIG').currently_available, true)
  await execute('DIG', { block_ref: ref })
  assert.equal(bot.calls.find(c => c[0] === 'dig')[1].x, 1)
})

test('dig uses an observed opaque ref, never auto-aims or equips, and records world/slot changes', async t => {
  const { bot, execute, block } = fixture(t)
  const target = block()
  const result = await execute('DIG', { block_ref: target })
  assert.equal(result.parameters.block_ref, target)
  assert.ok(result.started_at && result.finished_at)
  assert.equal(result.before.blocks.length, 1); assert.equal(result.after.blocks.length, 0)
  assert.equal(result.after.inventory_slots[11].count, 1)
  assert.ok(bot.calls.some(c => c[0] === 'dig' && c[2] === 'ignore'))
  assert.ok(!bot.calls.some(c => ['lookAt', 'look', 'equip', 'control'].includes(c[0])))
})

test('placement preserves chosen-slot operation and uses the specified face without tool search', async t => {
  const { bot, execute, block } = fixture(t)
  const target = block()
  await assert.rejects(execute('PLACE_BLOCK', { inventory_slot: 13, reference_block: target, face: 1 }), { code: 'EMPTY_SLOT' })
  assert.equal(bot.calls.length, 0)
  const result = await execute('PLACE_BLOCK', { inventory_slot: 36, reference_block: target, face: 1 })
  assert.equal(result.after.blocks.length, 2)
  assert.equal(result.after.inventory_slots[36].count, 7)
  assert.equal(bot.calls[0][3].forceLook, 'ignore')
  const next = await execute('PLACE_BLOCK', { inventory_slot: 10, reference_block: target, face: 2 })
  assert.deepEqual(next.explicit_slot_transfer, { source_slot: 10, hand_slot: 36 })
  assert.equal(bot.inventory.slots[36].count, 3)
})

test('select, use, swing and exact-slot drop do not interpret item names', async t => {
  const { bot, execute } = fixture(t)
  bot.inventory.slots[36].name = 'anything'; bot.inventory.slots[36].displayName = 'renamed'
  await execute('SELECT_HOTBAR_SLOT', { slot: 1 })
  await assert.rejects(execute('USE_HELD_ITEM'), { code: 'EMPTY_HAND' })
  await execute('SELECT_HOTBAR_SLOT', { slot: 0 })
  await execute('USE_HELD_ITEM', { duration_ms: 1 })
  await execute('SWING_ARM')
  await execute('DROP_ITEM', { slot: 36, amount: 2 })
  assert.equal(bot.inventory.slots[36].count, 6)
  assert.equal(bot.inventory.slots[10].count, 4)
  assert.deepEqual(bot.calls.filter(c => ['use', 'release', 'swing'].includes(c[0])).map(c => c[0]), ['use', 'release', 'swing'])
})

test('inventory transfer respects exact source, destination and count; equipment uses specified destination', async t => {
  const { bot, execute } = fixture(t)
  await execute('MOVE_INVENTORY_ITEM', { source_slot: 10, target_slot: 12, amount: 2 })
  assert.equal(bot.inventory.slots[10].count, 2); assert.equal(bot.inventory.slots[12].count, 2)
  await execute('EQUIP_FROM_SLOT', { source_slot: 12, equipment_slot: 5 })
  assert.equal(bot.inventory.slots[45].count, 2); assert.equal(bot.inventory.slots[12], null)
  assert.ok(!bot.calls.some(c => c[0] === 'hotbar'))
})

test('block use works with empty hands; entity interaction and attack use only refs', async t => {
  const { body, bot, execute, block, entity } = fixture(t)
  bot.inventory.updateSlot(36, null)
  await execute('INTERACT_BLOCK', { block_ref: block() })
  await execute('INTERACT_ENTITY', { entity_ref: entity() })
  await execute('ATTACK_ENTITY', { entity_ref: entity() })
  assert.ok(bot.calls.some(c => c[0] === 'packet' && c[1] === 'block_place'))
  assert.ok(bot.calls.some(c => c[0] === 'interact_entity' && c[1] === 2))
  assert.ok(bot.calls.some(c => c[0] === 'attack' && c[1] === 2))
  assert.ok(!bot.calls.some(c => c[0] === 'lookAt'))
  const ref = body.observe().nearbyEntities[0].entity_ref
  delete bot.entities[2]
  await assert.rejects(execute('ATTACK_ENTITY', { entity_ref: ref }), { code: 'INVALID_REFERENCE' })
})

test('invalid ordinary attack target returns feedback without a packet, reconnect or replacement target', async t => {
  const { body, bot, execute, entity } = fixture(t)
  for (const name of ['item', 'experience_orb']) {
    bot.entities[2].entityType = bot.registry.entitiesByName[name].id
    bot.entities[2].name = 'debug_name_does_not_decide'
    const ref = entity()
    await assert.rejects(execute('ATTACK_ENTITY', { entity_ref: ref }), e => {
      assert.equal(e.code, 'INVALID_ATTACK_TARGET')
      assert.equal(e.details.constraint_category, 'ENVIRONMENT_CONSTRAINT')
      assert.equal(e.details.corrective_action_taken, false)
      return true
    })
    assert.equal(body.status().connected, true)
  }
  assert.equal(bot.calls.length, 0)
  bot.entities[2].entityType = bot.registry.entitiesByName.cow.id
  await execute('ATTACK_ENTITY', { entity_ref: entity() })
  assert.deepEqual(bot.calls, [['attack', 2]])
})

test('empty crafting-slot click returns NO_EFFECT without waiting for a nonexistent update or disconnecting', async t => {
  const { body, bot, execute } = fixture(t)
  const id = body.observe().inventoryScreen.container_id
  await assert.rejects(execute('CLICK_SLOT', { container_id: id, slot: 4, mouse_button: 1 }), e => {
    assert.equal(e.code, 'NO_EFFECT')
    assert.equal(e.details.constraint_category, 'ENVIRONMENT_CONSTRAINT')
    return true
  })
  assert.equal(bot.calls.length, 0)
  assert.equal(body.status().connected, true)
  // Clicking that same empty slot with a real cursor stack remains available.
  await execute('CLICK_SLOT', { container_id: id, slot: 10, mouse_button: 0 })
  await execute('CLICK_SLOT', { container_id: id, slot: 4, mouse_button: 1 })
  assert.equal(bot.inventory.slots[4].count, 1)
})

test('container opens through world feedback and provides raw slots for take/put/move/close', async t => {
  const { body, bot, execute, block } = fixture(t)
  const window = bot.makeContainer(); bot.setItem(window, 0, 1, 3); bot.nextWindow = window
  await execute('INTERACT_BLOCK', { block_ref: block() })
  const id = body.observe().container.container_id
  await execute('TAKE_CONTAINER_ITEM', { container_id: id, source_slot: 0, target_slot: 9, amount: 1 })
  assert.equal(window.slots[9].count, 1); assert.equal(window.slots[0].count, 2)
  await execute('PUT_CONTAINER_ITEM', { container_id: id, source_slot: 9, target_slot: 1, amount: 1 })
  await execute('MOVE_CONTAINER_ITEM', { container_id: id, source_slot: 1, target_slot: 2, amount: 1 })
  assert.equal(window.slots[2].count, 1)
  await assert.rejects(execute('TAKE_CONTAINER_ITEM', { container_id: id, source_slot: 2, target_slot: 3, amount: 1 }), { code: 'INVALID_SLOT_REGION' })
  await execute('CLOSE_CONTAINER', { container_id: id })
  assert.equal(body.observe().container, null)
  bot.currentWindow = bot.makeContainer()
  await assert.rejects(execute('CLOSE_CONTAINER', { container_id: id }), { code: 'STALE_WINDOW' })
})

test('personal and table crafting grids operate by slots; result is supplied only by the environment', async t => {
  const { body, bot, execute, block } = fixture(t)
  await execute('OPEN_CRAFTING_INTERFACE')
  assert.deepEqual(body.observe().crafting.input_slots, [1, 2, 3, 4])
  await execute('MOVE_ITEM_TO_CRAFT_SLOT', { source_slot: 10, target_slot: 1, amount: 1 })
  await assert.rejects(execute('TAKE_CRAFT_RESULT', { target_slot: 13 }), { code: 'EMPTY_SLOT' })
  // Server fixture supplies an arbitrary output; the bridge has no recipe information.
  bot.setItem(bot.inventory, 0, 2, 4)
  await execute('TAKE_CRAFT_RESULT', { target_slot: 13 })
  assert.equal(bot.inventory.slots[13].type, 2)
  await execute('CLOSE_CRAFTING_INTERFACE')
  assert.equal(body.observe().crafting, null)
  const table = bot.makeCrafting(); bot.setItem(table, 10, 1, 2); bot.nextWindow = table
  await execute('INTERACT_BLOCK', { block_ref: block() })
  await execute('OPEN_CRAFTING_INTERFACE')
  assert.equal(body.observe().crafting.input_slots.length, 9)
  await execute('MOVE_ITEM_TO_CRAFT_SLOT', { source_slot: 10, target_slot: 9, amount: 1 })
  await execute('CLOSE_CRAFTING_INTERFACE')
  assert.equal(bot.currentWindow, null)
})

test('furnace output slot is not misclassified as a nine-slot crafting grid', async t => {
  const { body, bot, execute } = fixture(t)
  bot.currentWindow = bot.makeContainer(); bot.currentWindow.type = 'minecraft:furnace'; bot.currentWindow.craftingResultSlot = 2
  assert.equal(body.observe().actionSpace.find(a => a.action_id === 'OPEN_CRAFTING_INTERFACE').currently_available, false)
  await assert.rejects(execute('OPEN_CRAFTING_INTERFACE'), { code: 'NO_CRAFTING_LAYOUT' })
})

test('reach failure has trace and causes no movement, aiming, equipment or replay', async t => {
  const { body, bot, execute } = fixture(t, { observation: { blockRadius: 8, entityRadius: 16, maxBlocks: 64, maxEntities: 64 } })
  bot.blocks.clear(); bot.blocks.set('7,64,0', { type: 1, name: 'debug', position: new Vec3(7, 64, 0), diggable: true })
  const ref = body.observe().nearbyBlocks[0].block_ref
  await assert.rejects(execute('DIG', { block_ref: ref }), e => {
    assert.equal(e.code, 'OUT_OF_REACH'); assert.equal(e.details.corrective_action_taken, false)
    assert.ok(e.details.before && e.details.after && e.details.started_at); return true
  })
  assert.equal(bot.calls.length, 0)
})

test('partial slot failure preserves cursor as feedback; explicit CLICK_SLOT can resolve it', async t => {
  const { body, bot, execute } = fixture(t)
  bot.failClickAt = 2
  await assert.rejects(execute('MOVE_INVENTORY_ITEM', { source_slot: 10, target_slot: 12, amount: 4 }), { code: 'ACTION_FAILED' })
  assert.equal(bot.calls.filter(c => c[0] === 'click').length, 2)
  assert.equal(body.observe().inventoryScreen.cursor.count, 4)
  await assert.rejects(execute('DROP_ITEM', { slot: 36, amount: 1 }), { code: 'CURSOR_OCCUPIED' })
  bot.failClickAt = null
  await execute('CLICK_SLOT', { container_id: body.observe().inventoryScreen.container_id, slot: 12, mouse_button: 0 })
  assert.equal(bot.inventory.slots[12].count, 4)
})

test('latched sprint/sneak survive short motion, while stop/death clear them and invalidate old refs', async t => {
  const { bot, execute, block } = fixture(t)
  const ref = block()
  await execute('SPRINT_START'); await execute('SNEAK_START')
  await execute('MOVE_BACKWARD_SHORT')
  assert.equal(bot.controls.sprint, true); assert.equal(bot.controls.sneak, true)
  await execute('SPRINT_STOP'); await execute('SNEAK_STOP')
  assert.equal(bot.controls.sprint, false)
  await execute('LOOK_DELTA', { yaw_delta: 0.15, pitch_delta: 0.1 })
  await execute('TURN_LEFT_SMALL'); await execute('TURN_RIGHT_SMALL')
  await execute('LOOK_AT', { object_ref: ref })
  bot.emit('death'); bot.emit('spawn')
  await assert.rejects(execute('DIG', { block_ref: ref }), { code: 'INVALID_REFERENCE' })
})
