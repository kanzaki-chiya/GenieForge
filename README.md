# GenieForge · 帝国时代2决定版 Mod 工作台

> 一款面向《帝国时代 II：决定版》Mod 制作者的桌面工具，让你**告别每次官方更新都要全量重做**的痛苦。

**Language / 语言**：[English](README.en.md) · 简体中文（当前）

[![平台](https://img.shields.io/badge/平台-Windows-lightgrey)](#安装)　[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

---

## 这是什么？

帝国时代2决定版的游戏数据全部存放在一个约 10MB 的 `empires2_x2_p1.dat` 文件里（单位、科技、效果、文明加成、费用等）。传统的 AGE 工具只能「打开 → 改 → 存」，每次官方更新后，由于 ID 漂移、新内容插入，原来的修改只能在新版上从头再改一遍。

GenieForge 在完整解析 dat 的基础上，提供三项核心能力：

- **语义补丁**：把改动写成按「名称」定位的补丁，官方更新后在新版 dat 上重新套用，只需处理匹配不上的少数条目。
- **dat 对比**：列出两个 dat 之间新增、删除、修改的条目，以及同名条目的 ID 漂移。
- **AGE 式编辑**：科技、单位、文明、效果四类数据都能直接在表单里修改，编号自动显示为名称。

---

## 功能

### 数据编辑
- 科技 / 单位 / 文明 / 效果四个页面，按 AGE 的字段分组展示，修改即时生效，支持撤销 / 重做。
- 枚举字段（类型、资源、护甲、效果指令等）用下拉选择，子表（费用、攻击、护甲、效果指令等）可增删行。
- 单位页可切换文明查看各文明的单位数据，并支持按维度（Class、Type、HP 等）筛选。
- 整条复制 / 粘贴（`Ctrl+C` / `Ctrl+V`），把一个条目的全部字段复制到另一个条目。
- 科技页的效果字段可一键跳转到对应效果。
- 配置游戏语言文件后，名称显示为游戏内的中文名。

### 对比
- **对比差异页**：选择基准与目标两个 dat，查看新增 / 删除 / 修改数量、逐条变更与 ID 漂移，并可直接「导出为补丁」。
- **页内对比**：在任一数据页点击「对比」，与另一个 dat 中的同一条目逐字段对比，差异项可单独或全部「应用」到当前数据。

### 补丁
- 可视化补丁编辑器：新建补丁、逐步填写目标与操作、预览命中结果后再应用；补丁以 YAML 文件保存在 `patches/` 目录。
- 目标按名称精确匹配，其次按名称正则，最后按「费用 + 前置科技 + 效果」签名匹配；匹配不到或匹配到多个时会列为冲突，交给你确认。
- 支持的操作：`set`（设为）、`add`（加）、`multiply`（乘）、`append` / `remove`（列表增删）。
- 应用补丁可整体撤销。

### 版本记录
- 每次保存都会记录一个版本（文件路径 + 哈希），可在「版本」页回滚到该文件。版本记录仅在本次运行期间保留。

### 公共 API
- 内置 HTTP 接口，脚本或 AI Agent 可以完成「加载 → 查询 → 修改 / 应用补丁 → 保存」全流程，详见 [API 文档](docs/api.md) 与 [Agent 对接指南](docs/agent.md)。

---

## 安装

### 下载发布版（Windows）

1. 从 [GitHub Releases](../../releases) 下载 `GenieForge-<版本>-windows.zip`；
2. 解压后运行 `GenieForge.exe`。

在工作台点击「检查更新」可查询是否有新版本。

### 从源码运行

需要 Python 3.11+ 与 Node.js 18+。

```bash
pip install -r backend/requirements.txt -r desktop/requirements.txt
cd frontend && npm install && npm run build && cd ..
python desktop/run.py
```

自行打包见 [`build/README.md`](build/README.md)。

---

## 快速上手

1. 在「设置」中选择游戏语言文件 `key-value-strings-utf8.txt`（位于游戏目录 `resources/<语言>/strings/key-value/` 下，用于显示中文名，可跳过）；
2. 在「工作台」选择要编辑的 `empires2_x2_p1.dat` 并点击「加载」（首次解析约需 10～15 秒）；
3. 在左侧「数据浏览」切换科技 / 单位 / 文明 / 效果，直接修改字段；
4. 回到「工作台」点击「保存」。

> 游戏运行时 dat 文件会被锁定，请先关闭游戏；修改前建议备份原文件。

### 官方更新后的推荐流程

```
① 用旧版官方 dat 与你的 mod dat 做对比，「导出为补丁」（或直接维护补丁文件）
② 加载新版官方 dat
③ 在「补丁」页打开补丁，先「预览」
④ 对冲突 / 未匹配的步骤手动修正
⑤ 「应用」后保存为新版 mod
```

### 补丁示例

```yaml
version: 1
based_on: "VER 8.8"
steps:
  - name: "织布机金费 30"
    target: { table: techs, name: "Loom" }
    op: set
    field: "resource_costs.gold.amount"   # 按资源类型定位，不依赖下标
    value: 30
```

---

## 常见问题

**Q：会不会改坏游戏文件？**
A：工具只读写你指定的文件。写回是字节级无损的，与原版格式完全兼容；仍建议先备份。

**Q：官方更新后补丁一定能套上吗？**
A：按名称定位的步骤不受 ID 漂移影响，大多数能直接套用。若官方改了条目名称，或签名（费用 / 前置科技）发生变化，该步骤会显示为「冲突」或「未匹配」，需要手动调整。

**Q：中文名显示不出来？**
A：在「设置」中确认语言文件路径正确，然后点「刷新」。

**Q：支持哪些 dat 版本？**
A：已验证决定版 `VER 7.8 / 8.4 / 8.8`。

---

## 致谢

- [Advanced Genie Editor (AGE)](https://github.com/Tapsa/AGE) —— 格式参考与对照工具；
- [genieutils-py](https://github.com/SiegeEngineers/genieutils-py) —— dat 读写库；
- 帝国时代2决定版 Mod 社区。

## 许可

[MIT License](LICENSE)（依赖库遵循各自的开源协议）。
