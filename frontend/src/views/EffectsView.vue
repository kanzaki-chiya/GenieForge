<template>
  <div class="editor" @keydown.ctrl.67="cp.copy(currentId)" @keydown.ctrl.86="cp.paste(currentId)">
    <div class="body">
      <!-- 左栏：列表（宽 260px） -->
      <div class="list-panel">
        <div class="list-filter">
          <el-input
            v-model="q"
            placeholder="搜索效果名…"
            size="small"
            clearable
            @keyup.enter="fetch"
            @clear="fetch"
          />
          <div class="dim-selects">
            <span class="lbl">命令数</span>
            <el-input v-model="minCmds" placeholder="≥" size="small" clearable style="width: 64px" @keyup.enter="fetch" @clear="fetch" />
            <el-input v-model="maxCmds" placeholder="≤" size="small" clearable style="width: 64px" @keyup.enter="fetch" @clear="fetch" />
          </div>
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
            <el-table-column prop="commands" label="命令" width="50" align="right">
              <template #default="{ row }">
                <span class="mono" style="color: var(--muted)">{{ row.commands }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="list-foot">
          <el-pagination
            v-model:current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            size="small"
            @current-change="fetch"
          />
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
          <div class="grid1">
            <Field
              label="Effect Name"
              :modified="isFieldModified('name')"
              :original-value="getOriginalValue('name')"
              @revert="revertField('name')"
            >
              <FieldControl type="text" :model-value="detail.name" @commit="(v) => save('name', v)" />
            </Field>
          </div>

          <div class="group-title">效果命令（{{ detail.effect_commands.length }} 条）</div>
          <div v-for="(ec, i) in detail.effect_commands" :key="i" class="cmd">
            <div class="cmd-head">
              <span class="cmd-idx mono">#{{ i }}</span>
              <EnumSelect meta-name="effect-types" :model-value="ec.type" style="width: 200px" @change="(v) => onTypeChange(i, v)" />
              <span class="cmd-desc">{{ ec.description }}</span>
              <span class="cmd-del" @click="removeCmd(i)" title="删除命令">✕</span>
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
      <div class="main-panel empty-panel" v-else>
        <el-empty description="选择左侧效果查看详情" />
      </div>

      <!-- 右栏：关联面板（宽 260px） -->
      <RelationPanel table="effects" :entity-id="detail?.id ?? null" />
    </div>

    <!-- 改动转为补丁对话框 -->
    <PatchFromChangesDialog v-model="patchDialogVisible" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore, useHistoryStore, getEntityKey } from '../stores'
import { api } from '../api/client'
import EnumSelect from '../components/EnumSelect.vue'
import FieldControl from '../components/FieldControl.vue'
import RelationPanel from '../components/RelationPanel.vue'
import PatchFromChangesDialog from '../components/PatchFromChangesDialog.vue'
import Field from '../components/Field.vue'
import { useCopyPaste } from '../composables/useCopyPaste'

const cp = useCopyPaste('effects')
const appStore = useAppStore()
const historyStore = useHistoryStore()
const route = useRoute()
const router = useRouter()
const patchDialogVisible = ref(false)

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const q = ref('')
const detail = ref<any>(null)
const currentId = ref(-1)
const unitItems = ref<{ value: number; label: string }[]>([])
const techItems = ref<{ value: number; label: string }[]>([])
// 条件搜索：命令数区间
const minCmds = ref('')
const maxCmds = ref('')

function openCompare() {
  if (!detail.value) return
  router.push({ path: `/compare/effects/${detail.value.id}` })
}

function currentEntityKey(): string {
  return getEntityKey('effects', currentId.value)
}

function isRowModified(id: number): boolean {
  return historyStore.hasChanges('effects', id)
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
  const key = getEntityKey('effects', data.id)
  historyStore.recordBaseline(key, data, ['name'])
  historyStore.syncEntity(key, data)
}

async function fetch() {
  const params: Record<string, string | number> = { page: page.value, page_size: pageSize }
  if (q.value) params.q = q.value
  if (minCmds.value !== '') params.min_cmds = Number(minCmds.value)
  if (maxCmds.value !== '') params.max_cmds = Number(maxCmds.value)
  const r: any = await api.effects(params)
  rows.value = r.items
  total.value = r.total
}

