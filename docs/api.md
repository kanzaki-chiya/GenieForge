# 公共 API 文档

基址：`http://127.0.0.1:8342`（端口可配置）
鉴权：可选 `X-API-Key`（默认本机信任）
在线文档：启动后端后访问 `/docs`（OpenAPI/Swagger，自动生成）

## 端点总表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查与版本 |
| GET / PUT | `/api/config` | 配置（游戏目录、语言、端口、Token） |
| POST | `/api/dat/load` | 加载 dat（body `{path}`），返回元信息 |
| GET | `/api/dat/info` | 当前 dat 版本与各表数量 |
| POST | `/api/dat/save` | 保存（body 可选 `{path}`） |
| GET | `/api/techs` | 科技列表（分页/筛选/投影） |
| GET | `/api/techs/{id}` | 科技详情 |
| PATCH | `/api/techs/{id}` | 修改科技字段 |
| GET | `/api/effects` / `/api/effects/{id}` | 效果列表/详情 |
| GET | `/api/civs` / `/api/civs/{id}` | 文明列表/详情 |
| GET | `/api/units` | 单位查询（按文明/ID） |
| POST | `/api/batch` | 批量修改（body：目标集 + op） |
| POST | `/api/diff` | 对比两个 dat（body `{base, target}`） |
| POST | `/api/patch/apply` | 应用语义补丁（body `{patch}` 或 `{path}`） |
| POST | `/api/patch/generate` | 从 diff 生成补丁 |
| GET | `/api/search?q=` | 全局搜索（名称/ID，跨表） |
| GET | `/api/refs/forward/{table}/{id}` | 正向引用 |
| GET | `/api/refs/reverse/{table}/{id}` | 反向引用 |
| GET | `/api/names/{id}` | 名称解析 |
| GET | `/api/version/list` | 版本历史 |
| POST | `/api/version/checkout` | 回滚到某版本 |
| GET | `/api/update/check` | 检查应用更新 |

## 示例（Agent 调用链）

```bash
# 加载 dat
curl -X POST http://127.0.0.1:8342/api/dat/load \
     -H "Content-Type: application/json" \
     -d '{"path":"D:/AoE2DE/resources/_common/dat/empires2_x2_p1.dat"}'

# 应用一条语义补丁（织布机金费改 30）
curl -X POST http://127.0.0.1:8342/api/patch/apply \
     -H "Content-Type: application/json" \
     -d '{"patch":"steps:\n  - target: {table: techs, name: Loom}\n    op: set\n    field: resource_costs.2.amount\n    value: 30"}'

# 保存
curl -X POST http://127.0.0.1:8342/api/dat/save \
     -H "Content-Type: application/json" \
     -d '{"path":"D:/AoE2DE/resources/_common/dat/empires2_x2_p1_mod.dat"}'
```
