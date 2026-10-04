export class BodyError extends Error {
  constructor(code, message) {
    super(message)
    this.name = 'BodyError'
    this.code = code
  }
}

export function requireObject(value, name) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new BodyError('INVALID_ARGUMENT', `${name} 必须是对象`)
  }
}

export function integer(value, name, min, max) {
  if (!Number.isSafeInteger(value) || value < min || value > max) {
    throw new BodyError('INVALID_ARGUMENT', `${name} 必须是 ${min} 到 ${max} 的整数`)
  }
  return value
}
