// Native input codecs. No target selection, prediction of world edits, retries or recipes.
import { Vec3 } from 'vec3'
import { BodyError } from './errors.js'

export const controls = ['forward', 'back', 'left', 'right', 'jump', 'sprint', 'sneak']
const fail = (code, message) => { throw new BodyError(code, message) }
const handName = hand => hand ? 'off_hand' : 'main_hand'

export function setInput(session, index, pressed) {
  const bot = session.bot, key = controls[index]
  session.modes ??= {}; session.modes[key] = !!pressed
  bot.setControlState(key, !!pressed)
  if (bot.supportFeature?.('newPlayerInputPacket')) {
    // Send the whole mask: Mineflayer's individual sneak update clears other packet bits.
    bot._client.write('player_input', { inputs: {
      forward: !!session.modes.forward, backward: !!session.modes.back, left: !!session.modes.left,
      right: !!session.modes.right, jump: !!session.modes.jump, shift: !!session.modes.sneak, sprint: !!session.modes.sprint
    } })
  }
}

export function blockHit(bot, block, requestedFace) {
  if (!bot.world?.raycast) fail('CARRIER_LIMITATION', 'Carrier has no collision ray sensor')
  const eye = bot.entity.position.offset(0, bot.entity.eyeHeight ?? 1.62, 0)
  const yaw = bot.entity.yaw, pitch = bot.entity.pitch
  const direction = new Vec3(-Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch))
  const hit = bot.world.raycast(eye, direction, bot.game?.gameMode === 'creative' ? 5 : 4.5)
  if (!hit || !hit.position.equals(block.position)) fail('NOT_IN_VIEW', 'Requested target is not the current collision ray hit')
  if (requestedFace !== undefined && hit.face !== requestedFace) fail('FACE_MISMATCH', 'Requested face is not the current ray hit face')
  return { face: hit.face, cursor: hit.intersect.minus(block.position) }
}

export function entityHit(bot, entity) {
  const eye = bot.entity.position.offset(0, bot.entity.eyeHeight ?? 1.62, 0)
  const yaw = bot.entity.yaw, pitch = bot.entity.pitch
  const dir = new Vec3(-Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch))
  if (!Number.isFinite(entity.width) || !Number.isFinite(entity.height)) fail('CARRIER_LIMITATION', 'Entity collision bounds unavailable')
  function entryDistance(candidate) {
    if (!candidate.position || !Number.isFinite(candidate.width) || !Number.isFinite(candidate.height)) return null
    let lo = 0, hi = bot.game?.gameMode === 'creative' ? 5 : 3
    for (const axis of ['x', 'y', 'z']) {
      const low = candidate.position[axis] - (axis === 'y' ? 0 : candidate.width / 2)
      const high = low + (axis === 'y' ? candidate.height : candidate.width)
      if (Math.abs(dir[axis]) < 1e-10) { if (eye[axis] < low || eye[axis] > high) return null; continue }
      const a = (low - eye[axis]) / dir[axis], b = (high - eye[axis]) / dir[axis]
      lo = Math.max(lo, Math.min(a, b)); hi = Math.min(hi, Math.max(a, b))
    }
    return lo <= hi ? lo : null
  }
  const lo = entryDistance(entity)
  if (lo === null) fail('NOT_IN_VIEW', 'Entity outside current ray/reach')
  for (const candidate of Object.values(bot.entities)) {
    if (candidate.id === entity.id || candidate.id === bot.entity.id) continue
    const distance = entryDistance(candidate)
    if (distance !== null && distance < lo) fail('OCCLUDED', 'Another entity occludes the requested target')
  }
  if (!bot.world?.raycast) fail('CARRIER_LIMITATION', 'Carrier has no collision ray sensor')
  if (bot.world.raycast(eye, dir, Math.max(0, lo - 0.001))) fail('OCCLUDED', 'A block occludes the entity ray')
  return eye.plus(dir.scaled(lo)).minus(entity.position)
}

export function sendBlockInput(bot, block, hand, face, cursor) {
  if (!bot.supportFeature('blockPlaceHasInsideBlock')) fail('CARRIER_LIMITATION', 'This raw input codec requires the audited modern block-use layout')
  bot._client.write('block_place', { location: block.position, direction: face, hand: handName(hand),
    cursorX: cursor.x, cursorY: cursor.y, cursorZ: cursor.z, insideBlock: false, worldBorderHit: false, sequence: 0 })
}

export function startDig(session, block, face) {
  if (session.dig) fail('DIG_ACTIVE', 'Finish or cancel the existing dig explicitly')
  session.bot._client.write('block_dig', { status: 0, location: block.position, face, sequence: 0 })
  session.dig = { position: block.position.clone(), face }
}

export function endDig(session, finish) {
  if (!session.dig) fail('NO_ACTIVE_DIG', 'No explicit dig is active')
  const { position, face } = session.dig
  session.bot._client.write('block_dig', { status: finish ? 2 : 1, location: position, face, sequence: 0 })
  session.dig = null
}

export async function nativeSlot(bot, window, p) {
  const allowed = { 0: [0, 1], 1: [0, 1], 2: [0, 1, 2, 3, 4, 5, 6, 7, 8], 4: [0, 1] }
  if (!(p.mode in allowed)) fail('CARRIER_LIMITATION', 'Creative clone, drag and double-click are not faithfully modeled by this carrier')
  if (!allowed[p.mode].includes(p.button)) fail('INVALID_ARGUMENT', 'Button incompatible with slot input mode')
  if (p.slot === -999 && p.mode !== 0) fail('INVALID_SLOT', 'Outside click only supports ordinary cursor drop')
  if (p.slot !== -999 && (p.slot < 0 || p.slot >= window.slots.length)) fail('INVALID_SLOT', 'Slot outside current window')
  if (!window.selectedItem && (p.slot === -999 || !window.slots[p.slot])) fail('NO_EFFECT', 'No cursor or slot item for this input')
  await bot.clickWindow(p.slot, p.button, p.mode)
}

export function sendEntityInput(bot, entity, p) {
  if (!bot.supportFeature('attackUsesOwnPacket')) fail('CARRIER_LIMITATION', 'Explicit hand/location input requires audited protocol layout')
  const hit = entityHit(bot, entity)
  const half = entity.width / 2
  const epsilon = 1e-7 // Floating point ray intersection tolerance, not aim correction.
  if (Math.abs(p.x) > half + epsilon || Math.abs(p.z) > half + epsilon || p.y < -epsilon || p.y > entity.height + epsilon) fail('INVALID_HIT_POSITION', 'Relative interaction point outside entity bounds')
  if (hit.distanceTo(new Vec3(p.x, p.y, p.z)) > 0.02) fail('HIT_MISMATCH', 'Relative point is not the current collision ray hit')
  bot._client.write('use_entity', { target: entity.id, hand: handName(p.hand),
    location: new Vec3(p.x, p.y, p.z), sneaking: !!bot.getControlState('sneak') })
}
