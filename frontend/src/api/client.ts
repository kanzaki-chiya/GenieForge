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

const qs = (params: Record<string, string | number | boolean | undefined>) => {
  const u = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== '') u.set(k, String(v))
  })
  const s = u.toString()
  return s ? '?' + s : ''
}

export const api = {
  // 健康 / 配置
  health: () => request('/api/health'),
  getConfig: () => request('/api/config'),
  setConfig: (cfg: Record<string, unknown>) =>
    request('/api/config', { method: 'PUT', body: JSON.stringify(cfg) }),

  // dat
  datInfo: () => request('/api/dat/info'),
  loadDat: (path: string) =>
    request('/api/dat/load', { method: 'POST', body: JSON.stringify({ path }) }),
  saveDat: (path?: string) =>
    request('/api/dat/save', { method: 'POST', body: JSON.stringify({ path }) }),
  datReloadLanguage: () => request('/api/dat/reload-language', { method: 'POST' }),
  undo: () => request('/api/dat/undo', { method: 'POST' }),
  redo: () => request('/api/dat/redo', { method: 'POST' }),

  // 资源
  techs: (params: Record<string, string | number> = {}) => request('/api/techs' + qs(params)),
  techNames: () => request('/api/techs/names'),
  techDetail: (id: number) => request(`/api/techs/${id}`),
  patchTech: (id: number, body: Record<string, unknown>) =>
    request(`/api/techs/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  effects: (params: Record<string, string | number> = {}) => request('/api/effects' + qs(params)),
  effectNames: () => request('/api/effects/names'),
  effectDetail: (id: number) => request(`/api/effects/${id}`),
  patchEffect: (id: number, body: Record<string, unknown>) =>
    request(`/api/effects/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  civs: () => request('/api/civs'),
  civDetail: (id: number) => request(`/api/civs/${id}`),
  patchCiv: (id: number, body: Record<string, unknown>) =>
    request(`/api/civs/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  units: (civ: number, q?: string, page?: number, pageSize?: number) =>
    request('/api/units' + qs({ civ, q, page, page_size: pageSize })),
  unitDetail: (civ: number, unitId: number) => request(`/api/units/${civ}/${unitId}`),
  patchUnit: (civ: number, unitId: number, body: Record<string, unknown>) =>
    request(`/api/units/${civ}/${unitId}`, { method: 'PATCH', body: JSON.stringify(body) }),

  // 搜索 / 名称 / 引用
  search: (q: string) => request('/api/search' + qs({ q })),
  names: (id: number) => request(`/api/names/${id}`),
  refsForward: (table: string, id: number) => request(`/api/refs/forward/${table}/${id}`),
  refsReverse: (table: string, id: number) => request(`/api/refs/reverse/${table}/${id}`),

  // 枚举元数据
  meta: (name: string) => request(`/api/meta/${name}`),

  // diff 目标对比
  diffLoadTarget: (path: string) =>
    request('/api/diff/target/load', { method: 'POST', body: JSON.stringify({ path }) }),
  diffEntity: (table: string, id: number, civ?: number) =>
    request(`/api/diff/target/entity/${table}/${id}` + (civ != null ? qs({ civ }) : '')),

  // 批量 / 对比 / 补丁
  batchPreview: (targets: unknown[], ops: unknown[]) =>
    request('/api/batch/preview', { method: 'POST', body: JSON.stringify({ targets, ops }) }),
  batch: (targets: unknown[], ops: unknown[]) =>
    request('/api/batch', { method: 'POST', body: JSON.stringify({ targets, ops }) }),
  diff: (base: string, target: string) =>
    request('/api/diff', { method: 'POST', body: JSON.stringify({ base, target }) }),
  patchApply: (patch: string) =>
    request('/api/patch/apply', { method: 'POST', body: JSON.stringify({ patch }) }),
  patchPreview: (patch: string) =>
    request('/api/patch/preview', { method: 'POST', body: JSON.stringify({ patch }) }),
  patchList: () => request('/api/patch/list'),
  patchSave: (name: string, content: string) =>
    request('/api/patch/save', { method: 'POST', body: JSON.stringify({ name, content }) }),
  patchDelete: (name: string) => request(`/api/patch/${name}`, { method: 'DELETE' }),
  patchGenerate: (base: string, target: string) =>
    request('/api/patch/generate', { method: 'POST', body: JSON.stringify({ base, target }) }),

  // 版本 / 更新
  versionList: () => request('/api/version/list'),
  versionCheckout: (id: number) =>
    request('/api/version/checkout', { method: 'POST', body: JSON.stringify({ id }) }),
  updateCheck: () => request('/api/update/check')
}
