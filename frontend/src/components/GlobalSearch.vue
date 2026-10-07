<template>
  <div ref="rootRef" class="global-search-container">
    <div
      class="search-box"
      :class="{ focused: isOpen, disabled: disabled }"
      @click="handleContainerClick"
    >
      <svg
        class="search-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" />
      </svg>
      <input
        ref="inputRef"
        v-model="query"
        type="text"
        class="search-input"
        :placeholder="placeholderText"
        :disabled="disabled"
        @focus="onFocus"
        @input="onInput"
        @keydown="onKeyDown"
      />
      <span v-if="query" class="clear-btn" @click.stop="clearQuery">✕</span>
      <kbd class="shortcut-kbd">Ctrl K</kbd>
    </div>

    <!-- 下拉面板 -->
    <div v-if="isOpen && hasOptions" class="dropdown-panel">
      <!-- #ID 模式：快速跳转选项 -->
      <template v-if="isIdMode">
        <div class="dropdown-header">按 ID 跳转</div>
        <div
          v-for="(item, idx) in idOptions"
          :key="item.table"
          class="dropdown-item"
          :class="{ active: selectedIndex === idx }"
          @mouseenter="selectedIndex = idx"
          @mousedown.prevent="selectItem(item)"
        >
          <span class="item-badge">{{ item.tableLabel }}</span>
          <span class="item-name">{{ item.name }}</span>
          <span class="item-id mono">#{{ parsedId }}</span>
        </div>
      </template>

      <!-- 普通文字搜索：分组结果列表 -->
      <template v-else>
        <div v-if="loading" class="dropdown-empty">搜索中…</div>
        <div v-else-if="flatResults.length === 0" class="dropdown-empty">无匹配结果</div>
        <template v-else>
          <div v-for="group in groupedResults" :key="group.table" class="result-group">
            <div class="dropdown-header">
              <span>{{ group.label }}</span>
              <span class="mono header-count">{{ group.items.length }}</span>
            </div>
            <div
              v-for="item in group.items"
              :key="`${item.table}-${item.id}`"
              class="dropdown-item"
              :class="{ active: selectedIndex === item.globalIndex }"
              @mouseenter="selectedIndex = item.globalIndex"
              @mousedown.prevent="selectItem(item)"
            >
              <span class="item-id mono">#{{ item.id }}</span>
              <span class="item-name">{{ item.display_name || item.name || '未命名' }}</span>
              <span v-if="item.display_name && item.name && item.display_name !== item.name" class="item-sub">
                {{ item.name }}
              </span>
            </div>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'

const props = defineProps<{
  disabled?: boolean
}>()

const router = useRouter()

const rootRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const query = ref('')
const isOpen = ref(false)
const loading = ref(false)
const selectedIndex = ref(0)

const placeholderText = '搜索科技 / 效果 / 文明，或输入 #ID'

interface SearchHit {
  table: string
  id: number
  name: string
  display_name: string
}

interface IndexedHit extends SearchHit {
  globalIndex: number
}

const rawResults = ref<SearchHit[]>([])

let debounceTimer: ReturnType<typeof setTimeout> | null = null

// 判断是否是 #数字 模式
const parsedId = computed<number | null>(() => {
  const trimmed = query.value.trim()
  if (!trimmed.startsWith('#')) return null
  const numStr = trimmed.slice(1).trim()
  if (!numStr || !/^\d+$/.test(numStr)) return null
  return parseInt(numStr, 10)
})

const isIdMode = computed(() => parsedId.value !== null)

interface IdOptionItem {
  table: string
  tableLabel: string
  name: string
  id: number
}

const idOptions = computed<IdOptionItem[]>(() => {
  const id = parsedId.value
  if (id === null) return []
  return [
    { table: 'techs', tableLabel: '科技', name: `科技 #${id}`, id },
    { table: 'units', tableLabel: '单位', name: `单位 #${id}`, id },
    { table: 'civs', tableLabel: '文明', name: `文明 #${id}`, id },
    { table: 'effects', tableLabel: '效果', name: `效果 #${id}`, id },
  ]
})

const TABLE_LABELS: Record<string, string> = {
  techs: '科技',
  effects: '效果',
  civs: '文明',
  units: '单位',
}

const groupedResults = computed(() => {
  const groups: { table: string; label: string; items: IndexedHit[] }[] = []
  const tableOrder = ['techs', 'effects', 'civs']
  let curIndex = 0

  for (const t of tableOrder) {
    const hits = rawResults.value.filter((r) => r.table === t)
    if (hits.length > 0) {
      const items: IndexedHit[] = hits.map((hit) => ({
        ...hit,
        globalIndex: curIndex++,
      }))
      groups.push({
        table: t,
        label: TABLE_LABELS[t] || t,
        items,
      })
    }
  }
  return groups
})

