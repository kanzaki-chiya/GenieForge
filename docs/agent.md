# AI Agent 对接指南

GenieForge 提供完整的 HTTP 接口，让你自己的脚本或 AI Agent 无需点界面即可完成
「读数据 → 分析 → 批量修改 → 应用补丁 → 写回」全流程。

## 1. 启动后端

```bash
# 开发模式
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8342

# 或直接运行桌面壳（同时启动后端 + 开窗口）
python desktop/run.py
```

- 基址：`http://127.0.0.1:8342`（端口可在配置中改）
- 在线文档：`http://127.0.0.1:8342/docs`（OpenAPI/Swagger，自动生成）

## 2. 鉴权

默认本机信任、无需鉴权。若在配置中设置了 `api_key`，则**写操作**需携带：

```
X-API-Key: <你的 api_key>
```

读操作（GET）始终放行。

## 3. 推荐工作流

```python
import requests

BASE = "http://127.0.0.1:8342"

# 1) 加载 dat（约 10~14s，自动构建引用索引）
r = requests.post(f"{BASE}/api/dat/load", json={"path": "D:/AoE2DE/resources/_common/dat/empires2_x2_p1.dat"})
print(r.json()["version"], r.json()["counts"])

# 2) 读取并分析
techs = requests.get(f"{BASE}/api/techs", params={"q": "Banking"}).json()
detail = requests.get(f"{BASE}/api/techs/17").json()
print(detail["resource_costs"], detail["required_techs"])

# 3) 批量修改（先预览）
preview = requests.post(f"{BASE}/api/batch/preview", json={
    "targets": [{"table": "techs", "name_pattern": "C-Bonus*"}],
    "ops": [{"op": "multiply", "field": "resource_costs.0.amount", "value": 1.2}],
}).json()
print("影响", preview["affected"], "条")

# 4) 或直接应用语义补丁（按名称/签名定位，不依赖 ID）
report = requests.post(f"{BASE}/api/patch/apply", json={"patch": """
steps:
  - target: {table: techs, name: Loom}
    op: set
    field: resource_costs.gold.amount
    value: 30
"""}).json()
print(report["summary"])  # applied / conflicts / missing

# 5) 保存（字节级无损）
requests.post(f"{BASE}/api/dat/save", json={"path": "D:/AoE2DE/.../empires2_x2_p1_mod.dat"})
```

## 4. 端点速查

| 用途 | 端点 |
|------|------|
| 健康检查 | `GET /api/health` |
| 加载 / 信息 / 保存 | `POST /api/dat/load` · `GET /api/dat/info` · `POST /api/dat/save` |
| 撤销 / 重做 | `POST /api/dat/undo` · `POST /api/dat/redo` |
| 科技列表 / 详情 / 修改 | `GET /api/techs` · `GET /api/techs/{id}` · `PATCH /api/techs/{id}` |
| 效果 / 文明 / 单位 | `GET /api/effects[/{id}]` · `GET /api/civs[/{id}]` · `GET /api/units?civ=` |
| 批量修改 | `POST /api/batch/preview` · `POST /api/batch` |
| 对比差异 | `POST /api/diff`（body `{base, target}`） |
| 补丁应用 / 生成 | `POST /api/patch/apply` · `POST /api/patch/generate` |
| 搜索 / 名称 / 引用 | `GET /api/search?q=` · `GET /api/names/{id}` · `GET /api/refs/{forward\|reverse}/{table}/{id}` |
| 版本 / 回滚 | `GET /api/version/list` · `POST /api/version/checkout` |
| Git 集成 | `POST /api/git/init` · `GET /api/git/status` · `POST /api/git/commit` · `POST /api/git/checkout` |
| 应用更新 | `GET /api/update/check` · `POST /api/update/download` |

## 5. 关键约定

- **补丁字段路径**：点路径 `a.b.2.c`（`.2.` 为下标）；支持语义化资源定位
  `resource_costs.{food|wood|stone|gold}.amount`。
- **`resource_costs`** 按实际使用资源排序，`type` 标识资源（0=Food/1=Wood/2=Stone/3=Gold）。
- **`Civ.tech_tree_id` / `team_bonus_id`** 指向 effects 表，而非 techs 表。
- **分页**：列表接口用 `?page=&page_size=&q=`（`q` 为名称模糊搜索）。
- **写回**：字节级无损，兼容官方格式；建议写前先备份。

## 6. 完整 API 文档

见 [`docs/api.md`](api.md)；运行后访问 `/docs` 查看自动生成的交互式文档。
