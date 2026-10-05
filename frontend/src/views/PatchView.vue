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
        <span class="file-del" @click.stop="del(p)">✕</span>
      </div>
    </div>

    <div class="main">
      <div class="toolbar">
        <el-input v-model="currentName" size="small" placeholder="补丁名称" style="width: 220px" />
        <el-button size="small" @click="save">保存</el-button>
        <el-button size="small" type="primary" @click="preview">预览</el-button>
        <el-button size="small" type="primary" class="apply-btn" @click="applyPatch">应用</el-button>
        <span v-if="previewSummary" class="sum">
          命中 {{ previewSummary.applied ?? 0 }} · 冲突 {{ previewSummary.conflicts ?? 0 }} · 缺失 {{ previewSummary.missing ?? 0 }}
          <template v-if="(previewSummary.errors ?? 0) > 0">
            · <span class="sum-error">出错 {{ previewSummary.errors }}</span>
          </template>
          <template v-if="(previewSummary.rolled_back ?? 0) > 0">
            · <span class="sum-muted">已回滚 {{ previewSummary.rolled_back }}</span>
          </template>
          <template v-if="(previewSummary.skipped ?? 0) > 0">
            · <span class="sum-muted">未执行 {{ previewSummary.skipped }}</span>
          </template>
        </span>
      </div>

      <div class="body">
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

        <div class="preview" v-if="previewResult">
          <div class="preview-title">
            <span>预览结果</span>
            <span v-if="previewResult.rolled_back" class="rollback-badge">已全部回滚</span>
          </div>
          <div
            v-for="(r, i) in previewResult.results"
            :key="i"
            class="prev-item"
            :class="'status-' + r.status"
          >
            <div class="prev-item-top">
              <span class="prev-name">{{ r.name || '(未命名)' }}</span>
              <span class="status-tag" :class="'tag-' + r.status">
                {{ statusText(r.status) }}
              </span>
            </div>

            <!-- applied: 显示 old -> new -->
            <div v-if="r.status === 'applied'" class="prev-detail">
              <span class="prev-val mono">{{ fmt(r.old) }} → {{ fmt(r.new) }}</span>
              <span v-if="r.note" class="prev-note">{{ r.note }}</span>
            </div>

            <!-- rolled_back: 显示 old -> new 并标明已撤回 -->
            <div v-else-if="r.status === 'rolled_back'" class="prev-detail">
              <span class="prev-val mono strike">{{ fmt(r.old) }} → {{ fmt(r.new) }}</span>
              <span class="prev-badge-reverted">已撤回</span>
            </div>

            <!-- conflict: 显示候选数量 -->
            <div v-else-if="r.status === 'conflict'" class="prev-detail">
              <span class="prev-conflict">
                候选 ID: {{ r.candidates ? r.candidates.join(', ') : '多项' }}
              </span>
            </div>

            <!-- error: 显示原因（红） -->
            <div v-else-if="r.status === 'error'" class="prev-detail">
              <span class="prev-reason error">{{ r.reason || '无具体原因' }}</span>
            </div>

            <!-- skipped: 显示原因（灰） -->
            <div v-else-if="r.status === 'skipped'" class="prev-detail">
              <span class="prev-reason skipped">{{ r.reason || '无具体原因' }}</span>
            </div>

            <!-- missing / unsupported -->
            <div v-else-if="r.status === 'missing'" class="prev-detail">
              <span class="prev-muted">未找到匹配目标</span>
            </div>
            <div v-else-if="r.status === 'unsupported'" class="prev-detail">
              <span class="prev-muted">不支持的操作类型或目标字段</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAppStore } from '../stores'
import Field from '../components/Field.vue'

const appStore = useAppStore()
const files = ref<{ name: string; content: string }[]>([])
const currentName = ref('')
const steps = ref<any[]>([])
const previewResult = ref<any>(null)
const previewSummary = ref<any>(null)

const tables = ['techs', 'effects', 'civs', 'units']
const ops = ['set', 'add', 'multiply', 'relative', 'append', 'remove']

