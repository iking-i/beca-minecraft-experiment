// Carrier operations only. No recipes, pathfinding, goals, item-name decisions or retries.
import { readFileSync } from 'node:fs'
import { randomUUID } from 'node:crypto'
import { Vec3 } from 'vec3'
import { BodyError, requireObject } from './errors.js'
import { controls, setInput, blockHit, entityHit, sendBlockInput, startDig, endDig, nativeSlot, sendEntityInput } from './native_inputs.js'

export const actionCatalog = JSON.parse(readFileSync(new URL('../action-space.json', import.meta.url)))
const faces = [new Vec3(0, -1, 0), new Vec3(0, 1, 0), new Vec3(0, 0, -1), new Vec3(0, 0, 1), new Vec3(-1, 0, 0), new Vec3(1, 0, 0)]
const point = p => ({ x: p.x, y: p.y, z: p.z })
export const slotData = (item, slot) => ({ slot, item_type_id: item?.type ?? null, count: item?.count ?? 0,
  metadata: Number.isFinite(item?.metadata) ? item.metadata : null, durability: Number.isFinite(item?.durabilityUsed) ? item.durabilityUsed : null })
const fail = (code, message) => {
  const error = new BodyError(code, message)
  if (['INVALID_ATTACK_TARGET', 'NO_EFFECT'].includes(code)) error.constraint_category = 'ENVIRONMENT_CONSTRAINT'
  throw error
}
export function validateParameters(definition, parameters) {
  requireObject(parameters, 'parameters')
  for (const key of Object.keys(parameters)) if (!(key in definition.parameters)) fail('INVALID_ARGUMENT', `Unknown parameter ${key}`)
  for (const [key, schema] of Object.entries(definition.parameters)) {
    const value = parameters[key]
    if (value === undefined && schema.optional) continue
    if ((schema.type === 'string' && (typeof value !== 'string' || !value.length || value.length > 128)) ||
      (schema.type === 'number' && !Number.isFinite(value)) ||
      (schema.type === 'integer' && !Number.isSafeInteger(value)) ||
      (schema.minimum !== undefined && value < schema.minimum) || (schema.maximum !== undefined && value > schema.maximum)) {
      fail('INVALID_ARGUMENT', `Invalid parameter ${key}`)
    }
  }
}

