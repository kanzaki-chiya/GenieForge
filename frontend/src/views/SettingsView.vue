<template>
  <div>
    <h2>设置</h2>
    <el-form label-width="100px" style="max-width: 520px">
      <el-form-item label="游戏目录">
        <el-input v-model="config.game_dir" placeholder="AoE2 DE 安装目录（用于定位语言文件）" />
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
      <el-form-item label="更新通道">
        <el-select v-model="config.update_channel">
          <el-option label="稳定版" value="stable" />
          <el-option label="预发布" value="prerelease" />
        </el-select>
      </el-form-item>
      <el-form-item label="自动更新">
        <el-switch v-model="config.auto_update" />
      </el-form-item>
      <el-form-item label="GitHub 仓库">
        <el-input v-model="config.github_repo" placeholder="owner/repo" />
      </el-form-item>
      <el-form-item label="API Key">
        <el-input v-model="config.api_key" placeholder="留空则不鉴权；设置后写操作需 X-API-Key" show-password />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="save">保存</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const config = reactive({
  game_dir: '',
  language: 'zh-CN',
  port: 8342,
  update_channel: 'stable',
  auto_update: true,
  github_repo: '',
  api_key: ''
})
const loading = ref(false)

async function load() {
  const r: any = await api.getConfig().catch(() => ({}))
  Object.assign(config, r)
}

async function save() {
  loading.value = true
  try {
    await api.setConfig({ ...config })
    ElMessage.success('已保存')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
