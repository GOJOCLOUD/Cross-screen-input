#!/usr/bin/env python3
"""生成 electron-builder 可用的多尺寸 icon.ico（避免仅 256 单层导致 Windows 构建失败）。"""
from __future__ import annotations

import os
import sys


def main() -> int:
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo, "hotspot/images/app-icon-1080x1080.png")
    out_path = os.path.join(repo, "electron/build/icon.ico")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    try:
        from PIL import Image
    except ImportError:
        print("需要 Pillow：pip install pillow", file=sys.stderr)
        return 1

    src = Image.open(src_path).convert("RGBA")
    sizes_px = (256, 128, 64, 48, 32, 16)
    icons = [src.resize((w, h), Image.LANCZOS) for w, h in [(s, s) for s in sizes_px]]
    icons[0].save(
        out_path,
        format="ICO",
        sizes=[(im.width, im.height) for im in icons],
        append_images=icons[1:],
    )
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
