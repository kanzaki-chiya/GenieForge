<template>
  <div class="editor">
    <div class="toolbar">
      <el-input
        v-model="q"
        placeholder="搜索效果名…"
        size="small"
        clearable
        style="width: 260px"
        @keyup.enter="fetch"
        @clear="fetch"
      />
      <el-button size="small" @click="fetch">搜索</el-button>
      <span class="count">共 {{ total }} 条 · 当前 #{{ currentId }}</span>
    </div>

    <div class="body">
      <div class="list">
        <el-table
          :data="rows"
          size="small"
          highlight-current-row
          height="100%"
          @current-change="onSelect"
        >
          <el-table-column prop="id" label="ID" width="64" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="commands" label="命令数" width="64" align="right" />
        </el-table>
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          size="small"
          @current-change="fetch"
        />
      </div>

      <div class="form" v-if="detail">
        <div class="form-scroll">
          <div class="group-title">基础信息</div>
          <div class="grid1">
            <Field label="Effect Name">
              <FieldControl type="text" :model-value="detail.name" @commit="(v) => save('name', v)" />
            </Field>
          </div>

          <div class="group-title">效果命令（{{ detail.effect_commands.length }} 条）</div>
          <SubTable
            :columns="cmdCols"
            :model-value="detail.effect_commands"
            @cell-commit="onCmdCell"
            @add-row="onCmdAdd"
            @insert-row="onCmdInsert"
            @remove-row="onCmdRemove"
          />
        </div>
      </div>
      <div class="form" v-else>
        <el-empty description="选择左侧效果查看详情" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import EnumSelect from '../components/EnumSelect.vue'
import FieldControl from '../components/FieldControl.vue'
import SubTable from '../components/SubTable.vue'
import Field from '../components/Field.vue'

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const q = ref('')
const detail = ref<any>(null)
const currentId = ref(-1)

const cmdCols = [
  { key: 'type', label: '类型', type: 'enum', metaName: 'effect-types', width: 170 },
  { key: 'a', label: 'a', type: 'number', width: 80 },
  { key: 'b', label: 'b', type: 'number', width: 80 },
  { key: 'c', label: 'c', type: 'number', width: 80 },
  { key: 'd', label: 'd', type: 'number', width: 80 }
]
const cmdTemplate = () => ({ type: 0, a: -1, b: -1, c: -1, d: 0 })

async function fetch() {
  const r: any = await api.effects({ page: page.value, page_size: pageSize, q: q.value })
  rows.value = r.items
  total.value = r.total
}

async function onSelect(row: any) {
  if (!row) return
  currentId.value = row.id
  detail.value = await api.effectDetail(row.id)
}

function setDetail(dotted: string, value: unknown) {
  const parts = dotted.split('.')
  let cur: any = detail.value
  for (let i = 0; i < parts.length - 1; i++) cur = cur[parts[i]]
  cur[parts[parts.length - 1]] = value
}

async function save(field: string, value: unknown) {
  if (!detail.value) return
  try {
    await api.patchEffect(detail.value.id, { field, value })
    setDetail(field, value)
    ElMessage.success({ message: `${field} 已保存`, duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

function onCmdCell(p: { rowIndex: number; colKey: string; value: unknown }) {
  save(`effect_commands.${p.rowIndex}.${p.colKey}`, p.value)
}

async function onCmdAdd() {
  await saveTable([...detail.value.effect_commands, cmdTemplate()])
}

async function onCmdInsert(idx: number) {
  const rows = [...detail.value.effect_commands]
  rows.splice(idx, 0, cmdTemplate())
  await saveTable(rows)
}

async function onCmdRemove(idx: number) {
  await saveTable(detail.value.effect_commands.filter((_: unknown, i: number) => i !== idx))
}

async function saveTable(rows: unknown[]) {
  if (!detail.value) return
  try {
    await api.patchEffect(detail.value.id, { field: 'effect_commands', value: rows })
    setDetail('effect_commands', rows)
    ElMessage.success({ message: 'effect_commands 已更新', duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(fetch)
</script>

<style scoped>
.editor { height: 100%; display: flex; flex-direction: column; }
.toolbar { padding: 8px 12px; border-bottom: 1px solid #34373a; display: flex; align-items: center; gap: 8px; }
.count { color: #9a9a9a; font-size: 12px; }
.body { flex: 1; display: flex; min-height: 0; }
.list { width: 320px; border-right: 1px solid #34373a; display: flex; flex-direction: column; }
.form { flex: 1; min-width: 0; display: flex; }
.form-scroll { flex: 1; overflow: auto; padding: 12px 16px; }
.group-title { color: #e6e6e6; font-weight: 600; font-size: 13px; border-top: 1px solid #34373a; margin: 14px 0 8px; padding-top: 10px; }
.group-title:first-child { border-top: none; margin-top: 0; padding-top: 0; }
.grid1 { display: grid; grid-template-columns: 1fr; gap: 8px; }
</style>
