<template>
  <el-container class="app-shell">
    <el-aside width="190px" class="aside">
      <div class="logo">
        <span class="logo-mark">G</span> GenieForge
      </div>
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
    <el-container>
      <div v-if="showCompareBar" class="compare-bar">
        <span class="cb-label">对比模式</span>
        <el-switch :model-value="compare.state.active" @change="onToggleCompare" size="small" />
        <template v-if="compare.state.active">
          <FilePicker v-model="compare.state.path" placeholder="目标 dat 文件" />
          <el-button size="small" :loading="cbLoading" @click="loadCompare">加载</el-button>
          <span v-if="compare.state.version" class="cb-info">
            目标：科技 {{ compare.state.version.techs }} · 效果 {{ compare.state.version.effects }} · 文明 {{ compare.state.version.civs }}
          </span>
        </template>
      </div>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useCompare } from './composables/useCompare'
import FilePicker from './components/FilePicker.vue'

const compare = useCompare()
const route = useRoute()
const cbLoading = ref(false)

// 仅在数据浏览页显示对比条
const showCompareBar = computed(() =>
  ['techs', 'units', 'civs', 'effects'].includes(String(route.name))
)

async function onToggleCompare(v: boolean) {
  if (v) {
    if (!compare.state.path) {
      ElMessage.info('请先选择目标 dat 文件')
      compare.state.active = false
      return
    }
    await loadCompare()
    compare.state.active = true
  } else {
    compare.state.active = false
  }
}

async function loadCompare() {
  if (!compare.state.path) return
  cbLoading.value = true
  try {
    await compare.loadTarget(compare.state.path)
    compare.state.active = true
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    cbLoading.value = false
  }
}
</script>

<style scoped>
.app-shell {
  height: 100vh;
}
.aside {
  background: #232528;
  border-right: 1px solid #3c3f41;
  display: flex;
  flex-direction: column;
}
.logo {
  padding: 16px 16px 12px;
  font-size: 15px;
  font-weight: 600;
  color: #e6e6e6;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #3c3f41;
}
.logo-mark {
  display: inline-flex;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: #3574f0;
  color: #fff;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
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
.compare-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  border-bottom: 1px solid #3c3f41;
  background: #232528;
}
.cb-label {
  font-size: 12px;
  color: #e6e6e6;
  font-weight: 600;
}
.cb-info {
  font-size: 12px;
  color: #9a9a9a;
}
</style>
