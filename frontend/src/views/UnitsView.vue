<template>
  <div class="editor" @keydown.ctrl.67="cp.copy(currentUnit)" @keydown.ctrl.86="cp.paste(currentUnit)">
    <!-- 顶部文明切换条 -->
    <div class="civ-bar">
      <div class="civ-selector-wrap">
        <span class="civ-label">文明：</span>
        <div class="civ-btns">
          <span
            v-for="c in civs"
            :key="c.id"
            class="civ-btn"
            :class="{ active: c.id === civ }"
            @click="switchCiv(c.id)"
          >{{ (c.display_name || c.name).slice(0, 2) }}</span>
        </div>
      </div>
      <div class="civ-status-text">
        <span>当前文明：{{ civName }}</span>
        <span class="mono"> · 单位 #{{ currentUnit }}</span>
      </div>
    </div>

    <div class="body">
      <!-- 左栏：列表（宽 260px） -->
      <div class="list-panel">
        <div class="list-filter">
          <el-input
            v-model="q"
            placeholder="搜索单位名…"
            size="small"
            clearable
            @keyup.enter="fetch"
            @clear="fetch"
          />
          <div class="dim-selects">
            <el-select v-model="filterDim" size="small" placeholder="条件" @change="fetch">
              <el-option value="" label="全部维度" />
              <el-option v-for="d in filterDims" :key="d.key" :value="d.key" :label="d.label" />
            </el-select>
            <el-input
              v-if="filterDim"
              v-model="filterValue"
              placeholder="维度值"
              size="small"
              clearable
              style="width: 90px"
              @keyup.enter="fetch"
              @clear="fetch"
            />
            <el-select v-model="dim1" size="small" @change="fetch">
              <el-option v-for="d in unitDims" :key="d.key" :value="d.key" :label="d.label" />
            </el-select>
            <el-select v-model="dim2" size="small" @change="fetch">
              <el-option v-for="d in unitDims" :key="d.key" :value="d.key" :label="d.label" />
            </el-select>
          </div>
        </div>
        <div class="list-table-wrap">
          <el-table
            :data="rows"
            size="small"
            highlight-current-row
            height="100%"
            class="compact-table"
            @current-change="onSelect"
          >
            <el-table-column label="单位" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="row-name-cell">
                  <span :class="{ 'gold-text': isRowModified(row.unit_id) }">{{ formatUnit(row) }}</span>
                  <span v-if="isRowModified(row.unit_id)" class="row-dot" title="本次已修改"></span>
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="list-foot">
          <el-pagination
            v-model:current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            size="small"
            @current-change="fetch"
          />
        </div>
      </div>

      <!-- 中间：字段区 -->
      <div class="main-panel" v-if="detail && detail.present">
        <!-- 头部实体条目信息与操作 -->
        <div class="entity-header">
          <div class="entity-meta">
            <span class="mono entity-id">#{{ detail.unit_id }}</span>
            <h3 class="entity-title">{{ detail.name }}</h3>
            <span class="entity-civ-badge">{{ civName }}</span>
          </div>
          <div class="entity-actions">
            <el-button size="small" @click="openCompare">对比…</el-button>
            <el-button size="small" @click="cp.copy(currentUnit)">复制</el-button>
            <el-button size="small" @click="cp.paste(currentUnit)">粘贴</el-button>
            <el-button size="small" @click="patchDialogVisible = true">改动转为补丁</el-button>
          </div>
        </div>

        <div class="form-scroll">
          <div class="group-title">基础信息</div>
          <div class="grid4">
            <Field
              label="Internal Name"
              :modified="isFieldModified('name')"
              :original-value="getOriginalValue('name')"
              @revert="revertField('name')"
            >
              <FieldControl type="text" :model-value="detail.name" @commit="(v) => save('name', v)" />
            </Field>
            <Field
              label="Type"
              :modified="isFieldModified('type')"
              :original-value="getOriginalValue('type')"
              @revert="revertField('type')"
            >
              <EnumSelect meta-name="unit-types" :model-value="detail.type" @change="(v) => save('type', v)" />
            </Field>
            <Field
              label="Class"
              :modified="isFieldModified('class')"
              :original-value="getOriginalValue('class')"
              @revert="revertField('class')"
            >
              <EnumSelect meta-name="armors" :model-value="detail.class" @change="(v) => save('class', v)" />
            </Field>
            <Field
              label="ID"
              :modified="isFieldModified('id')"
              :original-value="getOriginalValue('id')"
              @revert="revertField('id')"
            >
              <FieldControl type="number" :model-value="detail.id" @commit="(v) => save('id', v)" />
            </Field>
          </div>
          <div class="grid4">
            <Field
              label="Copy ID"
              :modified="isFieldModified('copy_id')"
              :original-value="getOriginalValue('copy_id')"
              @revert="revertField('copy_id')"
            >
              <FieldControl type="number" :model-value="detail.copy_id" @commit="(v) => save('copy_id', v)" />
            </Field>
            <Field
              label="Base ID"
              :modified="isFieldModified('base_id')"
              :original-value="getOriginalValue('base_id')"
              @revert="revertField('base_id')"
            >
              <FieldControl type="number" :model-value="detail.base_id" @commit="(v) => save('base_id', v)" />
            </Field>
            <Field
              label="Trait"
              :modified="isFieldModified('trait')"
              :original-value="getOriginalValue('trait')"
              @revert="revertField('trait')"
            >
              <FieldControl type="number" :model-value="detail.trait" @commit="(v) => save('trait', v)" />
            </Field>
            <Field
              label="Civilization"
              :modified="isFieldModified('civilization')"
              :original-value="getOriginalValue('civilization')"
              @revert="revertField('civilization')"
            >
              <EnumSelect :preloaded="civItems" :model-value="detail.civilization" @change="(v) => save('civilization', v)" />
            </Field>
          </div>

          <div class="group-title">统计</div>
          <div class="grid4">
            <Field
              label="生命"
              :modified="isFieldModified('hit_points')"
              :original-value="getOriginalValue('hit_points')"
              @revert="revertField('hit_points')"
            >
              <FieldControl type="number" :model-value="detail.hit_points" @commit="(v) => save('hit_points', v)" />
            </Field>
            <Field
              label="速度"
              :modified="isFieldModified('speed')"
              :original-value="getOriginalValue('speed')"
              @revert="revertField('speed')"
            >
              <FieldControl type="number" :model-value="detail.speed" @commit="(v) => save('speed', v)" />
            </Field>
            <Field
              label="视野"
              :modified="isFieldModified('line_of_sight')"
              :original-value="getOriginalValue('line_of_sight')"
              @revert="revertField('line_of_sight')"
            >
              <FieldControl type="number" :model-value="detail.line_of_sight" @commit="(v) => save('line_of_sight', v)" />
            </Field>
            <Field
              label="驻军容量"
              :modified="isFieldModified('garrison_capacity')"
              :original-value="getOriginalValue('garrison_capacity')"
              @revert="revertField('garrison_capacity')"
            >
              <FieldControl type="number" :model-value="detail.garrison_capacity" @commit="(v) => save('garrison_capacity', v)" />
            </Field>
          </div>

          <div class="group-title">战斗</div>
          <div class="grid4">
            <Field
              label="基础护甲"
              :modified="isFieldModified('type_50.base_armor')"
              :original-value="getOriginalValue('type_50.base_armor')"
              @revert="revertField('type_50.base_armor')"
            >
              <FieldControl type="number" :model-value="detail.base_armor" @commit="(v) => save('type_50.base_armor', v)" />
            </Field>
            <Field
              label="最大射程"
              :modified="isFieldModified('type_50.max_range')"
              :original-value="getOriginalValue('type_50.max_range')"
              @revert="revertField('type_50.max_range')"
            >
              <FieldControl type="number" :model-value="detail.max_range" @commit="(v) => save('type_50.max_range', v)" />
            </Field>
            <Field
              label="最小射程"
              :modified="isFieldModified('type_50.min_range')"
              :original-value="getOriginalValue('type_50.min_range')"
              @revert="revertField('type_50.min_range')"
            >
              <FieldControl type="number" :model-value="detail.min_range" @commit="(v) => save('type_50.min_range', v)" />
            </Field>
            <Field
              label="装填时间"
              :modified="isFieldModified('type_50.reload_time')"
              :original-value="getOriginalValue('type_50.reload_time')"
              @revert="revertField('type_50.reload_time')"
            >
              <FieldControl type="number" :model-value="detail.reload_time" @commit="(v) => save('type_50.reload_time', v)" />
            </Field>
          </div>
          <div class="dual-table">
            <div class="half">
              <div class="sub-label">攻击 Attacks</div>
              <SubTable
                :columns="attackCols"
                :model-value="detail.attacks"
                @cell-commit="(p) => subSave('type_50.attacks', 'attacks', p)"
                @add-row="() => subAdd('type_50.attacks', 'attacks', { class_: 4, amount: 0 })"
                @insert-row="(i) => subInsert('type_50.attacks', 'attacks', i, { class_: 4, amount: 0 })"
                @remove-row="(i) => subRemove('type_50.attacks', 'attacks', i)"
              />
            </div>
            <div class="half">
              <div class="sub-label">护甲 Armors</div>
              <SubTable
                :columns="armorCols"
                :model-value="detail.armors"
                @cell-commit="(p) => subSave('type_50.armours', 'armors', p)"
                @add-row="() => subAdd('type_50.armours', 'armors', { class_: 1, amount: 0 })"
                @insert-row="(i) => subInsert('type_50.armours', 'armors', i, { class_: 1, amount: 0 })"
                @remove-row="(i) => subRemove('type_50.armours', 'armors', i)"
              />
            </div>
          </div>

          <div class="group-title">费用</div>
          <div class="costs">
            <div v-for="(rc, i) in detail.resource_costs" :key="i" class="cost-row">
              <EnumSelect meta-name="resource-types" :model-value="rc.type" @change="(v) => save(`creatable.resource_costs.${i}.type`, v)" />
              <Field
                :label="`费用 ${i}`"
                :modified="isFieldModified(`creatable.resource_costs.${i}.amount`)"
                :original-value="getOriginalValue(`creatable.resource_costs.${i}.amount`)"
                @revert="revertField(`creatable.resource_costs.${i}.amount`)"
              >
                <FieldControl type="number" :model-value="rc.amount" @commit="(v) => save(`creatable.resource_costs.${i}.amount`, v)" />
              </Field>
            </div>
          </div>

          <div class="group-title">资源存储</div>
          <div class="costs">
            <div v-for="(rs, i) in detail.resource_storages" :key="i" class="cost-row">
              <EnumSelect meta-name="resource-types" :model-value="rs.type" @change="(v) => save(`resource_storages.${i}.type`, v)" />
              <Field
                :label="`存储 ${i}`"
                :modified="isFieldModified(`resource_storages.${i}.amount`)"
                :original-value="getOriginalValue(`resource_storages.${i}.amount`)"
                @revert="revertField(`resource_storages.${i}.amount`)"
              >
                <FieldControl type="number" :model-value="rs.amount" @commit="(v) => save(`resource_storages.${i}.amount`, v)" />
              </Field>
            </div>
          </div>

          <div class="group-title">训练位置</div>
          <SubTable
            :columns="trainCols"
            :model-value="detail.train_locations"
            @cell-commit="(p) => subSave('creatable.train_locations', 'train_locations', p)"
            @add-row="() => subAdd('creatable.train_locations', 'train_locations', { unit_id: 0, train_time: 0, button_id: 0, hot_key_id: 0 })"
            @remove-row="(i) => subRemove('creatable.train_locations', 'train_locations', i)"
          />

          <div class="group-title">图形</div>
          <div class="grid4">
            <Field
              label="Icon"
              :modified="isFieldModified('icon_id')"
              :original-value="getOriginalValue('icon_id')"
              @revert="revertField('icon_id')"
            >
              <FieldControl type="number" :model-value="detail.icon_id" @commit="(v) => save('icon_id', v)" />
            </Field>
            <Field
              label="Special Graphic"
              :modified="isFieldModified('creatable.special_graphic')"
              :original-value="getOriginalValue('creatable.special_graphic')"
              @revert="revertField('creatable.special_graphic')"
            >
              <FieldControl type="number" :model-value="detail.special_graphic" @commit="(v) => save('creatable.special_graphic', v)" />
            </Field>
            <Field label="Standing">
              <FieldControl type="text" :model-value="detail.standing_graphic?.join('/')" @commit="(v) => saveStanding(v)" />
            </Field>
            <Field
              label="Dying"
              :modified="isFieldModified('dying_graphic')"
              :original-value="getOriginalValue('dying_graphic')"
              @revert="revertField('dying_graphic')"
            >
              <FieldControl type="number" :model-value="detail.dying_graphic" @commit="(v) => save('dying_graphic', v)" />
            </Field>
          </div>
          <div class="sub-label">Damage Graphics</div>
          <SubTable
            :columns="damageCols"
            :model-value="detail.damage_graphics"
            @cell-commit="(p) => subSave('damage_graphics', 'damage_graphics', p)"
            @add-row="() => subAdd('damage_graphics', 'damage_graphics', { graphic_id: -1, damage_percent: 0, apply_mode: 0 })"
            @remove-row="(i) => subRemove('damage_graphics', 'damage_graphics', i)"
          />

          <div class="group-title">属性</div>
          <div class="flags">
            <el-checkbox :model-value="detail.enabled === 1" @change="(v: any) => save('enabled', v ? 1 : 0)">Enabled</el-checkbox>
            <el-checkbox :model-value="detail.disabled === 1" @change="(v: any) => save('disabled', v ? 1 : 0)">Disabled</el-checkbox>
            <el-checkbox :model-value="detail.hide_in_editor === 1" @change="(v: any) => save('hide_in_editor', v ? 1 : 0)">Hide in Editor</el-checkbox>
            <el-checkbox :model-value="detail.hero_mode === 1" @change="(v: any) => save('creatable.hero_mode', v ? 1 : 0)">Hero Mode</el-checkbox>
          </div>
          <div class="grid4">
            <Field
              label="Interaction"
              :modified="isFieldModified('interaction_mode')"
              :original-value="getOriginalValue('interaction_mode')"
              @revert="revertField('interaction_mode')"
            >
              <FieldControl type="number" :model-value="detail.interaction_mode" @commit="(v) => save('interaction_mode', v)" />
            </Field>
            <Field
              label="Combat Level"
              :modified="isFieldModified('combat_level')"
              :original-value="getOriginalValue('combat_level')"
              @revert="revertField('combat_level')"
            >
              <FieldControl type="number" :model-value="detail.combat_level" @commit="(v) => save('combat_level', v)" />
            </Field>
            <Field
              label="Sort Number"
              :modified="isFieldModified('sort_number')"
              :original-value="getOriginalValue('sort_number')"
              @revert="revertField('sort_number')"
            >
              <FieldControl type="number" :model-value="detail.sort_number" @commit="(v) => save('sort_number', v)" />
            </Field>
            <Field
              label="Interface Kind"
              :modified="isFieldModified('interface_kind')"
              :original-value="getOriginalValue('interface_kind')"
              @revert="revertField('interface_kind')"
            >
              <FieldControl type="number" :model-value="detail.interface_kind" @commit="(v) => save('interface_kind', v)" />
            </Field>
          </div>

          <div class="group-title">碰撞 / 放置</div>
          <div class="grid4">
            <Field label="碰撞 X/Y/Z">
              <FieldControl type="text" :model-value="`${detail.collision_size_x}/${detail.collision_size_y}/${detail.collision_size_z}`" @commit="(v) => saveCollision(v)" />
            </Field>
            <Field label="轮廓 X/Y">
              <FieldControl type="text" :model-value="`${detail.outline_size_x}/${detail.outline_size_y}`" @commit="(v) => saveOutline(v)" />
            </Field>
            <Field
              label="障碍类型"
              :modified="isFieldModified('obstruction_type')"
              :original-value="getOriginalValue('obstruction_type')"
              @revert="revertField('obstruction_type')"
            >
              <FieldControl type="number" :model-value="detail.obstruction_type" @commit="(v) => save('obstruction_type', v)" />
            </Field>
            <Field
              label="障碍类别"
              :modified="isFieldModified('obstruction_class')"
              :original-value="getOriginalValue('obstruction_class')"
              @revert="revertField('obstruction_class')"
            >
              <FieldControl type="number" :model-value="detail.obstruction_class" @commit="(v) => save('obstruction_class', v)" />
            </Field>
          </div>
        </div>
      </div>
      <div class="main-panel empty-panel" v-else>
        <el-empty :description="detail && !detail.present ? '该文明无此单位' : '选择左侧单位查看详情'" />
      </div>

      <!-- 右栏：关联面板（宽 260px，单位表对应 unit_headers） -->
      <RelationPanel table="unit_headers" :entity-id="currentUnit >= 0 ? currentUnit : null" />
    </div>

    <!-- 改动转为补丁对话框 -->
    <PatchFromChangesDialog v-model="patchDialogVisible" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore, useHistoryStore, getEntityKey } from '../stores'
