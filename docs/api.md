# 公共 API 文档

基址：`http://127.0.0.1:8342`（仅监听本机）
鉴权：无需 API Key。本机脚本 / Agent 可直接调用；浏览器发起的请求只接受来自应用自身页面（`127.0.0.1:8342`、`localhost:8342`）与前端开发服务器（`:5173`）的 `Origin`，其他网页的请求返回 `403`。`Host` 也必须是 `127.0.0.1` 或 `localhost`。
在线文档：启动后访问 `/docs`（OpenAPI/Swagger，自动生成，以它为准）

大部分数据接口需要先 `POST /api/dat/load`，未加载时返回 `409`。

## 端点总表

### 基础

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查与版本 |
| GET / PUT | `/api/config` | 读取 / 更新配置（字段见下方「配置项」） |
| GET | `/api/meta/{name}` | 枚举表：`resource-types` / `effect-types` / `effect-attributes` / `armors` / `civ-resources` / `terrain-tables` / `unit-types` / `tech-types` |

### dat 加载与编辑

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/dat/load` | 加载 dat（body `{path}`），构建引用索引并加载语言文件 |
| GET | `/api/dat/info` | 当前 dat 版本、路径、是否有未保存修改、各表数量 |
| POST | `/api/dat/save` | 保存（body 可选 `{path}`，省略则覆盖原文件），并生成一条 `saved` 版本快照 |
| POST | `/api/dat/reload-language` | 重新加载配置中的语言文件 |
| POST | `/api/dat/undo` | 撤销一步 |
| POST | `/api/dat/redo` | 重做一步 |
| GET | `/api/dat/changes` | 查看本次修改记录（撤销栈中的结构化改动） |

### 数据表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/techs` | 科技列表（`?page=&page_size=&q=`，`q` 为名称包含匹配） |
| GET | `/api/techs/names` | 全部科技 ID + 名称 |
| GET | `/api/techs/{id}` | 科技详情（前置科技、费用、研究位置等） |
| PATCH | `/api/techs/{id}` | 修改字段：body `{field, value}`，或 `{字段: 值, …}` 一次改多个 |
| GET | `/api/effects` | 效果列表（`?page=&page_size=`，不支持名称过滤，按名称找请用 `/api/search`） |
| GET | `/api/effects/names` | 全部效果 ID + 名称 |
| GET | `/api/effects/{id}` | 效果详情（含效果指令） |
| PATCH | `/api/effects/{id}` | 修改字段：body `{field, value}` |
| GET | `/api/civs` | 文明列表 |
| GET | `/api/civs/{id}` | 文明详情（资源、科技树 / 团队加成引用） |
| PATCH | `/api/civs/{id}` | 修改字段：body `{field, value}` |
| GET | `/api/units?civ=` | 某文明的单位列表（`civ` 必填；可选 `q`、`only_present`、`page`、`page_size`） |
| GET | `/api/units/{unit_id}` | 主单位完整属性（攻击 / 护甲 / 费用） |
| GET | `/api/units/{civ}/{unit_id}` | 某文明下该单位的数据 |
| PATCH | `/api/units/{civ}/{unit_id}` | 修改某文明下该单位的字段：body `{field, value}` |
| POST | `/api/copy` | 整条复制：body `{table, src, dst, civ?}`（`table` 为 `techs` / `effects` / `civs` / `units`，`units` 需 `civ`） |

所有修改都进入撤销栈。字段用点路径表示，例如 `resource_costs.0.amount`。

### 查询与引用

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/search?q=` | 跨科技 / 效果 / 文明按名称搜索（最多 100 条） |
| GET | `/api/names/{id}?table=` | 名称解析；省略 `table` 时在科技 / 效果 / 文明中查找 |
| GET | `/api/refs/forward/{table}/{id}` | 该条目引用了谁 |
| GET | `/api/refs/reverse/{table}/{id}` | 谁引用了该条目 |

### 批量修改

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/batch/preview` | 预览：body `{targets, ops}`，返回受影响条目与旧值 / 新值 |
| POST | `/api/batch` | 执行（可整体撤销） |

