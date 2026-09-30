import { reactive } from 'vue'
import { api } from '../api/client'

// 全局对比状态（模块级单例，所有页面共享同一对比文件）
const state = reactive({
  active: false,
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
  }

  async function toggle(path?: string) {
    if (!state.active) {
      // 激活对比：若未加载或路径不同则加载
      if (path && path !== state.path) {
        await loadTarget(path)
      }
      state.active = true
    } else {
      state.active = false
    }
  }

  return { state, loadTarget, toggle }
}