import { api } from '../api/client'
import EnumSelect from '../components/EnumSelect.vue'
import FieldControl from '../components/FieldControl.vue'
import SubTable from '../components/SubTable.vue'
import Field from '../components/Field.vue'
import RelationPanel from '../components/RelationPanel.vue'
import PatchFromChangesDialog from '../components/PatchFromChangesDialog.vue'
import { useCopyPaste } from '../composables/useCopyPaste'

const cp = useCopyPaste('units')
const appStore = useAppStore()
const historyStore = useHistoryStore()
const route = useRoute()
const router = useRouter()
const patchDialogVisible = ref(false)

const civ = ref(0)
const civs = ref<{ id: number; name: string; display_name?: string }[]>([])
const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const q = ref('')
const dim1 = ref('name')
const dim2 = ref('none')
const detail = ref<any>(null)
const currentUnit = ref(-1)
const civItems = ref<{ value: number; label: string }[]>([])

const unitDims = [
  { key: 'none', label: '（无）' },
  { key: 'name', label: '名称' },
  { key: 'type', label: '类型' },
  { key: 'class', label: '类别' },
  { key: 'hit_points', label: '生命' },
  { key: 'line_of_sight', label: '视野' },
]

// 条件搜索（维度等值过滤，真正请求后端；dim1/dim2 保留为显示标记）
const filterDims = [
  { key: 'type', label: '类型' },
  { key: 'class', label: '类别' },
  { key: 'hit_points', label: '生命' },
  { key: 'line_of_sight', label: '视野' },
  { key: 'garrison_capacity', label: '驻军' },
  { key: 'speed', label: '速度' },
  { key: 'icon_id', label: '图标' },
]
const filterDim = ref('')
const filterValue = ref('')

