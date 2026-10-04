import { createMinecraftBody, loadConfig } from '../src/index.js'

// TEST_ONLY read-only world smoke test: no movement, chat, digging or placement.
let body
try {
  const config = await loadConfig(process.argv[2])
  config.reconnect.enabled = false
  body = createMinecraftBody(config)
  body.start()
  const deadline = Date.now() + config.connectTimeoutMs + 1000
  while (body.status().state !== 'ready') {
    if (body.status().state === 'disconnected') throw new Error(body.status().lastError?.message ?? '连接失败')
    if (Date.now() > deadline) throw new Error('等待进入世界超时')
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  // Give initial chunk and inventory packets time to arrive after spawn.
  await new Promise(resolve => setTimeout(resolve, 1000))
  const snapshot = body.observe()
  console.log(JSON.stringify({ result: 'connected-and-observed', position: snapshot.position,
    health: snapshot.health, hunger: snapshot.hunger, time: snapshot.time,
    nearbyEntities: snapshot.nearbyEntities.length, nearbyBlocks: snapshot.nearbyBlocks.length,
    inventoryStacks: snapshot.inventory.length, coverage: snapshot.coverage }, null, 2))
} catch (error) {
  console.error(`世界连接验证失败：${error.message}`)
  process.exitCode = 1
} finally {
  body?.stop()
}
