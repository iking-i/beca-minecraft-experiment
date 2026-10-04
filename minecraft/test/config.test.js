import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { loadConfig } from '../src/config.js'

test('runtime port override leaves persistent configuration and other options unchanged', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'beca-port-'))
  try {
    const path = join(dir, 'config.json')
    const original = JSON.stringify({ host: '127.0.0.1', port: 25565, username: 'TestBody',
      auth: 'offline', observation: { blockRadius: 3 }, reconnect: { enabled: false } })
    await writeFile(path, original)
    const overridden = await loadConfig(path, { port: 62227 })
    assert.equal(overridden.port, 62227)
    assert.equal(overridden.observation.blockRadius, 3)
    assert.equal(overridden.reconnect.enabled, false)
    assert.equal((await loadConfig(path)).port, 25565)
    assert.equal(await readFile(path, 'utf8'), original)
    for (const port of [0, 65536, NaN, 1.5, '62227']) {
      await assert.rejects(loadConfig(path, { port }), { code: 'INVALID_CONFIG' })
    }
  } finally {
    await rm(dir, { recursive: true, force: true })
  }
})
