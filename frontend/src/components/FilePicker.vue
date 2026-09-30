<template>
  <div class="file-picker">
    <el-input
      :model-value="modelValue"
      :placeholder="placeholder"
      size="small"
      clearable
      @update:model-value="$emit('update:modelValue', $event)"
    />
    <el-button size="small" @click="browse">浏览…</el-button>
    <input
      ref="fileInput"
      type="file"
      accept=".dat"
      style="display: none"
      @change="onFileChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{ modelValue: string; placeholder?: string }>()
const emit = defineEmits(['update:modelValue'])

const fileInput = ref<HTMLInputElement>()

async function browse() {
  const w = (window as any).pywebview
  if (w && w.api && typeof w.api.open_file_dialog === 'function') {
    try {
      const path = await w.api.open_file_dialog()
      if (path) emit('update:modelValue', path)
    } catch {
      /* 桌面壳调用失败时降级到浏览器选择 */
      fileInput.value?.click()
    }
  } else {
    fileInput.value?.click()
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const f = input.files?.[0]
  if (f) {
    // 浏览器模式拿不到完整路径，回退用文件名（桌面壳走原生对话框拿完整路径）
    emit('update:modelValue', (f as any).path || f.name)
  }
  input.value = ''
}
</script>

<style scoped>
.file-picker {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
