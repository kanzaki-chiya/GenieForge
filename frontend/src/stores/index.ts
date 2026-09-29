import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const datInfo = ref<any>(null)
  const loading = ref(false)

  function setDatInfo(info: any) {
    datInfo.value = info
  }

  return { datInfo, loading, setDatInfo }
})
