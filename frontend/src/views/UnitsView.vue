<template>
  <div class="editor">
    <div class="toolbar">
      <el-input
        v-model="q"
        placeholder="搜索单位名…"
        size="small"
        clearable
        style="width: 240px"
        @keyup.enter="fetch"
        @clear="fetch"
      />
      <span class="lbl">文明</span>
      <div class="civ-btns">
        <span
          v-for="c in civs"
          :key="c.id"
          class="civ-btn"
          :class="{ active: c.id === civ }"
          @click="switchCiv(c.id)"
        >{{ c.name.slice(0, 2) }}</span>
      </div>
      <span class="count">{{ civName }} · 单位 #{{ currentUnit }}</span>
    </div>

    <div class="body">
      <div class="list">
        <el-table
          :data="rows"
          size="small"
          highlight-current-row
          height="100%"
          @current-change="onSelect"
        >
          <el-table-column prop="unit_id" label="ID" width="64" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="type" label="类型" width="56" />
        </el-table>
      </div>

      <div class="form" v-if="detail && detail.present">
        <div class="form-scroll">
          <div class="group-title">基础信息</div>
          <div class="grid4">
            <Field label="Internal Name"><FieldControl type="text" :model-value="detail.name" @commit="(v) => save('name', v)" /></Field>
            <Field label="Type"><EnumSelect meta-name="unit-types" :model-value="detail.type" @change="(v) => save('type', v)" /></Field>
            <Field label="Class"><EnumSelect meta-name="armors" :model-value="detail.class" @change="(v) => save('class', v)" /></Field>
            <Field label="ID"><FieldControl type="number" :model-value="detail.id" @commit="(v) => save('id', v)" /></Field>
          </div>
          <div class="grid4">
            <Field label="Copy ID"><FieldControl type="number" :model-value="detail.copy_id" @commit="(v) => save('copy_id', v)" /></Field>
            <Field label="Base ID"><FieldControl type="number" :model-value="detail.base_id" @commit="(v) => save('base_id', v)" /></Field>
            <Field label="Trait"><FieldControl type="number" :model-value="detail.trait" @commit="(v) => save('trait', v)" /></Field>
            <Field label="Civilization"><EnumSelect :preloaded="civItems" :model-value="detail.civilization" @change="(v) => save('civilization', v)" /></Field>
          </div>

          <div class="group-title">统计</div>
          <div class="grid4">
            <Field label="生命"><FieldControl type="number" :model-value="detail.hit_points" @commit="(v) => save('hit_points', v)" /></Field>
            <Field label="速度"><FieldControl type="number" :model-value="detail.speed" @commit="(v) => save('speed', v)" /></Field>
            <Field label="视野"><FieldControl type="number" :model-value="detail.line_of_sight" @commit="(v) => save('line_of_sight', v)" /></Field>
            <Field label="驻军容量"><FieldControl type="number" :model-value="detail.garrison_capacity" @commit="(v) => save('garrison_capacity', v)" /></Field>
          </div>

          <div class="group-title">战斗</div>
          <div class="grid4">
            <Field label="基础护甲"><FieldControl type="number" :model-value="detail.base_armor" @commit="(v) => save('type_50.base_armor', v)" /></Field>
            <Field label="最大射程"><FieldControl type="number" :model-value="detail.max_range" @commit="(v) => save('type_50.max_range', v)" /></Field>
            <Field label="最小射程"><FieldControl type="number" :model-value="detail.min_range" @commit="(v) => save('type_50.min_range', v)" /></Field>
            <Field label="装填时间"><FieldControl type="number" :model-value="detail.reload_time" @commit="(v) => save('type_50.reload_time', v)" /></Field>
          </div>
          <div class="dual-table">
            <div class="half">
              <div class="sub-label">攻击 Attacks</div>
              <SubTable :columns="attackCols" :model-value="detail.attacks" @cell-commit="(p) => subSave('type_50.attacks', 'attacks', p)" @add-row="() => subAdd('type_50.attacks', 'attacks', { class_: 4, amount: 0 })" @insert-row="(i) => subInsert('type_50.attacks', 'attacks', i, { class_: 4, amount: 0 })" @remove-row="(i) => subRemove('type_50.attacks', 'attacks', i)" />
            </div>
            <div class="half">
              <div class="sub-label">护甲 Armors</div>
              <SubTable :columns="armorCols" :model-value="detail.armors" @cell-commit="(p) => subSave('type_50.armours', 'armors', p)" @add-row="() => subAdd('type_50.armours', 'armors', { class_: 1, amount: 0 })" @insert-row="(i) => subInsert('type_50.armours', 'armors', i, { class_: 1, amount: 0 })" @remove-row="(i) => subRemove('type_50.armours', 'armors', i)" />
            </div>
          </div>

          <div class="group-title">费用</div>
          <div class="costs">
            <div v-for="(rc, i) in detail.resource_costs" :key="i" class="cost-row">
              <EnumSelect meta-name="resource-types" :model-value="rc.type" @change="(v) => save(`creatable.resource_costs.${i}.type`, v)" />
              <FieldControl type="number" :model-value="rc.amount" @commit="(v) => save(`creatable.resource_costs.${i}.amount`, v)" />
            </div>
          </div>

          <div class="group-title">资源存储</div>
          <div class="costs">
            <div v-for="(rs, i) in detail.resource_storages" :key="i" class="cost-row">
              <EnumSelect meta-name="resource-types" :model-value="rs.type" @change="(v) => save(`resource_storages.${i}.type`, v)" />
              <FieldControl type="number" :model-value="rs.amount" @commit="(v) => save(`resource_storages.${i}.amount`, v)" />
            </div>
          </div>

          <div class="group-title">训练位置</div>
          <SubTable :columns="trainCols" :model-value="detail.train_locations" @cell-commit="(p) => subSave('creatable.train_locations', 'train_locations', p)" @add-row="() => subAdd('creatable.train_locations', 'train_locations', { unit_id: 0, train_time: 0, button_id: 0, hot_key_id: 0 })" @remove-row="(i) => subRemove('creatable.train_locations', 'train_locations', i)" />

          <div class="group-title">图形</div>
          <div class="grid4">
            <Field label="Icon"><FieldControl type="number" :model-value="detail.icon_id" @commit="(v) => save('icon_id', v)" /></Field>
            <Field label="Special Graphic"><FieldControl type="number" :model-value="detail.special_graphic" @commit="(v) => save('creatable.special_graphic', v)" /></Field>
            <Field label="Standing"><FieldControl type="text" :model-value="detail.standing_graphic?.join('/')" @commit="(v) => saveStanding(v)" /></Field>
            <Field label="Dying"><FieldControl type="number" :model-value="detail.dying_graphic" @commit="(v) => save('dying_graphic', v)" /></Field>
          </div>
          <div class="sub-label">Damage Graphics</div>
          <SubTable :columns="damageCols" :model-value="detail.damage_graphics" @cell-commit="(p) => subSave('damage_graphics', 'damage_graphics', p)" @add-row="() => subAdd('damage_graphics', 'damage_graphics', { graphic_id: -1, damage_percent: 0, apply_mode: 0 })" @remove-row="(i) => subRemove('damage_graphics', 'damage_graphics', i)" />

          <div class="group-title">属性</div>
          <div class="flags">
            <el-checkbox :model-value="detail.enabled === 1" @change="(v: any) => save('enabled', v ? 1 : 0)">Enabled</el-checkbox>
            <el-checkbox :model-value="detail.disabled === 1" @change="(v: any) => save('disabled', v ? 1 : 0)">Disabled</el-checkbox>
            <el-checkbox :model-value="detail.hide_in_editor === 1" @change="(v: any) => save('hide_in_editor', v ? 1 : 0)">Hide in Editor</el-checkbox>
            <el-checkbox :model-value="detail.hero_mode === 1" @change="(v: any) => save('creatable.hero_mode', v ? 1 : 0)">Hero Mode</el-checkbox>
          </div>
          <div class="grid4">
            <Field label="Interaction"><FieldControl type="number" :model-value="detail.interaction_mode" @commit="(v) => save('interaction_mode', v)" /></Field>
            <Field label="Combat Level"><FieldControl type="number" :model-value="detail.combat_level" @commit="(v) => save('combat_level', v)" /></Field>
            <Field label="Sort Number"><FieldControl type="number" :model-value="detail.sort_number" @commit="(v) => save('sort_number', v)" /></Field>
            <Field label="Interface Kind"><FieldControl type="number" :model-value="detail.interface_kind" @commit="(v) => save('interface_kind', v)" /></Field>
          </div>

          <div class="group-title">碰撞 / 放置</div>
          <div class="grid4">
            <Field label="碰撞 X/Y/Z"><FieldControl type="text" :model-value="`${detail.collision_size_x}/${detail.collision_size_y}/${detail.collision_size_z}`" @commit="(v) => saveCollision(v)" /></Field>
            <Field label="轮廓 X/Y"><FieldControl type="text" :model-value="`${detail.outline_size_x}/${detail.outline_size_y}`" @commit="(v) => saveOutline(v)" /></Field>
            <Field label="障碍类型"><FieldControl type="number" :model-value="detail.obstruction_type" @commit="(v) => save('obstruction_type', v)" /></Field>
            <Field label="障碍类别"><FieldControl type="number" :model-value="detail.obstruction_class" @commit="(v) => save('obstruction_class', v)" /></Field>
          </div>
        </div>
      </div>
      <div class="form" v-else>
        <el-empty :description="detail && !detail.present ? '该文明无此单位' : '选择左侧单位查看详情'" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import EnumSelect from '../components/EnumSelect.vue'
