# 方案 C：帝国时代2决定版 Mod 桌面工具 —— 产品与技术方案

> 版本：v1.0　|　日期：2026-09-29
> 目标：在开源库 `genieutils-py` 之上，构建一个 **Python 后端 + Web 前端** 的桌面应用，解决 AGE 的三大痛点，并支持 GitHub 自动更新、版本管理、批量修改、美观的批量对比、mod 补丁生成，以及面向 Agent 的公共 API。

---

## 1. 项目概述

### 1.1 背景与痛点回顾

| 痛点 | 现状 | 本方案目标 |
|------|------|-----------|
| 无增量修改 | 官方每次更新，ID 漂移，全量重做 | 语义化补丁，官方更新后一键套用，只改少量适配 |
| 无对比功能 | 两个 dat 差异靠人肉对照 | 结构化批量 diff，可视化、可筛选、可批量操作 |
| 无关联跳转 | tech/效果全靠编号人工搜索 | 引用关系图 + 反向索引，双向跳转 |
| 无版本管理 | 修改记录散落在 `修改清单.txt` | 补丁文件 + Git 版本管理，可回溯/重放 |
| 无自动化接口 | 只能手动点 UI | 公共 REST API，Agent 可自动完成修改 |

### 1.2 设计原则

1. **核心与界面解耦**：所有能力先做成后端服务（Python 函数 + REST API），UI 只是调用方。这样 Agent 和桌面 UI 共用同一套能力。
2. **数据只解析一次**：dat 解析约 10~14s，解析结果在内存中缓存，读写走内存对象模型，不重复解析。
3. **字节级无损**：写回必须字节级无损（字符串 latin-1 双向处理），保证官方格式完全兼容。
4. **桌面为主、浏览器兼容**：同一套前端，既能跑在桌面窗口里，也能在浏览器打开（便于调试与 Agent 远程访问）。
5. **美观 + 高效 UE**：虚拟滚动、键盘快捷键、主题切换、批量操作入口显性化。

---

## 2. 总体架构

### 2.1 架构图

```
┌──────────────────────────────────────────────────────────────────┐
│  桌面窗口（pywebview 原生窗口）                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  前端 SPA（Vue 3 + TS + Element Plus）                      │  │
│  │  表格编辑 · 批量操作 · diff 视图 · 引用跳转 · 补丁管理 · 版本 │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │  HTTP / WebSocket                  │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                 ┌────────────▼─────────────┐
                 │  FastAPI（localhost:PORT） │──> /docs (OpenAPI 自动文档)
                 │   REST API + WS 推送       │<── 供 Agent 调用的「公共 API」
                 └────────────┬─────────────┘
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
┌───────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ 数据核心 Core  │   │  diff / 补丁引擎  │   │  引用索引 + 名称  │
│ 解析/缓存/写回 │   │ 三级 diff + patch │   │  正向/反向跳转    │
└───────┬───────┘   └──────────────────┘   └──────────────────┘
        │
        ▼
   genieutils-py（latin-1 补丁后）+ 语言文件 + AGE3Names 元数据
```

### 2.2 为什么选这个结构

- **FastAPI 做后端**：自带 OpenAPI/Swagger 文档（`/docs`），天然满足「公共 API 供 Agent 调取」；Pydantic 做参数校验与响应模型。
- **pywebview 做桌面壳**：Python 直接开原生窗口（Windows 用 Edge WebView2），无需打包 Chromium，体积小；同一份前端也能在浏览器跑。
- **Vue 3 + Element Plus**：中文生态成熟、表格/树/对话框/抽屉组件齐全，适合「美观 + 大量表格数据」场景。

---

## 3. 技术栈详解

### 3.1 后端

| 组件 | 选型 | 说明 |
|------|------|------|
| 语言 | Python 3.11+ | 与 genieutils-py 要求一致 |
| Web 框架 | FastAPI + Uvicorn | REST + 自动 OpenAPI 文档 + WebSocket |
| 数据模型 | Pydantic v2 | 请求/响应校验 |
| dat 核心 | genieutils-py（含 latin-1 补丁） | 解析/写回决定版 dat |
| 任务队列 | 内置线程 + `asyncio` | 解析/写回等重任务异步化 |
| 配置 | `platformdirs` + JSON | 跨平台配置目录 |

### 3.2 前端

