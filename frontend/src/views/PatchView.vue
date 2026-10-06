<template>
  <div class="editor">
    <div class="list">
      <div class="list-head">
        <span>补丁文件</span>
        <el-button size="small" @click="newPatch">+ 新建</el-button>
      </div>
      <div
        v-for="p in files"
        :key="p.name"
        class="file-item"
        :class="{ active: p.name === currentName }"
        @click="load(p)"
      >
        <span class="file-name">{{ p.name }}</span>
        <span v-if="statusOf(p.name)" class="file-badge" :class="'badge-' + statusOf(p.name)!.kind">
          {{ statusOf(p.name)!.text }}
        </span>
        <span class="file-del" @click.stop="del(p)">✕</span>
      </div>
    </div>

    <div class="main">
      <div class="toolbar">
        <el-input v-model="currentName" size="small" placeholder="补丁名称" style="width: 220px" />
        <el-button size="small" @click="save">保存</el-button>
        <span v-if="dirty" class="dirty-tip">{{ hasCommentRaw ? '未保存（保存后注释会丢失）' : '未保存' }}</span>
        <el-segmented v-model="mode" :options="modeOptions" size="small" />
        <el-button size="small" type="primary" @click="preview">预览</el-button>
        <el-button size="small" type="primary" class="apply-btn" @click="applyPatch">
          应用 {{ applyCountText }}
        </el-button>
        <span v-if="hasUnresolved" class="skip-tip">冲突和未匹配的步骤将被跳过</span>
      </div>

      <div v-if="mode === 'edit'" class="body">
        <div class="steps">
          <div v-for="(s, i) in steps" :key="i" class="step">
            <div class="step-head">
              <span class="step-idx">步骤 {{ i + 1 }}</span>
              <span class="step-del" @click="removeStep(i)">✕</span>
            </div>
            <div class="step-grid">
              <Field label="名称"><el-input v-model="s.name" size="small" /></Field>
              <Field label="表"><el-select v-model="s.table" size="small"><el-option v-for="t in tables" :key="t" :value="t" :label="t" /></el-select></Field>
              <Field label="目标名"><el-input v-model="s.targetName" size="small" /></Field>
              <Field label="操作"><el-select v-model="s.op" size="small"><el-option v-for="o in ops" :key="o" :value="o" :label="o" /></el-select></Field>
              <Field label="字段"><el-input v-model="s.field" size="small" placeholder="如 resource_costs.gold.amount" /></Field>
              <Field label="值"><el-input v-model="s.value" size="small" /></Field>
            </div>
          </div>
          <el-button size="small" style="margin-top: 8px" @click="addStep">+ 添加步骤</el-button>
        </div>
      </div>

      <div v-else class="body">
        <div class="steps">
          <div v-if="!previewResult" class="check-empty">点“预览”查看命中 / 冲突 / 未匹配。</div>
          <div
            v-for="(card, i) in checkCards"
            :key="card.step"
            class="check-card"
            :class="'status-' + card.items[0].status"
          >
            <div class="check-top">
              <span class="check-name">{{ stepTitle(card.step) }}</span>
              <span class="status-tag" :class="'tag-' + card.items[0].status">{{ statusText(card.items[0].status) }}</span>
            </div>
            <div class="check-target">{{ stepTarget(card.step) }}</div>

            <template v-for="(r, j) in card.items" :key="j">
              <!-- 命中 -->
              <div v-if="r.status === 'applied'" class="check-detail">
                <span class="prev-val mono">#{{ r.id }} {{ fmt(r.old) }} → {{ fmt(r.new) }}</span>
                <span v-if="r.note" class="prev-note">{{ r.note }}</span>
              </div>

              <!-- 冲突：候选多选 + 记住选择 -->
              <div v-else-if="r.status === 'conflict'" class="check-detail col">
                <el-checkbox-group v-model="selected[card.step]">
                  <el-checkbox
                    v-for="c in (r.candidate_details || [])"
                    :key="c.id"
                    :value="c.id"
                    class="cand"
                  >
                    #{{ c.id }} {{ c.display_name || c.name }}
                  </el-checkbox>
                </el-checkbox-group>
                <div class="check-actions">
                  <el-button
                    size="small"
                    :disabled="!(selected[card.step] || []).length"
                    @click="remember(card.step)"
                  >
                    记住选择
                  </el-button>
                  <span v-if="rememberWarnings[card.step]" class="warn">{{ rememberWarnings[card.step] }}</span>
                </div>
              </div>

              <!-- 未匹配：推荐采用 / 跳过 -->
              <div v-else-if="r.status === 'missing'" class="check-detail col">
                <template v-if="(r.suggestions || []).length">
                  <div class="sugg-title">按签名找到相似条目：</div>
                  <div v-for="s in (r.suggestions || [])" :key="s.id" class="sugg">
                    <span class="sugg-name">#{{ s.id }} {{ s.display_name || s.name }}</span>
                    <span class="sugg-reasons">{{ (s.reasons || []).join(' · ') }}</span>
                    <el-button size="small" @click="adopt(card.step, s.id)">采用</el-button>
                  </div>
                </template>
                <div v-else class="prev-muted">未找到匹配目标，也没有相似推荐。</div>
                <div class="check-actions">
                  <el-button size="small" @click="skipStep(card.step)">跳过此步</el-button>
                  <span v-if="skipped.has(card.step)" class="prev-muted">已加入跳过</span>
                </div>
              </div>

              <!-- 出错 / 已回滚 / 未执行：沿用旧样式 -->
              <div v-else-if="r.status === 'rolled_back'" class="check-detail">
                <span class="prev-val mono strike">#{{ r.id }} {{ fmt(r.old) }} → {{ fmt(r.new) }}</span>
                <span class="prev-badge-reverted">已撤回</span>
              </div>
              <div v-else-if="r.status === 'error'" class="check-detail">
                <span class="prev-reason error">{{ r.reason || '无具体原因' }}</span>
              </div>
              <div v-else-if="r.status === 'skipped'" class="check-detail">
                <span class="prev-reason skipped">{{ r.reason || '无具体原因' }}</span>
              </div>
              <div v-else class="check-detail">
                <span class="prev-muted">不支持的操作类型或目标字段</span>
              </div>
            </template>
          </div>
        </div>

        <div class="preview" v-if="previewResult">
          <div class="preview-title">
            <span>预览汇总</span>
            <span v-if="previewResult.rolled_back" class="rollback-badge">已全部回滚</span>
          </div>
          <div class="sum-line">
            命中 {{ previewSummary.applied ?? 0 }} · 冲突 {{ previewSummary.conflicts ?? 0 }} · 未匹配 {{ previewSummary.missing ?? 0 }}
          </div>
          <div v-if="(previewSummary.errors ?? 0) > 0" class="sum-line">
            <span class="sum-error">出错 {{ previewSummary.errors }}</span>
          </div>
          <div class="sum-note">
            冲突和未匹配的步骤不会被应用。处理完后重新预览，确认无误再应用；整份补丁可以一步撤销。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAppStore } from '../stores'
