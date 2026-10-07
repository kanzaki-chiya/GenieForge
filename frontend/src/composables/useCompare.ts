import { reactive } from 'vue'
import { api } from '../api/client'

// 全局对比状态（模块级单例，所有页面共享同一对比目标 dat）
const state = reactive({
  path: '',
  loaded: false,
  version: null as { techs: number; effects: number; civs: number } | null
})

export function useCompare() {
  async function loadTarget(path: string) {
    const info: any = await api.diffLoadTarget(path)
    state.path = path
    state.loaded = true
    state.version = info
    return info
  }

  // 按版本加载（由 EntityCompare 调 API 后登记）
  function markLoaded(source: string, info: { techs: number; effects: number; civs: number } | null) {
    state.path = source
    state.loaded = true
    state.version = info
  }

  return { state, loadTarget, markLoaded }
}
