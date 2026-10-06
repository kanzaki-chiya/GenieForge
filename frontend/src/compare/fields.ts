// 各数据表的字段定义（并排对比页与各数据页共用同一套定义）。
//
// - scalar：单值字段。`key` 是详情接口返回的键；`path` 是写回时的点路径（省略即同 key）。
// - list：子表字段。`path` 是写回时 PATCH 的字段名；`columns` 只用于展示列；
//   `pick` 用于把详情里的行（如文明的 resources 是 {index,value,name}）还原成可写回的值。

export type TableKey = 'techs' | 'units' | 'civs' | 'effects'

export interface ScalarField {
  key: string
  label: string
  path?: string
}

export interface ListColumn {
  key: string
  label: string
}

export interface ListField {
  key: string
  label: string
  path: string
  columns: ListColumn[]
  pick?: (row: any) => unknown
}

export interface TableFields {
  scalar: ScalarField[]
  list: ListField[]
}

export const TABLES: TableKey[] = ['techs', 'units', 'civs', 'effects']

export const TABLE_LABELS: Record<TableKey, string> = {
  techs: '科技',
  units: '单位',
  civs: '文明',
  effects: '效果'
}

export const TABLE_ROUTES: Record<TableKey, string> = {
  techs: '/techs',
  units: '/units',
  civs: '/civs',
  effects: '/effects'
}

export function isTableKey(value: string): value is TableKey {
  return (TABLES as string[]).includes(value)
}

export function scalarPath(f: ScalarField): string {
  return f.path || f.key
}

export const FIELDS: Record<TableKey, TableFields> = {
  techs: {
    scalar: [
      { key: 'name', label: '内部名称' },
      { key: 'type', label: '类型' },
      { key: 'civ', label: '文明' },
      { key: 'repeatable', label: '可重复' },
      { key: 'full_tech_mode', label: 'Full Tech Mode' },
      { key: 'icon_id', label: '图标' },
      { key: 'effect_id', label: '效果' },
      { key: 'language_dll_name', label: '语言名' },
      { key: 'language_dll_description', label: '描述' },
      { key: 'language_dll_help', label: '帮助' },
      { key: 'language_dll_tech_tree', label: '科技树' }
    ],
    list: [
      { key: 'required_techs', label: '前置科技', path: 'required_techs', columns: [] },
      {
        key: 'resource_costs',
        label: '费用',
        path: 'resource_costs',
        columns: [
          { key: 'type', label: '资源' },
          { key: 'amount', label: '数量' }
        ]
      },
      {
        key: 'research_locations',
        label: '研究位置',
        path: 'research_locations',
        columns: [
          { key: 'location_id', label: '建筑' },
          { key: 'research_time', label: '研究时间' },
          { key: 'button_id', label: '按钮' },
          { key: 'hot_key_id', label: '快捷键' }
        ]
      }
    ]
  },
  units: {
    scalar: [
      { key: 'name', label: '内部名称' },
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
      { key: 'base_armor', label: '基础护甲', path: 'type_50.base_armor' },
      { key: 'max_range', label: '最大射程', path: 'type_50.max_range' },
      { key: 'min_range', label: '最小射程', path: 'type_50.min_range' },
      { key: 'reload_time', label: '装填时间', path: 'type_50.reload_time' },
      { key: 'icon_id', label: '图标' },
      { key: 'special_graphic', label: 'Special Graphic', path: 'creatable.special_graphic' },
      { key: 'dying_graphic', label: 'Dying Graphic' },
      { key: 'enabled', label: 'Enabled' },
      { key: 'disabled', label: 'Disabled' },
      { key: 'hide_in_editor', label: 'Hide in Editor' },
      { key: 'hero_mode', label: 'Hero Mode', path: 'creatable.hero_mode' },
      { key: 'interaction_mode', label: 'Interaction' },
      { key: 'combat_level', label: 'Combat Level' },
      { key: 'sort_number', label: 'Sort Number' },
      { key: 'interface_kind', label: 'Interface Kind' },
      { key: 'obstruction_type', label: '障碍类型' },
      { key: 'obstruction_class', label: '障碍类别' }
    ],
    list: [
      {
        key: 'attacks',
        label: '攻击',
        path: 'type_50.attacks',
        columns: [
          { key: 'class_', label: '类别' },
          { key: 'amount', label: '数值' }
        ]
      },
      {
        key: 'armors',
        label: '护甲',
        path: 'type_50.armours',
        columns: [
          { key: 'class_', label: '类别' },
          { key: 'amount', label: '数值' }
        ]
      },
      {
        key: 'resource_costs',
        label: '费用',
        path: 'creatable.resource_costs',
        columns: [
          { key: 'type', label: '资源' },
          { key: 'amount', label: '数量' }
        ]
      },
      {
        key: 'resource_storages',
        label: '资源存储',
        path: 'resource_storages',
        columns: [
          { key: 'type', label: '资源' },
          { key: 'amount', label: '数量' }
        ]
      },
      {
        key: 'train_locations',
        label: '训练位置',
        path: 'creatable.train_locations',
        columns: [
          { key: 'unit_id', label: '建筑 ID' },
          { key: 'train_time', label: '时间' },
          { key: 'button_id', label: '按钮' },
          { key: 'hot_key_id', label: '快捷键' }
        ]
      },
      {
        key: 'damage_graphics',
        label: 'Damage Graphics',
        path: 'damage_graphics',
        columns: [
          { key: 'graphic_id', label: '图形 ID' },
          { key: 'damage_percent', label: '伤害阈值 %' },
          { key: 'apply_mode', label: '模式' }
        ]
      }
    ]
  },
  civs: {
    scalar: [
      { key: 'name', label: '内部名称' },
      { key: 'player_type', label: 'Player Type' },
      { key: 'icon_set', label: 'Icon Set' },
      { key: 'tech_tree_id', label: '科技树' },
      { key: 'team_bonus_id', label: '团队加成' }
    ],
    list: [
      {
        key: 'resources',
        label: '资源',
        path: 'resources',
        columns: [],
        pick: (row) => (row && typeof row === 'object' && 'value' in row ? row.value : row)
      }
    ]
  },
  effects: {
    scalar: [{ key: 'name', label: '内部名称' }],
    list: [
      {
        key: 'effect_commands',
        label: '效果命令',
        path: 'effect_commands',
        columns: [
          { key: 'type', label: '类型' },
          { key: 'a', label: 'A' },
          { key: 'b', label: 'B' },
          { key: 'c', label: 'C' },
          { key: 'd', label: 'D' }
        ]
      }
    ]
  }
}
