# 枚举元数据

本目录存放解析和展示 dat 时用到的枚举名映射表，由后端 `/api/meta/{name}` 提供给前端下拉框：

| 文件 | 内容 |
|------|------|
| `effect_types.json` | 效果指令类型（`EffectCommand.type`） |
| `effect_attributes.json` | 效果指令可修改的单位属性 |
| `resource_types.json` | 资源类型 |
| `civ_resources.json` | 文明资源槽位 |
| `armors.json` | 护甲 / 攻击类别 |
| `terrain_tables.json` | 地形表 |
| `unit_types.json` | 单位类型 |
| `tech_types.json` | 科技类型 |

这些表最初从 Advanced Genie Editor（AGE）的 `AGE3Names*.ini` 提取。需要重新提取时运行：

```bash
python backend/metadata/extract_from_age3.py <AGE3NamesV0007.ini> [输出目录]
```

ini 文件来自第三方工具 AGE，不入库（可放在已忽略的 `other/` 目录）。