const attackCols = [
  { key: 'class_', label: '类别', type: 'enum', metaName: 'armors', width: 140 },
  { key: 'amount', label: '数值', type: 'number', width: 90 },
]

const armorCols = [
  { key: 'class_', label: '类别', type: 'enum', metaName: 'armors', width: 140 },
  { key: 'amount', label: '数值', type: 'number', width: 90 },
]

const trainCols = [
  { key: 'unit_id', label: '建筑 ID', type: 'number', width: 90 },
  { key: 'train_time', label: '时间', type: 'number', width: 80 },
  { key: 'button_id', label: '按钮', type: 'number', width: 70 },
  { key: 'hot_key_id', label: '快捷键', type: 'number', width: 70 },
]

const damageCols = [
  { key: 'graphic_id', label: '图形 ID', type: 'number', width: 90 },
  { key: 'damage_percent', label: '伤害阈值 %', type: 'number', width: 100 },
  { key: 'apply_mode', label: '模式', type: 'number', width: 70 },
]

const civName = computed(() => {
  const found = civs.value.find((c) => c.id === civ.value)
  return found ? found.display_name || found.name : ''
})

function currentEntityKey(): string {
  return getEntityKey('units', currentUnit.value, civ.value)
}

function isRowModified(unitId: number): boolean {
  return historyStore.hasChanges('units', unitId, civ.value)
}