- `targets`：数组，每项与补丁 `target` 相同（`table` + `name` / `name_pattern` / `signature`）。
- `ops`：数组，每项 `{op, field, value}`，`op` 为 `set` / `add` / `multiply`。
- 注意：批量修改的 `field` 不支持 `resource_costs.gold` 这类语义写法，需写下标；对整数字段使用小数倍率会得到小数，请使用整数结果。

### 对比

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/diff` | 对比两个 dat（body `{base, target}`），返回各表增删数量、逐条变更与 ID 漂移 |
| POST | `/api/diff/target/load` | 按路径加载一个对比用的目标 dat（body `{path}`），不影响当前编辑的 dat |
| POST | `/api/diff/target/load-version` | 按版本 id 加载对比目标（body `{id}`），返回内容同 `/target/load`，另附 `version` |
| GET | `/api/diff/target/entity/{table}/{id}?civ=` | 读取目标 dat 中某条目的详情（结构与当前 dat 详情相同） |

### 补丁

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/patch/preview` | 预览：body `{patch}`（YAML 文本）或 `{path}`，不修改数据 |
| POST | `/api/patch/apply` | 应用补丁（可整体撤销），返回逐步结果与汇总 |
| POST | `/api/patch/generate` | 从两个 dat 的差异生成补丁：body `{base, target}` |
| POST | `/api/patch/from-changes` | 从本次修改记录生成补丁 YAML：body `{indices?}`，返回 `{yaml, count, skipped}` |
| GET | `/api/patch/list` | 列出 `patches/` 目录下的补丁 |
| POST | `/api/patch/save` | 保存补丁：body `{name, content}`（文件名只保留字母、数字、`_`、`-`） |
| DELETE | `/api/patch/{name}` | 删除补丁 |

### 版本、Git 与更新

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/version/list` | 版本列表：`{versions, total_size}`（`total_size` 为快照目录实际占用字节） |
| POST | `/api/version/checkout` | 回滚到某个版本：body `{id, force?}`，加载快照内容，工作路径仍是原 dat，需保存才写回 |
| POST | `/api/version/import` | 把任意 dat 存为版本：body `{path, label}`，路径不存在返回 400 |
| DELETE | `/api/version/{id}` | 删除版本（没有其他记录引用同一快照时一并删除快照文件） |
| POST | `/api/git/init` | 在补丁目录初始化 Git 仓库 |
| GET | `/api/git/status` | 补丁目录的 Git 状态 |
| GET | `/api/git/log?n=` | 提交历史 |
| POST | `/api/git/commit` | 提交：body `{message}` |
| POST | `/api/git/checkout` | 切换到某提交：body `{ref}` |
| GET | `/api/update/check` | 检查 GitHub Releases 是否有新版本 |
| POST | `/api/update/download` | 下载更新包到应用缓存目录：body `{asset_url, sha256?}`，`asset_url` 必须是本项目 GitHub Release 的下载地址 |

#### 版本快照存放位置

`platformdirs.user_data_dir("GenieForge", appauthor=False) / "versions"`（Windows 下即
`%LOCALAPPDATA%\GenieForge\versions`）：

- `snapshots/<sha256>.dat`：快照文件，按内容哈希命名，**内容相同的 dat 只存一份**；
- `index.json`：版本记录列表，原子写入（先写临时文件再 `os.replace`），损坏时按空列表处理。

每条记录为 `{id, label, kind, sha256, size, source_path, created_at}`，`kind` 为 `saved`（保存时自动生成）
或 `imported`（`/api/version/import` 导入）。`id` 自增并持久化，重启后不重复。
`POST /api/dat/save` 成功后自动生成一条 `saved` 记录。

## 配置项

`PUT /api/config` 接受以下字段（均可选）：

| 字段 | 说明 |
|------|------|
| `language_file` | 游戏语言文件 `key-value-strings-utf8.txt` 的路径 |
| `language` | 界面语言（`zh-CN` / `en`） |
| `update_channel` | 更新通道（默认 `stable`） |
| `auto_update` | 是否自动更新 |
| `auto_save` | 是否自动保存 |
| `project_dir` | 补丁工程目录（Git 接口使用，默认 `patches`） |

检查更新时如遇 GitHub 限流，可设置环境变量 `GITHUB_TOKEN`。

## 补丁格式

```yaml
version: 1
based_on: "VER 8.8"          # 可选，仅作记录
steps:
  - name: "织布机金费 30"     # 步骤名，出现在结果报告中
    target:
      table: techs            # techs / effects / civs …
      name: "Loom"            # 1) 名称精确匹配
      # name_pattern: "^C-Bonus"   # 2) 名称正则（Python re.match，从开头匹配）
      # signature: {effect_id: 22} # 3) 签名：effect_id / resource_costs / required_techs
    op: set                   # set / add / multiply / append / remove
    field: "resource_costs.gold.amount"
    value: 30
