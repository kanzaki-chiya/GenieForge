<template>
  <el-dialog
    v-model="visible"
    title="全局搜索"
    width="560px"
    :show-close="false"
    @opened="focusInput"
  >
    <el-input
      ref="inputRef"
      v-model="q"
      size="large"
      placeholder="搜索科技 / 单位 / 效果 / 文明，或输入 #ID"
      clearable
      :prefix-icon="Search"
      @input="onInput"
      @keyup.enter="onEnter"
    />
    <div class="hits">
      <template v-if="idJump.length">
        <div class="hit-group">#ID 直达</div>
        <div v-for="j in idJump" :key="j.path + j.id" class="hit" @click="go(j.path, j.id)">
          <span class="hit-table">{{ j.label }}</span>
          <span class="hit-name mono">#{{ j.id }}</span>
        </div>
      </template>
      <template v-for="(items, table) in grouped" :key="table">
        <div class="hit-group">{{ TABLE_LABELS[table] || table }}</div>
        <div v-for="r in items" :key="table + r.id" class="hit" @click="go(routeOf(table), r.id)">
          <span class="hit-table mono">#{{ r.id }}</span>
          <span class="hit-name">{{ r.display_name || r.name }}</span>
        </div>
      </template>
      <div v-if="q && !idJump.length && !results.length" class="no-hit">无匹配结果</div>
      <div v-if="!q" class="no-hit">输入名称搜索，或输入 #ID 直达（如 #22）</div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { api } from '../api/client'

const visible = defineModel<boolean>({ default: false })
const q = ref('')
const results = ref<{ table: string; id: number; name: string; display_name?: string }[]>([])
const inputRef = ref()

const TABLE_LABELS: Record<string, string> = { techs: '科技', effects: '效果', civs: '文明', units: '单位' }
const ROUTES: Record<string, string> = { techs: '/techs', effects: '/effects', civs: '/civs', units: '/units' }

const router = useRouter()

function routeOf(table: string): string {
  return ROUTES[table] || '/'
}

// #22 → 跨表直达候选
const idJump = computed(() => {
  const m = /^#?(\d+)$/.exec(q.value.trim())
  if (!m) return []
  const id = Number(m[1])
  return [
    { path: '/techs', id, label: '科技' },
    { path: '/effects', id, label: '效果' },
    { path: '/civs', id, label: '文明' },
    { path: '/units', id, label: '单位' }
  ]
})

const grouped = computed(() => {
  const g: Record<string, typeof results.value> = {}
  for (const r of results.value) (g[r.table] ||= []).push(r)
  return g
})

let timer: ReturnType<typeof setTimeout> | undefined

function onInput() {
  clearTimeout(timer)
  const kw = q.value.trim()
  if (!kw || /^#?\d+$/.test(kw)) {
    results.value = []
    return
  }
  timer = setTimeout(async () => {
    try {
      const r: any = await api.search(kw)
      results.value = r.results || []
    } catch {
      results.value = []
    }
  }, 200)
}

function onEnter() {
  const first = results.value[0]
  if (first) go(routeOf(first.table), first.id)
}

function go(path: string, id: number) {
  visible.value = false
  q.value = ''
  results.value = []
  router.push({ path, query: { id: String(id) } })
}

function focusInput() {
  inputRef.value?.focus?.()
}
</script>

<style scoped>
.hits { margin-top: 10px; max-height: 380px; overflow: auto; }
.hit-group { font-size: 11px; color: var(--el-text-color-secondary); letter-spacing: 0.08em; padding: 8px 4px 2px; }
.hit { display: flex; gap: 10px; align-items: center; padding: 6px 8px; border-radius: 5px; cursor: pointer; font-size: 13px; }
.hit:hover { background: var(--el-fill-color); }
.hit-table { color: var(--el-text-color-secondary); width: 48px; flex-shrink: 0; }
.hit-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.no-hit { color: var(--el-text-color-placeholder); font-size: 12px; padding: 16px 8px; text-align: center; }
.mono { font-family: Consolas, monospace; font-variant-numeric: tabular-nums; }
</style>