| 组件 | 选型 | 说明 |
|------|------|------|
| 框架 | Vue 3 + TypeScript | Composition API |
| 构建 | Vite | 快速 HMR |
| UI 库 | Element Plus（备选 Naive UI） | 表格/树/抽屉/表单 |
| 表格 | 虚拟滚动（`vue-virtual-scroller` 或 Element Plus v2 内置） | 万级行流畅 |
| diff 渲染 | 自研结构 diff 树 + 红绿高亮 | 侧边对比 |
| 状态 | Pinia | 全局状态（当前 dat、选择集、索引） |
| 图表 | ECharts（可选，做数量统计图） | 摘要可视化 |

### 3.3 桌面壳

| 方案 | 选型 | 说明 |
|------|------|------|
| 桌面壳 | **pywebview**（主） | Python 原生窗口，加载 `http://127.0.0.1:PORT` |
| 兜底 | 浏览器模式 | 开发调试 / 远程访问直接用浏览器打开 |

> 说明：pywebview 与 FastAPI 的 JS↔Python 通信，统一走 HTTP REST（而非 pywebview 的 js_api 桥），这样「桌面 UI」和「Agent」走完全相同的 API，逻辑单一。

### 3.4 打包与自动更新

| 组件 | 选型 | 说明 |
|------|------|------|
| 打包 | PyInstaller（onedir / 单 exe） | 连同 Vue 构建产物打包 |
| 更新源 | GitHub Releases | 应用自身更新走 GitHub |
| 更新器 | 内置轻量 updater | 拉取最新 Release → 校验 SHA256 → 替换重启 |
| 更新协议 | semver 比较 + `latest` 标记 | 支持稳定/预发布通道 |

### 3.5 数据核心依赖

- `genieutils-py`：读/写 `empires2_x2_p1.dat`（支持 `VER 7.8 / 8.4 / 8.8`）。
- **语言文件**：`key-value-strings-utf8.txt`（游戏目录内，`编号 "文本"` 格式），用于本地化显示名。
- **枚举元数据**：`AGE3NamesV0007.ini`（护甲/地形/文明资源 500 项等枚举名），随应用内置并可扩展。

---

## 4. 功能需求明细

### 4.1 游戏目录配置与名称本地化

- **配置游戏目录**：手动选择或自动探测 AoE2 DE 安装目录（Steam：`steamapps/common/AoE2DE`；微软商店版自动读注册表）。
- **自动发现数据文件**：在游戏目录下定位 `empires2_x2_p1.dat` 与语言文件 `key-value-strings-utf8.txt`（找不到时允许手动指定）。
- **两层命名解析**：
  1. **内部名**（英文，如 `Loom`、`British`）：来自 dat 的 `name` 字段，用作「稳定匹配键」。
  2. **显示名**（中文，如「织布机」「不列颠」）：由 `language_dll_name` 等编号查语言文件得到。
- UI 中所有列表/跳转默认显示**中文名**，内部名作次级标注（如 `织布机 (Loom) #22`）。
- 支持语言切换（简中/英文），只需切换语言文件来源。

### 4.2 编辑功能（覆盖 AGE 能力点）

- **表浏览与编辑**：科技（Techs）、效果（Effects）、效果指令（EffectCommand）、文明（Civs）、文明单位覆盖（Civ.units）、单位头（UnitHeaders）、科技树（TechTree）等。
- **单元格编辑**：双击/回车编辑，按字段类型校验（int / float / 枚举下拉 / 引用选择器）。
- **引用型字段用选择器而非裸编号**：例如 `effect_id` 下拉显示目标效果中文名，选完即完成跳转定位。
- **撤销/重做**：基于命令栈（command pattern）实现，支持跨表撤销。
- **搜索/筛选**：按名称、ID、任意字段过滤；支持正则。

### 4.3 批量修改（核心能力）

- **多选批量**：表格多选 → 右键 → 批量操作（赋值 / 加 / 乘 / 相对增减）。
- **条件批量**：规则构建器（条件 + 动作），例如「所有 `C-Bonus*` 科技的 `resource_costs` 金费 ×2」。
- **查找替换**：全表按字段查找替换。
- **批量模板**：常用批量规则保存为模板，可重复套用（如「双倍文明特效」「种田科技效率表」）。
- **应用预览**：批量操作前展示影响行数 + 前后值预览，确认后执行，可整体撤销。

### 4.4 美观的批量对比差异（核心能力）

