#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════
#  海报预览图生成 —— 把 out/ 里的大图缩到最长边 1400px 的 JPG
#
#  为什么要它：聊天/网页预览会把大图压到 ~1400px，直接看原图既慢又费流量；
#  生成一份预览 JPG 方便快速检查版式。
#
#  用法：  python make_preview.py --root <项目目录> [--only a4|social|square|banner|all]
#
#  独立成脚本的原因：原来把这段 Python 塞在 build 脚本的 heredoc 里，
#  PowerShell 5.1 传 `-c` 参数会吞掉引号 —— 换个 shell 就崩。拆出来两边都能用。
# ═══════════════════════════════════════════════════════════════════

import argparse
import os
import sys


def main():
    ap = argparse.ArgumentParser(description="海报预览图生成")
    ap.add_argument("--root", default=None, help="项目目录（含 out/），默认当前目录")
    ap.add_argument("--only", default="all", help="只生成某个格式的预览（a4/social/square/banner）")
    a = ap.parse_args()

    root = os.path.abspath(a.root or os.getcwd())

    try:
        from PIL import Image
    except ImportError:
        print("  （没装 Pillow，跳过预览图生成）")
        return 0

    names = ["poster-a4", "poster-social", "poster-square", "poster-story",
             "poster-cute", "poster-term", "poster-photo", "poster-wide", "poster-banner"]
    if a.only != "all":
        names = [n for n in names if n in (a.only, "poster-" + a.only)]

    for n in names:
        p = os.path.join(root, "out", f"{n}.png")
        if not os.path.exists(p):
            continue
        im = Image.open(p)
        if im.mode in ("RGBA", "LA", "P"):
            alpha = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(alpha, mask=alpha.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        w, h = im.size
        k = min(1.0, 1400 / max(w, h))          # 预览最长边 1400
        pv = im.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
        pv.save(os.path.join(root, "out", f"{n}_preview.jpg"), quality=93)
        print(f"  ✅ {n}_preview.jpg  {pv.size[0]}x{pv.size[1]}  (原图 {w}x{h})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
