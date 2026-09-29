<template>
  <div>
    <h2>概览</h2>
    <el-alert
      v-if="!datInfo"
      type="info"
      title="尚未加载 dat 文件"
      description="请在下方选择游戏数据文件（empires2_x2_p1.dat）开始使用。"
      show-icon
      :closable="false"
    />
    <el-descriptions v-else :column="3" border style="margin-top: 12px">
      <el-descriptions-item label="版本">{{ datInfo.version }}</el-descriptions-item>
      <el-descriptions-item label="路径">{{ datInfo.path }}</el-descriptions-item>
      <el-descriptions-item label="状态">{{ datInfo.dirty ? '已修改' : '干净' }}</el-descriptions-item>
      <el-descriptions-item v-for="(v, k) in datInfo.counts" :key="k" :label="k">
        {{ v }}
      </el-descriptions-item>
    </el-descriptions>

    <div style="margin-top: 16px">
      <el-input
        v-model="path"
        placeholder="输入 dat 文件路径，如 D:/AoE2DE/resources/_common/dat/empires2_x2_p1.dat"
        style="max-width: 560px"
      />
      <el-button type="primary" style="margin-left: 8px" :loading="loading" @click="load">
        加载 dat
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAppStore } from '../stores'

const store = useAppStore()
const path = ref('')
const datInfo = ref<any>(null)
const loading = ref(false)

async function load() {
  if (!path.value) return ElMessage.warning('请先输入 dat 文件路径')
  loading.value = true
  try {
    datInfo.value = await api.loadDat(path.value)
    store.setDatInfo(datInfo.value)
    ElMessage.success('加载成功')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    datInfo.value = await api.datInfo()
  } catch {
    /* 后端未就绪时静默 */
  }
})
</script>