- **三级 diff**：
  1. **表级**：各表数量变化（科技 +N、文明 +N、效果 +N）。
  2. **记录级**：同名记录逐字段差异。
  3. **引用级**：ID 漂移检测（同名实体 ID 变化）。
- **可视化**：
  - 顶部摘要卡片（新增/删除/修改数量，可点按跳转）。
  - 左旧右新双栏并排，字段差异红/绿高亮。
  - 变更列表可按「表 / 变化类型 / 关键词」筛选、排序。
  - 支持「只看我关心的表」勾选，隐藏无变化项。
- **批量操作**：在 diff 结果上多选，批量「接受/回退/复制到补丁」。

### 4.5 生成 / 应用 mod 补丁（核心能力）

- **补丁 DSL**（YAML）：语义化描述修改（见 §5.4），用「名称/签名」定位而非裸 ID。
- **生成补丁**：
  1. 从「官方版 vs 我的 mod 版」diff 反向生成补丁；
  2. 或从当前编辑会话的变更记录生成补丁。
- **应用补丁**：选官方新版 dat → 应用补丁 → 预览冲突报告（找不到目标/匹配多个）→ 写回新 mod。
- **补丁管理**：补丁列表、启停、排序、合并、导出/导入，每个补丁是独立可版本化文件。

### 4.6 关联跳转

- **正向跳转**：Tech → Effect / 前置科技 / 所属文明；Civ → 科技树 / 团队加成 / 单位覆盖。
- **反向跳转**：Effect → 引用它的 Tech 列表；Unit → 覆盖它的文明列表。
- **交互**：引用字段点击跳转，悬停显示中文名预览，前进/后退导航历史（面包屑）。

### 4.7 版本管理

- **工程模型**：`工程 = 基准官方版本 + 补丁集合`。
- **版本历史**：记录每次应用补丁/编辑的快照，可回溯、可对比任意两个版本。
- **Git 集成**：补丁与配置用 Git 管理（提交/回滚/分支），便于备份与多人协作。
- **基准版本跟踪**：记录当前工程基于哪个官方 dat（版本号 + 文件哈希），官方更新时提示「可 rebase」。

### 4.8 GitHub 连接与自动更新

- **应用自身自动更新**：启动时查 GitHub Releases → 有新版提示 → 下载 → 校验 → 替换重启；支持「检查更新」「自动/手动」开关。
- **Mod 工程 GitHub 同步**：连接一个 GitHub 仓库，push/pull 补丁与配置，实现备份与协作。

### 4.9 公共 API（供 Agent 调取）

- 完整 REST API（见 §7），自带 OpenAPI 文档（`/docs`）。
- **本地鉴权**：localhost 绑定 + 可选 API Token（`X-API-Key`），保证只有本机/授权 Agent 能改。
- **设计目标**：Agent 可「读数据 → 分析 → 批量修改 → 应用补丁 → 写回」，全程无需人工点 UI。

### 4.10 其他（UE）

- **主题**：深色/浅色，跟随系统。
- **快捷键**：保存 `Ctrl+S`、查找 `Ctrl+F`、跳转引用 `Ctrl+Click`、撤销 `Ctrl+Z` 等。
- **布局**：左导航树 + 中间主表 + 右侧详情面板 + 底部（diff/日志）抽屉，可拖拽缩放、可记忆。

---

## 5. 核心实现逻辑

### 5.1 数据核心：解析 / 缓存 / 写回

```
DatCore（单例，线程安全）
  ├─ load(path) -> DatFile   # zlib 解压 + genieutils 解析（~10s，缓存）
  ├─ get()    -> 当前 DatFile 对象
  ├─ save(path)              # 对象 -> 字节（latin-1 补丁）-> zlib 压缩 -> 落盘
  ├─ dirty 标记 / 撤销栈
  └─ hash 校验（解析后与写回前各算一次，保证无损）
```

- **关键补丁（必须内置）**：字符串 latin-1 双向（`String.from_bytes` / `String.to_bytes` / `write_debug_string`），否则非 ASCII 字符串写回损坏。此补丁已实测验证，封装为 `genieutils_fix.apply()`。
- **异步化**：`load` / `save` / `diff` 是重任务，用后台线程 + 前端进度条（WebSocket 推送进度）。

### 5.2 名称解析

```
NameResolver
  ├─ 内部名表  : Tech.name / Civ.name / Effect.name（dat 内建）
  ├─ 语言表    : key-value-strings-utf8.txt -> {int: str}（id -> 中文）
  └─ 枚举表    : AGE3Names*.ini -> {表名: {int: str}}（护甲/地形/资源/效果指令类型）
  resolve(entity) -> { internal, display, id }
```