import FieldControl from '../components/FieldControl.vue'
import SubTable from '../components/SubTable.vue'
import Field from '../components/Field.vue'

const civs = ref<any[]>([])
const civItems = ref<{ value: number; label: string }[]>([])
const civ = ref(0)
const civName = ref('')
const rows = ref<any[]>([])
const detail = ref<any>(null)
const currentUnit = ref(-1)
const q = ref('')

const attackCols = [
  { key: 'class_', label: '类别', type: 'enum', metaName: 'armors', width: 150 },
  { key: 'amount', label: '数值', type: 'number', width: 100 }
]
const armorCols = [
  { key: 'class_', label: '类别', type: 'enum', metaName: 'armors', width: 150 },
  { key: 'amount', label: '数值', type: 'number', width: 100 }
]
const trainCols = [
  { key: 'unit_id', label: '单位', type: 'number', width: 90 },
  { key: 'train_time', label: '训练时间', type: 'number', width: 90 },
  { key: 'button_id', label: '按钮 ID', type: 'number', width: 90 }
]
const damageCols = [
  { key: 'graphic_id', label: '图形', type: 'number', width: 90 },
  { key: 'damage_percent', label: '伤害 %', type: 'number', width: 90 },
  { key: 'apply_mode', label: '模式', type: 'number', width: 80 }
]

