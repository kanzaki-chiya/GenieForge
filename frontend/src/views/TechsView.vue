<template>
  <div>
    <h2>科技</h2>
    <el-table :data="rows" border stripe style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="type" label="类型" width="120" />
      <el-table-column prop="effect_id" label="效果 ID" width="120" />
    </el-table>
    <el-pagination
      v-model:current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next, total"
      style="margin-top: 12px"
      @current-change="fetch"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api/client'

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const loading = ref(false)

async function fetch() {
  loading.value = true
  try {
    const data = await api.techs({ page: page.value, page_size: pageSize })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

onMounted(fetch)
</script>
