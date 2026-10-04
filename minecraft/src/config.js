import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { BodyError, integer, requireObject } from './errors.js'

export const defaultConfigPath = fileURLToPath(new URL('../config.json', import.meta.url))

export function validateConfig(input) {
  requireObject(input, 'config')
  const config = structuredClone(input)
  for (const key of ['host', 'username']) {
    if (typeof config[key] !== 'string' || !config[key].trim()) {
      throw new BodyError('INVALID_CONFIG', `${key} 不能为空`)
    }
  }
  config.port = integer(config.port, 'port', 1, 65535)
  config.auth ??= 'offline'
  if (!['offline', 'microsoft'].includes(config.auth)) {
    throw new BodyError('INVALID_CONFIG', 'auth 只能是 offline 或 microsoft')
  }
  if (config.auth === 'offline' && !/^[A-Za-z0-9_]{3,16}$/.test(config.username)) {
    throw new BodyError('INVALID_CONFIG', '离线用户名须为 3–16 位字母、数字或下划线')
  }
  config.version ??= false
  if (config.version !== false && (typeof config.version !== 'string' || !config.version.trim())) {
    throw new BodyError('INVALID_CONFIG', 'version 必须为版本字符串或 false（自动检测）')
  }
  config.connectTimeoutMs = integer(config.connectTimeoutMs ?? 30000, 'connectTimeoutMs', 100, 600000)
  config.actionTimeoutMs = integer(config.actionTimeoutMs ?? 15000, 'actionTimeoutMs', 100, 120000)
  requireObject(config.reconnect ??= {}, 'reconnect')
  config.reconnect.enabled ??= true
  if (typeof config.reconnect.enabled !== 'boolean') throw new BodyError('INVALID_CONFIG', 'reconnect.enabled 必须是布尔值')
  config.reconnect.initialDelayMs = integer(config.reconnect.initialDelayMs ?? 1000, 'reconnect.initialDelayMs', 10, 300000)
  config.reconnect.maxDelayMs = integer(config.reconnect.maxDelayMs ?? 30000, 'reconnect.maxDelayMs', config.reconnect.initialDelayMs, 600000)
  requireObject(config.observation ??= {}, 'observation')
  config.observation.blockRadius = integer(config.observation.blockRadius ?? 4, 'blockRadius', 1, 8)
  config.observation.entityRadius = integer(config.observation.entityRadius ?? 16, 'entityRadius', 1, 64)
  config.observation.maxBlocks = integer(config.observation.maxBlocks ?? 64, 'maxBlocks', 1, 512)
  config.observation.maxEntities = integer(config.observation.maxEntities ?? 64, 'maxEntities', 1, 512)
  return config
}

export async function loadConfig(path = defaultConfigPath, { port } = {}) {
  try {
    const config = JSON.parse((await readFile(path, 'utf8')).replace(/^\uFEFF/, ''))
    if (port !== undefined) config.port = port
    return validateConfig(config)
  } catch (error) {
    throw new BodyError('INVALID_CONFIG', `无法读取配置 ${path}: ${error.message}`)
  }
}
