"""pywebview 桌面壳：开原生窗口加载本地后端（方案 §2.1 / §3.3）。

启动顺序：
1. 后台线程启动 FastAPI（localhost:8342）；
2. 打开原生窗口加载 ``http://127.0.0.1:8342``（前端由后端托管）。
"""

import threading

import uvicorn
import webview

HOST = "127.0.0.1"
PORT = 8342


def main() -> None:
    from backend.app.main import app

    server = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": app, "host": HOST, "port": PORT, "log_level": "warning"},
        daemon=True,
    )
    server.start()

    webview.create_window(
        "GenieForge",
        f"http://{HOST}:{PORT}",
        width=1280,
        height=800,
        min_size=(960, 600),
    )
    webview.start()


if __name__ == "__main__":
    main()
