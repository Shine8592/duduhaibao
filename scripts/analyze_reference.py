#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════════
#  参考图结构化分析 —— 提取「海报语法」，不抄海报内容
#
#  借鉴竞品 poster-style-transfer 的核心理念：
#  「Extract poster grammar, not poster content.」
#  区别在于：它靠模型"看"图给一段提示词；这里用**可测量的方式**给出：
#    · 色板（按面积 / 饱和度 / 明度推断角色，附 WCAG 对比度）
#    · 版面结构（横带 + 竖栏，按百分比）
#    · 比例与建议对应的本仓格式
#  并画一张**带标注的结构叠加图**，人一眼能核验检测对不对。
#
#  用途：拿到一张喜欢的海报 → 得到它的"语法" → 用本仓产线（data + tokens + 模板）
#       在**不复制内容**的前提下重建一个同语法的版式。
#
#  用法：python scripts/analyze_reference.py --image <参考图> [--out <目录>] [--name ref]
#  产物：<out>/<name>-analysis.png（叠加图）
#        <out>/<name>-report.md（人读报告）
#        <out>/<name>-palette.typ（可直接粘进 styles.typ 的配色片段）
# ═══════════════════════════════════════════════════════════════════

import argparse
import datetime
import json
import os
import sys
from collections import Counter

# 本仓内置格式 → 比例，用于"建议对应格式"
BUILTIN = [
    ("poster-a4", 210 / 297, "A4 打印（≈3:4）"),
    ("poster-social", 1080 / 1440, "朋友圈 / 小红书（3:4）"),
    ("poster-square", 1.0, "方形封面（1:1）"),
    ("poster-story", 1080 / 1920, "竖屏 Story（9:16）"),
    ("poster-wide", 1920 / 1080, "横版头图（16:9）"),
    ("poster-banner", 800 / 2000, "易拉宝（80×200cm）"),
]


def lum(c):
    r, g, b = (c[i] / 255 for i in range(3))
    f = lambda x: x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = lum(a), lum(b); hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def sat(c):
    return max(c) - min(c)


def hexs(c):
    return "#{:02X}{:02X}{:02X}".format(*c)


def near(a, b, tol=26):
    return sum(abs(a[i] - b[i]) for i in range(3)) <= tol


