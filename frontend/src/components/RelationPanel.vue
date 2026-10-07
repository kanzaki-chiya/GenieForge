<template>
  <aside class="side-panel" aria-label="关联面板">
    <div class="panel-inner">
      <!-- 引用了 -->
      <section class="section">
        <h4 class="section-title">引用了 ({{ forwardRefs.length }})</h4>
        <div v-if="loading" class="empty-hint">加载中…</div>
        <div v-else-if="forwardRefs.length === 0" class="empty-hint">无</div>
        <div v-else class="ref-list">
          <div
            v-for="(refItem, idx) in forwardRefs"
            :key="`fwd-${idx}`"
            class="ref-card"
            @click="navigateTo(refItem)"
          >
            <div class="card-header">
              <span class="ref-badge">{{ getTableLabel(refItem.table) }}</span>
              <span class="ref-name">{{ refItem.name || '未命名' }}</span>
              <span class="ref-id mono">#{{ refItem.id }}</span>
            </div>
            <div v-if="refItem.field" class="card-field mono">
              {{ refItem.field }}
            </div>
          </div>
        </div>
      </section>

      <!-- 被引用 -->
      <section class="section">
        <h4 class="section-title">被引用 ({{ reverseRefs.length }})</h4>
        <div v-if="loading" class="empty-hint">加载中…</div>
        <div v-else-if="reverseRefs.length === 0" class="empty-hint">无</div>
        <div v-else class="ref-list">
          <div
            v-for="(refItem, idx) in reverseRefs"
            :key="`rev-${idx}`"
            class="ref-row"
            @click="navigateTo(refItem)"
          >
            <div class="row-left">
              <span class="ref-badge">{{ getTableLabel(refItem.table) }}</span>
              <span class="ref-name">{{ refItem.name || '未命名' }}</span>
              <span class="ref-id mono">#{{ refItem.id }}</span>
            </div>
            <div v-if="refItem.field" class="row-field mono">
              {{ refItem.field }}
            </div>
          </div>
        </div>
      </section>

      <!-- 本次修改 -->
      <section class="section changes-section">
        <h4 class="section-title">本次修改 ({{ changesList.length }})</h4>
        <div v-if="changesLoading" class="empty-hint">加载中…</div>
        <div v-else-if="changesList.length === 0" class="empty-hint">无</div>
        <div v-else class="change-list">
          <div
            v-for="ch in changesList"
            :key="`ch-${ch.index}`"
            class="change-card"
            :class="{ inconvertible: !ch.convertible }"
            :title="formatChangeTooltip(ch)"
            @click="jumpToChange(ch)"
          >
            <template v-if="ch.table">
              <div class="card-header">
                <span class="ref-badge">{{ getTableLabel(ch.table) }}</span>
                <span class="change-name">{{ ch.current_name || ch.name || '未命名' }}</span>
                <span class="change-id mono">#{{ ch.id }}<template v-if="ch.civ != null"> (C{{ ch.civ }})</template></span>
              </div>
              <div class="card-field mono">{{ ch.field }}</div>
              <div class="change-values mono">
                <span class="val-old">{{ formatValue(ch.old) }}</span>
                <span class="val-arrow">→</span>
                <span class="val-new">{{ formatValue(ch.new) }}</span>
              </div>
            </template>
            <template v-else>
              <div class="card-header">
                <span class="ref-badge op-badge">操作</span>
                <span class="change-desc mono">{{ ch.desc }}</span>
              </div>
            </template>
            <div v-if="!ch.convertible && ch.reason" class="change-reason">
              {{ ch.reason }}
            </div>
          </div>
        </div>
      </section>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores'
import { api } from '../api/client'

export interface RefItem {
  table: string
  id: number
  name: string | null
  field: string
}

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
  table: 'techs' | 'unit_headers' | 'civs' | 'effects' | string
  entityId: number | null | undefined
}>()

const router = useRouter()
const appStore = useAppStore()
const changesList = ref<ChangeItem[]>([])
const changesLoading = ref(false)

const forwardRefs = ref<RefItem[]>([])
const reverseRefs = ref<RefItem[]>([])
const loading = ref(false)

const TABLE_MAP: Record<string, string> = {
  techs: '科技',
  effects: '效果',
  civs: '文明',
  unit_headers: '单位',
  units: '单位',
}

function getTableLabel(t: string): string {
  return TABLE_MAP[t] || t
}

