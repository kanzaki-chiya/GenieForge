# 枚举元数据

本目录存放解析 `dat` 时需要的枚举名映射表（方案 §3.5）：

- 效果指令类型（`EffectCommand.type` → 含义）
- 护甲 / 地形 / 资源等枚举名（初始从 AGE 的 `AGE3Names*.ini` 提取）

> 注意：这些 `.ini` 源文件来自第三方工具 Advanced Genie Editor，属于 `other/`
> 目录且**不入库**。请按需将提取后的枚举表（如 `effect_types.json`、
> `armors.json`）放入本目录，供 `NameResolver` / 前端下拉选择器使用。