import Field from '../components/Field.vue'

const appStore = useAppStore()
const files = ref<{ name: string; content: string }[]>([])
const statuses = ref<Record<string, { applied: number; conflicts: number; missing: number; errors: number; ok: boolean }>>({})
const currentName = ref('')
// steps 为表单行；fullSpec 为后端 parse 的完整 spec（保留表单没有的字段）。
const steps = ref<any[]>([])
const fullSpec = ref<any>({ version: 1, steps: [] })
const rawYaml = ref('')
const dirty = ref(false)
// 程序性赋值（load / 删除 / 记住选择回填）不算用户修改：置位期间跳过 watch。
let quietSteps = false
function setSteps(rows: any[]) {
  quietSteps = true
  steps.value = rows
}
const mode = ref<'check' | 'edit'>('check')
const modeOptions = [
  { label: '检查', value: 'check' },
  { label: '编辑步骤', value: 'edit' }
]
const previewResult = ref<any>(null)
const previewSummary = ref<any>(null)
// 检查模式的就地处理状态：步骤下标 → 选中 id；手动 skip 的步骤下标。
const selected = ref<Record<number, number[]>>({})
const skipped = ref<Set<number>>(new Set())
const rememberWarnings = ref<Record<number, string>>({})
const hasCommentRaw = computed(() => hasComment(rawYaml.value))
const tables = ['techs', 'effects', 'civs', 'units']
const ops = ['set', 'add', 'multiply', 'relative', 'append', 'remove']

