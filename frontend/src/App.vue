<template>
  <el-container class="app-shell" direction="vertical">
    <!-- 顶栏：品牌 + dat 状态 + 全局搜索 + 保存/撤销/重做（改版①） -->
    <div class="topbar">
      <div class="brand">GenieForge</div>
      <div v-if="datInfo && datInfo.version" class="filechip">
        <span class="fname">{{ fileName }}</span>
        <span class="fver">VER {{ datInfo.version }}</span>
        <span v-if="datInfo.dirty" class="fdirty"><span class="dot"></span>未保存</span>
        <span v-else class="fclean">已保存</span>
      </div>
      <div v-else class="filechip"><span class="fnone">尚未加载 dat</span></div>
      <div class="search" @click="searchOpen = true">
        <el-input
          :model-value="''"
          size="small"
          readonly
          placeholder="搜索科技 / 单位 / 效果 / 文明，或输入 #ID"
        >
          <template #suffix><span class="kbd">Ctrl K</span></template>
        </el-input>
      </div>
      <div class="actions">
        <el-button size="small" :disabled="!loaded" @click="doUndo">撤销</el-button>
        <el-button size="small" :disabled="!loaded" @click="doRedo">重做</el-button>
        <el-button size="small" type="primary" :disabled="!loaded" @click="doSave">保存</el-button>
      </div>
    </div>

    <el-container class="below">
      <el-aside width="190px" class="aside">
        <el-menu :default-active="$route.path" router class="menu">
          <el-menu-item index="/">
            <span>工作台</span>
          </el-menu-item>
          <el-sub-menu index="data">
            <template #title><span>数据浏览</span></template>
            <el-menu-item index="/techs">科技</el-menu-item>
            <el-menu-item index="/units">单位</el-menu-item>
            <el-menu-item index="/civs">文明</el-menu-item>
            <el-menu-item index="/effects">效果</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="tools">
            <template #title><span>工具</span></template>
            <el-menu-item index="/diff">对比差异</el-menu-item>
            <el-menu-item index="/patch">补丁</el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/version">
            <span>版本</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <span>设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>

    <GlobalSearch v-model="searchOpen" />
  </el-container>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from './api/client'
import GlobalSearch from './components/GlobalSearch.vue'
import { useAppStore } from './stores'

const store = useAppStore()
const datInfo = computed(() => store.datInfo)
const loaded = computed(() => !!datInfo.value?.version)
const fileName = computed(() => {
  const p: string | undefined = datInfo.value?.path
  return p ? p.split(/[\\/]/).pop() : ''
})

const searchOpen = ref(false)
let pollTimer: ReturnType<typeof setInterval> | undefined

async function doSave() {
  try {
    const r: any = await api.saveDat()
    ElMessage.success(`已保存：${r.path.split(/[\\/]/).pop()}`)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    store.refresh()
  }
}

async function doUndo() {
  try {
    const r: any = await api.undo()
    ElMessage.info(`已撤销：${r.description}`)
  } catch (e: any) {
    ElMessage.warning(e.message)
  } finally {
    store.refresh()
  }
}

async function doRedo() {
  try {
    const r: any = await api.redo()
    ElMessage.info(`已重做：${r.description}`)
  } catch (e: any) {
    ElMessage.warning(e.message)
  } finally {
    store.refresh()
  }
}

function onKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    searchOpen.value = true
    return
  }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault()
    if (loaded.value) doSave()
    return
  }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
    e.preventDefault()
    if (loaded.value) doUndo()
  }
}

onMounted(() => {
  store.refresh()
  // 轻量轮询：编辑操作分散在各页面，用 dirty 状态驱动顶栏展示
  pollTimer = setInterval(() => store.refresh(), 5000)
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  clearInterval(pollTimer)
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.app-shell {
  height: 100vh;
}
.topbar {
  height: 46px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 14px;
  background: #232528;
  border-bottom: 1px solid #3c3f41;
  flex-shrink: 0;
}
.brand {
  font-weight: 700;
  font-size: 14px;
  color: #e6e6e6;
}
.filechip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 10px;
  border: 1px solid #3c3f41;
  border-radius: 5px;
  background: #1e1f22;
  font-size: 12px;
}
.fname { color: #d4d4d4; }
.fver { color: #9a9a9a; }
.fdirty { color: #e0a43a; display: inline-flex; align-items: center; gap: 5px; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #e0a43a; display: inline-block; }
.fclean { color: #6a9955; }
.fnone { color: #6f6f6f; }
.search { flex: 1; max-width: 460px; cursor: text; }
.search :deep(.el-input__wrapper) { cursor: text; }
.kbd { font-size: 10px; color: #6f6f6f; border: 1px solid #3c3f41; border-radius: 3px; padding: 0 4px; font-family: Consolas, monospace; }
.actions { margin-left: auto; display: flex; gap: 8px; }
.below { flex: 1; min-height: 0; }
.aside {
  background: #232528;
  border-right: 1px solid #3c3f41;
  display: flex;
  flex-direction: column;
}
.logo {
  display: none;
}
.menu {
  border-right: none;
  background: transparent;
  flex: 1;
  padding: 4px 0;
}
.main {
  padding: 0;
  overflow: auto;
}
</style>
