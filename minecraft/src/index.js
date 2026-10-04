import mineflayer from 'mineflayer'
import minecraftData from 'minecraft-data'
import { createBody } from './body.js'
import { BodyError } from './errors.js'
import { validateConfig } from './config.js'

export { loadConfig } from './config.js'
export { BodyError } from './errors.js'

// Only a frozen interface leaves the public entry point. The bot stays private.
export function createMinecraftBody(config, { logger = console } = {}) {
  const validated = validateConfig(config)
  if (validated.version !== false && !minecraftData(validated.version)) {
    throw new BodyError('INVALID_CONFIG', `当前协议数据不支持版本 ${validated.version}`)
  }
  return createBody(validated, { logger, createBot: options => mineflayer.createBot(options) })
}
