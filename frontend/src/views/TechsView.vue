<template>
  <div class="editor">
    <div class="toolbar">
      <el-input
        v-model="q"
        placeholder="搜索科技名…"
        size="small"
        clearable
        style="width: 280px"
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
          <el-table-column prop="display_name" label="显示名" width="120" />
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
          <div class="grid4">
            <Field label="Internal Name">
              <FieldControl type="text" :model-value="detail.name" @commit="(v) => save('name', v)" />
            </Field>
            <Field label="Type">
              <EnumSelect meta-name="tech-types" :model-value="detail.type" @change="(v) => save('type', v)" />
            </Field>
            <Field label="Civilization">
              <EnumSelect :preloaded="civItems" :model-value="detail.civ" @change="(v) => save('civ', v)" />
            </Field>
            <Field label="Repeatable">
              <el-checkbox :model-value="detail.repeatable === 1" @change="(v: boolean | string | number) => save('repeatable', v ? 1 : 0)" />
            </Field>
          </div>
          <div class="grid4">
            <Field label="Effect">
              <EnumSelect :preloaded="effectItems" :model-value="detail.effect_id" @change="(v) => save('effect_id', v)" />
            </Field>
            <Field label="Full Tech Mode">
              <FieldControl type="number" :model-value="detail.full_tech_mode" @commit="(v) => save('full_tech_mode', v)" />
            </Field>
            <Field label="Icon">
              <FieldControl type="number" :model-value="detail.icon_id" @commit="(v) => save('icon_id', v)" />
            </Field>
          </div>

          <div class="group-title">语言</div>
          <div class="grid4">
            <Field label="Lang Name"><FieldControl type="number" :model-value="detail.language_dll_name" @commit="(v) => save('language_dll_name', v)" /></Field>
            <Field label="Description"><FieldControl type="number" :model-value="detail.language_dll_description" @commit="(v) => save('language_dll_description', v)" /></Field>
            <Field label="Help"><FieldControl type="number" :model-value="detail.language_dll_help" @commit="(v) => save('language_dll_help', v)" /></Field>
            <Field label="Tech Tree"><FieldControl type="number" :model-value="detail.language_dll_tech_tree" @commit="(v) => save('language_dll_tech_tree', v)" /></Field>
          </div>

          <div class="group-title">前置科技</div>
          <div class="grid6">
            <Field v-for="(rt, i) in detail.required_techs" :key="i" :label="`前置 ${i}`">
              <EnumSelect :preloaded="techItems" :model-value="rt" @change="(v) => save(`required_techs.${i}`, v)" />
            </Field>
          </div>

          <div class="group-title">费用</div>
          <div class="costs">
            <div v-for="(rc, i) in detail.resource_costs" :key="i" class="cost-row">
              <EnumSelect meta-name="resource-types" :model-value="rc.type" @change="(v) => save(`resource_costs.${i}.type`, v)" />
              <FieldControl type="number" :model-value="rc.amount" @commit="(v) => save(`resource_costs.${i}.amount`, v)" />
            </div>
          </div>

          <div class="group-title">研究位置</div>
          <SubTable
            :columns="researchColumns"
            :model-value="detail.research_locations"
            :template="researchTemplate"
            @update-row="onResearchChange"
          />
        </div>
      </div>
      <div class="form" v-else>
        <el-empty description="选择左侧科技查看详情" />
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

const techItems = ref<{ value: number; label: string }[]>([])
const effectItems = ref<{ value: number; label: string }[]>([])
const civItems = ref<{ value: number; label: string }[]>([])

const researchColumns = [
  { key: 'location_id', label: '位置', type: 'number', width: 90 },
  { key: 'research_time', label: '研究时间', type: 'number', width: 90 },
  { key: 'button_id', label: '按钮 ID', type: 'number', width: 90 },
  { key: 'hot_key_id', label: '快捷键', type: 'number', width: 90 }
]
const researchTemplate = () => ({ location_id: 0, research_time: 0, button_id: 0, hot_key_id: 0 })

async function fetch() {
  const r: any = await api.techs({ page: page.value, page_size: pageSize, q: q.value })
  rows.value = r.items
  total.value = r.total
}

async function loadRefs() {
  const [tn, en, cv]: any[] = await Promise.all([api.techNames(), api.effectNames(), api.civs()])
  techItems.value = tn.items.map((x: any) => ({ value: x.id, label: x.name }))
  effectItems.value = en.items.map((x: any) => ({ value: x.id, label: x.name }))
  civItems.value = cv.items.map((x: any) => ({ value: x.id, label: x.name }))
}

async function onSelect(row: any) {
  if (!row) return
  currentId.value = row.id
  detail.value = await api.techDetail(row.id)
}

function setDetail(dotted: string, value: unknown) {
  const parts = dotted.split('.')
  let cur: any = detail.value
  for (let i = 0; i < parts.length - 1; i++) {
    cur = cur[parts[i]]
  }
  cur[parts[parts.length - 1]] = value
}

async function save(field: string, value: unknown) {
  if (!detail.value) return
  try {
    await api.patchTech(detail.value.id, { field, value })
    setDetail(field, value)
    ElMessage.success({ message: `${field} 已保存`, duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

function onResearchChange(p: { rowIndex: number; colKey: string }) {
  save(`research_locations.${p.rowIndex}.${p.colKey}`, detail.value.research_locations[p.rowIndex][p.colKey])
}

onMounted(() => {
  fetch()
  loadRefs()
})
</script>

<style scoped>
.editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.toolbar {
  padding: 8px 12px;
  border-bottom: 1px solid #34373a;
  display: flex;
  align-items: center;
  gap: 8px;
}
.count {
  color: #9a9a9a;
  font-size: 12px;
}
.body {
  flex: 1;
  display: flex;
  min-height: 0;
}
.list {
  width: 320px;
  border-right: 1px solid #34373a;
  display: flex;
  flex-direction: column;
}
.form {
  flex: 1;
  min-width: 0;
  display: flex;
}
.form-scroll {
  flex: 1;
  overflow: auto;
  padding: 12px 16px;
}
.group-title {
  color: #e6e6e6;
  font-weight: 600;
  font-size: 13px;
  border-top: 1px solid #34373a;
  margin: 14px 0 8px;
  padding-top: 10px;
}
.group-title:first-child {
  border-top: none;
  margin-top: 0;
  padding-top: 0;
}
.grid4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px 12px;
}
.grid6 {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px 10px;
}
.costs {
  display: flex;
  gap: 12px;
}
.cost-row {
  flex: 1;
  display: flex;
  gap: 6px;
}
</style>
