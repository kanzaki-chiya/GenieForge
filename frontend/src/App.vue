<template>
  <el-container class="app-shell">
    <el-aside width="200px" class="aside">
      <div class="logo">GenieForge</div>
      <el-menu :default-active="$route.path" router>
        <el-menu-item index="/">概览</el-menu-item>
        <el-menu-item index="/techs">科技</el-menu-item>
        <el-menu-item index="/diff">对比</el-menu-item>
        <el-menu-item index="/patch">补丁</el-menu-item>
        <el-menu-item index="/version">版本</el-menu-item>
        <el-menu-item index="/settings">设置</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts"></script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
}
.app-shell {
  height: 100vh;
}
.logo {
  padding: 16px;
  font-weight: 700;
  font-size: 18px;
}
.aside {
  border-right: 1px solid var(--el-border-color);
}
</style>