function isFieldModified(fieldPath: string): boolean {
  return historyStore.isFieldModified(currentEntityKey(), fieldPath)
}

function getOriginalValue(fieldPath: string): unknown {
  return historyStore.getOriginalValue(currentEntityKey(), fieldPath)
}

async function revertField(fieldPath: string) {
  const orig = getOriginalValue(fieldPath)
  if (orig === undefined) return
  await save(fieldPath, orig)
}

function registerDetailBaseline(data: any) {
  const key = getEntityKey('units', data.unit_id, civ.value)
  historyStore.recordBaseline(key, data, [
    'name',
    'type',
    'class',
    'id',
    'copy_id',
    'base_id',
    'trait',
    'civilization',
    'hit_points',
    'speed',
    'line_of_sight',
    'garrison_capacity',
    'icon_id',
    'dying_graphic',
    'enabled',
    'disabled',
    'hide_in_editor',
    'interaction_mode',
    'combat_level',
    'sort_number',
    'interface_kind',
    'obstruction_type',
    'obstruction_class',
  ])

  // 记录子路径基础值
  historyStore.ensureFieldBaseline(key, 'type_50.base_armor', data.base_armor)
  historyStore.ensureFieldBaseline(key, 'type_50.max_range', data.max_range)
  historyStore.ensureFieldBaseline(key, 'type_50.min_range', data.min_range)
  historyStore.ensureFieldBaseline(key, 'type_50.reload_time', data.reload_time)
  historyStore.ensureFieldBaseline(key, 'creatable.special_graphic', data.special_graphic)
  historyStore.ensureFieldBaseline(key, 'creatable.hero_mode', data.hero_mode)

  if (Array.isArray(data.resource_costs)) {
    data.resource_costs.forEach((rc: any, i: number) => {
      if (rc) {
        historyStore.ensureFieldBaseline(key, `creatable.resource_costs.${i}.type`, rc.type)
        historyStore.ensureFieldBaseline(key, `creatable.resource_costs.${i}.amount`, rc.amount)
      }
    })
  }
  if (Array.isArray(data.resource_storages)) {
    data.resource_storages.forEach((rs: any, i: number) => {
      if (rs) {
        historyStore.ensureFieldBaseline(key, `resource_storages.${i}.type`, rs.type)
        historyStore.ensureFieldBaseline(key, `resource_storages.${i}.amount`, rs.amount)
      }
    })
  }
  historyStore.syncEntity(key, data)
}