```

- 三种定位方式按「名称 → 正则 → 签名」依次尝试，前一种有结果就不再往后。
- 命中 0 条记为 `missing`，命中多条记为 `conflict`，两者都不会修改数据。
- 返回的 `summary` 含 `applied` / `conflicts` / `missing` / `unsupported` 计数。

## 数据模型说明

- `Tech.resource_costs` 按实际使用的资源排列，资源类型由 `type` 字段标识（0=Food / 1=Wood / 2=Stone / 3=Gold）。例如「织布机 Loom」只耗黄金，黄金在 `resource_costs.0`，而不是固定下标 3。
- 补丁字段支持语义化资源定位：`resource_costs.gold.amount` 会自动解析为对应下标（`food` / `wood` / `stone` / `gold`）。
- `Civ.tech_tree_id` 与 `Civ.team_bonus_id` 指向 **effects 表**，不是 techs 表。
- `unit_headers` 只含 `exists` / `task_list`；完整单位属性在 `Civ.units[]`，可通过 `/api/units/{unit_id}` 查询。
- 效果指令类型（`EffectCommand.type`）的含义见 `backend/metadata/effect_types.json`。
- 显示名需要配置语言文件；未配置时回退为内部英文名。

## 示例

```bash
# 加载 dat
curl -X POST http://127.0.0.1:8342/api/dat/load \
     -H "Content-Type: application/json" \
     -d '{"path":"D:/AoE2DE/resources/_common/dat/empires2_x2_p1.dat"}'

# 预览并应用补丁（织布机金费改 30）
curl -X POST http://127.0.0.1:8342/api/patch/apply \
     -H "Content-Type: application/json" \
     -d '{"patch":"steps:\n  - target: {table: techs, name: Loom}\n    op: set\n    field: resource_costs.gold.amount\n    value: 30"}'

# 批量修改预览（所有 C-Bonus 开头的科技，第一项费用 ×2）
curl -X POST http://127.0.0.1:8342/api/batch/preview \
     -H "Content-Type: application/json" \
     -d '{"targets":[{"table":"techs","name_pattern":"^C-Bonus"}],"ops":[{"op":"multiply","field":"resource_costs.0.amount","value":2}]}'

# 对比两个版本
curl -X POST http://127.0.0.1:8342/api/diff \
     -H "Content-Type: application/json" \
     -d '{"base":"D:/back/empires2_x2_p1_old.dat","target":"D:/back/empires2_x2_p1_new.dat"}'

# 另存为
curl -X POST http://127.0.0.1:8342/api/dat/save \
     -H "Content-Type: application/json" \
     -d '{"path":"D:/AoE2DE/resources/_common/dat/empires2_x2_p1_mod.dat"}'
```
