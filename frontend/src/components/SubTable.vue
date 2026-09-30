<template>
  <div class="subtable">
    <el-table :data="modelValue" size="small" border>
      <el-table-column
        v-for="col in columns"
        :key="col.key"
        :label="col.label"
        :width="col.width"
      >
        <template #default="{ row, $index }">
          <FieldControl
            :type="col.type"
            :model-value="row[col.key]"
            :meta-name="col.metaName"
            @update:model-value="(v: unknown) => update($index, col.key, v)"
            @commit="() => commit($index, col.key)"
          />
        </template>
      </el-table-column>
      <el-table-column label="" width="40" align="center">
        <template #default="{ $index }">
          <span class="del" @click="remove($index)">✕</span>
        </template>
      </el-table-column>
    </el-table>
    <div class="actions">
      <el-button size="small" @click="add">+ Add</el-button>
      <el-button size="small" @click="insertFirst">Insert New</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import FieldControl from './FieldControl.vue'

const props = defineProps<{
  columns: { key: string; label: string; type: string; metaName?: string; width?: number }[]
  modelValue: Record<string, unknown>[]
  template: () => Record<string, unknown>
}>()
const emit = defineEmits(['update:modelValue', 'update-row', 'add-row', 'remove-row'])

function update(rowIndex: number, colKey: string, value: unknown) {
  const rows = props.modelValue.map((r, i) =>
    i === rowIndex ? { ...r, [colKey]: value } : r
  )
  emit('update:modelValue', rows)
}

function commit(rowIndex: number, colKey: string) {
  emit('update-row', { rowIndex, colKey, row: props.modelValue[rowIndex] })
}

function add() {
  emit('update:modelValue', [...props.modelValue, props.template()])
  emit('add-row', props.modelValue.length)
}

function insertFirst() {
  emit('update:modelValue', [props.template(), ...props.modelValue])
}

function remove(index: number) {
  emit('update:modelValue', props.modelValue.filter((_, i) => i !== index))
  emit('remove-row', index)
}
</script>

<style scoped>
.subtable {
  border: 1px solid #3c3f41;
  border-radius: 5px;
  overflow: hidden;
}
.actions {
  padding: 6px 8px;
  border-top: 1px solid #34373a;
}
.del {
  color: #9a9a9a;
  cursor: pointer;
}
.del:hover {
  color: #ff6b6b;
}
</style>
