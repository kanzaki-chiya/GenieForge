<template>
  <div>
    <h2>对比差异</h2>
    <el-form label-width="80px" style="max-width: 640px">
      <el-form-item label="基准 dat">
        <el-input v-model="base" placeholder="旧版 / 官方版 dat 路径" />
      </el-form-item>
      <el-form-item label="目标 dat">
        <el-input v-model="target" placeholder="新版 / 我的 mod 版 dat 路径" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="run">开始对比</el-button>
      </el-form-item>
    </el-form>

    <el-row v-if="report" :gutter="12" style="margin-bottom: 12px">
      <el-col v-for="(v, k) in report.table" :key="k" :span="6">
        <el-card shadow="hover">
          <div>{{ k }}</div>
          <div style="font-size: 20px">
            {{ v.base }} → {{ v.target }}
            <span :style="{ color: v.delta > 0 ? 'red' : v.delta < 0 ? 'green' : 'gray' }">
              ({{ v.delta > 0 ? '+' : '' }}{{ v.delta }})
            </span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-collapse v-if="report && report.id_drift.length">
      <el-collapse-item :title="`ID 漂移（${report.id_drift.length}）`" name="drift">
        <el-table :data="report.id_drift" size="small" border>
          <el-table-column prop="table" label="表" width="100" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="base_id" label="基准 ID" width="100" />
          <el-table-column prop="target_id" label="目标 ID" width="100" />
        </el-table>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const base = ref('')
const target = ref('')
const report = ref<any>(null)
const loading = ref(false)

async function run() {
  if (!base.value || !target.value) return ElMessage.warning('请填写基准与目标 dat 路径')
  loading.value = true
  try {
    report.value = await api.diff(base.value, target.value)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>
