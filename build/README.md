# 打包与更新

本目录存放 PyInstaller 配置与更新清单（方案 §3.4）。

- `genieforge.spec`：PyInstaller 打包配置（onedir），打包前需先 `npm run build`
  生成 `frontend/dist`。
- 更新走 GitHub Releases：Release 附 `.zip`/`.exe` 与 `checksums.txt`（SHA256），
  应用启动时按 semver 比较并校验哈希后替换重启。

## 打包流程

```bash
# 1. 构建前端
cd frontend && npm install && npm run build

# 2. 打包
pip install pyinstaller
pyinstaller build/genieforge.spec
```
