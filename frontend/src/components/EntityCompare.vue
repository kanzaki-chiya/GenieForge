<template>
  <el-dialog
    :model-value="modelValue"
    :title="`对比：${title}`"
    width="92%"
    top="3vh"
    destroy-on-close
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="cmp">
      <div class="cmp-bar">
        <span class="bar-label">对比版本</span>
        <el-select
          v-model="versionId"
          size="small"
          style="width: 300px"
          placeholder="选择已保存的版本"
          @change="loadVersion"
        >
          <el-option v-for="v in versions" :key="v.id" :value="v.id" :label="`v${v.id} · ${v.description}`" />
        </el-select>
        <span class="bar-sep">或</span>
        <FilePicker v-model="filePath" placeholder="选择目标 dat 文件" style="width: 260px" />
        <el-button size="small" :loading="loadingTarget" @click="loadFile">加载文件</el-button>
        <span v-if="targetInfo" class="bar-info">
          科技 {{ targetInfo.techs }} · 效果 {{ targetInfo.effects }} · 文明 {{ targetInfo.civs }}
        </span>
        <span class="bar-note">左：当前 dat（可编辑）　右：对比版本（只读）</span>
      </div>

      <div v-if="!targetLoaded" class="cmp-empty"><el-empty description="选择版本或文件作为对比目标" /></div>
      <div v-else-if="loading" class="cmp-empty"><el-empty description="加载目标实体中…" /></div>
      <div v-else-if="!target" class="cmp-empty"><el-empty description="目标中不存在该实体" /></div>
      <div v-else class="cmp-body">
        <div class="cmp-head">
          <span class="sum">
            <span v-if="diffCount > 0"><span class="sum-n">{{ diffCount }}</span> 处差异</span>
            <span v-else class="sum-none">无差异</span>
          </span>
          <el-button v-if="diffCount > 0" size="small" type="primary" @click="applyAll">全部应用（{{ diffCount }}）</el-button>
        </div>

        <div class="cols">
          <div class="col">
            <div class="col-head"><strong>当前 dat</strong></div>
            <template v-for="g in groups" :key="g.title">
              <div class="group-title">{{ g.title }}</div>
              <div v-for="f in g.fields" :key="f.key" class="frow" :class="{ diff: isDiff(f.key) }">
                <span class="flabel">{{ f.label }}</span>
                <span class="fval">
                  <FieldControl
                    :type="ctrlType(f.type)"
                    :model-value="baseline[f.key]"
                    :meta-name="f.metaName"
                    :preloaded="optionsFor(f)"
                    @commit="(v: unknown) => emit('edit', { field: f.key, value: v })"
                  />
                </span>
              </div>
            </template>
            <template v-for="lf in lists" :key="lf.key">
              <div class="group-title">{{ lf.label }}（{{ listLen('base', lf.key) }} 条）</div>
              <table class="sub">
                <thead>
                  <tr><th v-for="c in lf.columns" :key="c.key" :style="{ width: (c.width || 100) + 'px' }">{{ c.label }}</th></tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in baseRows(lf.key)" :key="i">
                    <td v-for="c in lf.columns" :key="c.key">{{ cellText(row, c) }}</td>
                  </tr>
                  <tr v-if="!baseRows(lf.key).length"><td :colspan="lf.columns.length" class="muted">（无）</td></tr>
                </tbody>
              </table>
            </template>
          </div>

          <div class="col col-target">
            <div class="col-head"><strong>对比版本</strong><span class="ro-tag">只读</span></div>
            <template v-for="g in groups" :key="g.title">
              <div class="group-title">{{ g.title }}</div>
              <div v-for="f in g.fields" :key="f.key" class="frow" :class="{ diff: isDiff(f.key) }">
                <span class="flabel">{{ f.label }}</span>
                <span class="fval ro">{{ fmtScalar(f, target?.[f.key]) }}</span>
                <el-button v-if="isDiff(f.key)" size="small" type="primary" class="apply" @click="applyField(f.key)">← 应用</el-button>
              </div>
            </template>
            <template v-for="lf in lists" :key="lf.key">
              <div class="group-title">
                {{ lf.label }}（{{ listLen('target', lf.key) }} 条）
                <el-button v-if="listDiffCount(lf.key) > 0" size="small" type="primary" class="apply" @click="applyListAll(lf)">← 应用整表</el-button>
              </div>
              <table class="sub">
                <thead>
                  <tr><th v-for="c in lf.columns" :key="c.key" :style="{ width: (c.width || 100) + 'px' }">{{ c.label }}</th><th class="op-col"></th></tr>
                </thead>
                <tbody>
                  <tr v-for="(it, i) in mergedRows(lf.key)" :key="i" :class="it.kind">
                    <template v-if="it.kind !== 'removed'">
                      <td v-for="c in lf.columns" :key="c.key">{{ cellText(it.target, c) }}</td>
                    </template>
                    <template v-else>
                      <td v-for="c in lf.columns" :key="c.key" class="muted">—</td>
                    </template>
                    <td class="op-col">
                      <span v-if="it.kind === 'added'" class="tag add">新增</span>
                      <span v-else-if="it.kind === 'removed'" class="tag del">删除</span>
                      <span v-else-if="it.kind === 'modified'" class="tag mod">修改</span>
                      <el-button v-if="it.kind !== 'same'" size="small" type="primary" link @click="applyRow(lf, it, i)">
                        ← {{ it.kind === 'added' ? '添加' : it.kind === 'removed' ? '移除' : '应用' }}
                      </el-button>
                    </td>
                  </tr>
                  <tr v-if="!mergedRows(lf.key).length"><td :colspan="lf.columns.length + 1" class="muted">（无）</td></tr>
                </tbody>
              </table>
            </template>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { api } from '../api/client'
