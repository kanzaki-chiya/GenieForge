import { defineStore } from 'pinia'
import { reactive } from 'vue'

export type TableKey = 'techs' | 'units' | 'civs' | 'effects'

// 用于生成实体的唯一标识 key
export function getEntityKey(table: TableKey, id: number | string, civId?: number): string {
  if (table === 'units' && civId != null) {
    return `${table}:${civId}:${id}`
  }
  return `${table}:${id}`
}

function isScalar(val: unknown): boolean {
  if (val === null || val === undefined) return true
  const t = typeof val
  return t === 'string' || t === 'number' || t === 'boolean'
}

function getNestedValue(obj: unknown, path: string): unknown {
  if (!obj || typeof obj !== 'object') return undefined
  const parts = path.split('.')
  let cur: unknown = obj
  for (const p of parts) {
    if (!cur || typeof cur !== 'object') return undefined
    cur = (cur as Record<string, unknown>)[p]
  }
  return cur
}

export const useHistoryStore = defineStore('history', () => {
  // 记录每个条目第一次打开时的标量字段快照
  // key: entityKey, value: Record<string, unknown>
  const baselines = reactive<Record<string, Record<string, unknown>>>({})

  // 记录条目当前已被修改的标量字段集
  // key: entityKey, value: Record<string, { original: unknown; current: unknown }>
  const changes = reactive<Record<string, Record<string, { original: unknown; current: unknown }>>>({})

  /**
   * 当条目详情初次加载成功时记录基准值（若已有记录则不覆盖，确保代表会话初次打开的值）
   * @param key 实体键 (例如 'techs:22' 或 'units:0:4')
   * @param detail 对象详情
   * @param scalarKeys 可选：指定作为标量检测的字段列表，如果不传则自动扫描第一层标量字段
   */
  function recordBaseline(key: string, detail: Record<string, unknown>, scalarKeys?: string[]) {
    if (baselines[key]) return // 已存在首次快照，不重复覆盖

    const snapshot: Record<string, unknown> = {}
    if (scalarKeys && scalarKeys.length > 0) {
      for (const k of scalarKeys) {
        if (k in detail && isScalar(detail[k])) {
          snapshot[k] = detail[k]
        }
      }
    } else {
      for (const [k, v] of Object.entries(detail)) {
        if (isScalar(v)) {
          snapshot[k] = v
        }
      }
    }
    baselines[key] = snapshot
  }

  /**
   * 也可以单字段记入基准值（如果需要支持嵌套标量路径如 'type_50.base_armor'）
   */
  function ensureFieldBaseline(key: string, fieldPath: string, value: unknown) {
    if (!baselines[key]) {
      baselines[key] = {}
    }
    if (!(fieldPath in baselines[key]) && isScalar(value)) {
      baselines[key][fieldPath] = value
    }
  }

  /**
   * 当字段发生变动或同步时，更新该字段与原值的比较状态
   */
  function trackFieldChange(key: string, fieldPath: string, currentValue: unknown) {
    const baselineObj = baselines[key]
    if (!baselineObj || !(fieldPath in baselineObj)) {
      return
    }
    const original = baselineObj[fieldPath]

    // 比较当前值与原值
    const isModified = !Object.is(original, currentValue) && String(original) !== String(currentValue)

    if (isModified) {
      if (!changes[key]) {
        changes[key] = {}
      }
      changes[key][fieldPath] = { original, current: currentValue }
    } else {
      if (changes[key] && fieldPath in changes[key]) {
        delete changes[key][fieldPath]
        if (Object.keys(changes[key]).length === 0) {
          delete changes[key]
        }
      }
    }
  }

  /**
   * 按已记录的原值，逐个字段（包括 required_techs.0、resource_costs.0.amount 等嵌套路径）
   * 从最新 detail 取值，重新计算该条目的改动状态。
   * 每次加载详情时在 recordBaseline 之后调用。
   * mapPath：保存路径与 detail 结构不一致时（如单位的 type_50.base_armor 对应 detail.base_armor），把前者映射为后者。
   * 注意：已知限制——撤销的是别的条目时，那个条目的列表圆点要等下次打开它时才更新。
   */
  function syncEntity(key: string, detail: unknown, mapPath?: (fieldPath: string) => string) {
    const baselineObj = baselines[key]
    if (!baselineObj || !detail) return

    for (const fieldPath of Object.keys(baselineObj)) {
      const currentVal = getNestedValue(detail, mapPath ? mapPath(fieldPath) : fieldPath)
      trackFieldChange(key, fieldPath, currentVal)
    }
  }

  /**
   * 检查单个字段是否有被修改
   */
  function isFieldModified(key: string, fieldPath: string, currentValue?: unknown): boolean {
    const baselineObj = baselines[key]
    if (!baselineObj || !(fieldPath in baselineObj)) {
      return false
    }
    if (currentValue !== undefined) {
      const orig = baselineObj[fieldPath]
      return !Object.is(orig, currentValue) && String(orig) !== String(currentValue)
    }
    return Boolean(changes[key]?.[fieldPath])
  }

  /**
   * 获取某个字段的原值
   */
  function getOriginalValue(key: string, fieldPath: string): unknown {
    return baselines[key]?.[fieldPath]
  }

  /**
   * 检查某个条目（以 key 或者 table+id）是否有任何改动
   */
  function isEntityModified(key: string): boolean {
    const c = changes[key]
    return Boolean(c && Object.keys(c).length > 0)
  }

  /**
   * 检查条目是否修改（重载方便视图中调用，支持 table, id, civId）
   */
  function hasChanges(table: TableKey, id: number | string, civId?: number): boolean {
    const key = getEntityKey(table, id, civId)
    return isEntityModified(key)
  }

  /**
   * 清空所有原值与修改记录（重新加载 dat 时调用）
   */
  function clearAll() {
    for (const k of Object.keys(baselines)) {
      delete baselines[k]
    }
    for (const k of Object.keys(changes)) {
      delete changes[k]
    }
  }

  return {
    baselines,
    changes,
    recordBaseline,
    ensureFieldBaseline,
    trackFieldChange,
    syncEntity,
    isFieldModified,
    getOriginalValue,
    isEntityModified,
    hasChanges,
    clearAll,
  }
})
