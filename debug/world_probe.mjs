// DEBUG_ONLY experimenter inspection; never constructs or restores individual A.
import { createMinecraftBody, loadConfig } from '../minecraft/src/index.js'
import { writeFile } from 'node:fs/promises'

const body = createMinecraftBody(await loadConfig())
try {
  body.start()
  const deadline = Date.now() + 35000
  while (!body.status().connected) {
    if (Date.now() > deadline) throw new Error(JSON.stringify(body.status()))
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  await new Promise(resolve => setTimeout(resolve, 1200))
  const observation = body.observe()
  await writeFile(new URL('../storage/stage3-world-probe.json', import.meta.url), JSON.stringify(observation, null, 2))
  console.log(JSON.stringify(observation))
} finally {
  body.stop()
}