function emptyStep() {
  return { name: '', table: 'techs', targetName: '', op: 'set', field: '', value: '' }
}

// 检查卡片：预览结果按原步骤下标分组（override 展开的多条明细共用一步）。
const checkCards = computed(() => {
  const results: any[] = previewResult.value?.results || []
  const groups = new Map<number, any[]>()
  const order: number[] = []
  results.forEach((r: any) => {
    const k = typeof r.step === 'number' ? r.step : -1
    if (!groups.has(k)) {
      groups.set(k, [])
      order.push(k)
    }
    groups.get(k)!.push(r)
  })
  return order.map((k) => ({ step: k < 0 ? 0 : k, items: groups.get(k)! }))
})

const hasUnresolved = computed(() => {
  const s = previewSummary.value
  if (!s) return false
  return (s.conflicts ?? 0) > 0 || (s.missing ?? 0) > 0
})

const applyCountText = computed(() => {
  const s = previewSummary.value
  if (!s) return ''
  const n = (s.applied ?? 0)
  return n ? `${n} 步` : ''
})

function statusOf(name: string): { kind: string; text: string } | null {
  const s = statuses.value[name]
  if (!s) return null
  if (s.errors > 0) return { kind: 'error', text: '出错' }
  if (s.ok) return { kind: 'ok', text: '全部命中' }
  const parts: string[] = []
  if (s.conflicts > 0) parts.push(`${s.conflicts} 冲突`)
  if (s.missing > 0) parts.push(`${s.missing} 未匹配`)
  return { kind: 'warn', text: parts.join(' / ') }
}

function stepTitle(stepIdx: number) {
  const name = steps.value[stepIdx]?.name || fullSpec.value.steps?.[stepIdx]?.name || '(未命名)'
  return `步骤 ${stepIdx + 1} · ${name}`
}

function stepTarget(stepIdx: number) {
  const s = fullSpec.value.steps?.[stepIdx] || {}
  const t = s.target || {}
  const bits = [`表 ${t.table || '?'}`]
  if (t.name) bits.push(`匹配 ${t.name}`)
  if (t.name_pattern) bits.push(`正则 ${t.name_pattern}`)
  if (t.signature) bits.push('签名')
  bits.push(`操作 ${s.op || 'set'} · 字段 ${s.field || '—'}`)
  return bits.join(' · ')
}

async function fetchList() {
  const r: any = await api.patchList()
  files.value = r.items
}

async function fetchStatus() {
  // 未加载 dat 时后端 409：不显示徽标。
  try {
    const r: any = await api.patchStatus()
    const map: Record<string, any> = {}
    for (const it of r.items || []) map[it.name] = it
    statuses.value = map
  } catch {
    statuses.value = {}
  }
}

async function refreshFileState() {
  await fetchList()
  await fetchStatus()
}

function specToRows(spec: any) {
  return ((spec.steps || []) as any[]).map((s: any) => ({
    name: s.name || '',
    table: s.target?.table || 'techs',
    targetName: s.target?.name || '',
    op: s.op || 'set',
    field: s.field ?? '',
    value: s.value != null ? String(s.value) : ''
  }))
}

function rowsToSpec() {
  // 表单改动合并回完整 spec：表单没有的字段（name_pattern、signature、based_on 等）原样保留。
  const spec = JSON.parse(JSON.stringify(fullSpec.value || { version: 1, steps: [] }))
  spec.steps = (spec.steps || []).map((orig: any, i: number) => {
    const row = steps.value[i]
    if (!row) return orig
    const next = { ...orig }
    next.name = row.name || '(未命名)'
    next.target = { ...(orig.target || {}), table: row.table }
    if (row.targetName) next.target.name = row.targetName
    else delete next.target.name
    next.op = row.op
    next.field = row.field
    next.value = coerceValue(row.value)
    return next
  })
  return spec
}

