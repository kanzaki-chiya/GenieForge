# 公共 API 文档

基址：`http://127.0.0.1:8342`（端口可配置）
鉴权：可选 `X-API-Key`（默认本机信任；设置 `api_key` 后，写操作需携带该请求头）
在线文档：启动后端后访问 `/docs`（OpenAPI/Swagger，自动生成）

## 端点总表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查与版本 |
| GET / PUT | `/api/config` | 配置（游戏目录、语言、端口、更新通道、GitHub 仓库） |
| POST | `/api/dat/load` | 加载 dat（body `{path}`），返回元信息并构建引用索引 |
| GET | `/api/dat/info` | 当前 dat 版本与各表数量 |
| POST | `/api/dat/save` | 保存（body 可选 `{path}`），记录版本 |
| POST | `/api/dat/undo` | 撤销一步（字段级命令） |
| POST | `/api/dat/redo` | 重做一步 |
| GET | `/api/techs` | 科技列表（分页 `?page=&page_size=&q=`） |
| GET | `/api/techs/{id}` | 科技详情（含前置科技名、费用、研究位置） |
| PATCH | `/api/techs/{id}` | 修改科技字段（body `{field,value}` 或 `{字段:值}`） |
| GET | `/api/effects` / `/api/effects/{id}` | 效果列表/详情（含效果指令） |
| GET | `/api/civs` / `/api/civs/{id}` | 文明列表/详情（含科技树/团队加成引用） |
| GET | `/api/units?civ=&q=` | 单位查询（按文明的单位覆盖） |
| POST | `/api/batch/preview` | 批量修改预览（body：目标集 + op） |
| POST | `/api/batch` | 批量修改执行（命令模式，可整体撤销） |
| POST | `/api/diff` | 对比两个 dat（body `{base, target}`），三级 diff |
| POST | `/api/patch/apply` | 应用语义补丁（body `{patch}` 或 `{path}`） |
| POST | `/api/patch/generate` | 从 diff 反向生成补丁 |
| GET | `/api/search?q=` | 全局搜索（名称，跨表） |
| GET | `/api/refs/forward/{table}/{id}` | 正向引用 |
| GET | `/api/refs/reverse/{table}/{id}` | 反向引用 |
| GET | `/api/names/{id}?table=` | 名称解析（内部名/显示名） |
| GET | `/api/version/list` | 版本历史 |
| POST | `/api/version/checkout` | 回滚到某版本 |
| GET | `/api/update/check` | 检查应用更新（GitHub Releases） |
| POST | `/api/update/download` | 下载更新包并校验 SHA256 |
| POST | `/api/git/init` | 初始化补丁工程 Git 仓库 |
| GET | `/api/git/status` | 工程 Git 状态（分支/变更） |
| GET | `/api/git/log` | 工程提交历史 |
| POST | `/api/git/commit` | 提交工程变更（body `{message}`） |
| POST | `/api/git/checkout` | 回滚到某提交（body `{ref}`） |

## 数据模型说明

- `Tech.resource_costs` 是**按实际使用的资源排序**的元组，资源类型由 `type`
  字段标识（0=Food / 1=Wood / 2=Stone / 3=Gold）。例如「织布机 Loom」只耗黄金，
  故黄金在 `resource_costs.0`，而非固定下标 2。
- 补丁字段路径支持**语义化资源定位**：`resource_costs.gold.amount` 会自动解析为
  对应下标（`food`/`wood`/`stone`/`gold`），无需关心下标位置。
- `Civ.tech_tree_id` 与 `Civ.team_bonus_id` 均指向 **effects 表**（科技树 /
  团队加成效果），而非 techs 表。
- 显示名（中文）需要配置游戏目录并加载语言文件 `key-value-strings-utf8.txt`；
  未配置时回退为内部英文名。

## 示例（Agent 调用链）

```bash
# 加载 dat
curl -X POST http://127.0.0.1:8342/api/dat/load \
     -H "Content-Type: application/json" \
     -d '{"path":"D:/AoE2DE/resources/_common/dat/empires2_x2_p1.dat"}'

# 应用一条语义补丁（织布机金费改 30，按资源类型定位）
curl -X POST http://127.0.0.1:8342/api/patch/apply \
     -H "Content-Type: application/json" \
     -d '{"patch":"steps:\n  - target: {table: techs, name: Loom}\n    op: set\n    field: resource_costs.gold.amount\n    value: 30"}'

# 批量修改（所有 C-Bonus* 科技费用 ×1.2，先预览）
curl -X POST http://127.0.0.1:8342/api/batch/preview \
     -H "Content-Type: application/json" \
     -d '{"targets":[{"table":"techs","name_pattern":"C-Bonus*"}],"ops":[{"op":"multiply","field":"resource_costs.0.amount","value":1.2}]}'

# 对比两个版本
curl -X POST http://127.0.0.1:8342/api/diff \
     -H "Content-Type: application/json" \
     -d '{"base":"D:/back/empires2_x2_p1_old.dat","target":"D:/back/empires2_x2_p1_new.dat"}'

# 保存
curl -X POST http://127.0.0.1:8342/api/dat/save \
     -H "Content-Type: application/json" \
     -d '{"path":"D:/AoE2DE/resources/_common/dat/empires2_x2_p1_mod.dat"}'
```
