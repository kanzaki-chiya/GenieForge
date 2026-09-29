<template>
  <div>
    <h2>设置</h2>
    <el-form label-width="100px" style="max-width: 480px">
      <el-form-item label="游戏目录">
        <el-input v-model="config.game_dir" placeholder="AoE2 DE 安装目录（可自动探测）" />
      </el-form-item>
      <el-form-item label="语言">
        <el-select v-model="config.language">
          <el-option label="简体中文" value="zh-CN" />
          <el-option label="English" value="en" />
        </el-select>
      </el-form-item>
      <el-form-item label="端口">
        <el-input-number v-model="config.port" :min="1" :max="65535" />
      </el-form-item>
      <el-form-item label="自动更新">
        <el-switch v-model="config.auto_update" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="save">保存</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'

const config = reactive({
  game_dir: '',
  language: 'zh-CN',
  port: 8342,
  auto_update: true
})

function save() {
  // TODO: PUT /api/config
  ElMessage.success('已保存（占位）')
}
</script>
