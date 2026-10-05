<template>
  <div class="app-layout">
    <!-- 顶栏 -->
    <header class="topbar">
      <!-- 左：Logo -->
      <div class="brand">
        <svg
          class="brand-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="var(--gold)"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M4 20 12 4l8 16Z" />
          <path d="M8 14h8" />
        </svg>
        <span>GenieForge</span>
      </div>

      <!-- 中：文件状态 -->
      <div class="filechip">
        <template v-if="datInfo && datInfo.version">
          <span class="filechip-name mono" :title="datInfo.path || ''">
            {{ fileName }}
          </span>
          <span class="filechip-ver">{{ datInfo.version }}</span>
          <span v-if="datInfo.dirty" class="filechip-dirty">
            <span class="dot"></span>有未保存改动
          </span>
        </template>
        <template v-else>
          <span class="filechip-empty">未加载 dat</span>
        </template>
      </div>

      <!-- 中间：全局搜索 -->
      <div class="topbar-search">
        <GlobalSearch :disabled="!datInfo?.version" />
      </div>
      <!-- 顶栏右侧：撤销 / 重做 / 保存 -->
      <div class="actions">
        <button
          type="button"
          class="btn"
          :disabled="!datInfo?.version || isActing"
          @click="handleUndo"
        >
          撤销
        </button>
        <button
          type="button"
          class="btn"
          :disabled="!datInfo?.version || isActing"
          @click="handleRedo"
        >
          重做
        </button>
        <button
          type="button"
          class="btn primary"
          :disabled="!datInfo?.version || isActing"
          @click="handleSave"
        >
          保存
        </button>
      </div>
    </header>

    <!-- 主体区域：左侧导航 + 内容区 -->
    <div class="body">
      <!-- 左侧导航 -->
      <nav class="nav" aria-label="主导航">
        <!-- 首页 / 工作台入口 -->
        <router-link
          to="/"
          class="navbtn"
          :class="{ on: isNavActive('/') }"
        >
          <span>工作台</span>
        </router-link>

        <span class="navgroup">数据</span>
        <router-link
          to="/techs"
          class="navbtn"
          :class="{ on: isNavActive('/techs') }"
        >
          <span>科技</span>
          <span v-if="datInfo?.counts?.techs != null" class="mono nav-count">
            {{ datInfo.counts.techs }}
          </span>
        </router-link>
        <router-link
          to="/units"
          class="navbtn"
          :class="{ on: isNavActive('/units') }"
        >
          <span>单位</span>
          <span v-if="datInfo?.counts?.unit_headers != null" class="mono nav-count">
            {{ datInfo.counts.unit_headers }}
          </span>
        </router-link>
        <router-link
          to="/civs"
          class="navbtn"
          :class="{ on: isNavActive('/civs') }"
        >
          <span>文明</span>
          <span v-if="datInfo?.counts?.civs != null" class="mono nav-count">
            {{ datInfo.counts.civs }}
          </span>
        </router-link>
        <router-link
          to="/effects"
          class="navbtn"
          :class="{ on: isNavActive('/effects') }"
        >
          <span>效果</span>
          <span v-if="datInfo?.counts?.effects != null" class="mono nav-count">
            {{ datInfo.counts.effects }}
          </span>
        </router-link>

        <span class="navgroup navgroup-gap">工具</span>
        <router-link
          to="/diff"
          class="navbtn"
          :class="{ on: isNavActive('/diff') }"
        >
          <span>对比</span>
        </router-link>
        <router-link
          to="/patch"
          class="navbtn"
          :class="{ on: isNavActive('/patch') }"
        >
          <span>补丁</span>
        </router-link>
        <router-link
          to="/version"
          class="navbtn"
          :class="{ on: isNavActive('/version') }"
        >
          <span>版本</span>
        </router-link>

        <div class="nav-spacer"></div>

        <router-link
          to="/settings"
          class="navbtn"
          :class="{ on: isNavActive('/settings') }"
        >
          <span>设置</span>
        </router-link>
      </nav>

      <!-- 路由内容区 -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore } from './stores'
import { api } from './api/client'
import GlobalSearch from './components/GlobalSearch.vue'
const route = useRoute()
const appStore = useAppStore()
const isActing = ref(false)

const datInfo = computed(() => appStore.datInfo)

const fileName = computed(() => {
  const p = datInfo.value?.path
  if (!p) return ''
  const segs = p.replace(/\\/g, '/').split('/')
  return segs[segs.length - 1] || p
})