const flatResults = computed<IndexedHit[]>(() => {
  return groupedResults.value.flatMap((g) => g.items)
})

const hasOptions = computed(() => {
  if (isIdMode.value) return idOptions.value.length > 0
  return true
})

function handleContainerClick() {
  if (props.disabled) return
  inputRef.value?.focus()
}

function onFocus() {
  if (props.disabled) return
  if (query.value.trim()) {
    isOpen.value = true
  }
}

function clearQuery() {
  query.value = ''
  rawResults.value = []
  isOpen.value = false
}

function onInput() {
  if (props.disabled) return
  selectedIndex.value = 0
  const q = query.value.trim()
  if (!q) {
    isOpen.value = false
    rawResults.value = []
    return
  }

  isOpen.value = true

  if (isIdMode.value) {
    if (debounceTimer) clearTimeout(debounceTimer)
    return
  }

  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    executeSearch(q)
  }, 200)
}

async function executeSearch(keyword: string) {
  if (!keyword || props.disabled) return
  loading.value = true
  try {
    const res: any = await api.search(keyword)
    rawResults.value = res.results || []
  } catch {
    rawResults.value = []
  } finally {
    loading.value = false
  }
}

function selectItem(item: { table: string; id: number }) {
  isOpen.value = false
  const targetPath = `/${item.table}`
  router.push({ path: targetPath, query: { id: String(item.id) } })
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    isOpen.value = false
    inputRef.value?.blur()
    return
  }

  if (!isOpen.value) {
    if (e.key === 'ArrowDown' || e.key === 'Enter') {
      onInput()
    }
    return
  }

  const maxLen = isIdMode.value ? idOptions.value.length : flatResults.value.length
  if (maxLen === 0) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value + 1) % maxLen
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value - 1 + maxLen) % maxLen
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (isIdMode.value) {
      const target = idOptions.value[selectedIndex.value]
      if (target) selectItem(target)
    } else {
      const target = flatResults.value[selectedIndex.value]
      if (target) selectItem(target)
    }
  }
}

function handleGlobalKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    if (!props.disabled) {
      inputRef.value?.focus()
      inputRef.value?.select()
      if (query.value.trim()) {
        isOpen.value = true
      }
    }
  }
}

function handleClickOutside(e: MouseEvent) {
  if (rootRef.value && !rootRef.value.contains(e.target as Node)) {
    isOpen.value = false
  }
}

watch(
  () => props.disabled,
  (val) => {
    if (val) {
      isOpen.value = false
      query.value = ''
    }
  }
)

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
  document.removeEventListener('click', handleClickOutside)
  if (debounceTimer) clearTimeout(debounceTimer)
})
</script>

<style scoped>
.global-search-container {
  position: relative;
  width: 100%;
  max-width: 440px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--raise);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0 10px;
  height: 32px;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.search-box.focused {
  border-color: var(--gold);
  box-shadow: 0 0 0 1px var(--gold);
}

.search-box.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.search-icon {
  width: 14px;
  height: 14px;
  color: var(--muted);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-family: inherit;
  font-size: 12px;
  color: var(--fg);
  min-width: 0;
}

.search-input::placeholder {
  color: var(--muted);
}

.search-input:disabled {
  cursor: not-allowed;
}

.clear-btn {
  font-size: 11px;
  color: var(--muted);
  cursor: pointer;
  padding: 2px 4px;
}

.clear-btn:hover {
  color: var(--fg);
}

.shortcut-kbd {
  font-family: var(--f-mono);
  font-size: 11px;
  color: var(--muted);
  background: #181b20;
  border: 1px solid var(--line-strong);
  border-radius: 4px;
  padding: 1px 6px;
  line-height: 1.4;
  white-space: nowrap;
  pointer-events: none;
}

/* 下拉菜单 */
.dropdown-panel {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #181b20;
  border: 1px solid var(--line);
  border-radius: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
  max-height: 380px;
  overflow-y: auto;
  z-index: 1000;
  padding: 6px 0;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
  padding: 6px 12px 4px;
  letter-spacing: 0.05em;
}

.header-count {
  font-size: 10px;
  color: var(--muted);
}

.dropdown-empty {
  padding: 16px 12px;
  text-align: center;
  color: var(--muted);
  font-size: 12px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.1s;
}

.dropdown-item:hover,
.dropdown-item.active {
  background: var(--raise);
}

.item-badge {
  font-size: 11px;
  color: var(--gold);
  background: var(--gold-bg);
  border: 1px solid var(--gold-edge);
  border-radius: 4px;
  padding: 1px 6px;
  flex-shrink: 0;
}

.item-id {
  font-size: 11px;
  color: var(--muted);
  flex-shrink: 0;
  min-width: 32px;
}

.item-name {
  color: var(--fg);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.item-sub {
  font-size: 11px;
  color: var(--muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 140px;
}
</style>
