<template>
  <el-input
    v-if="type === 'text' || type === 'number'"
    v-model="local"
    size="small"
    :placeholder="placeholder"
    @blur="commit"
    @keyup.enter="commit"
  />
  <EnumSelect
    v-else-if="type === 'enum'"
    :model-value="modelValue as number | null | undefined"
    :meta-name="metaName!"
    :preloaded="preloaded"
    :placeholder="placeholder"
    @change="onEnum"
  />
  <el-checkbox
    v-else-if="type === 'boolean'"
    :model-value="Boolean(modelValue)"
    @change="onBool"
  />
  <el-input v-else v-model="local" size="small" :placeholder="placeholder" @blur="commit" />
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import EnumSelect from './EnumSelect.vue'

const props = defineProps<{
  type: 'text' | 'number' | 'enum' | 'boolean' | string
  modelValue: unknown
  metaName?: string
  preloaded?: { value: number; label: string }[]
  placeholder?: string
}>()
const emit = defineEmits(['update:modelValue', 'commit'])

const local = ref('')

watch(
  () => props.modelValue,
  (v) => {
    local.value = v == null ? '' : String(v)
  },
  { immediate: true }
)

function commit() {
  let v: unknown = local.value
  if (props.type === 'number') {
    v = local.value.trim() === '' ? 0 : Number(local.value)
    if (Number.isNaN(v as number)) v = 0
  }
  emit('update:modelValue', v)
  emit('commit', v)
}

function onEnum(v: number) {
  emit('update:modelValue', v)
  emit('commit', v)
}

function onBool(v: boolean) {
  emit('update:modelValue', v)
  emit('commit', v)
}
</script>
