#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
img_resize.py —— 读取图片分辨率 & 缩放到任意指定分辨率

功能：
  1. 打印原始分辨率
  2. 缩放到指定 WxH，支持三种模式：
     - stretch : 直接拉伸铺满（可能变形）
     - fit     : 等比缩放 + 填充边（不变形，留边）
     - crop    : 等比缩放 + 居中裁剪（不变形，不留边）

依赖：pip install Pillow
用法：
  python img_resize.py input.jpg 500 300 --mode stretch --out out.png
  python img_resize.py input.jpg 500 300 --mode fit --bg 255,255,255
  python img_resize.py input.jpg 500 300 --mode crop
"""
import argparse
from PIL import Image


def parse_bg(s: str):
    """把 '255,255,255' 或 '#ffffff' 解析成 RGB 元组"""
    s = s.strip()
    if s.startswith("#"):
        h = s.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(int(x) for x in s.split(","))


def resize(img: Image.Image, W: int, H: int, mode: str, bg=(255, 255, 255)) -> Image.Image:
    """核心：把 img 变成严格 W×H 像素"""
    if mode == "stretch":
        # 直接重采样到目标尺寸，铺满；可能改变长宽比
        return img.resize((W, H), Image.LANCZOS)

    if mode == "fit":
        # 等比缩放（不放大超过目标），再居中贴到目标画布上，空余用 bg 填充
        tmp = img.copy()
        tmp.thumbnail((W, H), Image.LANCZOS)      # 等比缩到能放进 W×H 的最大尺寸
        canvas = Image.new(img.mode, (W, H), bg)
        canvas.paste(tmp, ((W - tmp.size[0]) // 2, (H - tmp.size[1]) // 2))
        return canvas

    if mode == "crop":
        # 等比缩放填满目标，再多出来的部分居中裁掉；不变形也不留边
        src_w, src_h = img.size
        scale = max(W / src_w, H / src_h)         # 取能"盖住"目标的缩放比
        new_w, new_h = round(src_w * scale), round(src_h * scale)
        tmp = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - W) // 2
        top = (new_h - H) // 2
        return tmp.crop((left, top, left + W, top + H))

    raise ValueError(f"未知模式: {mode}")


def main():
    ap = argparse.ArgumentParser(description="读取分辨率并缩放到指定尺寸")
    ap.add_argument("input", help="输入图片路径")
    ap.add_argument("width", type=int, help="目标宽度(px)")
    ap.add_argument("height", type=int, help="目标高度(px)")
    ap.add_argument("--mode", choices=["stretch", "fit", "crop"], default="stretch",
                    help="缩放模式：stretch=拉伸 / fit=等比+留边 / crop=等比+居中裁剪")
    ap.add_argument("--bg", default="255,255,255",
                    help="fit 模式的填充色，如 255,255,255 或 #ffffff")
    ap.add_argument("--out", default=None, help="输出路径（默认 <输入名>_WxH.png）")
    args = ap.parse_args()

    img = Image.open(args.input)
    print(f"原始分辨率: {img.size[0]} × {img.size[1]}  模式={img.mode}")

    result = resize(img.convert(img.mode), args.width, args.height,
                    args.mode, parse_bg(args.bg))

    out = args.out or f"{args.input.rsplit('.', 1)[0]}_{args.width}x{args.height}.png"
    result.save(out)
    print(f"输出分辨率: {result.size[0]} × {result.size[1]}  ->  {out}")


if __name__ == "__main__":
    main()