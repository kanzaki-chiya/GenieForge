<template>
  <div class="editor">
    <div class="list">
      <div class="list-head">
        <span>补丁</span>
        <el-button size="small" type="primary" @click="newPatch">+ 新建</el-button>
      </div>
      <div v-for="p in files" :key="p.name" class="file-item" :class="{ active: p.name === currentName }" @click="load(p)">
        <span class="file-name">{{ p.name }}</span>
        <span class="file-del" @click.stop="del(p)">✕</span>
      </div>
    </div>

    <div class="main">
      <div class="toolbar">
        <el-input v-model="currentName" size="small" placeholder="补丁名称" style="width: 220px" />
        <el-button size="small" @click="save">保存</el-button>
        <el-button size="small" type="primary" @click="preview">预览</el-button>
        <el-button size="small" type="success" @click="applyPatch">应用</el-button>
        <span v-if="previewSummary" class="sum">
          命中 {{ previewSummary.applied }} · 冲突 {{ previewSummary.conflicts }} · 缺失 {{ previewSummary.missing }}
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
          <div class="preview-title">预览结果</div>
          <div v-for="(r, i) in previewResult.results" :key="i" class="prev-item" :class="r.status">
            <span class="prev-name">{{ r.name }}</span>
            <span class="prev-status">{{ statusText(r.status) }}</span>
            <span v-if="r.status === 'applied'" class="prev-val">{{ fmt(r.old) }} → {{ fmt(r.new) }}</span>
            <span v-else-if="r.status === 'conflict'" class="prev-val">命中 {{ r.candidates.length }} 个候选</span>
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
import Field from '../components/Field.vue'

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
  return { applied: '命中', conflict: '冲突', missing: '缺失', unsupported: '不支持' }[s] || s
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
    ElMessage.success(`已应用：命中 ${r.summary.applied} 条`)
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
.editor { height: 100%; display: flex; }
.list { width: 220px; border-right: 1px solid #34373a; overflow: auto; padding: 8px; }
.list-head { display: flex; align-items: center; justify-content: space-between; padding: 4px 4px 10px; font-weight: 600; color: #e6e6e6; }
.file-item { padding: 7px 10px; border-radius: 5px; cursor: pointer; display: flex; justify-content: space-between; font-size: 12px; color: #d4d4d4; }
.file-item.active { background: #3574f0; color: #fff; }
.file-del { color: #9a9a9a; }
.file-item.active .file-del { color: #fff; }
.main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.toolbar { padding: 8px 12px; border-bottom: 1px solid #34373a; display: flex; align-items: center; gap: 8px; }
.sum { color: #9a9a9a; font-size: 12px; }
.body { flex: 1; display: flex; min-height: 0; }
.steps { flex: 1; overflow: auto; padding: 12px 16px; }
.step { border: 1px solid #34373a; border-radius: 6px; padding: 8px 12px; margin-bottom: 10px; }
.step-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.step-idx { font-weight: 600; font-size: 13px; color: #e6e6e6; }
.step-del { color: #9a9a9a; cursor: pointer; }
.step-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px 12px; }
.preview { width: 340px; border-left: 1px solid #34373a; overflow: auto; padding: 12px; }
.preview-title { font-weight: 600; color: #e6e6e6; margin-bottom: 10px; }
.prev-item { padding: 6px 8px; border-radius: 5px; margin-bottom: 6px; font-size: 12px; border: 1px solid #34373a; }
.prev-item.applied { background: #1c2e20; }
.prev-item.conflict { background: #2e2918; }
.prev-item.missing { background: #2e1a1a; }
.prev-item.unsupported { background: #232528; }
.prev-name { display: block; color: #e6e6e6; }
.prev-status { color: #9a9a9a; margin-right: 8px; }
.prev-val { font-family: var(--font-mono); color: #8ae0a8; }
</style>