async function loadCivs() {
  const r: any = await api.civs()
  civs.value = r.items
  civItems.value = r.items.map((x: any) => ({ value: x.id, label: x.name }))
}

async function switchCiv(id: number) {
  civ.value = id
  civName.value = civs.value.find((c) => c.id === id)?.name || ''
  detail.value = null
  await fetch()
}

async function fetch() {
  const r: any = await api.units(civ.value, q.value || undefined)
  rows.value = r.items
}

async function onSelect(row: any) {
  if (!row) return
  currentUnit.value = row.unit_id
  detail.value = await api.unitDetail(civ.value, row.unit_id)
}

function setDetail(dotted: string, value: unknown) {
  const parts = dotted.split('.')
  let cur: any = detail.value
  for (let i = 0; i < parts.length - 1; i++) cur = cur[parts[i]]
  cur[parts[parts.length - 1]] = value
}

async function save(field: string, value: unknown) {
  if (!detail.value) return
  try {
    await api.patchUnit(civ.value, detail.value.unit_id, { field, value })
    setDetail(field, value)
    ElMessage.success({ message: `${field} 已保存`, duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function saveStanding(v: string) {
  const parts = String(v).split('/').map((x) => Number(x))
  if (parts.length === 2 && !parts.some(Number.isNaN)) {
    await save('standing_graphic.0', parts[0])
    await save('standing_graphic.1', parts[1])
  }
}

async function saveCollision(v: string) {
  const parts = String(v).split('/').map((x) => Number(x))
  if (parts.length === 3 && !parts.some(Number.isNaN)) {
    await save('collision_size_x', parts[0])
    await save('collision_size_y', parts[1])
    await save('collision_size_z', parts[2])
  }
}

async function saveOutline(v: string) {
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
  const rows = [...detail.value[key], template]
  await saveTable(path, key, rows)
}

async function subInsert(path: string, key: string, idx: number, template: Record<string, unknown>) {
  const rows = [...detail.value[key]]
  rows.splice(idx, 0, template)
  await saveTable(path, key, rows)
}

async function subRemove(path: string, key: string, idx: number) {
  const rows = detail.value[key].filter((_: unknown, i: number) => i !== idx)
  await saveTable(path, key, rows)
}

async function saveTable(path: string, key: string, rows: unknown[]) {
  if (!detail.value) return
  try {
    await api.patchUnit(civ.value, detail.value.unit_id, { field: path, value: rows })
    setDetail(key, rows)
    ElMessage.success({ message: `${key} 已更新`, duration: 1000 })
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

onMounted(async () => {
  await loadCivs()
  if (civs.value.length) await switchCiv(0)
})
</script>

<style scoped>
.editor { height: 100%; display: flex; flex-direction: column; }
.toolbar { padding: 8px 12px; border-bottom: 1px solid #34373a; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.lbl { color: #9a9a9a; font-size: 12px; }
.civ-btns { display: flex; gap: 3px; flex-wrap: wrap; max-width: 60%; }
.civ-btn { font-size: 11px; padding: 2px 6px; border-radius: 4px; cursor: pointer; color: #d4d4d4; background: #2b2d30; border: 1px solid #3c3f41; }
.civ-btn.active { background: #3574f0; border-color: #3574f0; color: #fff; }
.count { color: #9a9a9a; font-size: 12px; }
.body { flex: 1; display: flex; min-height: 0; }
.list { width: 280px; border-right: 1px solid #34373a; display: flex; flex-direction: column; }
.form { flex: 1; min-width: 0; display: flex; }
.form-scroll { flex: 1; overflow: auto; padding: 12px 16px; }
.group-title { color: #e6e6e6; font-weight: 600; font-size: 13px; border-top: 1px solid #34373a; margin: 14px 0 8px; padding-top: 10px; }
.group-title:first-child { border-top: none; margin-top: 0; padding-top: 0; }
.grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px 12px; }
.dual-table { display: flex; gap: 12px; margin-top: 8px; }
.half { flex: 1; min-width: 0; }
.sub-label { color: #9a9a9a; font-size: 11px; margin-bottom: 4px; }
.costs { display: flex; gap: 12px; }
.cost-row { flex: 1; display: flex; gap: 6px; }
.flags { display: flex; gap: 16px; margin-bottom: 10px; flex-wrap: wrap; }
</style>