function coerceValue(text: string) {
  const t = (text ?? '').trim()
  if (t === '') return ''
  if (t === 'true') return true
  if (t === 'false') return false
  if (/^-?\d+$/.test(t)) return parseInt(t, 10)
  if (/^-?\d*\.\d+$/.test(t)) return parseFloat(t)
  return text
}

async function currentYaml(): Promise<string> {
  const { yaml } = await api.patchDump(rowsToSpec())
  return yaml
}

function hasComment(text: string) {
  return text.split('\n').some((l) => l.trimStart().startsWith('#'))
}

async function load(p: { name: string; content: string }) {
  currentName.value = p.name
  rawYaml.value = p.content
  try {
    const { spec } = await api.patchParse(p.content)
    fullSpec.value = spec
    setSteps(specToRows(spec))
    if (hasComment(p.content)) ElMessage.warning('保存后注释会丢失')
  } catch (e: any) {
    fullSpec.value = { version: 1, steps: [] }
    setSteps([])
    ElMessage.error(e.message)
  }
  dirty.value = false
  mode.value = 'check'
  previewResult.value = null
  previewSummary.value = null
  selected.value = {}
  skipped.value = new Set()
  rememberWarnings.value = {}
}

function newPatch() {
  fullSpec.value = { version: 1, steps: [{ name: '', target: { table: 'techs' }, op: 'set', field: '', value: '' }] }
  setSteps([emptyStep()])
  currentName.value = 'new_patch'
  rawYaml.value = ''
  dirty.value = true
  previewResult.value = null
  previewSummary.value = null
  selected.value = {}
  skipped.value = new Set()
}

function addStep() {
  steps.value.push(emptyStep())
  const specSteps = fullSpec.value.steps || (fullSpec.value.steps = [])
  specSteps.push({ name: '', target: { table: 'techs' }, op: 'set', field: '', value: '' })
  dirty.value = true
}

function removeStep(i: number) {
  steps.value.splice(i, 1)
  fullSpec.value.steps?.splice(i, 1)
  dirty.value = true
}

watch(steps, () => {
  if (quietSteps) {
    quietSteps = false
    return
  }
  dirty.value = true
}, { deep: true })

function statusText(s: string) {
  const map: Record<string, string> = {
    applied: '命中',
    conflict: '冲突',
    missing: '未匹配',
    unsupported: '不支持',
    error: '出错',
    rolled_back: '已回滚',
    skipped: '已跳过'
  }
  return map[s] || s
}

function fmt(v: unknown) {
  return v == null ? '—' : String(v)
}

function buildPayload(yaml: string) {
  const overrides: Record<number, number[]> = {}
  for (const [k, v] of Object.entries(selected.value)) {
    if ((v || []).length) overrides[Number(k)] = v
  }
  const skip = [...skipped.value]
  return { overrides, skip }
}