function emptyStep() {
  return { name: '', table: 'techs', targetName: '', op: 'set', field: '', value: '' }
}

function stepsToYaml() {
  const lines = ['version: 1', 'steps:']
  for (const s of steps.value) {
    lines.push(`  - name: ${s.name || '(未命名)'}`)
    lines.push(`    target: {table: ${s.table}, name: ${s.targetName}}`)
    lines.push(`    op: ${s.op}`)
    lines.push(`    field: ${s.field}`)
    lines.push(`    value: ${s.value}`)
  }
  return lines.join('\n')
}

async function fetchList() {
  const r: any = await api.patchList()
  files.value = r.items
}

async function load(p: { name: string; content: string }) {
  currentName.value = p.name
  try {
    const spec = parseYaml(p.content)
    steps.value = (spec.steps || []).map((s: any) => ({
      name: s.name || '',
      table: s.target?.table || 'techs',
      targetName: s.target?.name || '',
      op: s.op || 'set',
      field: s.field || '',
      value: s.value != null ? String(s.value) : ''
    }))
  } catch {
    steps.value = []
  }
  previewResult.value = null
  previewSummary.value = null
}

// 极简 YAML 解析（补丁结构固定：version + steps 列表）
function parseYaml(text: string): any {
  const spec: any = { steps: [] }
  const lines = text.split('\n')
  let cur: any = null
  for (const line of lines) {
    if (line.startsWith('  - name:')) {
      cur = { name: line.replace('  - name:', '').trim() }
      spec.steps.push(cur)
    } else if (cur && line.includes('target:')) {
      const m = line.match(/table:\s*(\w+).*name:\s*(.*)/)
      if (m) cur.target = { table: m[1], name: m[2].replace(/[{}]/g, '').trim() }
    } else if (cur && line.includes('op:')) {
      cur.op = line.replace('    op:', '').trim()
    } else if (cur && line.includes('field:')) {
      cur.field = line.replace('    field:', '').trim()
    } else if (cur && line.includes('value:')) {
      cur.value = line.replace('    value:', '').trim()
    }
  }
  return spec
}

function newPatch() {
  steps.value = [emptyStep()]
  currentName.value = 'new_patch'
  previewResult.value = null
  previewSummary.value = null
}

function addStep() {
  steps.value.push(emptyStep())
}

function removeStep(i: number) {
  steps.value.splice(i, 1)
}

function statusText(s: string) {
  const map: Record<string, string> = {
    applied: '命中',
    conflict: '冲突',
    missing: '缺失',
    unsupported: '不支持',
    error: '出错',
    rolled_back: '已回滚',
    skipped: '未执行'
  }
  return map[s] || s
}

function fmt(v: unknown) {
  return v == null ? '—' : String(v)
}

async function preview() {
  try {
    const r: any = await api.patchPreview(stepsToYaml())
    previewResult.value = r
    previewSummary.value = r.summary
    ElMessage.success('预览完成')
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function applyPatch() {
  try {
    const r: any = await api.patchApply(stepsToYaml())
    previewResult.value = r
    previewSummary.value = r.summary
    await appStore.refreshDatInfo()

    if (r.rolled_back) {
      ElMessage.error('补丁有步骤出错，已全部回滚')
    } else {
      ElMessage.success(`已应用：命中 ${r.summary?.applied ?? 0} 条`)
      appStore.bumpRevision()
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
    await api.patchSave(currentName.value, stepsToYaml())
    ElMessage.success('已保存')
    await fetchList()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function del(p: { name: string }) {
  try {
    await api.patchDelete(p.name)
    if (p.name === currentName.value) {
      steps.value = []
      previewResult.value = null
    }
    await fetchList()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(fetchList)
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
  justify-content: space-between;
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

/* 预览栏 */
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

/* 状态标签配色：命中蓝、冲突金、出错红、已回滚/未执行/不支持灰 */
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

/* 缺失 / 出错：红 */
.tag-missing,
.tag-error {
  background: var(--red-bg);
  color: var(--red);
  border: 1px solid #6b2f38;
}

/* 已回滚 / 未执行 / 不支持：灰 */
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
