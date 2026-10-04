import test from 'node:test'
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { Vec3 } from 'vec3'
import { createBody } from '../src/body.js'
import { actionCatalog } from '../src/capabilities.js'
import { CapabilityBot } from '../testing/capability_bot.js'

function fixture(t) {
  const bot = new CapabilityBot(); let connectionOptions
  const body = createBody({ host:'127.0.0.1',port:25565,username:'TestBody',auth:'offline',reconnect:{enabled:false} },
    {createBot:opts => { connectionOptions=opts; return bot },logger:{info(){},warn(){},error(){}}})
  body.start(); bot.emit('spawn'); t.after(() => body.stop())
  const run = (name,parameters={}) => body.perform({code:actionCatalog.actions.find(a=>a.action_id===name).code,parameters})
  const available = name => body.observe().actionSpace.find(a=>a.action_id===name).currently_available
  return { bot,body,run,available,connectionOptions }
}

test('independent held keys compose across short moves; releasing one preserves the others', async t => {
  const {bot,body,run,available}=fixture(t)
  assert.equal(available('CONTROL_INPUT'),true)
  await run('CONTROL_INPUT',{control:0,pressed:1}); await run('CONTROL_INPUT',{control:4,pressed:1})
  await run('MOVE_BACKWARD_SHORT')
  assert.equal(bot.controls.forward,true); assert.equal(bot.controls.jump,true); assert.equal(bot.controls.back,false)
  await run('CONTROL_INPUT',{control:0,pressed:0})
  assert.equal(body.observe().controlModes.forward,false); assert.equal(bot.controls.jump,true)
  await assert.rejects(run('CONTROL_INPUT',{control:7,pressed:1}),{code:'INVALID_ARGUMENT'})
  bot.emit('death'); await assert.rejects(run('CONTROL_INPUT',{control:0,pressed:1}),{code:'NOT_READY'})
  assert.ok(Object.values(bot.controls).every(v=>!v))
})

test('hand use stays held until explicit release; empty use is an input, not a promise of consumption', async t => {
  const {bot,body,run,available}=fixture(t)
  assert.equal(available('USE_START'),true)
  const result=await run('USE_START',{hand:1})
  assert.equal(result.code,35); assert.equal(result.action_id,undefined)
  assert.deepEqual(result.result,{input_sent:1,effect_acknowledged:0})
  assert.ok(Array.isArray(result.before.control_modes))
  assert.equal(body.observe().bodyInputs.hand,1); assert.equal(bot.usingHeldItem,true)
  await assert.rejects(run('USE_START',{hand:0}),{code:'USE_ACTIVE'})
  await assert.rejects(run('USE_START',{hand:2}),{code:'INVALID_ARGUMENT'})
  await run('NO_OP'); assert.equal(bot.usingHeldItem,true)
  bot.usingHeldItem = false // A server can reject empty-item use while the requested input remains held.
  assert.equal(body.observe().bodyInputs.hand,1)
  await run('USE_RELEASE'); assert.equal(bot.usingHeldItem,false)
  await assert.rejects(run('USE_RELEASE'),{code:'NO_ACTIVE_USE'})
  assert.equal(bot.calls.filter(c=>c[0]==='use').length,1)
  await run('USE_START',{hand:0}); bot.emit('death'); assert.equal(bot.usingHeldItem,false)
})

test('dig start/cancel/finish preserve exact target; only environment feedback changes a block', async t => {
  const {bot,body,run,available}=fixture(t); const ref=body.observe().crosshair.target_ref
  assert.equal(available('DIG_CANCEL'),false); assert.equal(available('DIG_FINISH'),false)
  await run('DIG_START',{block_ref:ref}); assert.equal(available('DIG_CANCEL'),true)
  assert.equal(body.observe().nearbyBlocks.length,1)
  await assert.rejects(run('DIG_START',{block_ref:ref}),{code:'DIG_ACTIVE'})
  await run('DIG_CANCEL'); assert.equal(body.observe().nearbyBlocks.length,1)
  await assert.rejects(run('DIG_CANCEL'),{code:'NO_ACTIVE_DIG'})
  await run('DIG_START',{block_ref:ref}); await run('DIG_FINISH')
  assert.equal(body.observe().nearbyBlocks.length,0)
  await assert.rejects(run('DIG_FINISH'),{code:'NO_ACTIVE_DIG'})
  await assert.rejects(run('DIG_START',{block_ref:ref}),{code:'INVALID_REFERENCE'})
  assert.ok(!bot.calls.some(c=>c[0]==='dig'))
  assert.deepEqual(bot.calls.filter(c=>c[1]==='block_dig').map(c=>c[2].status),[0,1,0,2])
})

