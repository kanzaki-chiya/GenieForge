<template>
  <div>
    <h2>科技</h2>
    <el-input
      v-model="q"
      placeholder="搜索科技名（回车触发）"
      style="max-width: 320px; margin-bottom: 12px"
      clearable
      @keyup.enter="fetch"
      @clear="fetch"
    >
      <template #append>
        <el-button @click="fetch">搜索</el-button>
      </template>
    </el-input>

    <el-table :data="rows" border stripe v-loading="loading" @row-click="openDetail">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="display_name" label="显示名" />
      <el-table-column prop="type" label="类型" width="90" />
      <el-table-column prop="effect_id" label="效果 ID" width="100" />
    </el-table>
    <el-pagination
      v-model:current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next, total"
      style="margin-top: 12px"
      @current-change="fetch"
    />

    <el-drawer v-model="drawer" :title="detail ? `${detail.name} (#${detail.id})` : ''" size="40%">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="显示名">{{ detail.display_name }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ detail.type }}</el-descriptions-item>
          <el-descriptions-item label="效果 ID">{{ detail.effect_id }}</el-descriptions-item>
          <el-descriptions-item label="文明">{{ detail.civ }}</el-descriptions-item>
        </el-descriptions>

        <h4>资源费用</h4>
        <el-table :data="detail.resource_costs" size="small" border>
          <el-table-column prop="type_name" label="资源" />
          <el-table-column prop="amount" label="数量" />
          <el-table-column prop="flag" label="标志" width="80" />
        </el-table>

        <h4>前置科技</h4>
        <el-tag v-for="t in detail.required_techs" :key="t.id" style="margin: 2px">
          {{ t.name }} (#{{ t.id }})
        </el-tag>
        <div v-if="!detail.required_techs.length" style="color: #999">无</div>

        <h4>快速修改（金费）</h4>
        <el-input-number v-model="goldAmount" :step="1" />
        <el-button type="primary" style="margin-left: 8px" @click="setGold">应用</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const q = ref('')
const loading = ref(false)
const drawer = ref(false)
const detail = ref<any>(null)
const goldAmount = ref(0)

async function fetch() {
  loading.value = true
  try {
    const data: any = await api.techs({ page: page.value, page_size: pageSize, q: q.value })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function openDetail(row: any) {
  detail.value = await api.techDetail(row.id)
  const gold = detail.value.resource_costs?.find((c: any) => c.type_name === 'Gold')
  goldAmount.value = gold?.amount ?? 0
  drawer.value = true
}

async function setGold() {
  // 找到金费的字段路径并 PATCH
  const goldIdx = detail.value.resource_costs?.findIndex((c: any) => c.type_name === 'Gold')
  if (goldIdx === undefined || goldIdx < 0) return ElMessage.warning('该科技无金费字段')
  try {
    await api.patchTech(detail.value.id, {
      field: `resource_costs.${goldIdx}.amount`,
      value: goldAmount.value
    })
    ElMessage.success('已修改')
    detail.value = await api.techDetail(detail.value.id)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(fetch)
</script>
