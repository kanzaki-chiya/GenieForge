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
          >{{ c.name.slice(0, 2) }}</span>
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
                  <span :class="{ 'gold-text': isRowModified(row.id) }">{{ formatUnit(row) }}</span>
                  <span v-if="isRowModified(row.id)" class="row-dot" title="本次已修改"></span>
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

    <!-- 对比抽屉 -->
    <DiffDrawer
      v-if="detail"
      v-model="diffVisible"
      :table="'units'"
      :entity-id="detail.unit_id"
      :civ="civ"
      :title="detail.name"
      :baseline="detail"
      :scalar-fields="scalarFields"
      :list-fields="listFields"
      @apply="onApplyDiff"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore, useHistoryStore, getEntityKey } from '../stores'
import { api } from '../api/client'
import EnumSelect from '../components/EnumSelect.vue'
import FieldControl from '../components/FieldControl.vue'
import SubTable from '../components/SubTable.vue'
import Field from '../components/Field.vue'
import DiffDrawer from '../components/DiffDrawer.vue'
import RelationPanel from '../components/RelationPanel.vue'
import { useCopyPaste } from '../composables/useCopyPaste'

const cp = useCopyPaste('units')
const appStore = useAppStore()
const historyStore = useHistoryStore()
const route = useRoute()

const civ = ref(0)
const civs = ref<{ id: number; name: string }[]>([])
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
const diffVisible = ref(false)

const unitDims = [
  { key: 'none', label: '（无）' },
  { key: 'name', label: '名称' },
  { key: 'type', label: '类型' },
  { key: 'class', label: '类别' },
  { key: 'hit_points', label: '生命' },
  { key: 'line_of_sight', label: '视野' },
]

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

const scalarFields = [
  { key: 'name', label: '名称' },
  { key: 'type', label: '类型' },
  { key: 'class', label: '类别' },
  { key: 'id', label: 'ID' },
  { key: 'copy_id', label: 'Copy ID' },
  { key: 'base_id', label: 'Base ID' },
  { key: 'trait', label: 'Trait' },
  { key: 'civilization', label: '文明' },
  { key: 'hit_points', label: '生命' },
  { key: 'speed', label: '速度' },
  { key: 'line_of_sight', label: '视野' },
  { key: 'garrison_capacity', label: '驻军容量' },
  { key: 'base_armor', label: '基础护甲' },
  { key: 'max_range', label: '最大射程' },
  { key: 'min_range', label: '最小射程' },
  { key: 'reload_time', label: '装填时间' },
  { key: 'icon_id', label: '图标' },
  { key: 'special_graphic', label: 'Special Graphic' },
  { key: 'dying_graphic', label: 'Dying Graphic' },
  { key: 'enabled', label: 'Enabled' },
  { key: 'disabled', label: 'Disabled' },
  { key: 'hide_in_editor', label: 'Hide in Editor' },
  { key: 'hero_mode', label: 'Hero Mode' },
  { key: 'interaction_mode', label: 'Interaction' },
  { key: 'combat_level', label: 'Combat Level' },
  { key: 'sort_number', label: 'Sort Number' },
  { key: 'interface_kind', label: 'Interface Kind' },
  { key: 'obstruction_type', label: '障碍类型' },
  { key: 'obstruction_class', label: '障碍类别' },
]

const listFields = [
  { key: 'attacks', label: '攻击' },
  { key: 'armors', label: '护甲' },
  { key: 'resource_costs', label: '费用' },
  { key: 'resource_storages', label: '资源存储' },
  { key: 'train_locations', label: '训练位置' },
  { key: 'damage_graphics', label: 'Damage Graphics' },
]

const civName = computed(() => {
  const found = civs.value.find((c) => c.id === civ.value)
  return found ? found.name : ''
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
  diffVisible.value = true
}

function onApplyDiff(p: { field: string; value: unknown; list: boolean }) {
  if (p.list) {
    const keyMap: Record<string, { path: string; key: string }> = {
      attacks: { path: 'type_50.attacks', key: 'attacks' },
      armors: { path: 'type_50.armours', key: 'armors' },
      train_locations: { path: 'creatable.train_locations', key: 'train_locations' },
      resource_costs: { path: 'creatable.resource_costs', key: 'resource_costs' },
      damage_graphics: { path: 'damage_graphics', key: 'damage_graphics' },
      resource_storages: { path: 'resource_storages', key: 'resource_storages' },
    }
    const m = keyMap[p.field]
    if (m) {
      saveTable(m.path, m.key, p.value as unknown[])
    }
  } else {
    save(p.field, p.value)
  }
}

async function loadCivs() {
  const r: any = await api.civs()
  civs.value = r.items
  civItems.value = r.items.map((x: any) => ({ value: x.id, label: x.name }))
}

async function switchCiv(c: number) {
  civ.value = c
  await fetch()
  if (currentUnit.value >= 0) {
    await selectUnit(currentUnit.value)
  }
}

async function fetch() {
  const r: any = await api.units(civ.value, q.value || undefined, page.value, pageSize)
  rows.value = r.items
  total.value = r.total
}

function formatUnit(row: any): string {
  if (!row) return ''
  const main = `#${row.id} ${row.name || '（未命名）'}`
  const dims: string[] = []
  if (row.dim1 != null) dims.push(String(row.dim1))
  if (row.dim2 != null) dims.push(String(row.dim2))
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
  await selectUnit(row.id)
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
    ElMessage.success({ message: `${key} 已更新`, duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

// 监听 route.query.id，跳转时保持当前文明不变，只切换单位
watch(
  () => route.query.id,
  async (newId) => {
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
  if (civs.value.length) {
    await switchCiv(0)
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