test('dig completion request does not synthesize air without an environment update', async t => {
  const {bot,body,run}=fixture(t); const ref=body.observe().crosshair.target_ref
  const original=bot._client.write
  bot._client.write=(name,p) => { if(name==='block_dig') bot.calls.push(['packet',name,p]); else original(name,p) }
  await run('DIG',{block_ref:ref})
  assert.equal(body.observe().nearbyBlocks.length,1)
})

test('respawn is conditional and never automatic; no action succeeds merely because a request was sent', async t => {
  const {bot,body,run,available,connectionOptions}=fixture(t)
  assert.equal(connectionOptions.respawn,false); assert.equal(available('RESPAWN'),false)
  await assert.rejects(run('RESPAWN'),{code:'INVALID_STATE'})
  bot.health=0; bot.emit('death')
  assert.equal(body.observe().bodyInputs.body_state,0)
  assert.deepEqual(body.observe().actionSpace.filter(a=>a.currently_available).map(a=>a.code),[40])
  assert.equal(bot.calls.filter(c=>c[0]==='respawn').length,0)
  const result=await run('RESPAWN'); assert.equal(result.after.inputs.body_state,0)
  assert.equal(bot.calls.filter(c=>c[0]==='respawn').length,1)
  bot.emit('respawn'); bot.health=20; bot.emit('spawn')
  assert.equal(available('RESPAWN'),false)
})

test('dismount uses explicit shift input, wake is conditional and neither fabricates server state', async t => {
  const {bot,body,run,available}=fixture(t)
  assert.equal(available('DISMOUNT'),false); assert.equal(available('WAKE'),false)
  await assert.rejects(run('DISMOUNT'),{code:'NOT_MOUNTED'}); await assert.rejects(run('WAKE'),{code:'NOT_SLEEPING'})
  bot.vehicle={id:3}; bot.isSleeping=true
  assert.equal(available('DISMOUNT'),true); assert.equal(available('WAKE'),true)
  await run('DISMOUNT'); assert.equal(bot.calls.findLast(c=>c[1]==='player_input')[2].inputs.shift,true)
  assert.equal(body.observe().bodyInputs.mounted,1)
  await run('WAKE'); assert.equal(body.observe().bodyInputs.sleeping,1)
  assert.equal(bot.calls.findLast(c=>c[1]==='entity_action')[2].actionId,'stop_sleeping')
  bot.vehicle=null; bot.isSleeping=false
  assert.equal(body.observe().bodyInputs.mounted,0)
})

test('raw slot input exposes native supported modes and refuses unsupported carriers without substitute clicks', async t => {
  const {bot,body,run,available}=fixture(t); const cid=body.observe().inventoryScreen.container_id
  assert.equal(available('SLOT_INPUT'),true)
  await run('SLOT_INPUT',{container_id:cid,slot:10,mode:2,button:1})
  assert.equal(bot.inventory.slots[37].count,4)
  await run('SLOT_INPUT',{container_id:cid,slot:37,mode:4,button:0})
  assert.equal(bot.inventory.slots[37].count,3)
  await run('SLOT_INPUT',{container_id:cid,slot:37,mode:1,button:0})
  const n=bot.calls.filter(c=>c[0]==='click').length
  for(const mode of [3,5,6]) await assert.rejects(run('SLOT_INPUT',{container_id:cid,slot:36,mode,button:0}),{code:'CARRIER_LIMITATION'})
  await assert.rejects(run('SLOT_INPUT',{container_id:cid,slot:36,mode:2,button:9}),{code:'INVALID_ARGUMENT'})
  await assert.rejects(run('SLOT_INPUT',{container_id:cid,slot:200,mode:0,button:0}),{code:'INVALID_SLOT'})
  await assert.rejects(run('SLOT_INPUT',{container_id:'old',slot:36,mode:0,button:0}),{code:'STALE_WINDOW'})
  await assert.rejects(run('SLOT_INPUT',{container_id:'old',slot:36,mode:0,button:0}),e=>e.message==='STALE_WINDOW')
  assert.equal(bot.calls.filter(c=>c[0]==='click').length,n)
  for(const a of body.observe().actionSpace.filter(a=>!a.formal_enabled)) {
    assert.equal(a.currently_available,false)
    await assert.rejects(body.perform({code:a.code,parameters:{}}),{code:'MACRO_NOT_FORMAL'})
  }
})

