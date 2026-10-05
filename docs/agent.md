# AI Agent 对接指南

GenieForge 提供 HTTP 接口，脚本或 AI Agent 无需操作界面即可完成「读数据 → 分析 → 修改 / 应用补丁 → 写回」全流程。

## 1. 启动后端

```bash
# 只启动后端（无窗口）
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8342

# 或启动桌面应用（后端 + 窗口）
python desktop/run.py
```

- 基址：`http://127.0.0.1:8342`
- 在线文档：`http://127.0.0.1:8342/docs`（OpenAPI/Swagger）
- 无需 API Key，后端只监听本机。请求不要携带 `Origin` 头（普通脚本默认不带），否则会被当作浏览器跨站请求拦截。

## 2. 推荐工作流

```python
import requests

BASE = "http://127.0.0.1:8342"

# 1) 加载 dat（约 10~15s，自动构建引用索引）
r = requests.post(f"{BASE}/api/dat/load", json={"path": "D:/AoE2DE/resources/_common/dat/empires2_x2_p1.dat"})
print(r.json()["version"], r.json()["counts"])

# 2) 读取并分析
techs = requests.get(f"{BASE}/api/techs", params={"q": "Banking"}).json()
tech_id = techs["items"][0]["id"]
detail = requests.get(f"{BASE}/api/techs/{tech_id}").json()
print(detail["resource_costs"], detail["required_techs"])

# 3) 批量修改：先预览，确认后执行
body = {
    "targets": [{"table": "techs", "name_pattern": "^C-Bonus"}],  # 正则
    "ops": [{"op": "multiply", "field": "resource_costs.0.amount", "value": 2}],
}
preview = requests.post(f"{BASE}/api/batch/preview", json=body).json()
print("影响", preview["affected"], "处")
requests.post(f"{BASE}/api/batch", json=body)

# 4) 或应用语义补丁（按名称 / 签名定位，不依赖 ID）
patch = """
steps:
  - target: {table: techs, name: Loom}
    op: set
    field: resource_costs.gold.amount
    value: 30
"""
print(requests.post(f"{BASE}/api/patch/preview", json={"patch": patch}).json()["summary"])
report = requests.post(f"{BASE}/api/patch/apply", json={"patch": patch}).json()
print(report["summary"])  # applied / conflicts / missing / unsupported

# 5) 另存为（字节级无损）
requests.post(f"{BASE}/api/dat/save", json={"path": "D:/mods/empires2_x2_p1_mod.dat"})
```

出错时可调用 `POST /api/dat/undo` 逐步撤销；批量修改和补丁应用都是一步整体撤销。

## 3. 关键约定

- **字段路径**：点路径 `a.b.2.c`，数字段为下标。补丁中额外支持 `resource_costs.{food|wood|stone|gold}.amount` 按资源类型定位；批量修改不支持，需写下标。
- **`resource_costs`**：按实际使用的资源排列，`type` 标识资源（0=Food / 1=Wood / 2=Stone / 3=Gold）。
- **`name_pattern`**：Python 正则，`re.match` 从名称开头匹配；不是通配符。
- **`Civ.tech_tree_id` / `team_bonus_id`**：指向 effects 表，不是 techs 表。
- **单位数据**：按文明存放，修改用 `PATCH /api/units/{civ}/{unit_id}`。
- **整数字段**：`multiply` 不会自动取整，请保证结果是整数。
- **写回**：建议另存为新文件，不要直接覆盖游戏目录中的原文件。

## 4. 完整端点

见 [`api.md`](api.md)，或运行后访问 `/docs`。
