// TEST_ONLY: an environment double using the installed protocol window implementation.
// Never imported by the real body entry point or A runtime.
import { EventEmitter } from 'node:events'
import { createRequire } from 'node:module'
import { Vec3 } from 'vec3'
const requireDependency = createRequire(import.meta.resolve('mineflayer'))
const windows = requireDependency('prismarine-windows')('26.1')
const Item = requireDependency('prismarine-item')('26.1')
const registry = requireDependency('prismarine-registry')('26.1')

export class CapabilityBot extends EventEmitter {
  constructor() {
    super()
    this.version = '26.1'
    this.registry = registry
    this.username = 'TestBody'
    this.entity = { id: 1, position: new Vec3(0, 64, 0), yaw: 0, pitch: 0, eyeHeight: 1.62 }
    this.entities = { 1: this.entity, 2: { id: 2, entityType: 17, name: 'debug_entity', width: 0.6, height: 1.8, position: new Vec3(0, 64, -2) } }
    this.inventory = windows.createWindow(0, 'minecraft:inventory', 'test')
    this.currentWindow = null
    this.QUICK_BAR_START = 36
    this.quickBarSlot = 0
    this.health = 20; this.food = 20
    this.game = { dimension: 'overworld' }; this.time = { timeOfDay: 1, day: 1 }
    this.controls = {}; this.calls = []
    this.blocks = new Map([['1,64,0', { name: 'debug_block', type: 1, diggable: true, position: new Vec3(1, 64, 0) }]])
    this.setItem(this.inventory, 36, 1, 8)
    this.setItem(this.inventory, 10, 1, 4)
    this.nextWindow = null
    this.world = { raycast: (eye, dir, range) => range < 2 ? null : { position: new Vec3(1,64,0), face: 1, intersect: new Vec3(1.5,65,0.5) } }
    this._client = { write: (name, packet) => {
      this.calls.push(['packet', name, packet])
      // TEST_ONLY environment responses: production never fabricates these updates.
      if (name === 'block_dig' && packet.status === 2) {
        const old = this.blockAt(packet.location)
        this.blocks.delete(`${packet.location.x},${packet.location.y},${packet.location.z}`)
        this.setItem(this.inventory, 11, 1, 1)
        this.emit('blockUpdate', old, this.blockAt(packet.location))
      }
      const packetItem = packet.hand === 'off_hand' || packet.hand === 1 ? this.inventory.slots[45] : this.heldItem
      if (name === 'block_place' && !this.nextWindow && packetItem) {
        const faces = [new Vec3(0,-1,0),new Vec3(0,1,0),new Vec3(0,0,-1),new Vec3(0,0,1),new Vec3(-1,0,0),new Vec3(1,0,0)]
        const pos = packet.location.plus(faces[packet.direction])
        this.blocks.set(`${pos.x},${pos.y},${pos.z}`, { name:'debug_placed',type:packetItem.type,diggable:true,position:pos })
        packetItem.count--
      }
      if (name === 'block_place' && this.nextWindow) { this.currentWindow = this.nextWindow; this.nextWindow = null; this.emit('windowOpen', this.currentWindow) }
    } }
  }
  get heldItem() { return this.inventory.slots[36 + this.quickBarSlot] }
  setItem(window, slot, type, count) { window.updateSlot(slot, new Item(type, count)); return window.slots[slot] }
  makeContainer() { return windows.createWindow(1, 'minecraft:generic_9x1', 'test') }
  makeCrafting() { return windows.createWindow(2, 'minecraft:crafting', 'test') }
  blockAt(p) { return this.blocks.get(`${p.x},${p.y},${p.z}`) ?? { name: 'air', type: 0, position: p, diggable: false } }
  supportFeature(name) { return ['blockPlaceHasInsideBlock','newPlayerInputPacket','attackUsesOwnPacket','entityActionUsesStringMapper'].includes(name) }
  clearControlStates() { this.controls = {} }
  setControlState(key, value) { this.controls[key] = value; this.calls.push(['control', key, value]) }
  getControlState(key) { return !!this.controls[key] }
  async look(yaw, pitch) { this.calls.push(['look', yaw, pitch]); this.entity.yaw = yaw; this.entity.pitch = pitch }
  async lookAt(p) { this.calls.push(['lookAt', p]); this.entity.yaw = p.x }
  canDigBlock(block) { return block.diggable }
  async dig(block, forceLook) {
    this.calls.push(['dig', point(block.position), forceLook])
    this.blocks.delete(`${block.position.x},${block.position.y},${block.position.z}`)
    this.setItem(this.inventory, 11, 1, 1)
  }
  async _placeBlockWithOptions(block, face, options) {
    this.calls.push(['place', point(block.position), point(face), options])
    const p = block.position.plus(face)
    this.blocks.set(`${p.x},${p.y},${p.z}`, { name: 'debug_placed', type: this.heldItem.type, diggable: true, position: p })
    this.heldItem.count--
  }
  setQuickBarSlot(slot) { this.calls.push(['hotbar', slot]); this.quickBarSlot = slot }
  activateItem(offhand = false) { this.calls.push(['use', offhand]); this.usingHeldItem = true }
  deactivateItem() { this.calls.push(['release']); this.usingHeldItem = false }
  swingArm() { this.calls.push(['swing']) }
  useOn(entity) { this.calls.push(['interact_entity', entity.id]) }
  attack(entity) { this.calls.push(['attack', entity.id]) }
  async clickWindow(slot, mouseButton, mode) {
    const window = this.currentWindow || this.inventory
    this.calls.push(['click', slot, mouseButton, mode])
    if (this.failClickAt === this.calls.filter(c => c[0] === 'click').length) throw new Error('injected slot rejection')
    window.acceptClick({ slot, mouseButton, mode, item: slot === -999 ? null : window.slots[slot] })
  }
  closeWindow(window) { this.calls.push(['close', window.id]); this.currentWindow = null; this.emit('windowClose', window) }
  chat(message) { this.calls.push(['chat', message]) }
  digTime() { return 1 }
  respawn() { this.calls.push(['respawn']) }
  async wake() { this.calls.push(['wake']) }
  stopDigging() { this.calls.push(['stopDigging']) }
  end(reason) { this.emit('end', reason) }
}
const point = p => ({ x: p.x, y: p.y, z: p.z })
