<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder || '选择'"
    size="small"
    filterable
    clearable
    style="width: 100%"
    @update:model-value="$emit('update:modelValue', $event)"
    @change="$emit('change', $event)"
  >
    <el-option
      v-for="item in items"
      :key="item.value"
      :value="item.value"
      :label="`${item.value} - ${item.label}`"
    />
  </el-select>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../api/client'

// 模块级枚举缓存，避免同一枚举重复请求
const cache = new Map<string, { value: number; label: string }[]>()

const props = defineProps<{
  modelValue: number | null | undefined
  metaName?: string
  placeholder?: string
  preloaded?: { value: number; label: string }[]
}>()
defineEmits(['update:modelValue', 'change'])

const fetched = ref<{ value: number; label: string }[]>([])

const items = computed(() => props.preloaded || fetched.value)

onMounted(async () => {
  if (!props.metaName || props.preloaded) return
  if (cache.has(props.metaName)) {
    fetched.value = cache.get(props.metaName) || []
    return
  }
  try {
    const r: any = await api.meta(props.metaName)
    const list = r.items || []
    cache.set(props.metaName, list)
    fetched.value = list
  } catch {
    /* 枚举加载失败时退化为空下拉，可手动输入 */
  }
})
</script>