- 显示名优先级：`language_dll_name` 查语言表 → 内部 `name` → `#ID`。
- 效果指令 `type` 的数字含义由枚举表映射（需维护「type → 含义」表，初始内置，支持编辑）。

### 5.3 结构化 diff 算法

```
diff(a: DatFile, b: DatFile) -> DiffReport
  对每张表：
    1. 建 key 映射（默认 name，可选 id 对齐）
    2. 集合差：added = keys(b) - keys(a)；removed = keys(a) - keys(b)
    3. 交集内逐字段对比（字段类型感知：数值/枚举/引用）
    4. 引用级：检测同名实体 id 变化（漂移）
  产出：按表分组、按变化类型分类的 ChangeItem 列表
```

- **性能**：先算每个记录的「指纹」（字段哈希），指纹相同跳过；只对变化记录做字段级展开。两个 8.3 万 KB 级对象模型 diff 控制在秒级。
- **ChangeItem** 结构：`{ table, key, id_a, id_b, changes: [{field, old, new}] }`，前端据此渲染红绿高亮。

### 5.4 语义补丁引擎

```yaml
# patch.yaml 示例
version: 1
based_on: "VER 8.4"          # 声明基准版本
steps:
  - name: "织布机金费 30"
    target: { table: techs, name: "Loom" }
    op: set
    field: "resource_costs.2.amount"     # 2 = gold 下标
    value: 30

  - name: "银行业贸易率 x1.1"
    target: { table: techs, name: "Banking" }
    op: multiply
    field: "effect.d"                    # 效果指令系数
    value: 1.1

  - name: "双倍文明特效"
    target: { table: techs, name_pattern: "C-Bonus*" }
    op: rule
    rule: "double_civ_bonus"             # 自定义规则函数
```

**匹配策略（解决 ID 漂移）**：

```
resolve_target(step.target, dat):
  1. 名称精确匹配（name == ...）
  2. 名称模式匹配（name_pattern 正则）
  3. 签名匹配（效果指令集合 + 费用 + 前置科技集合 的指纹）
  4. 相对位置匹配（同文明科技树内相对位置）
  返回：唯一命中 / 多个候选 / 未命中
```

- 唯一命中 → 应用；多个候选 → 进入冲突报告，人工/规则二选一；未命中 → 标记「需适配」。
- **op 类型**：`set` / `add` / `multiply` / `relative` / `rule`（自定义 Python 规则）/ `append` / `remove`。
- **应用结果**：生成 `ApplyReport`（成功数 / 冲突数 / 跳过数 + 明细），前端冲突面板逐条处理。

### 5.5 引用索引

```
RefIndex（解析后一次性构建，随编辑增量更新）
  ├─ forward:  {table: {id: [(target_table, target_id, field), ...]}}
  └─ reverse:  {table: {id: [(src_table, src_id, field), ...]}}
```

- 构建规则（硬编码引用关系表）：`tech.effect_id → effects`、`tech.required_techs[] → techs`、`civ.tech_tree_id/team_bonus_id → techs`、`civ.units[] → unit_headers` 等。
- 查询：`lookup_forward(table,id)` / `lookup_reverse(table,id)`，前端用于跳转与「谁引用了这个」。

### 5.6 批量修改执行

```
BatchExecutor
  ├─ 收集目标集（多选 / 条件过滤 / 模板）
  ├─ 生成操作集（op + 目标）
  ├─ 预览（影响数 + 前后值）
  └─ 执行（事务式：记录命令到撤销栈 → 逐条应用 → 标记 dirty）
```

- 所有批量操作走**命令模式**，可整体撤销/重做。

### 5.7 撤销 / 重做

- 命令栈：`{undo: fn, redo: fn, desc}`。编辑与批量操作统一入栈。
- 大对象模型下，快照成本高，故用「字段级反向命令」而非全量快照。

### 5.8 性能与大数据量

- **内存对象模型**约 8~10 万级对象，常驻内存。
- **API 响应**：列表接口分页 + 字段投影（只回传需要的列），不整表序列化。
- **前端表格**：虚拟滚动，避免万级 DOM 卡顿。
- **diff**：指纹预筛 + 惰性字段展开。

---

## 6. 数据模型（已实测确认）

