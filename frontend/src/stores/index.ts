import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

export const useAppStore = defineStore('app', () => {
  // dat 状态（顶栏常驻展示：文件名 / 版本 / 是否有未保存修改）
  const datInfo = ref<any>(null)
  const loading = ref(false)

  async function refresh() {
    try {
      datInfo.value = await api.datInfo()
    } catch {
      /* 后端未就绪时保持旧值 */
    }
  }

  function setDatInfo(info: any) {
    datInfo.value = info
  }

  return { datInfo, loading, refresh, setDatInfo }
})