async function loadRefs() {
  const [tn, un]: any[] = await Promise.all([api.techNames(), api.units(0, undefined, 1, 5000)])
  techItems.value = tn.items.map((x: any) => ({ value: x.id, label: x.name }))
  unitItems.value = (un.items || []).map((x: any) => ({ value: x.unit_id, label: x.display_name || x.name }))
}

async function selectById(id: number) {
  currentId.value = id
  const d = await api.effectDetail(id)
  registerDetailBaseline(d)
  detail.value = d
}

async function onSelect(row: any) {
  if (!row) return
  await selectById(row.id)
}

function paramsFor(type: number): { key: string; label: string; type: string }[] {
  if (type === 101) {
    return [
      { key: 'a', label: 'Tech', type: 'tech' },
      { key: 'b', label: 'Resource', type: 'resource' },
      { key: 'c', label: '0设/1改', type: 'number' },
      { key: 'd', label: 'Amount', type: 'number' },
    ]
  }
  if (type === 102) {
    return [
      { key: 'a', label: 'Tech', type: 'tech' },
      { key: 'b', label: '0/1', type: 'number' },
      { key: 'c', label: '0', type: 'number' },
      { key: 'd', label: '0', type: 'number' },
    ]
  }
  if (type === 103) {
    return [
      { key: 'a', label: 'Tech', type: 'tech' },
      { key: 'b', label: '0/1', type: 'number' },
      { key: 'c', label: '0', type: 'number' },
      { key: 'd', label: '0', type: 'number' },
    ]
  }
  if (type === 1 || type === 11 || type === 21) {
    return [
      { key: 'a', label: 'Unit', type: 'unit' },
      { key: 'b', label: 'Class', type: 'armor' },
      { key: 'c', label: 'Attribute', type: 'attribute' },
      { key: 'd', label: 'Amount', type: 'number' },
    ]
  }
  if (type === 4 || type === 5) {
    return [
      { key: 'a', label: 'Resource', type: 'resource' },
      { key: 'b', label: '0设/1改', type: 'number' },
      { key: 'c', label: 'Amount', type: 'number' },
      { key: 'd', label: '0', type: 'number' },
    ]
  }
  return [
    { key: 'a', label: 'A', type: 'number' },
    { key: 'b', label: 'B', type: 'number' },
    { key: 'c', label: 'C', type: 'number' },
    { key: 'd', label: 'D', type: 'number' },
  ]
}

async function save(field: string, value: unknown) {
  if (!detail.value) return
  try {
    await api.patchEffect(detail.value.id, { field, value })
    detail.value = { ...detail.value, [field]: value }
    historyStore.trackFieldChange(currentEntityKey(), field, value)
    await appStore.refreshDatInfo()
    appStore.bumpChangesRevision()
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
  detail.value = {
    ...detail.value,
    effect_commands: detail.value.effect_commands.map((c: any, idx: number) => (idx === i ? { ...c, type: v } : c)),
  }
}

async function addCmd() {
  const rowsData = [...detail.value.effect_commands, { type: 4, a: -1, b: -1, c: 0, d: 0 }]
  await saveTable(rowsData)
}

async function removeCmd(i: number) {
  await saveTable(detail.value.effect_commands.filter((_: unknown, idx: number) => idx !== i))
}

async function saveTable(rowsData: unknown[]) {
  if (!detail.value) return
  try {
    await api.patchEffect(detail.value.id, { field: 'effect_commands', value: rowsData })
    const id = detail.value.id
    detail.value = await api.effectDetail(id)
    await appStore.refreshDatInfo()
    appStore.bumpChangesRevision()
    ElMessage.success({ message: 'effect_commands 已更新', duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

// 监听 route.query.id 变化
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
  await loadRefs()
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

.dim-selects {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-top: 6px;
}

.lbl {
  color: var(--text-2, #9a9a9a);
  font-size: 12px;
}

.list-table-wrap {
  flex: 1;
  min-height: 0;
}

.list-foot {
  padding: 6px 8px;
  border-top: 1px solid var(--line);
  display: flex;
  justify-content: center;
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

.grid1 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.cmd {
  border: 1px solid var(--line);
  background: var(--raise);
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 8px;
}

.cmd-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cmd-idx {
  color: var(--muted);
  font-size: 11px;
}

.cmd-desc {
  color: #8ae0a8;
  font-size: 12px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cmd-del {
  color: var(--muted);
  cursor: pointer;
  padding: 2px 4px;
}

.cmd-del:hover {
  color: var(--red);
}

.cmd-params {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px 12px;
  margin-top: 8px;
}
</style>
