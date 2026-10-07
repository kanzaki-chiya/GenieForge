<template>
  <div class="home-container">
    <div class="page-header">
      <h2 class="page-title">工作台概览</h2>
      <span class="page-subtitle">GenieForge 帝国时代 2 决定版 dat 修改工作台</span>
    </div>

    <div class="cards-grid">
      <!-- 应用状态 -->
      <div class="theme-card">
        <div class="card-head">应用状态</div>
        <div class="card-body">
          <div v-if="health" class="status-row">
            <span class="status-badge live">在线</span>
            <span class="mono">v{{ health.version }}</span>
            <span class="status-desc">{{ health.status }}</span>
          </div>
          <div v-else class="status-row">
            <span class="status-badge offline">未连接</span>
            <span class="status-desc">请确认后端服务已启动</span>
          </div>
        </div>
      </div>

      <!-- dat 状态 -->
      <div class="theme-card flex-2">
        <div class="card-head">dat 文件状态</div>
        <div class="card-body">
          <div v-if="datInfo && datInfo.version">
            <div class="dat-info-main">
              <span class="dat-version-badge mono">VER {{ datInfo.version }}</span>
              <span class="dat-path mono" :title="datInfo.path || ''">{{ datInfo.path }}</span>
            </div>
            <div v-if="datInfo.counts" class="counts-row">
              <div class="count-item">
                <span class="count-label">科技</span>
                <span class="count-val mono">{{ datInfo.counts.techs ?? 0 }}</span>
              </div>
              <div class="count-item">
                <span class="count-label">单位</span>
                <span class="count-val mono">{{ datInfo.counts.unit_headers ?? 0 }}</span>
              </div>
              <div class="count-item">
                <span class="count-label">文明</span>
                <span class="count-val mono">{{ datInfo.counts.civs ?? 0 }}</span>
              </div>
              <div class="count-item">
                <span class="count-label">效果</span>
                <span class="count-val mono">{{ datInfo.counts.effects ?? 0 }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-dat-hint">
            尚未加载 dat 文件，请在下方选择 dat 文件加载。
          </div>
        </div>
      </div>
    </div>

    <!-- 操作区 -->
    <div class="theme-card op-card">
      <div class="card-head">操作</div>
      <div class="card-body">
        <div class="op-form">
          <div class="file-picker-wrap">
            <label class="op-label">dat 路径</label>
            <FilePicker v-model="datPath" placeholder="例如：empires2_x2_p1.dat 路径" />
          </div>
          <div class="op-actions">
            <button
              type="button"
              class="btn primary"
              :disabled="loading"
              @click="load"
            >
              {{ loading ? '加载中…' : '加载 dat' }}
            </button>
            <button
              type="button"
              class="btn"
              @click="checkUpdate"
            >
              检查更新
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAppStore, useHistoryStore } from '../stores'
import { api } from '../api/client'
import FilePicker from '../components/FilePicker.vue'

const health = ref<any>(null)
const appStore = useAppStore()
const historyStore = useHistoryStore()
const datInfo = computed(() => appStore.datInfo)
const datPath = ref('')
const loading = ref(false)

async function refresh() {
  health.value = await api.health().catch(() => null)
  await appStore.refreshDatInfo()
}

async function load() {
  if (!datPath.value) return ElMessage.warning('请填写 dat 路径')
  loading.value = true
  try {
    const r: any = await api.loadDat(datPath.value)
    // dat 重新加载成功后清空前端会话内记录的原值与修改历史
    historyStore.clearAll()
    await appStore.refreshDatInfo()
    ElMessage.success(`已加载，语言表条目 ${r.language_entries ?? 0}`)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function checkUpdate() {
  try {
    const r: any = await api.updateCheck()
    ElMessage.info(
      r.update_available
        ? `有新版本：${r.latest_version}`
        : `当前已是最新版（${r.current_version}）`
    )
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(refresh)
</script>

<style scoped>
.home-container {
  padding: 24px 32px;
  max-width: 1080px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--fg);
  letter-spacing: 0.02em;
}

.page-subtitle {
  font-size: 13px;
  color: var(--muted);
}

.cards-grid {
  display: flex;
  gap: 16px;
}

.theme-card {
  flex: 1;
  background: var(--raise);
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.theme-card.flex-2 {
  flex: 2;
}

.card-head {
  padding: 10px 16px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  border-bottom: 1px solid var(--line);
  background: #181b20;
  letter-spacing: 0.05em;
}

.card-body {
  padding: 16px;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.status-badge.live {
  background: var(--gold-bg);
  color: var(--gold);
  border: 1px solid var(--gold-edge);
}

.status-badge.offline {
  background: var(--red-bg);
  color: var(--red);
  border: 1px solid rgba(236, 122, 136, 0.3);
}

.status-desc {
  font-size: 13px;
  color: var(--fg-2);
}

.dat-info-main {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.dat-version-badge {
  font-size: 11px;
  color: var(--gold);
  background: var(--gold-bg);
  border: 1px solid var(--gold-edge);
  border-radius: 4px;
  padding: 2px 6px;
}

.dat-path {
  color: var(--fg-2);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-dat-hint {
  color: var(--muted);
  font-size: 13px;
}

.counts-row {
  display: flex;
  gap: 16px;
  padding-top: 10px;
  border-top: 1px solid var(--line);
}

.count-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.count-label {
  font-size: 11px;
  color: var(--muted);
}

.count-val {
  font-size: 16px;
  font-weight: 600;
  color: var(--fg);
}

.op-card {
  margin-top: 4px;
}

.op-form {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  flex-wrap: wrap;
}

.file-picker-wrap {
  flex: 1;
  min-width: 320px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.op-label {
  font-size: 12px;
  color: var(--fg-2);
}

.op-actions {
  display: flex;
  gap: 10px;
}

/* 按钮样式（与全局一致） */
.btn {
  font: inherit;
  font-size: 13px;
  color: var(--fg);
  background: #252931;
  border: 1px solid #353a44;
  border-radius: 6px;
  padding: 0 16px;
  min-height: 32px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}

.btn:hover:not(:disabled) {
  background: #2d323c;
  border-color: #4a5160;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.primary {
  background: var(--gold);
  border-color: var(--gold);
  color: var(--gold-ink);
  font-weight: 600;
}

.btn.primary:hover:not(:disabled) {
  filter: brightness(1.1);
}
</style>
