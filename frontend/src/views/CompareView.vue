<template>
  <div class="compare">
    <!-- 顶部：返回 / 标题 / 对比版本 / 只看差异 / 上下处 / 全部应用 -->
    <div class="cmp-top">
      <button type="button" class="link" @click="goBack">← 返回编辑</button>
      <strong class="title">
        {{ tableLabel }} <span class="mono id">#{{ entityId }}</span>
        <span class="name">{{ base?.name || '' }}</span>
      </strong>
      <div class="actions">
        <span class="lbl">对比版本</span>
        <el-select
          :model-value="compare.state.versionId"
          size="small"
          class="ver-select"
          placeholder="选择版本"
          @update:model-value="onPickVersion"
        >
          <el-option
            v-for="v in compare.state.versions"
            :key="v.id"
            :value="v.id"
            :label="versionLabel(v)"
          >
            <span>{{ versionLabel(v) }}</span>
            <el-tag size="small" :type="v.kind === 'imported' ? 'info' : 'success'" class="opt-tag">
              {{ kindLabel(v.kind) }}
            </el-tag>
          </el-option>
        </el-select>
        <el-checkbox :model-value="onlyDiff" size="small" @update:model-value="setOnlyDiff">
          只看差异
        </el-checkbox>
        <el-button size="small" :disabled="!navKeys.length" @click="gotoDiff(-1)">上一处</el-button>
        <el-button size="small" :disabled="!navKeys.length" @click="gotoDiff(1)">下一处</el-button>
        <el-button
          size="small"
          type="primary"
          :disabled="!navKeys.length"
          @click="confirmAllVisible = true"
        >
          全部应用（{{ navKeys.length }}）
        </el-button>
      </div>
    </div>

    <!-- 统计条 -->
    <div class="cmp-bar">
      <span><i class="sw mod"></i>修改 {{ counts.modified }}</span>
      <span><i class="sw add"></i>目标新增 {{ counts.added }}</span>
      <span><i class="sw del"></i>目标删除 {{ counts.removed }}</span>
      <span class="bar-hint">左：当前 dat，可应用　右：对比版本，只读</span>
    </div>

    <div v-if="!base" class="empty">
      <el-empty :description="baseError || '正在加载当前 dat 条目…'" />
    </div>

    <div v-else class="cmp-body">
      <div class="crow head">
        <span class="c-label"></span>
        <span class="c-val">
          当前 dat
          <em class="mono">{{ baseFile }}</em>
        </span>
        <span class="c-val">
          {{ rightTitle }}
          <em>只读</em>
        </span>
        <span class="c-act"></span>
      </div>

      <el-empty
        v-if="!compare.state.loaded"
        description="请先在右上角选择对比版本"
        :image-size="80"
      />
      <el-empty
        v-else-if="targetMissing"
        description="该版本中无此条目"
        :image-size="80"
      />
      <template v-else>
        <!-- 标量字段 -->
        <div v-if="visibleScalar.length" class="group">基础信息</div>
        <template v-for="f in visibleScalar" :key="'s-' + f.key">
          <div
            class="crow"
            :class="{ on: activeKey === 's:' + f.key, mod: isScalarDiff(f) }"
            :data-diff="'s:' + f.key"
          >
            <span class="c-label">{{ f.label }}</span>
            <span class="c-val" :class="{ old: isScalarDiff(f) }">{{ fmt(base[f.key]) }}</span>
            <span class="c-val" :class="{ new: isScalarDiff(f) }">{{ fmt(target?.[f.key]) }}</span>
            <span class="c-act">
              <el-button v-if="isScalarDiff(f)" size="small" @click="applyScalar(f)">
                ← 应用
              </el-button>
            </span>
          </div>
        </template>

        <!-- 子表字段 -->
        <template v-for="lf in visibleList" :key="'l-' + lf.key">
          <div class="group">{{ lf.label }}</div>
          <div class="crow subhead">
            <span class="c-label"></span>
            <span class="c-val subcols" :style="colsStyle(lf)">
              <b v-for="c in lf.columns" :key="c.key">{{ c.label }}</b>
              <b v-if="!lf.columns.length">值</b>
            </span>
            <span class="c-val subcols" :style="colsStyle(lf)">
              <b v-for="c in lf.columns" :key="c.key">{{ c.label }}</b>
              <b v-if="!lf.columns.length">值</b>
            </span>
            <span class="c-act"></span>
          </div>
          <div
            v-for="rd in rowsOf(lf)"
            :key="'l-' + lf.key + '-' + rd.index"
            class="crow"
            :class="[
              rd.kind === 'modified' ? 'mod' : rd.kind === 'added' ? 'add' : rd.kind === 'removed' ? 'del' : '',
              { on: activeKey === 'l:' + lf.key + ':' + rd.index }
            ]"
            :data-diff="'l:' + lf.key + ':' + rd.index"
          >
            <span class="c-label mono">{{ rowMark(rd) }}</span>
            <span class="c-val subcols" :style="colsStyle(lf)">
              <i v-for="(cell, ci) in cells(lf, rd.left)" :key="ci" :class="cellClass(rd, 'left')">
                {{ cell }}
              </i>
            </span>
            <span class="c-val subcols" :style="colsStyle(lf)">
              <i v-for="(cell, ci) in cells(lf, rd.right)" :key="ci" :class="cellClass(rd, 'right')">
                {{ cell }}
              </i>
            </span>
            <span class="c-act">
              <el-button v-if="rd.kind === 'modified'" size="small" @click="applyRow(lf, rd)">
                ← 应用
              </el-button>
              <el-button v-else-if="rd.kind === 'added'" size="small" @click="applyRow(lf, rd)">
                ← 添加
              </el-button>
              <el-button v-else-if="rd.kind === 'removed'" size="small" @click="applyRow(lf, rd)">
                ← 删除
              </el-button>
            </span>
          </div>
        </template>

        <div v-if="onlyDiff && !navKeys.length" class="no-diff">该条目与所选版本没有差异</div>
      </template>
    </div>

    <!-- 全部应用：页面内确认 -->
    <el-dialog v-model="confirmAllVisible" title="全部应用" width="380px">
      <p>把右侧版本的 {{ navKeys.length }} 处差异全部写入当前 dat？</p>
      <p class="dialog-hint">左栏字段将被覆盖为所选版本的值，之后可以撤销或保存。</p>
      <template #footer>
        <el-button size="small" @click="confirmAllVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="applying" @click="applyAll">
          确认应用
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAppStore } from '../stores'
import { useCompare, versionLabel } from '../composables/useCompare'
import { FIELDS, TABLE_LABELS, TABLE_ROUTES, isTableKey, scalarPath } from '../compare/fields'
import type { ListField, ScalarField } from '../compare/fields'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const compare = useCompare()

