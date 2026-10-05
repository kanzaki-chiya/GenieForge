# 打包与发布

本目录存放 PyInstaller 配置（`genieforge.spec`）与图标。

## 一键打包（Windows）

需要 Python 3.11+、Node.js 18+，并已安装依赖：

```bash
pip install -r backend/requirements.txt -r desktop/requirements.txt pyinstaller
cd frontend && npm install && cd ..
```

在仓库根目录执行：

```bat
build.bat 0.4.0                  :: 前端构建 + PyInstaller + zip + checksums
build.bat 0.4.0 --skip-frontend  :: 跳过前端构建，使用已有的 frontend/dist
```

也可以用 Python 脚本，流程相同：

```bash
python scripts/build.py --version 0.4.0 [--skip-frontend]
```

产物位于 `release/<版本>/`：

- `GenieForge-<版本>-windows.zip`：解压即用的程序目录；
- `checksums.txt`：各文件的 SHA256。

## 手动打包

```bash
cd frontend && npm run build && cd ..   # 生成 frontend/dist
python -m PyInstaller --noconfirm build/genieforge.spec
```

输出在 `dist/GenieForge/`。

## 发布

把 zip 与 `checksums.txt` 上传到 GitHub Release，tag 使用 `v<版本>`。应用内「检查更新」按 semver 比较最新 Release 的 tag。