function openCompare() {
  if (!detail.value || !detail.value.present) return
  router.push({ path: `/compare/units/${detail.value.unit_id}`, query: { civ: String(civ.value) } })
}

async function loadCivs() {
  const r: any = await api.civs()
  civs.value = r.items
  civItems.value = r.items.map((x: any) => ({ value: x.id, label: x.display_name || x.name }))
}

async function switchCiv(c: number) {
  civ.value = c
  await fetch()
  if (currentUnit.value >= 0) {
    await selectUnit(currentUnit.value)
  }
}

async function fetch() {
  const r: any = await api.units(
    civ.value,
    q.value || undefined,
    page.value,
    pageSize,
    filterDim.value || undefined,
    filterDim.value ? filterValue.value : undefined
  )
  rows.value = r.items
  total.value = r.total
}

// dim1/dim2 为 AGE 式显示标记：从行数据取维度值展示
function dimMark(key: string, row: any): string {
  if (!key || key === 'none' || key === 'name') return ''
  const v = row[key]
  return v == null ? '' : `${v}`
}

function formatUnit(row: any): string {
  if (!row) return ''
  // 单位 dat 内部名常为空串，优先用语言表解析出的本地化名
  const main = `#${row.unit_id} ${row.display_name || row.name || '（未命名）'}`
  const dims: string[] = []
  const m1 = dimMark(dim1.value, row)
  const m2 = dimMark(dim2.value, row)
  if (m1) dims.push(m1)
  if (m2) dims.push(m2)
  return dims.length ? `${main} · ${dims.join(' · ')}` : main
}

