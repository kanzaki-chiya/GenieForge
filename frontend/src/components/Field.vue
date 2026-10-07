<template>
  <div class="field" :class="{ 'is-modified': modified }">
    <div class="field-header">
      <span class="field-label" :title="label">{{ label }}</span>
      <div v-if="modified" class="field-diff-indicator">
        <span class="diff-dot" title="字段已修改"></span>
        <span class="diff-orig-text" :title="String(originalValue)">
          原值 <span class="mono diff-orig-val">{{ originalDisplay }}</span>
        </span>
        <button
          type="button"
          class="revert-btn"
          title="还原为原值"
          @click="$emit('revert')"
        >
          还原
        </button>
      </div>
    </div>
    <div class="field-control">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  modified?: boolean
  originalValue?: unknown
}>()

defineEmits<{
  (e: 'revert'): void
}>()

const originalDisplay = computed(() => {
  if (props.originalValue === undefined || props.originalValue === null) {
    return '无'
  }
  const s = String(props.originalValue)
  if (s.length > 20) {
    return s.slice(0, 18) + '…'
  }
  return s
})
</script>

<style scoped>
.field {
  display: flex;
  flex-direction: column;
}

.field-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 3px;
  min-height: 18px;
}

.field-label {
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.field-diff-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--gold);
  flex-shrink: 0;
}

.diff-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gold);
  display: inline-block;
  box-shadow: 0 0 4px rgba(224, 164, 58, 0.6);
}

.diff-orig-text {
  color: var(--gold);
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.diff-orig-val {
  font-weight: 500;
}

.revert-btn {
  font: inherit;
  font-size: 11px;
  color: var(--fg);
  background: #252931;
  border: 1px solid #353a44;
  border-radius: 4px;
  padding: 0 5px;
  height: 18px;
  line-height: 16px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}

.revert-btn:hover {
  background: var(--raise);
  border-color: var(--gold);
  color: var(--gold);
}

.field-control {
  position: relative;
}

.is-modified :deep(.el-input__wrapper),
.is-modified :deep(.el-select__wrapper) {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 1px var(--gold) inset !important;
}
</style>