test('block and entity input send the explicit hand/point; no view, face or equipment correction', async t => {
  const {bot,body,run,available}=fixture(t)
  assert.equal(available('BLOCK_INPUT'),true); assert.equal(available('ENTITY_INPUT'),true)
  const ref=body.observe().crosshair.target_ref
  const p={block_ref:ref,hand:1,face:1,cursor_x:0.5,cursor_y:1,cursor_z:0.5}
  await run('BLOCK_INPUT',p)
  assert.equal(bot.calls.find(c=>c[1]==='block_place')[2].hand,'off_hand')
  await assert.rejects(run('BLOCK_INPUT',{...p,face:2}),{code:'FACE_MISMATCH'})
  await assert.rejects(run('BLOCK_INPUT',{...p,cursor_x:0}),{code:'HIT_MISMATCH'})
  await assert.rejects(run('BLOCK_INPUT',{...p,hand:2}),{code:'INVALID_ARGUMENT'})
  const er=body.observe().nearbyEntities[0].entity_ref
  await run('ENTITY_INPUT',{entity_ref:er,hand:1,x:0,y:1.62,z:0.3})
  assert.equal(bot.calls.find(c=>c[1]==='use_entity')[2].hand,'off_hand')
  await assert.rejects(run('ENTITY_INPUT',{entity_ref:er,hand:0,x:2,y:0,z:0}),{code:'INVALID_HIT_POSITION'})
  await assert.rejects(run('ENTITY_INPUT',{entity_ref:'old',hand:0,x:0,y:0,z:0}),{code:'INVALID_REFERENCE'})
  bot.entities[3]={id:3,width:0.6,height:1.8,position:new Vec3(0,64,-1)}
  await assert.rejects(run('ENTITY_INPUT',{entity_ref:er,hand:1,x:0,y:1.62,z:0.3}),{code:'OCCLUDED'})
  delete bot.entities[3]
  bot.world.raycast=()=>null
  await assert.rejects(run('BLOCK_INPUT',p),{code:'NOT_IN_VIEW'})
  bot.entity.yaw=Math.PI
  await assert.rejects(run('ENTITY_INPUT',{entity_ref:er,hand:0,x:0,y:0,z:0}),{code:'NOT_IN_VIEW'})
  assert.ok(!bot.calls.some(c=>['look','lookAt','equip'].includes(c[0])))
})

test('swap hand input is sent once, waits for server inventory evidence, and respects open GUI state', async t => {
  const {bot,body,run,available}=fixture(t)
  assert.equal(available('SWAP_HANDS'),true)
  await run('SWAP_HANDS')
  assert.equal(bot.calls.filter(c=>c[1]==='block_dig' && c[2].status===6).length,1)
  assert.equal(body.observe().inventorySlots[45].count,0)
  bot.currentWindow=bot.makeContainer()
  assert.equal(available('SWAP_HANDS'),false)
  await assert.rejects(run('SWAP_HANDS'),{code:'WINDOW_CONFLICT'})
})

test('raw modern packet codecs serialize using actual installed 26.1 protocol, including hand mappers', async t => {
  const {bot,body,run}=fixture(t)
  const require=createRequire(import.meta.resolve('mineflayer'))
  const {createSerializer}=require('minecraft-protocol')
  const serializer=createSerializer({state:'play',isServer:false,version:'26.1'})
  const h=body.observe().crosshair
  await run('BLOCK_INPUT',{block_ref:h.target_ref,hand:1,face:h.face,cursor_x:h.cursor_x,cursor_y:h.cursor_y,cursor_z:h.cursor_z})
  await run('ENTITY_INPUT',{entity_ref:body.observe().nearbyEntities[0].entity_ref,hand:1,x:0,y:1.62,z:0.3})
  await run('CONTROL_INPUT',{control:6,pressed:1}); await run('SWAP_HANDS')
  bot.isSleeping=true; await run('WAKE')
  await run('DIG_START',{block_ref:h.target_ref}); await run('DIG_CANCEL')
  for(const [,name,params] of bot.calls.filter(c=>c[0]==='packet')) assert.ok(serializer.createPacketBuffer({name,params}).length>0)
})

test('every new definition validates required/range parameters without any input on failure', async t => {
  const {bot,body}=fixture(t)
  for(const d of actionCatalog.actions.filter(d=>d.code>=34)) {
    await assert.rejects(body.perform({code:d.code,parameters:{unexpected:1}}),{code:'INVALID_ARGUMENT'})
    if (!Object.keys(d.parameters).length) continue
    await assert.rejects(body.perform({code:d.code,parameters:{}}),{code:'INVALID_ARGUMENT'})
  }
  assert.equal(bot.calls.length,0)
})