async function loadRefs() {
  if (props.entityId == null || props.entityId < 0) {
    forwardRefs.value = []
    reverseRefs.value = []
    return
  }

  loading.value = true
  try {
    const [fwd, rev]: any = await Promise.all([
      api.refsForward(props.table, props.entityId).catch(() => ({ refs: [] })),
      api.refsReverse(props.table, props.entityId).catch(() => ({ refs: [] })),
    ])
    forwardRefs.value = fwd.refs || []
    reverseRefs.value = rev.refs || []
  } finally {
    loading.value = false
  }
}

function navigateTo(item: RefItem) {
  const targetRoute = item.table === 'unit_headers' ? '/units' : `/${item.table}`
  router.push({
    path: targetRoute,
    query: { id: String(item.id) },
  })
}

async function loadChanges() {
  changesLoading.value = true
  try {
    const res = await api.datChanges().catch(() => ({ changes: [] }))
    changesList.value = res.changes || []
  } finally {
    changesLoading.value = false
  }
}

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

function formatChangeTooltip(ch: ChangeItem): string {
  if (!ch.table) {
    return `${ch.desc || '操作'}\n原因: ${ch.reason || '不可转换'}`
  }
  const lines = [
    `表: ${getTableLabel(ch.table)}`,
    `条目: ${ch.current_name || ch.name || '未命名'} #${ch.id}${ch.civ != null ? ` (Civ ${ch.civ})` : ''}`,
    `字段: ${ch.field}`,
    `旧值: ${formatValue(ch.old)}`,
    `新值: ${formatValue(ch.new)}`,
  ]
  if (!ch.convertible && ch.reason) {
    lines.push(`无法转为补丁: ${ch.reason}`)
  }
  return lines.join('\n')
}

function jumpToChange(ch: ChangeItem) {
  if (!ch.table) return
  const targetRoute = ch.table === 'units' ? '/units' : `/${ch.table}`
  const query: Record<string, string> = { id: String(ch.id) }
  if (ch.civ != null) {
    query.civ = String(ch.civ)
  }
  router.push({
    path: targetRoute,
    query,
  })
}

watch(
  () => [props.table, props.entityId],
  () => {
    loadRefs()
  },
  { immediate: true }
)

watch(
  () => [appStore.dataRevision, appStore.changesRevision],
  () => {
    loadChanges()
  },
  { immediate: true }
)

defineExpose({
  refreshChanges: loadChanges,
})
</script>

<style scoped>
.side-panel {
  width: 260px;
  flex: 0 0 260px;
  border-left: 1px solid var(--line);
  background: var(--panel);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.panel-inner {
  flex: 1;
  overflow-y: auto;
  padding: 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-title {
  margin: 0;
  font-size: 11px;
  color: var(--muted);
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.empty-hint {
  font-size: 12px;
  color: var(--muted);
  padding: 6px 4px;
}

.ref-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* 引用了卡片 */
.ref-card {
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--raise);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.ref-card:hover {
  border-color: var(--gold);
  background: #22262d;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
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

.ref-name {
  font-size: 12px;
  color: var(--fg);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.ref-id {
  font-size: 11px;
  color: var(--muted);
  flex-shrink: 0;
}

.card-field {
  font-size: 11px;
  color: var(--muted);
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 被引用行 */
.ref-row {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 6px 8px;
  border-radius: 5px;
  background: var(--raise);
  cursor: pointer;
  border: 1px solid transparent;
  transition: border-color 0.15s, background 0.15s;
}

.ref-row:hover {
  border-color: var(--gold);
  background: #22262d;
}

.row-left {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.row-field {
  font-size: 11px;
  color: var(--muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-left: 2px;
}

/* 本次修改 */
.changes-section {
  border-top: 1px solid var(--line);
  padding-top: 14px;
  margin-top: 4px;
}

.change-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.change-card {
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--raise);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.change-card:hover {
  border-color: var(--gold);
  background: #22262d;
}

.change-card.inconvertible {
  opacity: 0.65;
  background: #171a1f;
  border-style: dashed;
}

.change-card.inconvertible:hover {
  border-color: var(--line-strong, #3a3f49);
}

.change-name {
  font-size: 12px;
  color: var(--fg);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.change-id {
  font-size: 11px;
  color: var(--muted);
  flex-shrink: 0;
}

.change-desc {
  font-size: 12px;
  color: var(--fg-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.op-badge {
  background: #282d35;
  color: var(--muted);
  border-color: #3f4652;
}

.change-values {
  font-size: 11px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  font-weight: 500;
}

.change-reason {
  font-size: 11px;
  color: var(--red, #ec7a88);
  margin-top: 2px;
  line-height: 1.3;
}
</style>