async function preview() {
  try {
    const yaml = await currentYaml()
    const { overrides, skip } = buildPayload(yaml)
    const r: any = await api.patchPreview(yaml, overrides, skip)
    previewResult.value = r
    previewSummary.value = r.summary
    // 给每步初始化选中数组，避免 checkbox-group 绑动态空 key。
    const init: Record<number, number[]> = {}
    for (const item of r.results || []) {
      if (typeof item.step === 'number' && !(item.step in selected.value)) init[item.step] = []
    }
    selected.value = { ...selected.value, ...init }
    ElMessage.success('预览完成')
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function applyPatch() {
  try {
    const yaml = await currentYaml()
    const { overrides, skip } = buildPayload(yaml)
    const r: any = await api.patchApply(yaml, overrides, skip)
    previewResult.value = r
    previewSummary.value = r.summary
    await appStore.refreshDatInfo()

    if (r.rolled_back) {
      ElMessage.error('补丁有步骤出错，已全部回滚')
    } else {
      ElMessage.success(`已应用：命中 ${r.summary?.applied ?? 0} 条`)
      appStore.bumpRevision()
      await fetchStatus()
    }
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function save() {
  if (!currentName.value) {
    ElMessage.warning('请输入补丁名称')
    return
  }
  try {
    const yaml = await currentYaml()
    if (hasComment(rawYaml.value)) ElMessage.warning('保存后注释会丢失')
    await api.patchSave(currentName.value, yaml)
    rawYaml.value = yaml
    dirty.value = false
    ElMessage.success('已保存')
    await refreshFileState()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function del(p: { name: string }) {
  try {
    await api.patchDelete(p.name)
    if (p.name === currentName.value) {
      setSteps([])
      fullSpec.value = { version: 1, steps: [] }
      previewResult.value = null
      dirty.value = false
    }
    await refreshFileState()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

// 未匹配“采用”：把该推荐 id 作为这一步的 override。
function adopt(stepIdx: number, id: number) {
  selected.value[stepIdx] = [id]
  const s = new Set(skipped.value)
  s.delete(stepIdx)
  skipped.value = s
  ElMessage.success(`步骤 ${stepIdx + 1} 已指定 #${id}，重新预览确认`)
}

// “跳过此步”。
function skipStep(stepIdx: number) {
  skipped.value = new Set(skipped.value).add(stepIdx)
  delete selected.value[stepIdx]
  ElMessage.success(`步骤 ${stepIdx + 1} 已跳过，应用时不会执行`)
}

// 冲突“记住选择”：调 resolve 写回补丁，重新解析到编辑状态。
async function remember(stepIdx: number) {
  const ids = selected.value[stepIdx] || []
  if (!ids.length) return
  try {
    const yaml = await currentYaml()
    const r = await api.patchResolve(yaml, stepIdx, ids)
    const { spec } = await api.patchParse(r.yaml)
    fullSpec.value = spec
    setSteps(specToRows(spec))
    rawYaml.value = r.yaml
    dirty.value = true
    // 步骤数变了（1→N），旧下标全部失效，清空重来。
    selected.value = {}
    skipped.value = new Set()
    previewResult.value = null
    previewSummary.value = null
    if ((r.warnings || []).length) {
      rememberWarnings.value[stepIdx] = r.warnings.join('；')
      ElMessage.warning(r.warnings.join('；'))
    } else {
      ElMessage.success(`已改写为 ${r.steps_added} 步，记得保存`)
    }
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(async () => {
  await fetchList()
  await fetchStatus()
})

// dat 变化后刷新徽标。
watch(() => appStore.dataRevision, () => { fetchStatus() })
</script>

<style scoped>
.editor {
  height: 100%;
  display: flex;
  background: var(--app);
  color: var(--fg);
}

.list {
  width: 220px;
  border-right: 1px solid var(--line);
  background: var(--panel);
  overflow: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 6px 10px;
  font-weight: 600;
  color: var(--fg);
}

.file-item {
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--fg-2);
  transition: background 0.15s, color 0.15s;
}

.file-item:hover {
  background: var(--raise);
  color: var(--fg);
}

.file-item.active {
  background: #252931;
  color: #ffffff;
  box-shadow: inset 2px 0 0 var(--gold);
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.file-badge {
  font-size: 10px;
  border-radius: 4px;
  padding: 1px 6px;
  white-space: nowrap;
}

.badge-ok {
  background: var(--blue-bg);
  color: #9cc5f2;
  border: 1px solid #2f4a6b;
}

.badge-warn {
  background: var(--gold-bg);
  color: var(--gold);
  border: 1px solid var(--gold-edge);
}

.badge-error {
  background: var(--red-bg);
  color: var(--red);
  border: 1px solid #6b2f38;
}

.file-del {
  color: var(--muted);
  font-size: 11px;
  padding: 2px 4px;
}

.file-del:hover {
  color: var(--red);
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--app);
}

.toolbar {
  padding: 10px 16px;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  gap: 10px;
  background: #181b20;
  flex-wrap: wrap;
}

.dirty-tip {
  color: var(--gold);
  font-size: 12px;
}

.skip-tip {
  color: var(--gold);
  font-size: 12px;
}

.sum {
  color: var(--fg-2);
  font-size: 12px;
  margin-left: 8px;
}

.sum-error {
  color: var(--red);
  font-weight: 500;
}

.sum-muted {
  color: var(--muted);
}

.body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.steps {
  flex: 1;
  overflow: auto;
  padding: 16px 20px;
}

.step {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--raise);
  padding: 12px 14px;
  margin-bottom: 12px;
}

.step-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.step-idx {
  font-weight: 600;
  font-size: 13px;
  color: var(--fg);
}

.step-del {
  color: var(--muted);
  cursor: pointer;
  padding: 2px 6px;
}

.step-del:hover {
  color: var(--red);
}

.step-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px 14px;
}

.check-empty {
  color: var(--muted);
  font-size: 13px;
  padding: 20px 4px;
}

/* 检查模式步骤卡片 */
.check-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--raise);
  padding: 12px 14px;
  margin-bottom: 12px;
}

.check-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.check-name {
  font-weight: 600;
  font-size: 13px;
  color: var(--fg);
}

.check-target {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 8px;
}

.check-detail {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  font-size: 12px;
}

.check-detail.col {
  flex-direction: column;
  align-items: stretch;
}

.check-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.cand {
  margin-right: 12px;
}

.sugg-title {
  color: var(--fg-2);
}

.sugg {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
}

.sugg-name {
  font-weight: 600;
  color: var(--fg);
}

.sugg-reasons {
  flex: 1;
  color: var(--gold);
  font-size: 11px;
}

.warn {
  color: var(--gold);
  font-size: 11px;
}

/* 右侧汇总栏 */
.preview {
  width: 360px;
  border-left: 1px solid var(--line);
  background: var(--panel);
  overflow: auto;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  font-size: 14px;
  color: var(--fg);
  margin-bottom: 6px;
}

.rollback-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--red-bg);
  color: var(--red);
  border: 1px solid #6b2f38;
  font-weight: 500;
}

.sum-line {
  font-size: 13px;
  color: var(--fg);
}

.sum-note {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.6;
}

.prev-item {
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 12px;
  border: 1px solid var(--line);
  background: var(--raise);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.prev-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.prev-name {
  font-weight: 600;
  color: var(--fg);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 状态标签配色：命中蓝、冲突金、未匹配/出错红、已回滚/已跳过/不支持灰 */
.status-tag {
  font-size: 11px;
  border-radius: 4px;
  padding: 1px 7px;
  font-weight: 500;
  white-space: nowrap;
}

/* 命中：蓝 */
.tag-applied {
  background: var(--blue-bg);
  color: #9cc5f2;
  border: 1px solid #2f4a6b;
}

/* 冲突：金 */
.tag-conflict {
  background: var(--gold-bg);
  color: var(--gold);
  border: 1px solid var(--gold-edge);
}

/* 未匹配 / 出错：红 */
.tag-missing,
.tag-error {
  background: var(--red-bg);
  color: var(--red);
  border: 1px solid #6b2f38;
}

/* 已回滚 / 已跳过 / 不支持：灰 */
.tag-rolled_back,
.tag-skipped,
.tag-unsupported {
  background: #252931;
  color: var(--muted);
  border: 1px solid #353a44;
}

.prev-detail {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  font-size: 12px;
}

.prev-val {
  color: #9cc5f2;
}

.prev-val.strike {
  text-decoration: line-through;
  color: var(--muted);
}

.prev-badge-reverted {
  font-size: 10px;
  color: var(--muted);
  background: #23272e;
  border: 1px solid var(--line);
  padding: 0 5px;
  border-radius: 3px;
}

.prev-note {
  color: var(--gold);
  font-size: 11px;
}

.prev-conflict {
  color: var(--gold);
}

.prev-reason {
  word-break: break-all;
}

.prev-reason.error {
  color: var(--red);
}

.prev-reason.skipped {
  color: var(--muted);
}
.prev-muted {
  color: var(--muted);
}
</style>
