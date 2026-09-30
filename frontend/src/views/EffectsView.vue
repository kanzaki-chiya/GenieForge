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
      <el-button size="small" :disabled="!detail" @click="openCompare">对比</el-button>
    </div>

    <div class="body">
      <div class="list">
        <el-table :data="rows" size="small" highlight-current-row height="100%" @current-change="onSelect">
          <el-table-column prop="id" label="ID" width="64" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="commands" label="命令" width="56" align="right" />
        </el-table>
        <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" size="small" @current-change="fetch" />
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
          <div v-for="(ec, i) in detail.effect_commands" :key="i" class="cmd">
            <div class="cmd-head">
              <span class="cmd-idx">#{{ i }}</span>
              <EnumSelect meta-name="effect-types" :model-value="ec.type" style="width: 200px" @change="(v) => onTypeChange(i, v)" />
              <span class="cmd-desc">{{ ec.description }}</span>
              <span class="cmd-del" @click="removeCmd(i)">✕</span>
            </div>
            <div class="cmd-params">
              <Field v-for="p in paramsFor(ec.type)" :key="p.key" :label="p.label">
                <EnumSelect v-if="p.type === 'unit'" :preloaded="unitItems" :model-value="ec[p.key]" @change="(v) => saveCmd(i, p.key, v)" />
                <EnumSelect v-else-if="p.type === 'tech'" :preloaded="techItems" :model-value="ec[p.key]" @change="(v) => saveCmd(i, p.key, v)" />
                <EnumSelect v-else-if="p.type === 'armor'" meta-name="armors" :model-value="ec[p.key]" @change="(v) => saveCmd(i, p.key, v)" />
                <EnumSelect v-else-if="p.type === 'attribute'" meta-name="effect-attributes" :model-value="ec[p.key]" @change="(v) => saveCmd(i, p.key, v)" />
                <EnumSelect v-else-if="p.type === 'resource'" meta-name="resource-types" :model-value="ec[p.key]" @change="(v) => saveCmd(i, p.key, v)" />
                <FieldControl v-else type="number" :model-value="ec[p.key]" @commit="(v) => saveCmd(i, p.key, v)" />
              </Field>
            </div>
          </div>
          <el-button size="small" style="margin-top: 8px" @click="addCmd">+ 添加命令</el-button>
        </div>
      </div>
      <div class="form" v-else>
        <el-empty description="选择左侧效果查看详情" />
      </div>
    </div>

    <DiffDrawer
      v-if="detail"
      v-model="diffVisible"
      :table="'effects'"
      :entity-id="detail.id"
      :title="detail.name"
      :baseline="detail"
      :scalar-fields="scalarFields"
      :list-fields="listFields"
      @apply="onApplyDiff"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import EnumSelect from '../components/EnumSelect.vue'
import FieldControl from '../components/FieldControl.vue'
import DiffDrawer from '../components/DiffDrawer.vue'
import { useCompare } from '../composables/useCompare'

const compare = useCompare()
import Field from '../components/Field.vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const q = ref('')
const detail = ref<any>(null)
const currentId = ref(-1)
const unitItems = ref<{ value: number; label: string }[]>([])
const techItems = ref<{ value: number; label: string }[]>([])
const diffVisible = ref(false)

const scalarFields = [{ key: 'name', label: '名称' }]
const listFields = [{ key: 'effect_commands', label: '效果命令' }]

function openCompare() {
  diffVisible.value = true
}

function onApplyDiff(p: { field: string; value: unknown; list: boolean }) {
  if (p.list) {
    saveTable(p.value as unknown[])
  } else {
    save(p.field, p.value)
  }
}

