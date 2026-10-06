<template>
  <el-dialog
    v-model="visible"
    title="改动转为补丁"
    width="680px"
    class="patch-dialog"
    destroy-on-close
    :append-to-body="true"
  >
    <div v-loading="loading" class="dialog-body">
      <!-- 提示 -->
      <div class="desc-hint">
        将当前撤销栈中的修改记录生成语义补丁 YAML，基于名称与签名精确定位。
      </div>

      <!-- 可转换修改列表 -->
      <div class="section-box">
        <div class="section-head">
          <div class="head-left">
            <span class="head-title">可转换修改 ({{ convertibleChanges.length }})</span>
            <span class="head-sub">已选 {{ selectedIndices.length }} 项</span>
          </div>
          <el-checkbox
            v-if="convertibleChanges.length > 0"
            :model-value="isAllSelected"
            :indeterminate="isIndeterminate"
            @change="handleSelectAll"
          >
            全选
          </el-checkbox>
        </div>

        <div v-if="convertibleChanges.length === 0" class="empty-hint">
          当前没有可转换的修改记录
        </div>
        <div v-else class="changes-scroll">
          <el-checkbox-group v-model="selectedIndices" @change="onSelectionChange">
            <div
              v-for="ch in convertibleChanges"
              :key="`conv-${ch.index}`"
              class="change-item"
            >
              <el-checkbox :value="ch.index" class="item-checkbox">
                <span class="ref-badge">{{ getTableLabel(ch.table) }}</span>
                <span class="item-name">{{ ch.current_name || ch.name || '未命名' }}</span>
                <span class="item-id mono">#{{ ch.id }}</span>
                <span class="item-field mono">{{ ch.field }}</span>
                <span class="item-diff mono">
                  <span class="val-old">{{ formatValue(ch.old) }}</span>
                  <span class="val-arrow">→</span>
                  <span class="val-new">{{ formatValue(ch.new) }}</span>
                </span>
              </el-checkbox>
            </div>
          </el-checkbox-group>
        </div>
      </div>

      <!-- 无法转换记录 -->
      <div v-if="skippedChanges.length > 0" class="section-box skipped-box">
        <div class="section-head">
          <span class="head-title head-skipped">
            无法转换的修改 ({{ skippedChanges.length }})
          </span>
        </div>
        <div class="skipped-list">
          <div
            v-for="ch in skippedChanges"
            :key="`skip-${ch.index}`"
            class="skipped-item"
          >
            <div class="skipped-left">
              <span class="ref-badge op-badge">{{ ch.table ? getTableLabel(ch.table) : '操作' }}</span>
              <span class="skipped-desc mono">
                {{ ch.table ? `${ch.current_name || ch.name || '未命名'} #${ch.id}: ${ch.field}` : ch.desc }}
              </span>
            </div>
            <span class="skipped-reason">{{ ch.reason }}</span>
          </div>
        </div>
      </div>

      <!-- YAML 预览 -->
      <div class="section-box">
        <div class="section-head">
          <span class="head-title">补丁预览 (YAML)</span>
          <span class="preview-count mono">{{ stepCount }} 个步骤</span>
        </div>
        <div class="yaml-preview mono">{{ previewYaml || '# 没有选中的步骤' }}</div>
      </div>

      <!-- 补丁命名与保存 -->
      <div class="name-box">
        <label class="name-label">补丁名称</label>
        <el-input
          v-model="patchName"
          placeholder="例如：my_balance_patch"
          clearable
          class="name-input"
          @keydown.enter="handleSave"
        >
          <template #append>.yaml</template>
        </el-input>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="saving"
          :disabled="stepCount === 0 || !patchName.trim()"
          @click="handleSave"
        >
          保存补丁
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, h, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import { api } from '../api/client'

export interface ChangeItem {
  index: number
  table?: string
  id?: number
  civ?: number
  field?: string
  old?: any
  new?: any
  name?: string
  current_name?: string
  desc?: string
  convertible: boolean
  reason?: string
}

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
}>()

const router = useRouter()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const loading = ref(false)
const saving = ref(false)
const allChanges = ref<ChangeItem[]>([])
const selectedIndices = ref<number[]>([])
const patchName = ref('')
const previewYaml = ref('')
const stepCount = ref(0)

const TABLE_MAP: Record<string, string> = {
  techs: '科技',
  effects: '效果',
  civs: '文明',
  units: '单位',
  unit_headers: '单位',
}

function getTableLabel(t?: string): string {
  if (!t) return '条目'
  return TABLE_MAP[t] || t
}

const convertibleChanges = computed(() =>
  allChanges.value.filter((c) => c.convertible)
)

const skippedChanges = computed(() =>
  allChanges.value.filter((c) => !c.convertible)
)

const isAllSelected = computed(
  () =>
    convertibleChanges.value.length > 0 &&
    selectedIndices.value.length === convertibleChanges.value.length
)

const isIndeterminate = computed(
  () =>
    selectedIndices.value.length > 0 &&
    selectedIndices.value.length < convertibleChanges.value.length
)

