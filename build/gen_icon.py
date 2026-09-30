#!/usr/bin/env python3
"""生成应用图标 build/icon.ico（锻造锤主题，含多种尺寸）。

依赖 Pillow。运行：python build/gen_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent / "icon.ico"


def _draw(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size / 256.0  # 缩放系数，保证不同尺寸一致

    # 背景圆角方形（深蓝灰，锻造金属感）
    d.rounded_rectangle(
        [8 * s, 8 * s, 248 * s, 248 * s],
        radius=int(52 * s),
        fill=(38, 52, 70, 255),
    )

    # 锤头（橙金，横向圆角矩形）
    d.rounded_rectangle(
        [56 * s, 72 * s, 200 * s, 132 * s],
        radius=int(14 * s),
        fill=(240, 160, 48, 255),
    )
    # 锤头高光
    d.rounded_rectangle(
        [64 * s, 80 * s, 192 * s, 100 * s],
        radius=int(10 * s),
        fill=(250, 182, 76, 255),
    )

    # 锤柄（斜向右下）
    d.polygon(
        [
            (116 * s, 128 * s),
            (144 * s, 128 * s),
            (188 * s, 212 * s),
            (160 * s, 212 * s),
        ],
        fill=(206, 128, 36, 255),
    )
    # 锤柄端头
    d.rounded_rectangle(
        [154 * s, 204 * s, 196 * s, 220 * s],
        radius=int(8 * s),
        fill=(206, 128, 36, 255),
    )
    return img


def main() -> None:
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = [_draw(s) for s, _ in sizes]
    # 以最大尺寸为主图保存 ICO（Pillow 会内嵌多尺寸）
    images[-1].save(OUT, format="ICO", sizes=sizes)
    print(f"[icon] 已生成 {OUT}")


if __name__ == "__main__":
    main()
