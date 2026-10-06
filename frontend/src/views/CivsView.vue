<template>
  <div class="editor" @keydown.ctrl.67="cp.copy(currentId)" @keydown.ctrl.86="cp.paste(currentId)">
    <div class="body">
      <!-- 左栏：列表（宽 260px） -->
      <div class="list-panel">
        <div class="list-filter">
          <el-input
            v-model="q"
            placeholder="搜索文明名…"
            size="small"
            clearable
            @input="filterRows"
          />
        </div>
        <div class="list-table-wrap">
          <el-table
            :data="rows"
            size="small"
            highlight-current-row
            height="100%"
            class="compact-table"
            @current-change="onSelect"
          >
            <el-table-column prop="id" label="ID" width="52">
              <template #default="{ row }">
                <span class="mono" :class="{ 'gold-text': isRowModified(row.id) }">{{ row.id }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="名称" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="row-name-cell">
                  <span>{{ row.name }}</span>
                  <span v-if="isRowModified(row.id)" class="row-dot" title="本次已修改"></span>
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="list-foot">
          <span class="foot-text">共 {{ rows.length }} 项</span>
        </div>
      </div>

      <!-- 中间：字段区 -->
      <div class="main-panel" v-if="detail">
        <!-- 头部实体条目信息与操作 -->
        <div class="entity-header">
          <div class="entity-meta">
            <span class="mono entity-id">#{{ detail.id }}</span>
            <h3 class="entity-title">{{ detail.name }}</h3>
          </div>
          <div class="entity-actions">
            <el-button size="small" @click="openCompare">对比…</el-button>
            <el-button size="small" @click="cp.copy(currentId)">复制</el-button>
            <el-button size="small" @click="cp.paste(currentId)">粘贴</el-button>
            <el-button size="small" @click="patchDialogVisible = true">改动转为补丁</el-button>
          </div>
        </div>

        <div class="form-scroll">
          <div class="group-title">基础信息</div>
          <div class="grid4">
            <Field
              label="Internal Name"
              :modified="isFieldModified('name')"
              :original-value="getOriginalValue('name')"
              @revert="revertField('name')"
            >
              <FieldControl type="text" :model-value="detail.name" @commit="(v) => save('name', v)" />
            </Field>
            <Field
              label="Player Type"
              :modified="isFieldModified('player_type')"
              :original-value="getOriginalValue('player_type')"
              @revert="revertField('player_type')"
            >
              <FieldControl type="number" :model-value="detail.player_type" @commit="(v) => save('player_type', v)" />
            </Field>
            <Field
              label="Icon Set"
              :modified="isFieldModified('icon_set')"
              :original-value="getOriginalValue('icon_set')"
              @revert="revertField('icon_set')"
            >
              <FieldControl type="number" :model-value="detail.icon_set" @commit="(v) => save('icon_set', v)" />
            </Field>
          </div>
          <div class="grid2">
            <Field
              label="Technology Tree"
              :modified="isFieldModified('tech_tree_id')"
              :original-value="getOriginalValue('tech_tree_id')"
              @revert="revertField('tech_tree_id')"
            >
              <EnumSelect :preloaded="effectItems" :model-value="detail.tech_tree_id" @change="(v) => save('tech_tree_id', v)" />
            </Field>
            <Field
              label="Team Bonus"
              :modified="isFieldModified('team_bonus_id')"
              :original-value="getOriginalValue('team_bonus_id')"
              @revert="revertField('team_bonus_id')"
            >
              <EnumSelect :preloaded="effectItems" :model-value="detail.team_bonus_id" @change="(v) => save('team_bonus_id', v)" />
            </Field>
          </div>

          <div class="group-title">文明资源（{{ detail?.resources?.length || 0 }} 项）</div>
          <div class="table-card">
            <el-table :data="filteredResources" size="small" border height="420">
              <el-table-column prop="index" label="#" width="56">
                <template #default="{ row }">
                  <span class="mono" :class="{ 'gold-text': isFieldModified(`resources.${row.index}`) }">{{ row.index }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="name" label="资源" />
              <el-table-column label="值" width="160">
                <template #default="{ row }">
                  <div class="resource-cell">
                    <FieldControl
                      type="number"
                      :model-value="row.value"
                      @commit="(v) => save(`resources.${row.index}`, v)"
                    />
                    <button
                      v-if="isFieldModified(`resources.${row.index}`)"
                      type="button"
                      class="btn-sm-revert"
                      title="还原"
                      @click="revertField(`resources.${row.index}`)"
                    >
                      还原
                    </button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
      <div class="main-panel empty-panel" v-else>
        <el-empty description="选择左侧文明查看详情" />
      </div>

      <!-- 右栏：关联面板（宽 260px） -->
      <RelationPanel table="civs" :entity-id="detail?.id ?? null" />
    </div>

    <!-- 对比抽屉 -->
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

    <!-- 改动转为补丁对话框 -->
    <PatchFromChangesDialog v-model="patchDialogVisible" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore, useHistoryStore, getEntityKey } from '../stores'
import { api } from '../api/client'
import EnumSelect from '../components/EnumSelect.vue'
import FieldControl from '../components/FieldControl.vue'
import Field from '../components/Field.vue'
import DiffDrawer from '../components/DiffDrawer.vue'
import RelationPanel from '../components/RelationPanel.vue'
import PatchFromChangesDialog from '../components/PatchFromChangesDialog.vue'
import { useCopyPaste } from '../composables/useCopyPaste'

const cp = useCopyPaste('civs')
const appStore = useAppStore()
const historyStore = useHistoryStore()
const route = useRoute()
const patchDialogVisible = ref(false)

const rows = ref<any[]>([])
const allRows = ref<any[]>([])
const q = ref('')
const detail = ref<any>(null)
const currentId = ref(-1)
const effectItems = ref<{ value: number; label: string }[]>([])
const diffVisible = ref(false)

const scalarFields = [
  { key: 'name', label: '名称' },
  { key: 'player_type', label: 'Player Type' },
  { key: 'icon_set', label: 'Icon Set' },
  { key: 'tech_tree_id', label: '科技树' },
  { key: 'team_bonus_id', label: '团队加成' },
]
const listFields = [{ key: 'resources', label: '资源' }]

function openCompare() {
  diffVisible.value = true
}

function currentEntityKey(): string {
  return getEntityKey('civs', currentId.value)
}

function isRowModified(id: number): boolean {
  return historyStore.hasChanges('civs', id)
}

function isFieldModified(fieldPath: string): boolean {
  return historyStore.isFieldModified(currentEntityKey(), fieldPath)
}

function getOriginalValue(fieldPath: string): unknown {
  return historyStore.getOriginalValue(currentEntityKey(), fieldPath)
}

async function revertField(fieldPath: string) {
  const orig = getOriginalValue(fieldPath)
  if (orig === undefined) return
  await save(fieldPath, orig)
}

function registerDetailBaseline(data: any) {
  const key = getEntityKey('civs', data.id)
  historyStore.recordBaseline(key, data, ['name', 'player_type', 'icon_set', 'tech_tree_id', 'team_bonus_id'])
  if (Array.isArray(data.resources)) {
    data.resources.forEach((val: unknown, i: number) => {
      historyStore.ensureFieldBaseline(key, `resources.${i}`, val)
    })
  }
  historyStore.syncEntity(key, data)
}
const filteredResources = computed(() => {
  if (!detail.value || !detail.value.resources) return []
  return detail.value.resources.map((val: number, i: number) => ({
    index: i,
    name: `资源 #${i}`,
    value: val,
  }))
})

function filterRows() {
  const k = q.value.toLowerCase()
  rows.value = k ? allRows.value.filter((c) => c.name.toLowerCase().includes(k)) : allRows.value
}

async function fetch() {
  const r: any = await api.civs()
  allRows.value = r.items
  rows.value = r.items
}

async function selectById(id: number) {
  currentId.value = id
  const d = await api.civDetail(id)
  registerDetailBaseline(d)
  detail.value = d
}

async function onSelect(row: any) {
  if (!row) return
  await selectById(row.id)
}

function setDetail(field: string, value: unknown) {
  if (field.startsWith('resources.')) {
    const idx = parseInt(field.split('.')[1], 10)
    detail.value.resources[idx] = value
    return
  }
  detail.value[field] = value
}

async function save(field: string, value: unknown) {
  if (!detail.value) return
  try {
    await api.patchCiv(detail.value.id, { field, value })
    setDetail(field, value)
    historyStore.trackFieldChange(currentEntityKey(), field, value)
    await appStore.refreshDatInfo()
    appStore.bumpChangesRevision()
    ElMessage.success({ message: `${field} 已保存`, duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

function onApplyDiff(p: { field: string; value: unknown; list: boolean }) {
  if (p.list) {
    saveTable(p.field, p.value as unknown[])
  } else {
    save(p.field, p.value)
  }
}

async function saveTable(field: string, rowsData: unknown[]) {
  if (!detail.value) return
  try {
    await api.patchCiv(detail.value.id, { field, value: rowsData })
    detail.value[field] = rowsData
    await appStore.refreshDatInfo()
    appStore.bumpChangesRevision()
    ElMessage.success({ message: `${field} 已更新`, duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

// 监听 query.id
watch(
  () => route.query.id,
  async (newId) => {
    if (newId != null && newId !== '') {
      const id = Number(newId)
      if (!Number.isNaN(id) && id >= 0 && id !== currentId.value) {
        await selectById(id)
      }
    }
  }
)

// 撤销、重做、应用补丁后刷新当前选中条目详情和列表当前页
watch(
  () => appStore.dataRevision,
  async () => {
    await fetch()
    if (currentId.value >= 0) {
      await selectById(currentId.value)
    }
  }
)
onMounted(async () => {
  await fetch()
  const en: any = await api.effectNames()
  effectItems.value = en.items.map((x: any) => ({ value: x.id, label: x.name }))
  const qId = Number(route.query.id)
  if (!Number.isNaN(qId) && qId >= 0) {
    await selectById(qId)
  }
})
</script>

<style scoped>
.editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.body {
  flex: 1;
  display: flex;
  min-height: 0;
  height: 100%;
}

/* 左侧列表：260px */
.list-panel {
  width: 260px;
  flex: 0 0 260px;
  border-right: 1px solid var(--line);
  background: var(--panel);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.list-filter {
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
}

.list-table-wrap {
  flex: 1;
  min-height: 0;
}

.list-foot {
  padding: 6px 12px;
  border-top: 1px solid var(--line);
  font-size: 11px;
  color: var(--muted);
}

.row-name-cell {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
}

.row-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gold);
  flex-shrink: 0;
  box-shadow: 0 0 4px rgba(224, 164, 58, 0.6);
}

.gold-text {
  color: var(--gold);
  font-weight: 500;
}

/* 中间主字段区 */
.main-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: var(--app);
  height: 100%;
}

.empty-panel {
  align-items: center;
  justify-content: center;
}

.entity-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--line);
  background: #181b20;
  gap: 12px;
}

.entity-meta {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.entity-id {
  color: var(--muted);
  font-size: 14px;
}

.entity-title {
  margin: 0;
  font-size: 16px;
  color: var(--fg);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.entity-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.form-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 14px 18px 30px;
}

.group-title {
  color: var(--muted);
  font-weight: 600;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-top: 1px solid var(--line);
  margin: 18px 0 10px;
  padding-top: 10px;
}

.group-title:first-child {
  border-top: none;
  margin-top: 0;
  padding-top: 0;
}

.grid4 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px 12px;
}

.grid2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 12px;
  margin-top: 8px;
}

.table-card {
  border: 1px solid var(--line);
  border-radius: 6px;
  overflow: hidden;
}

.resource-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-sm-revert {
  font: inherit;
  font-size: 10px;
  color: var(--fg);
  background: #252931;
  border: 1px solid #353a44;
  border-radius: 3px;
  padding: 0 4px;
  height: 20px;
  cursor: pointer;
  white-space: nowrap;
}

.btn-sm-revert:hover {
  border-color: var(--gold);
  color: var(--gold);
}
</style>
