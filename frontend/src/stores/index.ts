import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

export * from './history'

export interface DatCounts {
  civs?: number
  techs?: number
  effects?: number
  unit_headers?: number
  graphics?: number
  sounds?: number
}

export interface DatInfo {
  version: string | null
  path: string | null
  source_sha256?: string | null
  dirty: boolean
  counts: DatCounts
  language_entries?: number
}

export const useAppStore = defineStore('app', () => {
  const datInfo = ref<DatInfo | null>(null)
  const loading = ref(false)

  function setDatInfo(info: DatInfo | null) {
    datInfo.value = info
  }

  async function refreshDatInfo(): Promise<DatInfo | null> {
    try {
      const info = (await api.datInfo()) as DatInfo
      datInfo.value = info
      return info
    } catch {
      datInfo.value = null
      return null
    }
  }

  return { datInfo, loading, setDatInfo, refreshDatInfo }
})
