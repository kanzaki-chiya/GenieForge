<template>
  <el-drawer :model-value="modelValue" :title="`对比：${title}`" size="46%" direction="rtl" @update:model-value="$emit('update:modelValue', $event)">
    <div class="target-bar">
      <span class="tb-label">目标文件</span>
      <FilePicker v-model="compare.state.path" placeholder="选择目标 dat 文件" />
      <el-button size="small" :loading="loadingTarget" @click="loadTargetFile">加载</el-button>
      <span v-if="compare.state.version" class="tb-info">科技 {{ compare.state.version.techs }} · 效果 {{ compare.state.version.effects }} · 文明 {{ compare.state.version.civs }}</span>
    </div>

    <div v-if="!compare.state.loaded" class="empty">
      <el-empty description="请先加载目标文件" />
    </div>
    <div v-else-if="loading" class="empty">
      <el-empty description="加载目标中…" />
    </div>
    <div v-else-if="!target" class="empty">
      <el-empty description="未加载目标实体" />
    </div>
    <div v-else class="diff-form">
      <div class="summary">
        <span v-if="diffCount > 0" class="sum-badge">{{ diffCount }} 处差异</span>
        <span v-else class="sum-none">无差异</span>
        <el-button v-if="diffCount > 0" size="small" type="primary" style="margin-left: 12px" @click="applyAll">应用全部</el-button>
      </div>

      <div v-for="f in scalarFields" :key="f.key" class="row" :class="{ diff: isDiff(f.key) }">
        <span class="label">{{ f.label }}</span>
        <span class="base">{{ fmt(baseline[f.key]) }}</span>
        <span class="arrow">→</span>
        <span class="target">{{ fmt(target[f.key]) }}</span>
        <el-button v-if="isDiff(f.key)" size="small" type="primary" @click="applyField(f.key)">应用</el-button>
      </div>

      <div v-for="lf in listFields" :key="lf.key" class="sub">
        <div class="sub-title">{{ lf.label }}（{{ listLen(lf.key) }} 条）</div>
        <div v-for="(it, i) in listItems(lf.key)" :key="i" class="row" :class="{ added: it.kind === 'added', removed: it.kind === 'removed', diff: it.kind === 'modified' }">
          <span class="label">{{ it.kind === 'added' ? '+' : it.kind === 'removed' ? '−' : '~' }} #{{ it.index }}</span>
          <span class="base">{{ it.base == null ? '—' : fmt(it.base) }}</span>
          <span class="arrow">→</span>
          <span class="target">{{ it.target == null ? '—' : fmt(it.target) }}</span>
          <el-button size="small" type="primary" @click="applyList(lf.key, it)">应用</el-button>
        </div>
        <div v-if="listItems(lf.key).length === 0" class="row"><span class="label">无差异</span></div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { api } from '../api/client'
import FilePicker from './FilePicker.vue'
import { useCompare } from '../composables/useCompare'

const compare = useCompare()
const loadingTarget = ref(false)

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

const target = ref<Record<string, unknown> | null>(null)
const loading = ref(false)

async function loadTargetFile() {
  if (!compare.state.path) return
  loadingTarget.value = true
  try {
    await compare.loadTarget(compare.state.path)
    await load()
  } finally {
    loadingTarget.value = false
  }
}

async function load() {
  if (!compare.state.loaded) return
  loading.value = true
  try {
    target.value = await api.diffEntity(props.table, props.entityId, props.civ || 0)
  } catch {
    target.value = null
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.modelValue, props.entityId, compare.state.loaded],
  () => {
    if (props.modelValue && compare.state.loaded) load()
  }
)

function eq(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

function isDiff(key: string): boolean {
  return !eq(props.baseline[key], target.value?.[key])
}

const diffCount = computed(() => {
  if (!target.value) return 0
  let n = scalarFields.filter((f) => isDiff(f.key)).length
  for (const lf of props.listFields) {
    n += listItems(lf.key).length
  }
  return n
})

const scalarFields = props.scalarFields
const baseline = props.baseline
const listFields = props.listFields

interface ListItem {
  kind: 'modified' | 'added' | 'removed'
  index: number
  base: unknown
  target: unknown
}

function listItems(key: string): ListItem[] {
  const bl = (props.baseline[key] as unknown[]) || []
  const tl = (target.value?.[key] as unknown[]) || []
  const out: ListItem[] = []
  for (let i = 0; i < bl.length; i++) {
    if (!tl.some((x) => eq(x, bl[i]))) {
      out.push({ kind: 'removed', index: i, base: bl[i], target: null })
    }
  }
  for (let i = 0; i < tl.length; i++) {
    if (!bl.some((x) => eq(x, tl[i]))) {
      out.push({ kind: 'added', index: i, base: null, target: tl[i] })
    }
  }
  return out
}

function fmt(v: unknown): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

function listLen(key: string): number {
  return ((target.value?.[key] as unknown[]) || []).length
}

async function applyField(key: string) {
  emit('apply', { field: key, value: target.value?.[key], list: false })
}

async function applyList(key: string, it: ListItem) {
  let rows = [...((props.baseline[key] as unknown[]) || [])]
  if (it.kind === 'added') {
    rows = [...rows, it.target]
  } else if (it.kind === 'removed') {
    rows = rows.filter((_, i) => i !== it.index)
  }
  emit('apply', { field: key, value: rows, list: true })
}

async function applyAll() {
  for (const f of props.scalarFields) {
    if (isDiff(f.key)) await applyField(f.key)
  }
  for (const lf of props.listFields) {
    for (const it of listItems(lf.key)) await applyList(lf.key, it)
  }
}
</script>

<style scoped>
.target-bar { display: flex; align-items: center; gap: 8px; padding: 4px 0 12px; border-bottom: 1px solid #34373a; margin-bottom: 10px; }
.tb-label { font-size: 12px; color: #9a9a9a; flex-shrink: 0; }
.tb-info { font-size: 11px; color: #9a9a9a; }
.empty { padding: 24px; }
.diff-form { padding: 0 4px; }
.summary { padding: 8px 4px 12px; display: flex; align-items: center; }
.sum-badge { color: #f5c542; font-size: 12px; }
.sum-none { color: #8ae0a8; font-size: 12px; }
.row { display: flex; align-items: center; gap: 10px; padding: 5px 8px; border-radius: 4px; font-size: 12px; }
.row.diff { background: #2e2918; }
.row.added { background: #1c2e20; }
.row.removed { background: #2e1a1a; }
.label { width: 120px; color: #9a9a9a; flex-shrink: 0; }
.base { color: #d4d4d4; }
.diff .base { color: #ff8a8a; text-decoration: line-through; }
.target { color: #d4d4d4; }
.diff .target, .added .target { color: #8ae0a8; }
.arrow { color: #9a9a9a; }
.sub { margin-top: 10px; }
.sub-title { color: #e6e6e6; font-weight: 600; font-size: 13px; margin-bottom: 6px; }
</style>
