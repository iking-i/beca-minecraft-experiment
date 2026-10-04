// TEST_ONLY external test-fixture construction. Never imported by formal A runtime.
// `keep` places blocks only into air; it never clears existing blocks/buildings.
import { createInterface } from 'node:readline'
import { writeFile } from 'node:fs/promises'
import { createMinecraftBody, loadConfig } from '../minecraft/src/index.js'

const commands = [
  '/forceload add -8 6 0 14',
  '/fill -8 130 6 0 130 14 glass keep',
  '/fill -8 135 6 0 135 14 glass keep',
  '/fill -8 131 6 -8 134 14 glass keep',
  '/fill 0 131 6 0 134 14 glass keep',
  '/fill -7 131 6 -1 134 6 glass keep',
  '/fill -7 131 14 -1 134 14 glass keep',
  '/tp BECA_Body -3.5 131 10.5 0 0',
  '/spawnpoint BECA_Body -4 131 10'
]
const body = createMinecraftBody(await loadConfig())
let input
async function check() {
  if (!body.status().connected) return console.log('ARENA_NOT_READY: body is not ready')
  const obs = body.observe()
  const p = obs.position
  const ready = p.x > -8 && p.x < 0 && p.z > 6 && p.z < 14 && Math.abs(p.y - 131) < 0.01 &&
    obs.nearbyBlocks.some(b => b.name === 'glass' && b.position.y === 130)
  const report = { ready, position: p, commands, experimenter_fixture: true,
    inside: { x: [-7, -1], z: [7, 13], floor_y: 130, roof_y: 135 }, observation: obs }
  await writeFile(new URL('../storage/stage3-arena.json', import.meta.url), JSON.stringify(report, null, 2))
  console.log(JSON.stringify({ kind: ready ? 'ARENA_READY' : 'ARENA_NOT_READY', position: p }))
  return ready
}
try {
  body.start()
  const deadline = Date.now() + 35000
  while (!body.status().connected) {
    if (Date.now() > deadline) throw new Error(JSON.stringify(body.status()))
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  for (const command of commands) {
    body.chat(command)
    await new Promise(resolve => setTimeout(resolve, command.startsWith('/forceload ') ? 3000 : 200))
  }
  await new Promise(resolve => setTimeout(resolve, 1200))
  if (!(await check())) {
    console.log('Server did not grant commands or fixture is not ready. Host can run these commands:')
    commands.forEach(command => console.log(command))
    console.log('Body stays connected. Type check after setup, or exit to stop this external tool.')
    input = createInterface({ input: process.stdin })
    await new Promise(resolve => input.on('line', async line => {
      if (line.trim() === 'exit' || (line.trim() === 'check' && await check())) resolve()
    }).on('close', resolve))
  }
} finally {
  input?.close()
  body.stop()
}