function paramsFor(type: number) {
  if (type === 101) {
    return [
      { key: 'a', label: 'Tech', type: 'tech' },
      { key: 'b', label: 'Resource', type: 'resource' },
      { key: 'c', label: '0设/1改', type: 'number' },
      { key: 'd', label: 'Amount', type: 'number' }
    ]
  }
  if (type === 102) {
    return [{ key: 'd', label: 'Tech', type: 'tech' }]
  }
  if (type === 103) {
    return [
      { key: 'a', label: 'Tech', type: 'tech' },
      { key: 'c', label: '0设/1改', type: 'number' },
      { key: 'd', label: 'Amount', type: 'number' }
    ]
  }
  const base = type % 10
  if ([0, 4, 5].includes(base)) {
    return [
      { key: 'a', label: 'Unit', type: 'unit' },
      { key: 'b', label: 'Class', type: 'armor' },
      { key: 'c', label: 'Attribute', type: 'attribute' },
      { key: 'd', label: 'Amount', type: 'number' }
    ]
  }
  if ([1, 6].includes(base)) {
    return [
      { key: 'a', label: 'Resource', type: 'resource' },
      { key: 'b', label: '模式', type: 'number' },
      { key: 'c', label: '倍率资源', type: 'resource' },
      { key: 'd', label: 'Amount', type: 'number' }
    ]
  }
  if (base === 2) return [{ key: 'a', label: 'Unit', type: 'unit' }, { key: 'b', label: '0禁用/1启用', type: 'number' }]
  if (base === 3) return [{ key: 'a', label: '源 Unit', type: 'unit' }, { key: 'b', label: '目标 Unit', type: 'unit' }, { key: 'c', label: '范围', type: 'number' }]
  if (base === 7) return [{ key: 'a', label: 'Unit', type: 'unit' }, { key: 'b', label: '来源', type: 'unit' }, { key: 'c', label: '次数', type: 'number' }]
  if (base === 8) return [{ key: 'a', label: 'Tech', type: 'tech' }, { key: 'b', label: '模式', type: 'number' }, { key: 'd', label: '值', type: 'number' }]
  return [{ key: 'a', label: 'a', type: 'number' }, { key: 'b', label: 'b', type: 'number' }, { key: 'c', label: 'c', type: 'number' }, { key: 'd', label: 'd', type: 'number' }]
}

async function fetch() {
  const r: any = await api.effects({ page: page.value, page_size: pageSize, q: q.value })
  rows.value = r.items
  total.value = r.total
}

async function loadRefs() {
  const [tn, un]: any[] = await Promise.all([api.techNames(), api.units(0, undefined)])
  techItems.value = tn.items.map((x: any) => ({ value: x.id, label: x.name }))
  unitItems.value = (un.items || []).map((x: any) => ({ value: x.unit_id, label: x.name }))
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

function saveCmd(i: number, key: string, value: unknown) {
  save(`effect_commands.${i}.${key}`, value)
}

function onTypeChange(i: number, v: number) {
  saveCmd(i, 'type', v)
  // 重新拉取描述
  detail.value = { ...detail.value, effect_commands: detail.value.effect_commands.map((c: any, idx: number) => idx === i ? { ...c, type: v } : c) }
}

async function addCmd() {
  const rows = [...detail.value.effect_commands, { type: 4, a: -1, b: -1, c: 0, d: 0 }]
  await saveTable(rows)
}

async function removeCmd(i: number) {
  await saveTable(detail.value.effect_commands.filter((_: unknown, idx: number) => idx !== i))
}

async function saveTable(rows: unknown[]) {
  if (!detail.value) return
  try {
    await api.patchEffect(detail.value.id, { field: 'effect_commands', value: rows })
    const id = detail.value.id
    detail.value = await api.effectDetail(id)
    ElMessage.success({ message: 'effect_commands 已更新', duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(async () => {
  await fetch()
  await loadRefs()
  const id = Number(route.query.id)
  if (!Number.isNaN(id) && id >= 0) {
    currentId.value = id
    detail.value = await api.effectDetail(id)
  }
})
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
.cmd { border: 1px solid #34373a; border-radius: 6px; padding: 8px 12px; margin-bottom: 8px; }
.cmd-head { display: flex; align-items: center; gap: 8px; }
.cmd-idx { color: #9a9a9a; font-size: 11px; }
.cmd-desc { color: #8ae0a8; font-size: 12px; flex: 1; }
.cmd-del { color: #9a9a9a; cursor: pointer; }
.cmd-params { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px 12px; margin-top: 8px; }
</style>
