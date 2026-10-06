<template>
  <div class="editor" @keydown.ctrl.67="cp.copy(currentId)" @keydown.ctrl.86="cp.paste(currentId)">
    <div class="toolbar">
      <el-input
        v-model="q"
        placeholder="搜索文明名…"
        size="small"
        clearable
        style="width: 240px"
        @input="filterRows"
      />
      <span class="count">当前 #{{ currentId }} · 资源 {{ detail?.resources?.length || 0 }} 项</span>
      <el-button size="small" :disabled="!detail" @click="openCompare">对比</el-button>
      <el-button size="small" :disabled="!detail" @click="cp.copy(currentId)">复制</el-button>
      <el-button size="small" :disabled="!detail" @click="cp.paste(currentId)">粘贴</el-button>
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
          <el-table-column prop="id" label="ID" width="56" />
          <el-table-column prop="name" label="名称" />
        </el-table>
      </div>

      <div class="form" v-if="detail">
        <div class="form-scroll">
          <div class="group-title">基础信息</div>
          <div class="grid4">
            <Field label="Internal Name"><FieldControl type="text" :model-value="detail.name" @commit="(v) => save('name', v)" /></Field>
            <Field label="Player Type"><FieldControl type="number" :model-value="detail.player_type" @commit="(v) => save('player_type', v)" /></Field>
            <Field label="Icon Set"><FieldControl type="number" :model-value="detail.icon_set" @commit="(v) => save('icon_set', v)" /></Field>
          </div>
          <div class="grid2">
            <Field label="Technology Tree">
              <EnumSelect :preloaded="effectItems" :model-value="detail.tech_tree_id" @change="(v) => save('tech_tree_id', v)" />
            </Field>
            <Field label="Team Bonus">
              <EnumSelect :preloaded="effectItems" :model-value="detail.team_bonus_id" @change="(v) => save('team_bonus_id', v)" />
            </Field>
          </div>

          <div class="group-title">文明资源（601 项）</div>
          <el-table :data="filteredResources" size="small" border height="480">
            <el-table-column prop="index" label="#" width="64" />
            <el-table-column prop="name" label="资源" />
            <el-table-column label="值" width="140">
              <template #default="{ row }">
                <FieldControl
                  type="number"
                  :model-value="row.value"
                  @commit="(v) => save(`resources.${row.index}`, v)"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <div class="form" v-else>
        <el-empty description="选择左侧文明查看详情" />
      </div>
    </div>

    <DiffDrawer
      v-if="detail"
      v-model="diffVisible"
      :table="'civs'"
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
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '../stores'
import { api } from '../api/client'
import EnumSelect from '../components/EnumSelect.vue'
import FieldControl from '../components/FieldControl.vue'
import Field from '../components/Field.vue'
import DiffDrawer from '../components/DiffDrawer.vue'
import { useCompare } from '../composables/useCompare'
import { useCopyPaste } from '../composables/useCopyPaste'

const compare = useCompare()
const cp = useCopyPaste('civs')
const appStore = useAppStore()
const rows = ref<any[]>([])
const allRows = ref<any[]>([])
const detail = ref<any>(null)
const currentId = ref(-1)
const q = ref('')
const effectItems = ref<{ value: number; label: string }[]>([])
const diffVisible = ref(false)

const scalarFields = [
  { key: 'name', label: '名称' },
  { key: 'player_type', label: '玩家类型' },
  { key: 'icon_set', label: '图标集' },
  { key: 'tech_tree_id', label: '科技树' },
  { key: 'team_bonus_id', label: '团队加成' }
]
const listFields: { key: string; label: string }[] = []

const filteredResources = computed(() => detail.value?.resources || [])

function openCompare() {
  diffVisible.value = true
}

function onApplyDiff(p: { field: string; value: unknown; list: boolean }) {
  save(p.field, p.value)
}

async function fetch() {
  const r: any = await api.civs()
  allRows.value = r.items
  rows.value = r.items
}

function filterRows() {
  const k = q.value.toLowerCase()
  rows.value = k ? allRows.value.filter((c) => c.name.toLowerCase().includes(k)) : allRows.value
}

async function onSelect(row: any) {
  if (!row) return
  currentId.value = row.id
  detail.value = await api.civDetail(row.id)
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
    await api.patchCiv(detail.value.id, { field, value })
    setDetail(field, value)
    await appStore.refreshDatInfo()
    ElMessage.success({ message: `${field} 已保存`, duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(async () => {
  await fetch()
  const en: any = await api.effectNames()
  effectItems.value = en.items.map((x: any) => ({ value: x.id, label: x.name }))
})
</script>

<style scoped>
.editor { height: 100%; display: flex; flex-direction: column; }
.toolbar { padding: 8px 12px; border-bottom: 1px solid #34373a; display: flex; align-items: center; gap: 8px; }
.count { color: #9a9a9a; font-size: 12px; }
.body { flex: 1; display: flex; min-height: 0; }
.list { width: 260px; border-right: 1px solid #34373a; display: flex; flex-direction: column; }
.form { flex: 1; min-width: 0; display: flex; }
.form-scroll { flex: 1; overflow: auto; padding: 12px 16px; }
.group-title { color: #e6e6e6; font-weight: 600; font-size: 13px; border-top: 1px solid #34373a; margin: 14px 0 8px; padding-top: 10px; }
.group-title:first-child { border-top: none; margin-top: 0; padding-top: 0; }
.grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px 12px; }
.grid2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px 12px; margin-top: 8px; }
</style>
