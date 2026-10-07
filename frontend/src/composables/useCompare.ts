// 全局对比状态（模块级单例）：四个数据页与并排对比页共享同一个「对比版本」选择。
import { reactive } from 'vue'
import { api } from '../api/client'

export interface VersionRecord {
  id: number
  label: string
  kind: string
  sha256: string
  size: number
  source_path: string
  created_at: number
}

const state = reactive({
  versions: [] as VersionRecord[],
  versionId: null as number | null,
  loaded: false,
  info: null as any
})

export function useCompare() {
  function selected(): VersionRecord | null {
    return state.versions.find((v) => v.id === state.versionId) ?? null
  }

  async function refreshVersions(): Promise<VersionRecord[]> {
    const r: any = await api.versionList()
    state.versions = r.versions || []
    // 版本被删掉后清空选择，避免右侧停留在已不存在的版本
    if (state.versionId != null && !state.versions.some((v) => v.id === state.versionId)) {
      state.versionId = null
      state.loaded = false
      state.info = null
    }
    return state.versions
  }

  /** 选中某个版本并加载它作为对比目标（POST /api/diff/target/load-version）。 */
  async function selectVersion(id: number | null) {
    if (id == null) {
      state.versionId = null
      state.loaded = false
      state.info = null
      return
    }
    const info: any = await api.diffLoadVersion(id)
    state.versionId = id
    state.loaded = true
    state.info = info
  }

  function clear() {
    state.versionId = null
    state.loaded = false
    state.info = null
  }

  return { state, selected, refreshVersions, selectVersion, clear }
}

export function versionLabel(v: VersionRecord): string {
  return `v${v.id} · ${v.label}`
}

export function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function formatTime(ts: number): string {
  const d = new Date(ts * 1000)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}
