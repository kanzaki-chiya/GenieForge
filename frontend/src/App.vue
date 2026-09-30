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
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts"></script>

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
</style>
