const DEFAULT_DEV_API_BASE = 'https://127.0.0.1:8443'
const API_BASE = (
  import.meta?.env?.VITE_API_BASE || (import.meta?.env?.DEV ? DEFAULT_DEV_API_BASE : '')
).replace(/\/$/, '')
const FALLBACK_ERROR_MESSAGE = '请求失败，请稍后重试'

function buildUrl(path) {
  return `${API_BASE}${path}`
}

function isApiEnvelope(payload) {
  return Boolean(
    payload &&
    typeof payload === 'object' &&
    typeof payload.code === 'number' &&
    typeof payload.message === 'string' &&
    Object.prototype.hasOwnProperty.call(payload, 'data')
  )
}

function readMessage(payload) {
  if (payload && typeof payload.message === 'string' && payload.message.trim()) {
    return payload.message.trim()
  }
  return FALLBACK_ERROR_MESSAGE
}

async function parseJson(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

async function requestApi(path, init) {
  let response
  try {
    response = await fetch(buildUrl(path), {
      credentials: 'include',
      ...(init || {}),
    })
  } catch {
    throw new Error(FALLBACK_ERROR_MESSAGE)
  }

  const payload = await parseJson(response)
  if (!isApiEnvelope(payload)) {
    throw new Error(FALLBACK_ERROR_MESSAGE)
  }

  if (!response.ok || payload.code !== 200) {
    throw new Error(readMessage(payload))
  }

  return payload.data
}

export async function fetchFonts() {
  const data = await requestApi('/api/fonts')
  return Array.isArray(data?.fonts) ? data.fonts : []
}

export async function fetchBackgrounds() {
  const data = await requestApi('/api/backgrounds')
  return Array.isArray(data?.backgrounds) ? data.backgrounds : []
}

export async function uploadBackground(file) {
  const form = new FormData()
  form.append('file', file)
  return requestApi('/api/upload', {
    method: 'POST',
    body: form,
  })
}

export async function generateHandwriting(payload) {
  const data = await requestApi('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return Array.isArray(data?.outputs) ? data.outputs : []
}

export function buildAssetUrl(path) {
  return `${API_BASE}${path}`
}