```
DatFile
├─ version: str                  # "VER 8.4"
├─ effects: list[Effect]         # Effect { name, effect_commands[] }
│            └─ EffectCommand { type:int, a:int, b:int, c:int, d:float }
├─ unit_headers: list[UnitHeaders]   # 当前 Python 版仅 { exists, task_list }
├─ civs: list[Civ]               # Civ { player_type, name, tech_tree_id,
│                                 #       team_bonus_id, resources[], icon_set, units[] }
│                                 #   units[]: list[Unit|None]（每文明单位覆盖，2382 槽）
├─ techs: list[Tech]             # Tech { required_techs[6], resource_costs[3],
│                                 #        effect_id, name, type, civ, repeatable,
│                                 #        research_locations[], language_dll_* }
└─ tech_tree: TechTree
```

> 注：`unit_headers` 在 genieutils-py 0.1.2 中字段较少（`exists` / `task_list`），完整的单位属性在 `Civ.units[unit_id]`（`Unit` 类，库内最大模块）。若需要「主单位级」元数据，需增强 `UnitHeaders` 解析，作为待办项。

---

## 7. 公共 API 设计

### 7.1 约定

- 基址：`http://127.0.0.1:8342`（端口可配置）
- 鉴权：`X-API-Key`（可关闭，本机默认信任）
- 文档：`/docs`（OpenAPI/Swagger，FastAPI 自动生成）
- 格式：JSON；大列表用 `?page=&page_size=&fields=&q=` 分页/投影/搜索

### 7.2 端点总表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查与版本 |
| GET/PUT | `/api/config` | 配置（游戏目录、语言、端口、Token） |
| POST | `/api/dat/load` | 加载 dat（body: `{path}`），返回元信息 |
| GET | `/api/dat/info` | 当前 dat 版本与各表数量 |
| POST | `/api/dat/save` | 保存（body 可选 `{path}`） |
| GET | `/api/techs` | 科技列表（分页/筛选/投影） |
| GET | `/api/techs/{id}` | 科技详情（含解析后的 effect/前置科技名） |
| PATCH | `/api/techs/{id}` | 修改科技字段 |
| GET | `/api/effects` / `/api/effects/{id}` | 效果列表/详情 |
| GET | `/api/civs` / `/api/civs/{id}` | 文明列表/详情 |
| GET | `/api/units` | 单位查询（按文明/ID） |
| PATCH | `/api/units/{civ}/{unit_id}` | 修改某文明单位覆盖 |
| POST | `/api/batch` | 批量修改（body: 目标集 + op），返回预览/结果 |
| POST | `/api/diff` | 对比两个 dat（body: `{base, target}`） |
| GET | `/api/diff/{job_id}` | 查询 diff 结果 |
| POST | `/api/patch/apply` | 应用补丁（body: 补丁内容或路径） |
| POST | `/api/patch/generate` | 从 diff/变更生成补丁 |
| GET | `/api/search?q=` | 全局搜索（名称/ID，跨表） |
| GET | `/api/refs/forward/{table}/{id}` | 正向引用 |
| GET | `/api/refs/reverse/{table}/{id}` | 反向引用 |
| GET | `/api/names/{id}` | 名称解析（内部名/中文名） |
| GET | `/api/version/list` | 版本历史 |
| POST | `/api/version/checkout` | 回滚到某版本 |
| GET | `/api/update/check` | 检查应用更新 |

### 7.3 示例：批量修改 + 应用补丁（Agent 调用链）

```http
POST /api/dat/load   { "path": "D:/.../empires2_x2_p1.dat" }

# Agent 读取并分析
GET  /api/techs?q=Banking
GET  /api/techs/17   # 返回解析后的效果指令、费用、前置科技名

# Agent 批量修改
POST /api/batch
{
  "targets": [ {"table":"techs","name":"Banking"} ],
  "ops":     [ {"op":"multiply","field":"effect.d","value":1.1} ]
}

# 或直接应用语义补丁
POST /api/patch/apply
{ "patch": "steps:\n  - target: {table: techs, name: Loom}\n    op: set\n    field: resource_costs.2.amount\n    value: 30" }

POST /api/dat/save   { "path": "D:/.../empires2_x2_p1_mod.dat" }
```

---

## 8. 目录结构