function formatValue(v: any): string {
  if (v === null || v === undefined) return 'null'
  if (typeof v === 'object') {
    try {
      return JSON.stringify(v)
    } catch {
      return String(v)
    }
  }
  return String(v)
}

function handleSelectAll(val: boolean | string | number) {
  if (val) {
    selectedIndices.value = convertibleChanges.value.map((c) => c.index)
  } else {
    selectedIndices.value = []
  }
  updatePreview()
}

function onSelectionChange() {
  updatePreview()
}

async function updatePreview() {
  try {
    const res = await api.patchFromChanges(selectedIndices.value)
    previewYaml.value = res.yaml || ''
    stepCount.value = res.count || 0
  } catch (e: any) {
    previewYaml.value = `# 预览生成失败: ${e.message}`
    stepCount.value = 0
  }
}

async function loadData() {
  loading.value = true
  try {
    const res = await api.datChanges().catch(() => ({ changes: [] }))
    allChanges.value = res.changes || []
    // 默认全选所有可转换的修改
    selectedIndices.value = convertibleChanges.value.map((c) => c.index)
    patchName.value = ''
    await updatePreview()
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  const name = patchName.value.trim()
  if (!name) {
    ElMessage.warning('请输入补丁名称')
    return
  }
  const safe = name.replace(/[^a-zA-Z0-9_-]/g, '')
  if (!safe) {
    ElMessage.warning('补丁名称仅支持英文、数字、下划线和连字符')
    return
  }
  if (!previewYaml.value) {
    ElMessage.warning('补丁内容为空')
    return
  }

  saving.value = true
  try {
    await api.patchSave(safe, previewYaml.value)
    visible.value = false
    ElNotification.success({
      title: '补丁已保存',
      message: h('div', { style: 'font-size: 13px; line-height: 1.6;' }, [
        h('div', `补丁 "${safe}.yaml" 保存成功（共 ${stepCount.value} 个步骤）。`),
        h(
          'a',
          {
            style: 'color: var(--gold); text-decoration: underline; cursor: pointer; display: inline-block; margin-top: 6px;',
            onClick: () => {
              router.push('/patch')
            },
          },
          '前往补丁管理页查看 →'
        ),
      ]),
      duration: 6000,
    })
  } catch (e: any) {
    ElMessage.error(`保存失败: ${e.message}`)
  } finally {
    saving.value = false
  }
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      loadData()
    }
  }
)
</script>

<style scoped>
.dialog-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.desc-hint {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}

.section-box {
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--raise);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.head-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--fg);
}

.head-sub {
  font-size: 11px;
  color: var(--muted);
  margin-left: 8px;
}

.head-skipped {
  color: var(--red, #ec7a88);
}

.empty-hint {
  font-size: 12px;
  color: var(--muted);
  padding: 6px 0;
}

.changes-scroll {
  max-height: 160px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.change-item {
  padding: 4px 6px;
  border-radius: 4px;
  background: var(--app);
  display: flex;
  align-items: center;
}

.change-item:hover {
  background: #252a32;
}

.item-checkbox {
  width: 100%;
  display: flex;
  align-items: center;
}

:deep(.el-checkbox__label) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ref-badge {
  font-size: 10px;
  color: var(--gold);
  background: var(--gold-bg);
  border: 1px solid var(--gold-edge);
  border-radius: 3px;
  padding: 0 4px;
  line-height: 1.4;
  flex-shrink: 0;
}

.op-badge {
  background: #282d35;
  color: var(--muted);
  border-color: #3f4652;
}

.item-name {
  color: var(--fg);
  font-weight: 500;
}

.item-id {
  color: var(--muted);
  font-size: 11px;
}

.item-field {
  color: var(--fg-2);
  margin-left: 4px;
}

.item-diff {
  margin-left: auto;
  padding-left: 8px;
  font-size: 11px;
}

.val-old {
  color: var(--muted);
}

.val-arrow {
  color: var(--muted);
  margin: 0 3px;
}

.val-new {
  color: var(--gold);
}

/* 无法转换区 */
.skipped-box {
  border-color: #3a2528;
  background: #181416;
}

.skipped-list {
  max-height: 100px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.skipped-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  padding: 3px 6px;
  background: var(--app);
  border-radius: 4px;
}

.skipped-left {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  overflow: hidden;
}

.skipped-desc {
  color: var(--fg-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.skipped-reason {
  color: var(--red, #ec7a88);
  font-size: 11px;
  flex-shrink: 0;
}

/* YAML 预览 */
.yaml-preview {
  background: var(--app);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 8px 10px;
  max-height: 140px;
  overflow-y: auto;
  font-size: 11px;
  color: var(--fg-2);
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.5;
}

.preview-count {
  font-size: 11px;
  color: var(--gold);
}

/* 命名 */
.name-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.name-label {
  font-size: 12px;
  color: var(--fg-2);
  font-weight: 500;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
