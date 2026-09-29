<template>
  <div>
    <h2>补丁</h2>
    <el-input
      v-model="patchText"
      type="textarea"
      :rows="10"
      placeholder="粘贴补丁 YAML，例如：&#10;steps:&#10;  - target: { table: techs, name: Loom }&#10;    op: set&#10;    field: resource_costs.2.amount&#10;    value: 30"
    />
    <el-button type="primary" style="margin-top: 12px" :loading="loading" @click="apply">
      应用补丁
    </el-button>

    <el-table v-if="results.length" :data="results" border style="margin-top: 16px">
      <el-table-column prop="name" label="步骤" />
      <el-table-column prop="status" label="状态">
        <template #default="{ row }">
          <el-tag :type="row.status === 'applied' ? 'success' : row.status === 'conflict' ? 'warning' : 'danger'">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const patchText = ref('')
const results = ref<any[]>([])
const loading = ref(false)

async function apply() {
  if (!patchText.value) return ElMessage.warning('请先粘贴补丁内容')
  loading.value = true
  try {
    const data = await api.patchApply(patchText.value)
    results.value = data.results || []
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>