```
aoe2-mod-tool/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口 + 路由注册
│   │   ├── api/               # 各资源路由（techs/effects/civs/...）
│   │   ├── core/
│   │   │   ├── dat_core.py    # 解析/缓存/写回
│   │   │   ├── genieutils_fix.py   # latin-1 补丁
│   │   │   ├── diff.py        # 三级 diff
│   │   │   ├── patch.py       # 语义补丁引擎
│   │   │   ├── refs.py        # 引用索引
│   │   │   ├── names.py       # 名称解析
│   │   │   └── batch.py       # 批量执行 + 命令栈
│   │   ├── schemas.py         # Pydantic 模型
│   │   └── config.py          # 配置读写
│   ├── metadata/              # 枚举表（effect type / 护甲 / 资源）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/             # 表格/编辑/diff/补丁/版本/设置
│   │   ├── components/        # 虚拟表格/diff树/引用跳转/批量对话框
│   │   ├── stores/            # Pinia
│   │   └── api/               # 后端 API 封装
│   └── package.json
├── desktop/
│   └── run.py                 # pywebview 启动（开窗口加载 localhost）
├── patches/                   # 用户补丁（Git 管理）
├── build/                     # PyInstaller 配置 + 更新清单
└── docs/
    └── api.md                 # 公共 API 文档（同步自 /docs）
```

---

## 9. 自动更新与版本管理流程

### 9.1 应用自身自动更新

```
启动/定时 -> GET GitHub /repos/{owner}/{repo}/releases/latest
         -> semver 比较本地版本
         -> 有新版本：下载 asset（.zip/exe）
         -> 校验 SHA256（Release 附 checksum）
         -> 写更新标记，退出后由 updater 替换文件并重启
         -> 失败回滚到旧版
```

- 配置项：更新通道（stable / prerelease）、自动/手动、代理。

### 9.2 Mod 工程版本管理

```
工程目录 patches/
  ├── 001_织布机费用.yaml
  ├── 002_种田科技.yaml
  ├── 003_双倍文明特效.yaml
  └── manifest.yaml   # 基准版本 + 补丁顺序 + 官方 dat 哈希

流程：
  官方更新 -> 载入新版 dat -> rebase（重放补丁 -> 冲突报告 -> 人工处理少数冲突）
          -> 生成新版 mod -> 提交 Git（含新基准版本）
```

- `manifest.yaml` 记录基准官方版本号与文件哈希，保证「补丁套用的对象」可追溯。

---

## 10. 分阶段实施计划

| 阶段 | 内容 | 产出 |
|------|------|------|
| P0 | 数据核心封装 + latin-1 补丁 + REST 骨架 | `dat_core` + FastAPI 空壳（已完成 PoC 验证） |
| P1 | 读/写/列表/详情 API + 名称解析 | 可查询、可改、中文名 |
| P2 | 三级 diff + 前端 diff 视图 | 批量对比可视化 |
| P3 | 语义补丁引擎 + 冲突报告 | 增量修改（核心） |
| P4 | 引用索引 + 跳转 + 批量操作 + 撤销 | 完整编辑体验 |
| P5 | 版本管理 + Git 集成 + GitHub 自动更新 | 工程化 |
| P6 | 公共 API 完善 + Agent 对接文档 + 打磨 UE | 自动化接口 |

---

## 11. 风险与对策

| 风险 | 对策 |
|------|------|
| 字符串编码损坏 | latin-1 补丁固化 + 写回前哈希校验 |
| `unit_headers` 字段不完整 | 增强解析；单位属性优先走 `Civ.units` |
| 效果指令 `type` 语义缺失 | 维护内置枚举表（初始从 AGE3Names 提取，支持编辑） |
| 名称重名/变更导致匹配歧义 | 三级匹配 + 签名/位置兜底 + 冲突人工确认 |
| 官方格式再升级 | 版本分支隔离（`VER 8.8` 已区分处理），跟进库更新 |
| 大对象模型性能 | 分页/投影/虚拟滚动/指纹预筛 |
| API 被非授权调用 | localhost 绑定 + 可选 Token，生产可关闭远程 |

---

## 12. 附：与现有成果的衔接

- `scripts/genie_poc.py`（本仓库）：解析/写回/diff 的 PoC，`apply_string_fix()` 直接复用为 `core/genieutils_fix.py`。
- `工具优化设计方案.md`（本仓库）：三大痛点的可行性分析，本方案是其「C 路线」的落地规格。
- 你的 `修改清单.txt` / `新的清单.txt`：作为首批补丁的**来源语料**，可逐条转成补丁 DSL 样例。
