// 后端 API 封装。桌面窗口与浏览器共用同一套 REST API（方案 §2.2）。

const BASE = 'http://127.0.0.1:8342'

export async function request<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  })
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${detail}`)
  }
  return res.json()
}

export const api = {
  health: () => request('/api/health'),
  datInfo: () => request('/api/dat/info'),
  loadDat: (path: string) =>
    request('/api/dat/load', { method: 'POST', body: JSON.stringify({ path }) }),
  saveDat: (path?: string) =>
    request('/api/dat/save', { method: 'POST', body: JSON.stringify({ path }) }),
  techs: (params: Record<string, string | number> = {}) =>
    request('/api/techs?' + new URLSearchParams(params as Record<string, string>)),
  civs: () => request('/api/civs'),
  diff: (base: string, target: string) =>
    request('/api/diff', { method: 'POST', body: JSON.stringify({ base, target }) }),
  patchApply: (patch: string) =>
    request('/api/patch/apply', { method: 'POST', body: JSON.stringify({ patch }) }),
  search: (q: string) => request('/api/search?' + new URLSearchParams({ q }))
}
