<template>
  <div>
    <h2>版本</h2>
    <el-button :loading="loading" @click="fetch">刷新</el-button>
    <el-table :data="versions" border stripe style="margin-top: 12px">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="path" label="路径" />
      <el-table-column prop="sha256" label="哈希" width="140">
        <template #default="{ row }">{{ (row.sha256 || '').slice(0, 12) }}…</template>
      </el-table-column>
      <el-table-column label="操作" width="90">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="checkout(row.id)">回滚</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api/client'

const versions = ref<any[]>([])
const loading = ref(false)

async function fetch() {
  loading.value = true
  try {
    const r: any = await api.versionList()
    versions.value = r.versions
  } finally {
    loading.value = false
  }
}

async function checkout(id: number) {
  try {
    await ElMessageBox.confirm(`回滚到版本 #${id}？将重新加载对应 dat 文件。`, '确认')
  } catch {
    return
  }
  try {
    await api.versionCheckout(id)
    ElMessage.success('已回滚')
    fetch()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(fetch)
</script>