import FilePicker from './FilePicker.vue'
import FieldControl from './FieldControl.vue'
import { useCompare } from '../composables/useCompare'

export interface CmpField {
  key: string
  label: string
  type: 'text' | 'number' | 'enum' | 'boolean'
  metaName?: string
  optionsKey?: string
}
export interface CmpList {
  key: string
  label: string
  columns: { key: string; label: string; type?: 'enum'; metaName?: string; optionsKey?: string; width?: number }[]
  /** 行级应用走点路径 ``key.index``（固定长度列表，如 required_techs / civ.resources）；
      valueKey 指定取行内哪个值，留空取行本身（数字数组）。 */
  dottedRow?: boolean
  valueKey?: string
}

const props = defineProps<{
  modelValue: boolean
  table: string
  entityId: number
  civ?: number
  title: string
  baseline: Record<string, unknown>
  groups: { title: string; fields: CmpField[] }[]
  lists: CmpList[]
  optionSets?: Record<string, { value: number; label: string }[]>
}>()
const emit = defineEmits(['update:modelValue', 'edit', 'apply'])

// 对比目标为模块级共享状态：四个数据页共用同一份已加载的目标 dat
const compare = useCompare()
const targetLoaded = computed(() => compare.state.loaded)

const versions = ref<any[]>([])
const versionId = ref<number | null>(null)
const filePath = ref('')
const loadingTarget = ref(false)
const target = ref<Record<string, unknown> | null>(null)
const loading = ref(false)
const targetInfo = ref<{ techs: number; effects: number; civs: number } | null>(compare.state.version)

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    targetInfo.value = compare.state.version
    if (!versions.value.length) {
      try {
        versions.value = ((await api.versionList()) as any).versions || []
      } catch {
        versions.value = []
      }
    }
    if (compare.state.loaded) await load()
  }
)

async function loadVersion(id: number) {
  if (id == null) return
  loadingTarget.value = true
  try {
    const info: any = await api.diffLoadVersion(id)
    compare.markLoaded(`version:${id}`, info)
    targetInfo.value = info
    await load()
  } finally {
    loadingTarget.value = false
  }
}

