<template>
  <!-- 平时只渲染轻量按钮，点击后才挂载虚拟滚动下拉：效果命令可达上百条、每条的单位/科技选项上千项，全量挂载会卡住切换 -->
  <el-select-v2
    v-if="active"
    ref="selectRef"
    :model-value="modelValue"
    :options="options"
    :placeholder="placeholder || '选择'"
    size="small"
    filterable
    clearable
    style="width: 100%"
    @update:model-value="$emit('update:modelValue', $event)"
    @change="$emit('change', $event)"
    @visible-change="onVisible"
  />
  <button v-else type="button" class="enum-lite" :title="display" @click="activate">
    <span :class="{ ph: display === '' }">{{ display || placeholder || '选择' }}</span>
    <span class="arrow">▾</span>
  </button>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { api } from '../api/client'

type Item = { value: number; label: string }

// 模块级枚举缓存，避免同一枚举重复请求
const cache = new Map<string, Item[]>()
// 每个选项数组对应的 value → label 索引，多个下拉共用同一数组时只建一次
const labelIndex = new WeakMap<Item[], Map<number, string>>()

function labelOf(items: Item[], value: number): string | undefined {
  let idx = labelIndex.get(items)
  if (!idx) {
    idx = new Map(items.map((x) => [x.value, x.label]))
    labelIndex.set(items, idx)
  }
  return idx.get(value)
}

const props = defineProps<{
  modelValue: number | null | undefined
  metaName?: string
  placeholder?: string
  preloaded?: Item[]
}>()
defineEmits(['update:modelValue', 'change'])

const fetched = ref<Item[]>([])
const active = ref(false)
const selectRef = ref<any>(null)

const items = computed(() => props.preloaded || fetched.value)
const options = computed(() => items.value.map((x) => ({ value: x.value, label: `${x.value} - ${x.label}` })))
const display = computed(() => {
  const v = props.modelValue
  if (v == null) return ''
  const label = labelOf(items.value, v)
  return label === undefined ? String(v) : `${v} - ${label}`
})

async function activate() {
  active.value = true
  await nextTick()
  selectRef.value?.focus?.()
  selectRef.value?.toggleMenu?.()
}

function onVisible(visible: boolean) {
  if (!visible) active.value = false
}

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

<style scoped>
.enum-lite {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 24px;
  padding: 0 8px;
  font: inherit;
  font-size: 12px;
  color: var(--el-text-color-regular);
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color);
  border-radius: var(--el-border-radius-base);
  cursor: pointer;
  text-align: left;
  overflow: hidden;
}
.enum-lite:hover {
  border-color: var(--el-border-color-hover);
}
.enum-lite > span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.enum-lite .ph {
  color: var(--el-text-color-placeholder);
}
.arrow {
  margin-left: 6px;
  color: var(--el-text-color-placeholder);
}
</style>