def detect_bg(im):
    w, h = im.size; px = im.load()
    pts = []
    for x in range(0, w, max(1, w // 40)):
        pts.append(px[x, 0]); pts.append(px[x, h - 1])
    for y in range(0, h, max(1, h // 40)):
        pts.append(px[0, y]); pts.append(px[w - 1, y])
    return Counter(pts).most_common(1)[0][0]


def profile_bands(vals, thresh, min_len):
    """连续超阈值的区段。"""
    out = []; cur = None
    for i, v in enumerate(vals):
        if v > thresh and cur is None:
            cur = i
        elif v <= thresh and cur is not None:
            if i - cur >= min_len:
                out.append([cur, i - 1])
            cur = None
    if cur is not None and len(vals) - cur >= min_len:
        out.append([cur, len(vals) - 1])
    return out


def main():
    ap = argparse.ArgumentParser(description="参考图结构化分析（提取海报语法）")
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--name", default="ref")
    ap.add_argument("--maxedge", type=int, default=900)
    a = ap.parse_args()

    if not os.path.exists(a.image):
        print("找不到图片：" + a.image)
        return 1
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("需要 Pillow：pip install pillow")
        return 1

    im = Image.open(a.image).convert("RGB")
    W0, H0 = im.size
    k = min(1.0, a.maxedge / max(W0, H0))
    if k < 1:
        im = im.resize((max(1, int(W0 * k)), max(1, int(H0 * k))), Image.LANCZOS)
    W, H = im.size

    outdir = a.out or os.path.dirname(os.path.abspath(a.image))
    os.makedirs(outdir, exist_ok=True)

    # ── 色板：量化 → 按面积/明度/饱和度推断角色 ──
    q = im.quantize(colors=16, method=Image.MEDIANCUT)
    pal = q.getpalette()
    cnt = q.getcolors(1 << 20) or []
    cols = sorted([(c, tuple(pal[i * 3:i * 3 + 3])) for c, i in cnt], reverse=True)
    total = sum(c for c, _ in cols) or 1
    bg = detect_bg(im)
    rest = [(c, col) for c, col in cols if not near(bg, col, 12)]

    def pick(pred, min_share=0.01):
        cand = [(c, col) for c, col in rest if c / total >= min_share and pred(col)]
        return max(cand, key=lambda x: x[0])[1] if cand else None

    dark = sorted(rest, key=lambda x: lum(x[1]))
    ink = dark[0][1] if dark else (0, 0, 0)
    brand = pick(lambda c: sat(c) > 40) or ink
    tint = max([(c, col) for c, col in cols if sat(col) < 30],
               key=lambda x: lum(x[1]))[1] if cols else bg
    bright = max([(c, col) for c, col in rest if sat(col) > 30],
                 key=lambda x: lum(x[1]), default=(0, brand))
    brand2 = bright[1]
    muted = next((col for _, col in dark[1:] if sat(col) < 60), ink)

    # ── 结构：横带 + 每带内竖栏 ──
    px = im.load()
    rowink = [0] * H
    for y in range(H):
        n = 0
        for x in range(W):
            if not near(px[x, y], bg, 30):
                n += 1
        rowink[y] = n
    bands = profile_bands(rowink, thresh=max(2, int(W * 0.006)), min_len=max(3, H // 200))

    struct = []
    for (y0, y1) in bands:
        colink = [0] * W
        for x in range(W):
            n = 0
            for y in range(y0, y1 + 1):
                if not near(px[x, y], bg, 30):
                    n += 1
            colink[x] = n
        colsx = profile_bands(colink, thresh=max(1, int((y1 - y0 + 1) * 0.06)),
                              min_len=max(2, W // 120))
        struct.append({
            "y": [round(y0 / H, 3), round(y1 / H, 3)],
            "height_pct": round((y1 - y0 + 1) / H * 100, 1),
            "columns": [[round(c0 / W, 3), round(c1 / W, 3)] for c0, c1 in colsx],
        })

    # ── 叠加图（可目视核验）──
    ov = im.copy(); d = ImageDraw.Draw(ov)
    for i, b in enumerate(struct):
        y0 = int(b["y"][0] * H); y1 = int(b["y"][1] * H)
        d.rectangle([0, y0, W - 1, y1], outline=(230, 40, 40), width=2)
        d.text((4, max(0, y0 + 2)), f"band{i} h{b['height_pct']}%", fill=(200, 20, 20))
        for c0, c1 in b["columns"]:
            d.rectangle([int(c0 * W), y0, int(c1 * W), y1], outline=(30, 90, 220), width=1)
    sw = 34
    for i, (name, col) in enumerate([("bg", bg), ("ink", ink), ("brand", brand),
                                     ("brand2", brand2), ("tint", tint), ("muted", muted)]):
        d.rectangle([i * (sw + 4), H - sw - 2, i * (sw + 4) + sw, H - 2], fill=col,
                    outline=(0, 0, 0))
    ov_path = os.path.join(outdir, f"{a.name}-analysis.png")
    ov.save(ov_path)

    # ── 报告 + Typst 配色片段 ──
    ratio = W0 / H0
    best = min(BUILTIN, key=lambda x: abs(x[1] - ratio))
    pal_lines = [
        "// 由 analyze_reference.py 从参考图推断（仅取「配色语法」，请人工校订）",
        f'  "ref-{a.name}": (',
        f'    label: "参考图提取", use: "从参考图 {os.path.basename(a.image)} 提取",',
        f'    brand: rgb("{hexs(brand)}"), brand2: rgb("{hexs(brand2)}"), tint: rgb("{hexs(tint)}"),',
        f'    ink: rgb("{hexs(ink)}"), muted: rgb("{hexs(muted)}"), rule: rgb("{hexs(tint)}"),',
        "  ),",
    ]
    pal_path = os.path.join(outdir, f"{a.name}-palette.typ")
    open(pal_path, "w", encoding="utf-8").write("\n".join(pal_lines) + "\n")

    rep = [
        f"# 参考图分析：{os.path.basename(a.image)}", "",
        f"- 原始尺寸：{W0}×{H0}（{ratio:.3f}）",
        f"- 建议本仓格式：**{best[0]}**（{best[2]}，比例 {best[1]:.3f}）",
        f"- 生成时间：{datetime.datetime.now().isoformat(timespec='seconds')}", "",
        "## 色板（推断，务必人工校订）", "",
        "| 角色 | 色值 | 说明 |", "|---|---|---|",
        f"| 背景 bg | `{hexs(bg)}` | 画面主底色 |",
        f"| 正文 ink | `{hexs(ink)}` | 最深的显著色 |",
        f"| 主色 brand | `{hexs(brand)}` | 最高饱和显著色 |",
        f"| 浅点缀 brand2 | `{hexs(brand2)}` | 较高明度的饱和色 |",
        f"| 极浅底 tint | `{hexs(tint)}` | 接近背景的浅色 |",
        f"| 次要 muted | `{hexs(muted)}` | 低饱和中明度 |", "",
        f"对比度：ink/bg = {contrast(ink, bg):.2f}:1，brand/bg = {contrast(brand, bg):.2f}:1"
        "（正文需 ≥4.5、大字 ≥3.0）", "",
        "## 版面结构（横带 + 竖栏，按百分比）", "",
        "| 带 | y 区间 | 高度 | 竖栏（x 区间） |", "|---|---|---|---|",
    ]
    for i, b in enumerate(struct):
        cols_txt = "、".join(f"{c0:.2f}–{c1:.2f}" for c0, c1 in b["columns"]) or "—"
        rep.append(f"| {i} | {b['y'][0]:.2f}–{b['y'][1]:.2f} | {b['height_pct']}% | {cols_txt} |")
    rep += ["", "## 下一步", "",
            f"1. 打开叠加图 `{os.path.basename(ov_path)}` **目视核验**检测是否合理；",
            f"2. 把 `{os.path.basename(pal_path)}` 的内容粘进 `example/lib/styles.typ` 并校准对比度；",
            "3. 按结构表新建 `templates/poster-*.typ`（数据仍来自 `lib/data.typ`）；",
            "4. **只借语法，不抄内容**——人物/文字/logo 一律替换。"]
    rep_path = os.path.join(outdir, f"{a.name}-report.md")
    open(rep_path, "w", encoding="utf-8").write("\n".join(rep) + "\n")

    print(f"  尺寸 {W0}×{H0} 比例 {ratio:.3f} → 建议 {best[0]}")
    print(f"  色板：bg {hexs(bg)}  ink {hexs(ink)}  brand {hexs(brand)}  "
          f"brand2 {hexs(brand2)}  tint {hexs(tint)}  muted {hexs(muted)}")
    print(f"  结构：{len(struct)} 个横带")
    print(f"  → {ov_path}")
    print(f"  → {rep_path}")
    print(f"  → {pal_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
