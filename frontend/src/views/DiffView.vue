<template>
  <div>
    <h2>对比差异</h2>
    <el-form label-width="80px" style="max-width: 720px">
      <el-form-item label="基准 dat">
        <FilePicker v-model="base" placeholder="旧版 / 官方版 dat 路径" />
      </el-form-item>
      <el-form-item label="目标 dat">
        <FilePicker v-model="target" placeholder="新版 / 我的 mod 版 dat 路径" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="run">开始对比</el-button>
        <el-button :disabled="!report" @click="generatePatch">导出为补丁</el-button>
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

    <el-card v-if="report" shadow="never" style="margin-top: 12px">
      <template #header>
        变更记录
        <el-tag size="small" type="success" style="margin-left: 6px">新增 {{ report.summary.added }}</el-tag>
        <el-tag size="small" type="danger" style="margin-left: 6px">删除 {{ report.summary.removed }}</el-tag>
        <el-tag size="small" type="warning" style="margin-left: 6px">修改 {{ report.summary.modified }}</el-tag>
        <el-tag size="small" type="info" style="margin-left: 6px">ID 漂移 {{ report.summary.id_drift }}</el-tag>
      </template>
      <el-table :data="records" size="small" border max-height="480">
        <el-table-column type="expand">
          <template #default="{ row }">
            <!-- 三种变化都渲染内容：added 显示新值、removed 显示旧值、modified 逐字段对比 -->
            <el-table v-if="row.change === 'modified'" :data="row.changes" size="small" border>
              <el-table-column prop="field" label="字段" width="220" />
              <el-table-column label="旧值">
                <template #default="{ row: c }"><span class="old-val">{{ fmtVal(c.old) }}</span></template>
              </el-table-column>
              <el-table-column label="新值">
                <template #default="{ row: c }"><span class="new-val">{{ fmtVal(c.new) }}</span></template>
              </el-table-column>
            </el-table>
            <div v-else-if="row.change === 'added'" class="expand-block">
              <div v-for="(v, k) in row.record" :key="k" class="kv"><span class="k">{{ k }}</span><span class="new-val">{{ fmtVal(v) }}</span></div>
            </div>
            <div v-else-if="row.change === 'removed'" class="expand-block">
              <div v-for="(v, k) in row.record" :key="k" class="kv"><span class="k">{{ k }}</span><span class="old-val">{{ fmtVal(v) }}</span></div>
            </div>
            <div v-else class="expand-block muted">（无详情）</div>
          </template>
        </el-table-column>
        <el-table-column prop="table" label="表" width="110" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="change" label="变化" width="110">
          <template #default="{ row }">
            <el-tag :type="row.change === 'added' ? 'success' : row.change === 'removed' ? 'danger' : 'warning'" size="small">
              {{ row.change }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import FilePicker from '../components/FilePicker.vue'

const base = ref('')
const target = ref('')
const report = ref<any>(null)
const loading = ref(false)

const records = computed(() => report.value?.records ?? [])

// 可读值：对象展开为 k=v 对，数组用分号连接，替代裸 JSON.stringify（TODO P0-2）
function fmtVal(v: unknown): string {
  if (v === null || v === undefined) return '—'
  if (Array.isArray(v)) return v.length ? v.map((x) => fmtVal(x)).join('；') : '（空）'
  if (typeof v === 'object') {
    return Object.entries(v as Record<string, unknown>)
      .filter(([, val]) => val !== null && val !== undefined)
      .map(([k, val]) => `${k}=${fmtVal(val)}`)
      .join(', ')
  }
  return String(v)
}

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

async function generatePatch() {
  try {
    const r: any = await api.patchGenerate(base.value, target.value)
    ElMessage.success('已生成补丁')
    navigator.clipboard?.writeText(r.patch)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}
</script>

<style scoped>
.expand-block { padding: 6px 12px; }
.expand-block .kv { display: flex; gap: 12px; padding: 2px 0; font-size: 12px; }
.expand-block .kv .k { width: 200px; flex-shrink: 0; color: var(--el-text-color-secondary); }
.old-val { color: #ec7a88; }
.new-val { color: #8ae0a8; }
.muted { color: var(--el-text-color-placeholder); }
</style>