// This module receives private session access; its returned facade exposes no bot.
export function createCapabilities({ action, ready, ensureSession, move, observe, respawn }) {
  const carrierRef = randomUUID().slice(0, 8)
  let sessionSeen, epochSeen, epoch = 0, nextRef = 0, references = new Map(), observed = new Set()
  let craftingOpen = false, windowSeen, windowSerial = 0
  function bind(session) {
    if (sessionSeen === session && epochSeen === session.referenceEpoch) return
    sessionSeen = session; epochSeen = session.referenceEpoch; epoch++; references = new Map(); observed = new Set(); craftingOpen = false; windowSeen = undefined
  }
  function ref(key, data) {
    let entry = references.get(key)
    if (!entry) { entry = { ref: `o${carrierRef}_${epoch}_${++nextRef}`, ...structuredClone(data) }; references.set(key, entry) }
    else Object.assign(entry, structuredClone(data))
    observed.add(entry.ref)
    return entry.ref
  }
  function windowId(bot) {
    const window = bot.currentWindow || bot.inventory
    if (windowSeen !== window) { windowSeen = window; windowSerial++ }
    return `w${carrierRef}_${epoch}_${windowSerial}`
  }
  function layout(bot) {
    const window = bot.currentWindow || bot.inventory
    const isGrid = !bot.currentWindow || ['minecraft:crafting', 'minecraft:crafting_table'].includes(window.type)
    const result = isGrid ? (window.craftingResultSlot ?? 0) : -1
    // Protocol slot layout, not recipe or block-use knowledge.
    const size = result < 0 ? 0 : (bot.currentWindow ? 9 : 4)
    return { result_slot: result, input_slots: Array.from({ length: size }, (_, i) => result + 1 + i) }
  }
  function screen(bot) {
    const window = bot.currentWindow || bot.inventory
    return { container_id: windowId(bot), slot_count: window.slots?.length ?? 46,
      inventory_start: window.inventoryStart ?? 9, inventory_end: window.inventoryEnd ?? 45,
      slot_state: (window.slots ?? []).map((item, i) => slotData(item, i)),
      cursor: slotData(window.selectedItem, -1), ...layout(bot) }
  }
  function describe(session, raw) {
    bind(session); const bot = session.bot
    observed = new Set()
    raw.nearbyBlocks.forEach(b => { b.block_ref = ref(`b:${bot.game?.dimension}:${b.position.x}:${b.position.y}:${b.position.z}`, { kind: 'block', position: b.position }) })
    raw.nearbyEntities.forEach(e => { e.entity_ref = ref(`e:${e.id}`, { kind: 'entity', id: e.id }); e.entity_id = e.id })
    // Retain references only for the bounded sensor sample. No hidden object memory.
    for (const [key, value] of references) if (!observed.has(value.ref)) references.delete(key)
    raw.inventorySlots = (bot.inventory.slots ?? Array.from({ length: 46 }, (_, i) => bot.inventory.items().find(item => item.slot === i))).map((item, i) => slotData(item, i))
    raw.selectedHotbarSlot = bot.quickBarSlot ?? 0
    raw.heldItem = slotData(bot.heldItem, (bot.QUICK_BAR_START ?? 36) + raw.selectedHotbarSlot)
    raw.controlModes = Object.fromEntries(controls.map(k => [k, !!session.modes?.[k]]))
    raw.controlState = controls.map(k => Number(!!session.modes?.[k]))
    raw.bodyInputs = { body_state: raw.bodyState, mounted: Number(!!bot.vehicle), sleeping: Number(!!bot.isSleeping),
      using_item: Number(!!bot.usingHeldItem), dig_active: Number(!!session.dig), hand: session.useHand ?? -1,
      offhand_item: slotData(bot.inventory.slots?.[45], 45), inventory_server_sequence: session.inventoryServerSequence ?? 0,
      slot_feedback_kind: 0 }
    const eye = bot.entity.position.offset(0, bot.entity.eyeHeight ?? 1.62, 0)
    const yaw = bot.entity.yaw, pitch = bot.entity.pitch
    const ray = bot.world?.raycast?.(eye, new Vec3(-Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch)), bot.game?.gameMode === 'creative' ? 5 : 4.5)
    const visible = ray && raw.nearbyBlocks.find(b => b.position.x === ray.position.x && b.position.y === ray.position.y && b.position.z === ray.position.z)
    raw.crosshair = visible ? { target_ref: visible.block_ref, face: ray.face,
      cursor_x: ray.intersect.x - ray.position.x, cursor_y: ray.intersect.y - ray.position.y, cursor_z: ray.intersect.z - ray.position.z } : null
    raw.entityCrosshair = null
    for (const entity of raw.nearbyEntities) {
      try {
        const hit = entityHit(bot, bot.entities[entity.id])
        raw.entityCrosshair = { target_ref: entity.entity_ref, x: hit.x, y: hit.y, z: hit.z }
        break
      } catch { /* Not a visible bounded entity ray hit; do not add hidden targets. */ }
    }
    raw.container = bot.currentWindow ? screen(bot) : null
    raw.inventoryScreen = screen(bot)
    raw.crafting = craftingOpen && layout(bot).result_slot >= 0 ? screen(bot) : null
    const window = bot.currentWindow || bot.inventory
    const slots = window.slots ?? []
    const requirements = { active_dig: !!session.dig, body_dead: raw.bodyState === 0, mounted: !!bot.vehicle, sleeping: !!bot.isSleeping,
      observed_object: observed.size > 0, observed_block: raw.nearbyBlocks.length > 0,
      observed_entity: raw.nearbyEntities.length > 0, inventory_item: raw.inventorySlots.some(s => s.count > 0),
      inventory_screen: !bot.currentWindow, held_item: !!bot.heldItem, empty_cursor: !window.selectedItem,
      open_container: !!bot.currentWindow, window_item: slots.some(Boolean),
      container_item: slots.slice(0, window.inventoryStart).some(Boolean),
      window_inventory_item: slots.slice(window.inventoryStart, window.inventoryEnd).some(Boolean),
      craft_layout: layout(bot).result_slot >= 0, open_crafting: craftingOpen && layout(bot).result_slot >= 0,
      craft_result: !!slots[layout(bot).result_slot]
    }
    raw.actionSpace = actionCatalog.actions.map(d => ({ code: d.code, action_id: d.action_id,
      category: 'BODY_CAPABILITY', parameter_schema: { type: 'object', properties: structuredClone(d.parameters),
        required: Object.entries(d.parameters).filter(([, s]) => !s.optional).map(([k]) => k), additionalProperties: false },
      currently_available: d.formal_enabled !== false && (d.action_id === 'RESPAWN' ? raw.bodyState === 0 : raw.bodyState !== 0) && d.environment_requirements.every(r => requirements[r]),
      formal_enabled: d.formal_enabled !== false, environment_requirement_codes: d.environment_requirements.map(r => actionCatalog.requirement_codes[r]),
      environment_requirements: [...d.environment_requirements],
      availability_source: 'ENVIRONMENT_CONSTRAINT', availability_is_success_prediction: false }))
    return raw
  }
  function target(bot, value, kind) {
    const entry = [...references.values()].find(r => r.ref === value && observed.has(value))
    if (!entry || (kind && entry.kind !== kind)) fail('INVALID_REFERENCE', 'Target is outside the current observed reference set')
    const object = entry.kind === 'block' ? bot.blockAt(new Vec3(entry.position.x, entry.position.y, entry.position.z)) : bot.entities[entry.id]
    if (!object || !object.position) fail('TARGET_UNAVAILABLE', 'Target is no longer available')
    return { kind: entry.kind, object }
  }
  function withinReach(bot, object, kind) {
    const eye = bot.entity.position.offset(0, bot.entity.eyeHeight ?? 1.62, 0)
    const p = object.position.offset(kind === 'block' ? 0.5 : 0, kind === 'block' ? 0.5 : 1, kind === 'block' ? 0.5 : 0)
    const limit = kind === 'block' ? 5 : 3
    if (eye.distanceTo(p) > limit) fail('OUT_OF_REACH', 'Target exceeds the bridge interaction reach limit')
  }
  function validateSlot(window, value) {
    if (!Number.isSafeInteger(value) || value < 0 || value >= window.slots.length) fail('INVALID_SLOT', 'Slot is outside this interface')
  }
  function inventoryOnly(bot) { if (bot.currentWindow) fail('WINDOW_CONFLICT', 'Inventory slots require the player inventory screen'); return bot.inventory }
  function openWindow(bot, id) {
    if (!bot.currentWindow) fail('NO_CONTAINER', 'No container is open')
    if (id !== windowId(bot)) fail('STALE_WINDOW', 'Container reference is stale')
    return bot.currentWindow
  }
  async function click(bot, window, signal, session, slot, button) {
    ensureSession(session, signal)
    if ((bot.currentWindow || bot.inventory) !== window) fail('WINDOW_CHANGED', 'Window changed during operation')
    await bot.clickWindow(slot, button, 0)
    ensureSession(session, signal)
  }
  async function transfer(bot, window, p, signal, session, result = false) {
    validateSlot(window, p.source_slot); validateSlot(window, p.target_slot)
    if (p.source_slot === p.target_slot) fail('INVALID_SLOT', 'Source and destination must differ')
    if (window.selectedItem) fail('CURSOR_OCCUPIED', 'Cursor contains an item; use CLICK_SLOT explicitly')
    const source = window.slots[p.source_slot], dest = window.slots[p.target_slot]
    if (!source) fail('EMPTY_SLOT', 'Source slot is empty')
    if (!result && (p.amount > source.count || p.amount < 1)) fail('INVALID_AMOUNT', 'Amount exceeds the source stack')
    if (dest) fail('TARGET_OCCUPIED', 'Explicit transfer requires an empty destination; use CLICK_SLOT for stacking or swapping')
    await click(bot, window, signal, session, p.source_slot, 0)
    if (result || p.amount === source.count) await click(bot, window, signal, session, p.target_slot, 0)
    else {
      for (let i = 0; i < p.amount; i++) await click(bot, window, signal, session, p.target_slot, 1)
      await click(bot, window, signal, session, p.source_slot, 0)
    }
  }
  async function equipSelectedSlot(bot, source, destination, signal, session) {
    const w = inventoryOnly(bot); validateSlot(w, source); validateSlot(w, destination)
    if (!w.slots[source]) fail('EMPTY_SLOT', 'Requested source slot is empty')
    if (w.selectedItem) fail('CURSOR_OCCUPIED', 'Cursor is occupied')
    if (destination !== source) {
      if (destination >= (bot.QUICK_BAR_START ?? 36) && destination < (bot.QUICK_BAR_START ?? 36) + 9) {
        // Number-key swap preserves the exact source stack, including equal-type stacks.
        ensureSession(session, signal)
        await bot.clickWindow(source, destination - (bot.QUICK_BAR_START ?? 36), 2)
        ensureSession(session, signal)
        return
      }
      await click(bot, w, signal, session, source, 0); await click(bot, w, signal, session, destination, 0)
      if (w.selectedItem) await click(bot, w, signal, session, source, 0)
    }
  }
  const sleep = (ms, signal) => new Promise((resolve, reject) => {
    const done = () => { clearTimeout(timer); signal.removeEventListener('abort', aborted) }
    const aborted = () => { done(); reject(signal.reason) }
    const timer = setTimeout(() => { done(); resolve() }, ms)
    signal.addEventListener('abort', aborted, { once: true })
  })
  async function performRequest(request) {
    requireObject(request, 'action request')
    const numeric = Object.hasOwn(request, 'code')
    const definition = actionCatalog.actions.find(d => numeric ? d.code === request.code : d.action_id === request.action_id)
    if (!definition) fail('UNKNOWN_ACTION', 'Action is not a formal body capability')
    if (numeric && definition.formal_enabled === false) fail('MACRO_NOT_FORMAL', 'Multi-input legacy convenience operation is debug-only')
    validateParameters(definition, request.parameters ?? {})
    const p = structuredClone(request.parameters ?? {})
    const before = observe()
    const session = definition.action_id === 'RESPAWN' ? sessionSeen : ready(); bind(session)
    const started_at = new Date().toISOString()
    const summary = raw => ({ position: raw.position, orientation: raw.orientation, inventory_slots: raw.inventorySlots,
      blocks: raw.nearbyBlocks.map(b => ({ block_ref: b.block_ref, block_type_id: b.type, position: b.position })),
      inventory_screen: raw.inventoryScreen, container: raw.container, crafting: raw.crafting, inputs: raw.bodyInputs,
      control_modes: numeric ? raw.controlState : raw.controlModes })
    const trace = { ...(numeric ? { code: definition.code } : { action_id: definition.action_id }), parameters: structuredClone(p), started_at, before: summary(before) }
    try {
      const dirs = { MOVE_FORWARD_SHORT: 'forward', MOVE_BACKWARD_SHORT: 'back', JUMP: 'jump', STRAFE_LEFT_SHORT: 'left', STRAFE_RIGHT_SHORT: 'right' }
      let value
      if (definition.action_id === 'RESPAWN') value = respawn()
      else if (dirs[definition.action_id]) value = await move({ direction: dirs[definition.action_id], durationMs: 120 })
      else value = await action(definition.action_id, async (session, signal) => {
        const bot = session.bot
        const window = bot.currentWindow || bot.inventory
        switch (definition.action_id) {
          case 'CONTROL_INPUT': setInput(session, p.control, p.pressed); break
          case 'USE_START':
            if (session.useHand >= 0) fail('USE_ACTIVE', 'Release existing held use explicitly')
            bot.activateItem(p.hand === 1); session.useHand = p.hand; break
          case 'USE_RELEASE':
            if (session.useHand < 0) fail('NO_ACTIVE_USE', 'No held input is active')
            bot.deactivateItem(); session.useHand = -1; break
          case 'SWAP_HANDS':
            inventoryOnly(bot)
            bot._client.write('block_dig', { status: 6, location: new Vec3(0, 0, 0), face: 0, sequence: 0 }); break
          case 'DISMOUNT':
            if (!bot.vehicle) fail('NOT_MOUNTED', 'No mounted body')
            setInput(session, 6, 1); break
          case 'WAKE':
            if (!bot.isSleeping) fail('NOT_SLEEPING', 'Body is not sleeping')
            // Installed bot.wake hardcodes legacy 2, which means stop_sprinting on 26.1.
            bot._client.write('entity_action', { entityId: bot.entity.id,
              actionId: bot.supportFeature('entityActionUsesStringMapper') ? 'stop_sleeping' : 2, jumpBoost: 0 }); break
          case 'SLOT_INPUT':
            if (p.container_id !== windowId(bot)) fail('STALE_WINDOW', 'Window reference is stale')
            await nativeSlot(bot, window, p); break
          case 'BLOCK_INPUT': {
            const t = target(bot, p.block_ref, 'block'); withinReach(bot, t.object, t.kind)
            const hit = blockHit(bot, t.object, p.face)
            const cursor = new Vec3(p.cursor_x, p.cursor_y, p.cursor_z)
            if (hit.cursor.distanceTo(cursor) > 0.02) fail('HIT_MISMATCH', 'Requested point is not the current collision ray hit')
            sendBlockInput(bot, t.object, p.hand, p.face, cursor); break
          }
          case 'ENTITY_INPUT': {
            const t = target(bot, p.entity_ref, 'entity'); withinReach(bot, t.object, t.kind)
            sendEntityInput(bot, t.object, p); break
          }
          case 'NO_OP': await sleep(120, signal); break
          case 'TURN_LEFT_SMALL': await bot.look(bot.entity.yaw + 0.15, bot.entity.pitch, true); break
          case 'TURN_RIGHT_SMALL': await bot.look(bot.entity.yaw - 0.15, bot.entity.pitch, true); break
          case 'LOOK_DELTA': await bot.look(bot.entity.yaw + p.yaw_delta, Math.max(-Math.PI / 2, Math.min(Math.PI / 2, bot.entity.pitch + p.pitch_delta)), true); break
          case 'SPRINT_START': case 'SPRINT_STOP': case 'SNEAK_START': case 'SNEAK_STOP': {
            const mode = definition.action_id.startsWith('SPRINT') ? 'sprint' : 'sneak'
            setInput(session, controls.indexOf(mode), Number(definition.action_id.endsWith('START'))); break
          }
          case 'LOOK_AT': {
            const t = target(bot, p.object_ref); await bot.lookAt(t.object.position.offset(t.kind === 'block' ? 0.5 : 0, t.kind === 'block' ? 0.5 : 1, t.kind === 'block' ? 0.5 : 0), true); break
          }
          case 'DIG': case 'DIG_START': {
            const t = target(bot, p.block_ref, 'block'); withinReach(bot, t.object, t.kind)
            const hit = blockHit(bot, t.object)
            if (!bot.canDigBlock(t.object)) fail('CANNOT_DIG', 'Current block/body cannot dig')
            // No Mineflayer bot.dig: it fabricates a local air update at timer completion.
            startDig(session, t.object, hit.face)
            if (definition.action_id === 'DIG') {
              const ms = bot.digTime(t.object)
              if (!Number.isFinite(ms)) { endDig(session, false); fail('CANNOT_DIG', 'Non-finite native dig duration') }
              await sleep(Math.max(1, ms), signal)
              endDig(session, true)
            }
            break
          }
          case 'DIG_CANCEL': endDig(session, false); break
          case 'DIG_FINISH': endDig(session, true); break
          case 'PLACE_BLOCK': {
            inventoryOnly(bot)
            const t = target(bot, p.reference_block, 'block'); withinReach(bot, t.object, t.kind)
            validateSlot(bot.inventory, p.inventory_slot)
            const hand = (bot.QUICK_BAR_START ?? 36) + (bot.quickBarSlot ?? 0)
            if (!bot.inventory.slots[p.inventory_slot]) fail('EMPTY_SLOT', 'Requested source slot is empty')
            if (p.inventory_slot !== hand) fail('HELD_SLOT_MISMATCH', 'Select or move the item with an explicit native input first')
            if (!bot.heldItem) fail('EMPTY_HAND', 'No item is held')
            if (!bot.blockAt(t.object.position.plus(faces[p.face]))) fail('BLOCK_UNLOADED', 'Destination is not loaded')
            const hit = blockHit(bot, t.object, p.face)
            sendBlockInput(bot, t.object, 0, hit.face, hit.cursor); break
          }
          case 'SELECT_HOTBAR_SLOT': bot.setQuickBarSlot(p.slot); break
          case 'USE_HELD_ITEM':
            if (session.useHand >= 0) fail('USE_ACTIVE', 'Release existing use explicitly')
            if (!bot.heldItem) fail('EMPTY_HAND', 'No item is held')
            try { bot.activateItem(); session.useHand = 0; await sleep(p.duration_ms ?? 120, signal) } finally { bot.deactivateItem(); session.useHand = -1 }
            break
          case 'SWING_ARM': bot.swingArm(); break
          case 'DROP_ITEM': {
            const w = inventoryOnly(bot); validateSlot(w, p.slot)
            if (w.selectedItem) fail('CURSOR_OCCUPIED', 'Cursor is occupied')
            if (!w.slots[p.slot]) fail('EMPTY_SLOT', 'Requested slot is empty')
            if (p.amount > w.slots[p.slot].count) fail('INVALID_AMOUNT', 'Amount exceeds the source stack')
            for (let i = 0; i < p.amount; i++) { ensureSession(session, signal); await bot.clickWindow(p.slot, 0, 4); ensureSession(session, signal) }
            break
          }
          case 'MOVE_INVENTORY_ITEM': await transfer(bot, inventoryOnly(bot), p, signal, session); break
          case 'EQUIP_FROM_SLOT': {
            const w = inventoryOnly(bot); validateSlot(w, p.source_slot)
            const destinations = [(bot.QUICK_BAR_START ?? 36) + (bot.quickBarSlot ?? 0), 5, 6, 7, 8, 45]
            const destination = destinations[p.equipment_slot]; validateSlot(w, destination)
            await equipSelectedSlot(bot, p.source_slot, destination, signal, session)
            break
          }
          case 'INTERACT_BLOCK': {
            const t = target(bot, p.block_ref, 'block'); withinReach(bot, t.object, t.kind)
            // activateBlock auto-aims. Use its negotiated packet codec without aim correction.
            const hit = blockHit(bot, t.object)
            sendBlockInput(bot, t.object, 0, hit.face, hit.cursor); break
          }
          case 'INTERACT_ENTITY': case 'ATTACK_ENTITY': {
            const t = target(bot, p.entity_ref, 'entity'); withinReach(bot, t.object, t.kind)
            entityHit(bot, t.object)
            if (definition.action_id === 'ATTACK_ENTITY') {
              // Protocol target validity, not a target-selection or survival policy.
              // Vanilla disconnects ordinary attack packets targeting these entity classes.
              // Registry names stay inside the carrier codec; A receives only type IDs/failure.
              const rejectedTypes = ['item', 'experience_orb'].map(name => bot.registry?.entitiesByName?.[name]?.id)
                .filter(Number.isSafeInteger)
              if (rejectedTypes.includes(t.object.entityType)) {
                fail('INVALID_ATTACK_TARGET', 'Target type cannot receive an ordinary entity-attack packet')
              }
              bot.attack(t.object)
            }
            else {
              const hit = entityHit(bot, t.object)
              sendEntityInput(bot, t.object, { hand: 0, x: hit.x, y: hit.y, z: hit.z })
            }
            break
          }
          case 'MOVE_CONTAINER_ITEM': case 'TAKE_CONTAINER_ITEM': case 'PUT_CONTAINER_ITEM': {
            const w = openWindow(bot, p.container_id)
            if (definition.action_id === 'TAKE_CONTAINER_ITEM' && !(p.source_slot < w.inventoryStart && p.target_slot >= w.inventoryStart && p.target_slot < w.inventoryEnd)) fail('INVALID_SLOT_REGION', 'TAKE requires container-to-inventory slots')
            if (definition.action_id === 'PUT_CONTAINER_ITEM' && !(p.source_slot >= w.inventoryStart && p.source_slot < w.inventoryEnd && p.target_slot < w.inventoryStart)) fail('INVALID_SLOT_REGION', 'PUT requires inventory-to-container slots')
            await transfer(bot, w, p, signal, session); break
          }
          case 'CLOSE_CONTAINER': bot.closeWindow(openWindow(bot, p.container_id)); craftingOpen = false; break
          case 'OPEN_CRAFTING_INTERFACE':
            if (layout(bot).result_slot < 0) fail('NO_CRAFTING_LAYOUT', 'Current screen has no crafting layout')
            craftingOpen = true; break
          case 'MOVE_ITEM_TO_CRAFT_SLOT':
            if (!craftingOpen || !layout(bot).input_slots.includes(p.target_slot)) fail('INVALID_CRAFT_SLOT', 'Target is not an open crafting input slot')
            await transfer(bot, window, p, signal, session); break
          case 'TAKE_CRAFT_RESULT': {
            const result = layout(bot).result_slot
            if (!craftingOpen || result < 0) fail('NO_CRAFTING_LAYOUT', 'No crafting interface is open')
            if (!(p.target_slot >= window.inventoryStart && p.target_slot < window.inventoryEnd)) fail('INVALID_SLOT_REGION', 'Result destination must be an inventory slot')
            await transfer(bot, window, { source_slot: result, target_slot: p.target_slot }, signal, session, true); break
          }
          case 'CLOSE_CRAFTING_INTERFACE': if (bot.currentWindow) bot.closeWindow(bot.currentWindow); craftingOpen = false; break
          case 'CLICK_SLOT':
            if (p.container_id !== windowId(bot)) fail('STALE_WINDOW', 'Window reference is stale')
            if (p.slot !== -999) validateSlot(window, p.slot)
            // An empty slot and empty cursor cannot move an item. Mineflayer waits for
            // a crafting-result update after these clicks, even when none is generated.
            // Return feedback without substituting a slot, action, or fabricated update.
            if (!window.selectedItem && (p.slot === -999 || !window.slots[p.slot])) {
              fail('NO_EFFECT', 'Requested slot click has neither a slot item nor a cursor item')
            }
            await click(bot, window, signal, session, p.slot, p.mouse_button); break
          default: fail('UNKNOWN_ACTION', 'Action not implemented')
        }
        ensureSession(session, signal)
        return { confirmation: 'sent; verify by subsequent observation' }
      })
      return { ...trace, finished_at: new Date().toISOString(), result: numeric ? { input_sent: 1, effect_acknowledged: 0 } : value, after: (() => { try { return summary(observe()) } catch { return null } })(),
        effect_attribution: 'temporal_observation_only' }
    } catch (error) {
      error.details = { ...trace, finished_at: new Date().toISOString(), after: (() => { try { return summary(observe()) } catch { return null } })(),
        ...(error.constraint_category ? { constraint_category: error.constraint_category } : {}),
        partial_effects_possible: true, corrective_action_taken: false, replayed: false }
      throw error
    }
  }
  async function perform(request) {
    try { return await performRequest(request) } catch (error) {
      // Human diagnostics/usage hints must not cross the numeric A-facing codec.
      if (request && Object.hasOwn(request, 'code')) error.message = error.code ?? 'ACTION_FAILED'
      throw error
    }
  }
  return { describe, perform }
}
