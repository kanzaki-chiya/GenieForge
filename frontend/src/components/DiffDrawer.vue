<template>
  <el-drawer v-model="visible" :title="`对比：${title}`" size="46%" direction="rtl">
    <div v-if="!target" class="empty">
      <el-empty description="请先选择目标 dat 文件" />
      <div style="text-align: center">
        <FilePicker v-model="targetPath" placeholder="目标 dat 路径" />
        <el-button type="primary" size="small" style="margin-left: 8px" :loading="loading" @click="loadTarget">加载目标</el-button>
      </div>
    </div>

    <div v-else-if="diffs.length === 0" class="empty">
      <el-empty description="无差异" />
    </div>

    <div v-else class="diff-list">
      <div class="summary">
        共 {{ diffs.length }} 处差异
        <el-button size="small" style="margin-left: 12px" @click="applyAll">应用全部</el-button>
      </div>

      <div v-for="d in diffs" :key="d.id" class="diff-item" :class="d.kind">
        <div class="diff-head">
          <span class="diff-label">{{ d.label }}</span>
          <span class="diff-kind">{{ kindText(d.kind) }}</span>
          <el-button size="small" type="primary" @click="apply(d)">应用</el-button>
        </div>
        <div class="diff-body">
          <span class="base-val">{{ formatVal(d.base) }}</span>
          <span class="arrow">→</span>
          <span class="target-val">{{ formatVal(d.target) }}</span>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import FilePicker from './FilePicker.vue'

const props = defineProps<{
  modelValue: boolean
  table: string
  entityId: number
  civ?: number
  title: string
  baseline: Record<string, unknown>
  scalarFields: { key: string; label: string }[]
  listFields: { key: string; label: string }[]
}>()
const emit = defineEmits(['update:modelValue', 'apply'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const targetPath = ref('')
const target = ref<Record<string, unknown> | null>(null)
const loading = ref(false)

interface DiffItem {
  id: string
  kind: 'modified' | 'added' | 'removed'
  label: string
  field: string
  base: unknown
  target: unknown
}

const diffs = ref<DiffItem[]>([])

async function loadTarget() {
  if (!targetPath.value) return
  loading.value = true
  try {
    await api.diffLoadTarget(targetPath.value)
    const r: any = await api.diffEntity(props.table, props.entityId, props.civ || 0)
    target.value = r
    computeDiffs()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function eq(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

function computeDiffs() {
  const out: DiffItem[] = []
  // 标量字段
  for (const f of props.scalarFields) {
    const b = props.baseline[f.key]
    const t = target.value?.[f.key]
    if (!eq(b, t)) {
      out.push({ id: f.key, kind: 'modified', label: f.label, field: f.key, base: b, target: t })
    }
  }
  // 子表字段（条目级：新增/删除/修改）
  for (const f of props.listFields) {
    const bl = (props.baseline[f.key] as unknown[]) || []
    const tl = (target.value?.[f.key] as unknown[]) || []
    // 删除：基准有、目标无
    for (let i = 0; i < bl.length; i++) {
      if (!tl.some((x) => eq(x, bl[i]))) {
        out.push({ id: `${f.key}:removed:${i}`, kind: 'removed', label: `${f.label}[${i}]`, field: f.key, base: bl[i], target: null })
      }
    }
    // 新增：目标有、基准无
    for (let i = 0; i < tl.length; i++) {
      if (!bl.some((x) => eq(x, tl[i]))) {
        out.push({ id: `${f.key}:added:${i}`, kind: 'added', label: `${f.label}[${i}]`, field: f.key, base: null, target: tl[i] })
      }
    }
  }
  diffs.value = out
}

function kindText(kind: string) {
  return { modified: '修改', added: '新增', removed: '删除' }[kind] || kind
}

function formatVal(v: unknown): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

async function apply(d: DiffItem) {
  // 子表差异：整体替换（基准列表 + 增删目标条目）
  if (props.listFields.some((f) => f.key === d.field)) {
    let rows = [...((props.baseline[d.field] as unknown[]) || [])]
    if (d.kind === 'added') {
      rows = [...rows, d.target]
    } else if (d.kind === 'removed') {
      rows = rows.filter((x, i) => i !== Number(d.id.split(':').pop()))
    }
    emit('apply', { field: d.field, value: rows, list: true })
  } else {
    emit('apply', { field: d.field, value: d.target, list: false })
  }
}

async function applyAll() {
  for (const d of diffs.value) {
    await apply(d)
  }
}
</script>

<style scoped>
.empty { padding: 24px; }
.diff-list { padding: 0 4px; }
.summary { color: #9a9a9a; font-size: 12px; padding: 8px 4px 12px; }
.diff-item { border: 1px solid #34373a; border-radius: 6px; padding: 8px 12px; margin-bottom: 8px; }
.diff-item.modified { background: #2e2918; }
.diff-item.added { background: #1c2e20; }
.diff-item.removed { background: #2e1a1a; }
.diff-head { display: flex; align-items: center; gap: 8px; }
.diff-label { font-weight: 600; font-size: 13px; color: #e6e6e6; }
.diff-kind { font-size: 11px; padding: 1px 8px; border-radius: 3px; }
.modified .diff-kind { background: #3c2f12; color: #f5c542; }
.added .diff-kind { background: #1e3a2a; color: #8ae0a8; }
.removed .diff-kind { background: #3a1e1e; color: #ff8a8a; }
.diff-body { margin-top: 6px; font-family: var(--font-mono); font-size: 12px; display: flex; gap: 10px; align-items: center; }
.base-val { color: #ff8a8a; text-decoration: line-through; }
.target-val { color: #8ae0a8; }
.arrow { color: #9a9a9a; }
</style>
