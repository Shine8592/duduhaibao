#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════════
#  风格横向对比 —— 用同一份数据渲染同一模板的多种配色风格，并拼成
#  一张**带标注的联系表**（contact sheet），一眼挑出想要的那套。
#
#  借鉴竞品的「对比多种风格，让用户挑」+ html-anything 的多候选预览。
#
#  用法：python render_styles.py --root <项目目录> [--only a4] [--sheet]
#  产物：out/style-<风格名>.png 与 out/styles-sheet.jpg（联系表）
# ═══════════════════════════════════════════════════════════════════

import argparse
import os
import re
import subprocess
import sys

FMT = {
    "a4": ("templates/poster-a4.typ", 96),
    "social": ("templates/poster-social.typ", 96),
    "square": ("templates/poster-square.typ", 96),
    "story": ("templates/poster-story.typ", 48),
    "wide": ("templates/poster-wide.typ", 96),
    "banner": ("templates/poster-banner.typ", 48),
}

# 常见中文字体候选（Windows / macOS / Linux）
CJK_FONTS = [
    r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def parse_styles(root):
    """返回 [(key, label)]，顺序即文件里的顺序。"""
    src = open(os.path.join(root, "lib", "styles.typ"), encoding="utf-8").read()
    out = []
    for m in re.finditer(r'"([a-z0-9\-]+)"\s*:\s*\(([\s\S]*?)\n\s*\),', src):
        lm = re.search(r'label:\s*"([^"]*)"', m.group(2))
        out.append((m.group(1), lm.group(1) if lm else m.group(1)))
    return out


def make_sheet(root, only, rows_of, items):
    """把渲染出的 style-*.png 拼成带标签的联系表。"""
    from PIL import Image, ImageDraw, ImageFont
    font = None
    for p in CJK_FONTS:
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, 30)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    cell_w = 360
    tiles = []
    for key, label in items:
        p = os.path.join(root, "out", f"style-{key}.png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        k = cell_w / im.width
        im = im.resize((cell_w, max(1, int(im.height * k))), Image.LANCZOS)
        tiles.append((key, label, im))

    if not tiles:
        return None
    cols = min(rows_of, len(tiles))
    rows = (len(tiles) + cols - 1) // cols
    cell_h = max(t[2].height for t in tiles) + 44
    gap = 16
    W = cols * cell_w + (cols + 1) * gap
    H = rows * cell_h + (rows + 1) * gap
    sheet = Image.new("RGB", (W, H), (238, 238, 240))
    d = ImageDraw.Draw(sheet)
    for i, (key, label, im) in enumerate(tiles):
        r, c = divmod(i, cols)
        x = gap + c * (cell_w + gap)
        y = gap + r * (cell_h + gap)
        sheet.paste(im, (x, y))
        d.text((x + 2, y + im.height + 6), f"{key}  {label}", fill=(40, 40, 45), font=font)
    out = os.path.join(root, "out", "styles-sheet.jpg")
    sheet.save(out, quality=90)
    return out


def main():
    ap = argparse.ArgumentParser(description="风格横向对比 + 联系表")
    ap.add_argument("--root", default=None)
    ap.add_argument("--only", default="a4", choices=list(FMT))
    ap.add_argument("--cols", type=int, default=5, help="联系表列数")
    ap.add_argument("--sheet", action="store_true", default=True)
    a = ap.parse_args()

    root = os.path.abspath(a.root or os.getcwd())
    template, ppi = FMT[a.only]
    items = parse_styles(root)
    os.makedirs(os.path.join(root, "out"), exist_ok=True)

    print(f"══ 风格对比：{a.only} × {len(items)} 套配色 ══")
    for key, label in items:
        out = os.path.join(root, "out", f"style-{key}.png")
        r = subprocess.run(
            ["typst", "compile", "--root", root, "--input", f"style={key}",
             "--format", "png", "--ppi", str(ppi), template, out],
            cwd=root, capture_output=True)
        print(f"  {'✅' if r.returncode == 0 else '❌'} {key}  {label}"
              + ("" if r.returncode == 0
                 else "  " + (r.stderr or b"").decode("utf-8", "replace")[:100]))

    sheet = make_sheet(root, a.only, a.cols, items)
    if sheet:
        print(f"  📋 联系表：{sheet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
