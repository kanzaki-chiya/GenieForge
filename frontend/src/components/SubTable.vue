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
            @commit="(v: unknown) => emit('cell-commit', { rowIndex: $index, colKey: col.key, value: v })"
          />
        </template>
      </el-table-column>
      <el-table-column label="" width="40" align="center">
        <template #default="{ $index }">
          <span class="del" @click="emit('remove-row', $index)">✕</span>
        </template>
      </el-table-column>
    </el-table>
    <div class="actions">
      <el-button size="small" @click="emit('add-row')">+ Add</el-button>
      <el-button size="small" @click="emit('insert-row', 0)">Insert New</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import FieldControl from './FieldControl.vue'

defineProps<{
  columns: { key: string; label: string; type: string; metaName?: string; width?: number }[]
  modelValue: Record<string, unknown>[]
}>()
const emit = defineEmits(['cell-commit', 'add-row', 'insert-row', 'remove-row'])
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