async function selectUnit(unitId: number) {
  currentUnit.value = unitId
  const d = await api.unitDetail(civ.value, unitId)
  if (d && d.present) {
    registerDetailBaseline(d)
  }
  detail.value = d
}

async function onSelect(row: any) {
  if (!row) return
  await selectUnit(row.unit_id)
}

function setDetail(field: string, value: unknown) {
  const parts = field.split('.')
  let cur: any = detail.value
  for (let i = 0; i < parts.length - 1; i++) {
    cur = cur[parts[i]]
  }
  cur[parts[parts.length - 1]] = value
}

async function save(field: string, value: unknown) {
  if (!detail.value) return
  try {
    await api.patchUnit(civ.value, detail.value.unit_id, { field, value })
    setDetail(field, value)
    historyStore.trackFieldChange(currentEntityKey(), field, value)
    await appStore.refreshDatInfo()
    appStore.bumpChangesRevision()
    ElMessage.success({ message: `${field} 已保存`, duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function saveStanding(v: unknown) {
  const parts = String(v).split('/').map((x) => Number(x))
  if (parts.length === 2 && !parts.some(Number.isNaN)) {
    await save('standing_graphic', parts)
  }
}

async function saveCollision(v: unknown) {
  const parts = String(v).split('/').map((x) => Number(x))
  if (parts.length === 3 && !parts.some(Number.isNaN)) {
    await save('collision_size_x', parts[0])
    await save('collision_size_y', parts[1])
    await save('collision_size_z', parts[2])
  }
}

async function saveOutline(v: unknown) {
  const parts = String(v).split('/').map((x) => Number(x))
  if (parts.length === 2 && !parts.some(Number.isNaN)) {
    await save('outline_size_x', parts[0])
    await save('outline_size_y', parts[1])
  }
}

function subSave(path: string, key: string, p: { rowIndex: number; colKey: string; value: unknown }) {
  save(`${path}.${p.rowIndex}.${p.colKey}`, p.value)
}

async function subAdd(path: string, key: string, template: Record<string, unknown>) {
  const rowsData = [...detail.value[key], template]
  await saveTable(path, key, rowsData)
}

async function subInsert(path: string, key: string, idx: number, template: Record<string, unknown>) {
  const rowsData = [...detail.value[key]]
  rowsData.splice(idx, 0, template)
  await saveTable(path, key, rowsData)
}

async function subRemove(path: string, key: string, idx: number) {
  const rowsData = detail.value[key].filter((_: unknown, i: number) => i !== idx)
  await saveTable(path, key, rowsData)
}

async function saveTable(path: string, key: string, rowsData: unknown[]) {
  if (!detail.value) return
  try {
    await api.patchUnit(civ.value, detail.value.unit_id, { field: path, value: rowsData })
    setDetail(key, rowsData)
    await appStore.refreshDatInfo()
    appStore.bumpChangesRevision()
    ElMessage.success({ message: `${key} 已更新`, duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

// 监听 route.query.id 与 route.query.civ，跳转时支持指定文明和单位
watch(
  () => [route.query.id, route.query.civ],
  async ([newId, newCiv]) => {
    if (newCiv != null && newCiv !== '') {
      const c = Number(newCiv)
      if (!Number.isNaN(c) && c >= 0 && c !== civ.value) {
        await switchCiv(c)
      }
    }
    if (newId != null && newId !== '') {
      const id = Number(newId)
      if (!Number.isNaN(id) && id >= 0 && id !== currentUnit.value) {
        await selectUnit(id)
      }
    }
  }
)

// 撤销、重做、应用补丁后刷新当前选中单位详情和列表当前页
watch(
  () => appStore.dataRevision,
  async () => {
    await fetch()
    if (currentUnit.value >= 0) {
      await selectUnit(currentUnit.value)
    }
  }
)
onMounted(async () => {
  await loadCivs()
  const qCiv = Number(route.query.civ)
  const initCiv = !Number.isNaN(qCiv) && qCiv >= 0 ? qCiv : 0
  if (civs.value.length) {
    await switchCiv(initCiv)
  }
  const qId = Number(route.query.id)
  if (!Number.isNaN(qId) && qId >= 0) {
    await selectUnit(qId)
  }
})
</script>

<style scoped>
.editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 顶部文明切换条 */
.civ-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 14px;
  background: #181b20;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
  gap: 12px;
}

.civ-selector-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.civ-label {
  color: var(--muted);
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
}

.civ-btns {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.civ-btn {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--fg-2);
  background: var(--raise);
  border: 1px solid var(--line);
  transition: all 0.15s;
}

.civ-btn:hover {
  border-color: var(--gold);
  color: var(--fg);
}

.civ-btn.active {
  background: var(--gold-bg);
  border-color: var(--gold);
  color: var(--gold);
  font-weight: 600;
}

.civ-status-text {
  font-size: 12px;
  color: var(--muted);
  white-space: nowrap;
}

.body {
  flex: 1;
  display: flex;
  min-height: 0;
  height: 100%;
}

/* 左侧列表：260px */
.list-panel {
  width: 260px;
  flex: 0 0 260px;
  border-right: 1px solid var(--line);
  background: var(--panel);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.list-filter {
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dim-selects {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.list-table-wrap {
  flex: 1;
  min-height: 0;
}

.list-foot {
  padding: 6px 8px;
  border-top: 1px solid var(--line);
  display: flex;
  justify-content: center;
}

.row-name-cell {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
}

.row-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gold);
  flex-shrink: 0;
  box-shadow: 0 0 4px rgba(224, 164, 58, 0.6);
}

.gold-text {
  color: var(--gold);
  font-weight: 500;
}

/* 中间主字段区 */
.main-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: var(--app);
  height: 100%;
}

.empty-panel {
  align-items: center;
  justify-content: center;
}

.entity-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--line);
  background: #181b20;
  gap: 12px;
}

.entity-meta {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.entity-id {
  color: var(--muted);
  font-size: 14px;
}

.entity-title {
  margin: 0;
  font-size: 16px;
  color: var(--fg);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.entity-civ-badge {
  font-size: 11px;
  color: var(--gold);
  background: var(--gold-bg);
  border: 1px solid var(--gold-edge);
  border-radius: 4px;
  padding: 1px 6px;
  white-space: nowrap;
}

.entity-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.form-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 14px 18px 30px;
}

.group-title {
  color: var(--muted);
  font-weight: 600;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-top: 1px solid var(--line);
  margin: 18px 0 10px;
  padding-top: 10px;
}

.group-title:first-child {
  border-top: none;
  margin-top: 0;
  padding-top: 0;
}

.grid4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px 12px;
}

.dual-table {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.half {
  flex: 1;
  min-width: 0;
}

.sub-label {
  color: var(--muted);
  font-size: 11px;
  margin-bottom: 4px;
}

.costs {
  display: flex;
  gap: 12px;
}

.cost-row {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.flags {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
</style>
