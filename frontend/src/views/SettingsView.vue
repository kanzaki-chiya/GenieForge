<template>
  <div class="settings">
    <h2>设置</h2>
    <el-form label-width="110px" style="max-width: 560px">
      <el-form-item label="语言文件">
        <FilePicker v-model="config.language_file" placeholder="key-value-strings-utf8.txt（用于显示中文名）" />
      </el-form-item>
      <el-form-item label="界面语言">
        <el-select v-model="config.language">
          <el-option label="简体中文" value="zh-CN" />
          <el-option label="English" value="en" />
        </el-select>
      </el-form-item>
      <el-form-item label="自动保存">
        <el-switch v-model="config.auto_save" />
        <span class="hint">开启后每次修改自动写回 dat 文件</span>
      </el-form-item>
      <el-form-item label="自动更新">
        <el-switch v-model="config.auto_update" />
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
import FilePicker from '../components/FilePicker.vue'

const config = reactive({
  language_file: '',
  language: 'zh-CN',
  auto_save: false,
  auto_update: true
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

<style scoped>
.settings { padding: 16px; }
.hint { margin-left: 12px; color: #9a9a9a; font-size: 12px; }
</style>