const table = computed(() => {
  const t = String(route.params.table || '')
  return isTableKey(t) ? t : 'techs'
})
const entityId = computed(() => Number(route.params.id))
const civ = computed(() => Number(route.query.civ ?? 0))
const tableLabel = computed(() => TABLE_LABELS[table.value])

const base = ref<any>(null)
const target = ref<any>(null)
const targetMissing = ref(false)
const baseError = ref('')
const onlyDiff = ref(false)
const activeKey = ref('')
const applying = ref(false)
const confirmAllVisible = ref(false)

const fields = computed(() => FIELDS[table.value])
const baseFile = computed(() => {
  const p = appStore.datInfo?.path || ''
  return p.replace(/\\/g, '/').split('/').pop() || ''
})
const rightTitle = computed(() => {
  const v = compare.selected()
  return v ? versionLabel(v) : '对比版本'
})

function kindLabel(kind: string): string {
  return kind === 'imported' ? '导入' : '已保存'
}

function eq(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

function fmt(v: unknown): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

// ------------------------------------------------------------------ 差异计算

function isScalarDiff(f: ScalarField): boolean {
  if (!target.value) return false
  return !eq(base.value?.[f.key], target.value?.[f.key])
}

interface RowDiff {
  index: number
  kind: 'same' | 'modified' | 'added' | 'removed'
  left: any
  right: any
}

function pickRows(detail: any, lf: ListField): any[] {
  const raw = (detail?.[lf.key] as any[]) || []
  return raw.map((r) => (lf.pick ? lf.pick(r) : r))
}

const rowCache = computed<Record<string, RowDiff[]>>(() => {
  const out: Record<string, RowDiff[]> = {}
  const t = target.value
  for (const lf of fields.value.list) {
    const left = pickRows(base.value, lf)
    const right = t ? pickRows(t, lf) : []
    const n = Math.max(left.length, right.length)
    const rows: RowDiff[] = []
    for (let i = 0; i < n; i++) {
      if (i >= left.length) rows.push({ index: i, kind: 'added', left: null, right: right[i] })
      else if (i >= right.length) rows.push({ index: i, kind: 'removed', left: left[i], right: null })
      else if (!eq(left[i], right[i]))
        rows.push({ index: i, kind: 'modified', left: left[i], right: right[i] })
      else rows.push({ index: i, kind: 'same', left: left[i], right: right[i] })
    }
    out[lf.key] = rows
  }
  return out
})

function rowsOf(lf: ListField): RowDiff[] {
  const rows = rowCache.value[lf.key] || []
  if (!target.value) return rows
  return onlyDiff.value ? rows.filter((r) => r.kind !== 'same') : rows
}

const visibleScalar = computed<ScalarField[]>(() =>
  onlyDiff.value ? fields.value.scalar.filter((f) => isScalarDiff(f)) : fields.value.scalar
)

const visibleList = computed<ListField[]>(() => {
  const hasRows = (lf: ListField) => (rowCache.value[lf.key] || []).length > 0
  if (!onlyDiff.value) return fields.value.list.filter(hasRows)
  return fields.value.list.filter(
    (lf) => (rowCache.value[lf.key] || []).some((r) => r.kind !== 'same')
  )
})

const counts = computed(() => {
  let modified = 0
  let added = 0
  let removed = 0
  if (target.value) {
    for (const f of fields.value.scalar) if (isScalarDiff(f)) modified++
    for (const lf of fields.value.list) {
      for (const r of rowCache.value[lf.key] || []) {
        if (r.kind === 'modified') modified++
        else if (r.kind === 'added') added++
        else if (r.kind === 'removed') removed++
      }
    }
  }
  return { modified, added, removed }
})

/** 与页面渲染顺序一致的差异锚点，供上一处 / 下一处使用。 */
const navKeys = computed<string[]>(() => {
  const keys: string[] = []
  if (!target.value) return keys
  for (const f of fields.value.scalar) if (isScalarDiff(f)) keys.push('s:' + f.key)
  for (const lf of fields.value.list) {
    for (const r of rowCache.value[lf.key] || []) {
      if (r.kind !== 'same') keys.push('l:' + lf.key + ':' + r.index)
    }
  }
  return keys
})

function setOnlyDiff(v: any) {
  onlyDiff.value = Boolean(v)
}

async function gotoDiff(dir: number) {
  const keys = navKeys.value
  if (!keys.length) return
  const cur = keys.indexOf(activeKey.value)
  const next = cur === -1 ? (dir > 0 ? 0 : keys.length - 1) : (cur + dir + keys.length) % keys.length
  activeKey.value = keys[next]
  await nextTick()
  document
    .querySelector(`[data-diff="${keys[next]}"]`)
    ?.scrollIntoView({ block: 'center', behavior: 'smooth' })
}

function rowMark(rd: RowDiff): string {
  if (rd.kind === 'added') return '+ #' + rd.index
  if (rd.kind === 'removed') return '− #' + rd.index
  if (rd.kind === 'modified') return '~ #' + rd.index
  return '#' + rd.index
}

function cells(lf: ListField, row: any): string[] {
  if (row === null || row === undefined) return ['（无此行）']
  if (!lf.columns.length) return [fmt(row)]
  return lf.columns.map((c) => fmt(row?.[c.key]))
}

function cellClass(rd: RowDiff, side: 'left' | 'right'): string {
  if (rd.kind === 'added') return side === 'right' ? 'v-new' : 'v-none'
  if (rd.kind === 'removed') return side === 'left' ? 'v-old' : 'v-none'
  if (rd.kind === 'modified') return side === 'left' ? 'v-old' : 'v-new'
  return ''
}

function colsStyle(lf: ListField) {
  const n = lf.columns.length || 1
  return { gridTemplateColumns: `repeat(${n}, minmax(0, 1fr))` }
}

// ------------------------------------------------------------------ 加载

async function loadBase() {
  baseError.value = ''
  try {
    if (table.value === 'techs') base.value = await api.techDetail(entityId.value)
    else if (table.value === 'effects') base.value = await api.effectDetail(entityId.value)
    else if (table.value === 'civs') base.value = await api.civDetail(entityId.value)
    else base.value = await api.unitDetail(civ.value, entityId.value)
  } catch (e: any) {
    base.value = null
    baseError.value = `当前 dat 条目加载失败：${e.message}`
  }
}

async function loadTarget() {
  target.value = null
  targetMissing.value = false
  if (!compare.state.loaded) return
  try {
    target.value = await api.diffEntity(table.value, entityId.value, civ.value)
  } catch {
    targetMissing.value = true
  }
}

async function onPickVersion(v: any) {
  const id = v === null || v === undefined ? null : Number(v)
  try {
    await compare.selectVersion(id)
    await loadTarget()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

// ------------------------------------------------------------------ 应用

async function patch(field: string, value: unknown) {
  if (table.value === 'techs') await api.patchTech(entityId.value, { field, value })
  else if (table.value === 'effects') await api.patchEffect(entityId.value, { field, value })
  else if (table.value === 'civs') await api.patchCiv(entityId.value, { field, value })
  else await api.patchUnit(civ.value, entityId.value, { field, value })
}

async function afterApply(field: string) {
  await loadBase()
  await appStore.refreshDatInfo()
  appStore.bumpRevision()
  await loadTarget()
  ElMessage.success({ message: `${field} 已应用`, duration: 1000 })
}

async function applyScalar(f: ScalarField) {
  if (!target.value) return
  try {
    await patch(scalarPath(f), target.value[f.key])
    await afterApply(f.label)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function applyRow(lf: ListField, rd: RowDiff) {
  if (!target.value) return
  const left = pickRows(base.value, lf)
  let rows: any[]
  if (rd.kind === 'modified') {
    rows = left.slice()
    rows[rd.index] = rd.right
  } else if (rd.kind === 'added') {
    rows = [...left, rd.right]
  } else {
    rows = left.filter((_, i) => i !== rd.index)
  }
  try {
    await patch(lf.path, rows)
    await afterApply(lf.label)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function applyAll() {
  if (!target.value) return
  applying.value = true
  try {
    for (const f of fields.value.scalar) {
      if (isScalarDiff(f)) await patch(scalarPath(f), target.value[f.key])
    }
    for (const lf of fields.value.list) {
      if (!eq(pickRows(base.value, lf), pickRows(target.value, lf))) {
        await patch(lf.path, pickRows(target.value, lf))
      }
    }
    confirmAllVisible.value = false
    await afterApply('全部差异')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    applying.value = false
  }
}

// ------------------------------------------------------------------ 导航 / 生命周期

function goBack() {
  router.push({ path: TABLE_ROUTES[table.value], query: { id: String(entityId.value) } })
}

watch(
  () => [route.params.table, route.params.id, route.query.civ],
  async () => {
    activeKey.value = ''
    await loadBase()
    await loadTarget()
  }
)

onMounted(async () => {
  compare.refreshVersions().catch(() => {})
  await loadBase()
  await loadTarget()
})
</script>

<style scoped>
.compare {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.cmp-top {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--line);
  background: #181b20;
}

.link {
  font: inherit;
  font-size: 12px;
  color: var(--link);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.link:hover {
  text-decoration: underline;
}

.title {
  font-size: 15px;
  color: var(--fg);
  font-weight: 600;
  white-space: nowrap;
}

.title .id {
  color: var(--muted);
  font-weight: 400;
}

.title .name {
  color: var(--fg-2);
  font-weight: 400;
  font-size: 13px;
  margin-left: 6px;
}

.actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}

.lbl {
  font-size: 12px;
  color: var(--muted);
}

.ver-select {
  width: 260px;
}

.opt-tag {
  margin-left: 6px;
}

.cmp-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 6px 16px;
  font-size: 12px;
  color: var(--fg-2);
  border-bottom: 1px solid var(--line);
  background: var(--panel);
}

.cmp-bar .bar-hint {
  margin-left: auto;
  color: var(--muted);
}

.sw {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  margin-right: 6px;
  vertical-align: -1px;
}

.sw.mod {
  background: var(--gold-bg);
  border: 1px solid var(--gold);
}

.sw.add {
  background: var(--blue-bg);
  border: 1px solid var(--blue);
}

.sw.del {
  background: var(--red-bg);
  border: 1px solid var(--red);
}

.empty {
  padding: 32px;
}

.cmp-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px 16px 40px;
}

.crow {
  display: grid;
  grid-template-columns: 150px minmax(0, 1fr) minmax(0, 1fr) 92px;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  border-top: 1px solid transparent;
}

.crow.head {
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--panel);
  border-bottom: 1px solid var(--line);
  color: var(--fg);
  font-weight: 600;
}

.crow.head em {
  color: var(--muted);
  font-weight: 400;
  font-style: normal;
  margin-left: 8px;
  font-size: 11px;
}

.crow.subhead {
  color: var(--muted);
  font-size: 11px;
  border-top: 1px dashed var(--line);
}

.crow.mod {
  background: var(--gold-bg);
}

.crow.add {
  background: var(--blue-bg);
}

.crow.del {
  background: var(--red-bg);
}

.crow.on {
  outline: 1px solid var(--gold);
  outline-offset: -1px;
}

.c-label {
  color: var(--muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.c-val {
  color: var(--fg-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 3px 8px;
  background: var(--raise);
  border: 1px solid var(--line);
  border-radius: 3px;
  min-height: 22px;
}

.c-val.old,
.v-old {
  color: var(--gold);
}

.c-val.new,
.v-new {
  color: var(--blue);
}

.v-none {
  color: var(--muted);
  font-style: italic;
}

.subcols {
  display: grid;
  gap: 8px;
}

.subcols i {
  font-style: normal;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subcols b {
  font-weight: 400;
  color: var(--muted);
}

.c-act {
  display: flex;
  justify-content: flex-end;
}

.group {
  margin: 12px 0 6px;
  color: var(--muted);
  font-weight: 600;
  font-size: 12px;
  letter-spacing: 0.06em;
}

.no-diff {
  padding: 24px;
  text-align: center;
  color: var(--muted);
  font-size: 12px;
}

.dialog-hint {
  color: var(--muted);
  font-size: 12px;
}
</style>
