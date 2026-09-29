<template>
  <div>
    <h2>补丁</h2>
    <el-input
      v-model="patchText"
      type="textarea"
      :rows="10"
      placeholder="粘贴补丁 YAML，例如：&#10;steps:&#10;  - name: 织布机金费 30&#10;    target: { table: techs, name: Loom }&#10;    op: set&#10;    field: resource_costs.0.amount&#10;    value: 30"
    />
    <el-button type="primary" style="margin-top: 12px" :loading="loading" @click="apply">
      应用补丁
    </el-button>

    <el-row v-if="report" :gutter="12" style="margin-top: 16px">
      <el-col :span="6">
        <el-tag type="success">成功 {{ report.summary.applied }}</el-tag>
      </el-col>
      <el-col :span="6">
        <el-tag type="warning">冲突 {{ report.summary.conflicts }}</el-tag>
      </el-col>
      <el-col :span="6">
        <el-tag type="danger">未命中 {{ report.summary.missing }}</el-tag>
      </el-col>
      <el-col :span="6">
        <el-tag type="info">不支持 {{ report.summary.unsupported }}</el-tag>
      </el-col>
    </el-row>

    <el-table v-if="report" :data="report.results" border style="margin-top: 12px">
      <el-table-column prop="name" label="步骤" />
      <el-table-column prop="status" label="状态" width="130">
        <template #default="{ row }">
          <el-tag
            :type="row.status === 'applied' ? 'success' : row.status === 'conflict' ? 'warning' : row.status === 'missing' ? 'danger' : 'info'"
            size="small"
          >
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="候选 ID">
        <template #default="{ row }">{{ row.candidates?.join(', ') ?? row.id }}</template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const patchText = ref('')
const report = ref<any>(null)
const loading = ref(false)

async function apply() {
  if (!patchText.value) return ElMessage.warning('请先粘贴补丁内容')
  loading.value = true
  try {
    report.value = await api.patchApply(patchText.value)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>
