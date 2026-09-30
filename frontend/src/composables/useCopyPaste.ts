import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

// 全局剪贴板（AGE 式整实体复制粘贴）
const clipboard = ref<{ table: string; src: number; civ: number } | null>(null)

export function useCopyPaste(table: string, civ?: () => number) {
  function copy(currentId: number) {
    if (currentId == null || currentId < 0) return
    clipboard.value = { table, src: currentId, civ: civ?.() ?? 0 }
    ElMessage.success(`已复制 ${table}[${currentId}]（Ctrl+V 粘贴）`)
  }

  async function paste(currentId: number) {
    if (currentId == null || currentId < 0) return
    if (!clipboard.value) return ElMessage.warning('剪贴板为空（先选中一行 Ctrl+C 复制）')
    if (clipboard.value.table !== table) return ElMessage.warning('剪贴板来自其他表')
    if (clipboard.value.src === currentId) return ElMessage.warning('不能粘贴到自身')
    try {
      await api.copyEntity(table, clipboard.value.src, currentId, civ?.() ?? 0)
      ElMessage.success(`已粘贴到 ${table}[${currentId}]`)
    } catch (e: any) {
      ElMessage.error(e.message)
    }
  }

  return { copy, paste, clipboard }
}