function isNavActive(path: string): boolean {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

function parseErrorMessage(err: any): string {
  if (err?.message) {
    const raw = String(err.message)
    // 尝试提取 JSON detail
    const idx = raw.indexOf('{')
    if (idx !== -1) {
      try {
        const parsed = JSON.parse(raw.slice(idx))
        if (parsed?.detail) return parsed.detail
      } catch {
        // fallback
      }
    }
    // 移除 409 Conflict: 前缀
    return raw.replace(/^\d+\s+[^:]+:\s*/, '')
  }
  return '操作失败'
}

async function handleUndo() {
  if (isActing.value) return
  isActing.value = true
  try {
    const r: any = await api.undo()
    ElMessage.success(`已撤销：${r.description || ''}`)
    await appStore.refreshDatInfo()
  } catch (e: any) {
    ElMessage.warning(parseErrorMessage(e))
  } finally {
    isActing.value = false
  }
}

async function handleRedo() {
  if (isActing.value) return
  isActing.value = true
  try {
    const r: any = await api.redo()
    ElMessage.success(`已重做：${r.description || ''}`)
    await appStore.refreshDatInfo()
  } catch (e: any) {
    ElMessage.warning(parseErrorMessage(e))
  } finally {
    isActing.value = false
  }
}

async function handleSave() {
  if (isActing.value) return
  isActing.value = true
  try {
    await api.saveDat()
    ElMessage.success('已保存 dat 文件')
    await appStore.refreshDatInfo()
  } catch (e: any) {
    ElMessage.error(parseErrorMessage(e))
  } finally {
    isActing.value = false
  }
}

onMounted(async () => {
  await appStore.refreshDatInfo()
})
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--app);
  color: var(--fg);
}

/* 顶栏 */
.topbar {
  flex: 0 0 48px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 16px;
  background: #181b20;
  border-bottom: 1px solid var(--line);
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  font-size: 15px;
  color: var(--fg);
  letter-spacing: 0.02em;
}

.brand-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}

.filechip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--app);
  font-size: 12px;
  max-width: 480px;
}

.filechip-name {
  color: var(--fg-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 260px;
}

.filechip-ver {
  color: var(--muted);
  font-size: 11px;
  white-space: nowrap;
}

.filechip-dirty {
  color: var(--gold);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  font-weight: 500;
}

.filechip-empty {
  color: var(--muted);
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--gold);
  display: inline-block;
  box-shadow: 0 0 6px rgba(224, 164, 58, 0.6);
}

.topbar-search {
  flex: 1;
  display: flex;
  justify-content: center;
  max-width: 480px;
  margin: 0 auto;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
/* 通用按钮（效果图规范） */
.btn {
  font: inherit;
  font-size: 13px;
  color: var(--fg);
  background: #252931;
  border: 1px solid #353a44;
  border-radius: 6px;
  padding: 0 14px;
  min-height: 30px;
  cursor: pointer;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, border-color 0.15s, opacity 0.15s;
}

.btn:hover:not(:disabled) {
  background: #2e333d;
  border-color: #444b58;
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn.primary {
  background: var(--gold);
  border-color: var(--gold);
  color: var(--gold-ink);
  font-weight: 700;
}

.btn.primary:hover:not(:disabled) {
  background: #ebae46;
  border-color: #ebae46;
}

/* 主体 */
.body {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

/* 左侧导航 */
.nav {
  flex: 0 0 188px;
  padding: 14px 10px;
  background: #15181c;
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.navgroup {
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.1em;
  padding: 0 10px;
  margin: 6px 0 4px;
}

.navgroup-gap {
  margin-top: 16px;
}

.navbtn {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font: inherit;
  font-size: 13px;
  color: var(--fg-2);
  background: transparent;
  border: 0;
  border-radius: 6px;
  padding: 0 10px;
  min-height: 34px;
  cursor: pointer;
  text-align: left;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}

.navbtn:hover {
  background: #1f232a;
  color: var(--fg);
}

.navbtn.on {
  background: #252931;
  color: #ffffff;
  box-shadow: inset 2px 0 0 var(--gold);
  font-weight: 500;
}

.nav-count {
  color: var(--muted);
  font-size: 11px;
}

.navbtn.on .nav-count {
  color: var(--fg-2);
}

.nav-spacer {
  flex: 1;
  min-height: 16px;
}

/* 内容区 */
.main-content {
  flex: 1;
  min-width: 0;
  overflow: auto;
  background: var(--app);
}
</style>
