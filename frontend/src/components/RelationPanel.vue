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
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'

export interface RefItem {
  table: string
  id: number
  name: string | null
  field: string
}

const props = defineProps<{
  table: 'techs' | 'unit_headers' | 'civs' | 'effects' | string
  entityId: number | null | undefined
}>()

const router = useRouter()

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

watch(
  () => [props.table, props.entityId],
  () => {
    loadRefs()
  },
  { immediate: true }
)
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
</style>
