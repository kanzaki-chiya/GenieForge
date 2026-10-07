<template>
  <div class="versions">
    <div class="head">
      <h2>版本</h2>
      <span class="mono total">快照占用 {{ formatSize(totalSize) }}</span>
      <el-button size="small" :loading="loading" @click="fetch">刷新</el-button>
    </div>

    <div class="import">
      <span class="lbl">导入版本</span>
      <FilePicker v-model="importPath" placeholder="选择 dat 文件" />
      <el-input v-model="importLabel" size="small" class="label-input" placeholder="标签（默认用文件名）" />
      <el-button size="small" :loading="importing" @click="doImport">导入</el-button>
    </div>

    <el-table :data="versions" border stripe class="table">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="label" label="标签" min-width="180" />
      <el-table-column label="类型" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.kind === 'imported' ? 'info' : 'success'">
            {{ row.kind === 'imported' ? '导入' : '已保存' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="时间" width="150">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="大小" width="100">
        <template #default="{ row }">{{ formatSize(row.size) }}</template>
      </el-table-column>
      <el-table-column label="哈希" width="140">
        <template #default="{ row }">
          <span class="mono">{{ (row.sha256 || '').slice(0, 12) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="useAsCompare(row)">对比</el-button>
          <el-button size="small" type="primary" @click="rollback(row)">回滚</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <p v-if="!versions.length" class="empty">还没有版本。保存 dat（自动生成）或用上方「导入版本」加入。</p>

    <!-- 有未保存修改时的回滚确认（页面内对话框） -->
    <el-dialog v-model="confirmVisible" title="回滚版本" width="400px">
      <p>放弃未保存修改并回滚到 v{{ pending?.id }} · {{ pending?.label }}？</p>
      <p class="hint">回滚只把快照内容读进内存，工作路径仍是当前 dat，需要保存才写回原文件。</p>
      <template #footer>
        <el-button size="small" @click="confirmVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="rolling" @click="doCheckout(true)">
          放弃修改并回滚
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import FilePicker from '../components/FilePicker.vue'
import { api } from '../api/client'
import { useAppStore, useHistoryStore } from '../stores'
import { useCompare, formatSize, formatTime, versionLabel } from '../composables/useCompare'

const appStore = useAppStore()
const historyStore = useHistoryStore()
const compare = useCompare()

const versions = ref<any[]>([])
const totalSize = ref(0)
const loading = ref(false)
const importing = ref(false)
const rolling = ref(false)
const importPath = ref('')
const importLabel = ref('')
const confirmVisible = ref(false)
const pending = ref<any>(null)

async function fetch() {
  loading.value = true
  try {
    const r: any = await api.versionList()
    versions.value = r.versions
    totalSize.value = r.total_size
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function doImport() {
  if (!importPath.value) {
    ElMessage.warning('请先选择要导入的 dat 文件')
    return
  }
  importing.value = true
  try {
    await api.versionImport(importPath.value, importLabel.value || undefined)
    ElMessage.success('已导入版本')
    importPath.value = ''
    importLabel.value = ''
    await fetch()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    importing.value = false
  }
}

/** 把该版本设为对比版本，之后到数据页用「对比…」打开并排对比。 */
async function useAsCompare(row: any) {
  try {
    await compare.selectVersion(row.id)
    await compare.refreshVersions()
    ElMessage.success({
      message: `已选择对比版本 ${versionLabel(row)}，到数据页点「对比…」查看`,
      duration: 2500
    })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function rollback(row: any) {
  pending.value = row
  if (appStore.datInfo?.dirty) {
    confirmVisible.value = true
    return
  }
  try {
    await ElMessageBox.confirm(`回滚到 v${row.id} · ${row.label}？`, '确认')
  } catch {
    return
  }
  await doCheckout(false)
}

async function doCheckout(force: boolean) {
  const row = pending.value
  if (!row) return
  rolling.value = true
  try {
    await api.versionCheckout(row.id, force)
    confirmVisible.value = false
    await appStore.refreshDatInfo()
    appStore.bumpRevision()
    historyStore.clearAll()
    ElMessage.success('已回滚，保存后写回原 dat')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    rolling.value = false
  }
}

async function remove(row: any) {
  try {
    await ElMessageBox.confirm(`删除版本 v${row.id} · ${row.label}？`, '确认', { type: 'warning' })
  } catch {
    return
  }
  try {
    await api.versionDelete(row.id)
    if (compare.state.versionId === row.id) compare.clear()
    ElMessage.success('已删除')
    await fetch()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(fetch)
</script>

<style scoped>
.versions {
  padding: 14px 18px 30px;
  height: 100%;
  overflow-y: auto;
}

.head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.head h2 {
  margin: 0;
  font-size: 17px;
  color: var(--fg);
}

.total {
  color: var(--muted);
  font-size: 12px;
  margin-right: auto;
}

.import {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--panel);
}

.import .lbl {
  font-size: 12px;
  color: var(--muted);
  flex-shrink: 0;
}

.import :deep(.file-picker) {
  flex: 1;
}

.label-input {
  width: 220px;
}

.table {
  width: 100%;
}

.empty {
  color: var(--muted);
  font-size: 12px;
  padding: 12px 2px;
}

.hint {
  color: var(--muted);
  font-size: 12px;
}
</style>
