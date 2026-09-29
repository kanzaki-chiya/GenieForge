<template>
  <div>
    <h2>概览</h2>

    <el-row :gutter="12">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>应用状态</template>
          <div v-if="health">版本 {{ health.version }} · 状态 {{ health.status }}</div>
          <div v-else>未连接后端</div>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>dat 状态</template>
          <div v-if="datInfo && datInfo.version">
            <div>版本：{{ datInfo.version }}　文件：{{ datInfo.path }}</div>
            <div v-if="datInfo.counts" style="margin-top: 6px">
              文明 {{ datInfo.counts.civs }} · 科技 {{ datInfo.counts.techs }} ·
              效果 {{ datInfo.counts.effects }} · 单位头 {{ datInfo.counts.unit_headers }}
            </div>
          </div>
          <div v-else>尚未加载 dat</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" style="margin-top: 12px">
      <template #header>操作</template>
      <el-form inline>
        <el-form-item label="dat 路径" style="width: 480px">
          <el-input v-model="datPath" placeholder="empires2_x2_p1.dat 路径" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="load">加载</el-button>
          <el-button :disabled="!datInfo?.version" @click="save">保存</el-button>
          <el-button :disabled="!datInfo?.version" @click="undo">撤销</el-button>
          <el-button :disabled="!datInfo?.version" @click="redo">重做</el-button>
          <el-button @click="checkUpdate">检查更新</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const health = ref<any>(null)
const datInfo = ref<any>(null)
const datPath = ref('')
const loading = ref(false)

async function refresh() {
  health.value = await api.health().catch(() => null)
  datInfo.value = await api.datInfo().catch(() => null)
}

async function load() {
  if (!datPath.value) return ElMessage.warning('请填写 dat 路径')
  loading.value = true
  try {
    const r = await api.loadDat(datPath.value)
    datInfo.value = r
    ElMessage.success(`已加载，语言表条目 ${(r as any).language_entries ?? 0}`)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function save() {
  try {
    await api.saveDat()
    ElMessage.success('已保存')
    refresh()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function undo() {
  try {
    const r = await api.undo()
    ElMessage.success(`已撤销：${(r as any).description}`)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function redo() {
  try {
    const r = await api.redo()
    ElMessage.success(`已重做：${(r as any).description}`)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function checkUpdate() {
  try {
    const r: any = await api.updateCheck()
    ElMessage.info(
      r.update_available
        ? `发现新版本 ${r.latest}（当前 ${r.current}）`
        : `已是最新（当前 ${r.current}）`
    )
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(refresh)
</script>