async function loadFile() {
  if (!filePath.value) return
  loadingTarget.value = true
  try {
    const info: any = await compare.loadTarget(filePath.value)
    targetInfo.value = info
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

function eq(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

function isDiff(key: string): boolean {
  return !!target.value && !eq(props.baseline[key], target.value[key])
}

const scalarDiffCount = computed(() => {
  if (!target.value) return 0
  return props.groups.reduce((n, g) => n + g.fields.filter((f) => isDiff(f.key)).length, 0)
})

function listDiffCount(key: string): number {
  return mergedRows(key).filter((r) => r.kind !== 'same').length
}

const diffCount = computed(() => {
  let n = scalarDiffCount.value
  for (const lf of props.lists) n += listDiffCount(lf.key)
  return n
})

// ------------------------------------------------------------------ 子表逐行对齐
interface MergedRow {
  kind: 'same' | 'modified' | 'added' | 'removed'
  base: unknown
  target: unknown
}

function mergedRows(key: string): MergedRow[] {
  const bl = (props.baseline[key] as unknown[]) || []
  const tl = (target.value?.[key] as unknown[]) || []
  const n = Math.max(bl.length, tl.length)
  const out: MergedRow[] = []
  for (let i = 0; i < n; i++) {
    const b = bl[i]
    const t = tl[i]
    if (b !== undefined && t !== undefined) out.push({ kind: eq(b, t) ? 'same' : 'modified', base: b, target: t })
    else if (b !== undefined) out.push({ kind: 'removed', base: b, target: null })
    else out.push({ kind: 'added', base: null, target: t })
  }
  return out
}

function baseRows(key: string): unknown[] {
  return (props.baseline[key] as unknown[]) || []
}

function listLen(which: 'base' | 'target', key: string): number {
  const src = which === 'base' ? props.baseline[key] : target.value?.[key]
  return ((src as unknown[]) || []).length
}

// ------------------------------------------------------------------ 应用
function applyField(key: string) {
  emit('apply', { field: key, value: target.value?.[key], list: false })
}

function applyRow(lf: CmpList, it: MergedRow, index: number) {
  // 固定长度列表的行级修改/新增走点路径（required_techs.2 / resources.17），删除走整表替换
  if (lf.dottedRow && it.kind !== 'removed') {
    const v = lf.valueKey ? (it.target as Record<string, unknown>)?.[lf.valueKey] : it.target
    emit('apply', { field: `${lf.key}.${index}`, value: v, list: false })
    return
  }
  const rows = [...((props.baseline[lf.key] as unknown[]) || [])]
  if (it.kind === 'added') rows.splice(index, 0, it.target)
  else if (it.kind === 'removed') rows.splice(index, 1)
  else rows[index] = it.target
  emit('apply', { field: lf.key, value: rows, list: true })
}

function applyListAll(lf: CmpList) {
  if (lf.dottedRow) {
    // 固定长度列表不能整表替换，逐行走点路径
    mergedRows(lf.key).forEach((it, i) => {
      if (it.kind !== 'same') applyRow(lf, it, i)
    })
    return
  }
  emit('apply', { field: lf.key, value: target.value?.[lf.key], list: true })
}

function applyAll() {
  for (const g of props.groups) {
    for (const f of g.fields) {
      if (isDiff(f.key)) applyField(f.key)
    }
  }
  for (const lf of props.lists) {
    if (listDiffCount(lf.key) > 0) applyListAll(lf)
  }
}

// ------------------------------------------------------------------ 显示
function optionsFor(f: { metaName?: string; optionsKey?: string }) {
  return f.optionsKey ? props.optionSets?.[f.optionsKey] : undefined
}

function ctrlType(t: CmpField['type']): string {
  return t === 'boolean' ? 'boolean' : t
}

function fmtScalar(f: CmpField, v: unknown): string {
  if (v === null || v === undefined) return '—'
  if (f.type === 'boolean') return v ? '是' : '否'
  if (f.type === 'enum') {
    const items = optionsFor(f)
    const hit = items?.find((x) => x.value === v)
    if (hit) return `${v} · ${hit.label}`
  }
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

function cellText(row: unknown, c: { key: string; type?: 'enum'; metaName?: string; optionsKey?: string }): string {
  if (row == null) return '—'
  // primitive 列表列 key 留空 → 行本身就是值（数字等）
  const v = c.key && typeof row === 'object' ? (row as Record<string, unknown>)[c.key] : row
  if (v === null || v === undefined) return '—'
  if (c.type === 'enum') {
    const items = c.optionsKey ? props.optionSets?.[c.optionsKey] : undefined
    const hit = items?.find((x) => x.value === v)
    if (hit) return `${v} · ${hit.label}`
  }
  return String(v)
}
</script>

<style scoped>
.cmp { display: flex; flex-direction: column; min-height: 480px; }
.cmp-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding-bottom: 10px; border-bottom: 1px solid var(--el-border-color-lighter); }
.bar-label { font-size: 12px; color: var(--el-text-color-secondary); flex-shrink: 0; }
.bar-sep { font-size: 12px; color: var(--el-text-color-secondary); }
.bar-info { font-size: 11px; color: var(--el-text-color-secondary); }
.bar-note { margin-left: auto; font-size: 11px; color: var(--el-text-color-secondary); }
.cmp-empty { padding: 48px 0; }
.cmp-head { display: flex; align-items: center; padding: 10px 0; }
.sum { font-size: 13px; margin-right: 12px; }
.sum-n { color: var(--el-color-warning); font-weight: 600; }
.sum-none { color: var(--el-color-success); }
.cols { display: flex; gap: 0; align-items: flex-start; }
.col { flex: 1; min-width: 0; padding-right: 16px; }
.col-target { border-left: 1px solid var(--el-border-color-lighter); padding-left: 16px; padding-right: 0; background: var(--el-fill-color-lighter); }
.col-head { display: flex; align-items: center; gap: 8px; font-size: 13px; padding-bottom: 6px; }
.ro-tag { font-size: 11px; color: var(--el-text-color-secondary); border: 1px solid var(--el-border-color); border-radius: 3px; padding: 0 6px; }
.group-title { color: var(--el-text-color-primary); font-weight: 600; font-size: 13px; border-top: 1px solid var(--el-border-color-lighter); margin: 12px 0 6px; padding-top: 8px; display: flex; align-items: center; }
.frow { display: flex; align-items: center; gap: 8px; padding: 2px 6px; border-radius: 4px; min-height: 30px; }
.frow.diff { background: rgba(224, 164, 58, 0.14); box-shadow: inset 2px 0 0 var(--el-color-warning); }
.flabel { width: 130px; flex-shrink: 0; font-size: 12px; color: var(--el-text-color-secondary); }
.fval { flex: 1; min-width: 0; }
.fval.ro { font-size: 12px; word-break: break-all; }
.apply { flex-shrink: 0; }
.sub { width: 100%; border-collapse: collapse; font-size: 12px; }
.sub th, .sub td { border: 1px solid var(--el-border-color-lighter); padding: 3px 8px; text-align: left; }
.sub th { background: var(--el-fill-color); color: var(--el-text-color-secondary); font-weight: 500; }
.sub tr.modified td { background: rgba(224, 164, 58, 0.14); }
.sub tr.added td { background: rgba(92, 155, 230, 0.14); }
.sub tr.removed td { background: rgba(236, 122, 136, 0.14); }
.sub .op-col { width: 90px; }
.tag { font-size: 11px; border-radius: 3px; padding: 0 6px; }
.tag.add { color: var(--el-color-primary); }
.tag.del { color: var(--el-color-danger); }
.tag.mod { color: var(--el-color-warning); }
.muted { color: var(--el-text-color-placeholder); font-style: italic; }
</style>
