// TEST_ONLY body/transport fixture. No actual Minecraft connection or recipes.
import { serveBody } from '../../bridge/server.js'
import { createBody } from '../../minecraft/src/body.js'
import { CapabilityBot } from '../../minecraft/testing/capability_bot.js'
import { readFileSync } from 'node:fs'

const fixtureOptions = JSON.parse(readFileSync(process.argv[2], 'utf8'))

let bot
const body = createBody({ host: '127.0.0.1', port: 25565, username: 'TestBody', auth: 'offline', reconnect: { enabled: false } },
  { logger: { info() {}, warn() {}, error() {} }, createBot: () => {
    bot = new CapabilityBot()
    if (fixtureOptions.fixture_window === 'container') {
      bot.nextWindow = bot.makeContainer(); bot.setItem(bot.nextWindow, 0, 1, 3)
    } else if (fixtureOptions.fixture_window === 'crafting') {
      bot.nextWindow = bot.makeCrafting(); bot.setItem(bot.nextWindow, 10, 1, 2)
      // Arbitrary environment-supplied output, not a recipe stored in the body.
      bot.setItem(bot.nextWindow, 0, 2, 4)
    }
    queueMicrotask(() => bot.emit('spawn')); return bot
  } })
serveBody(body)
