#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════════
#  风格横向对比 —— 用同一份数据渲染同一模板的多种配色风格
#
#  借鉴竞品的「对比三种风格，让用户挑」：同一个版式换 6 套色，并排看效果。
#
#  用法：python render_styles.py --root <项目目录> [--only a4]
#  产物：out/style-<风格名>.png
# ═══════════════════════════════════════════════════════════════════

import argparse
import os
import re
import subprocess
import sys

# 格式 → (模板, 预览 ppi)
FMT = {
    "a4": ("templates/poster-a4.typ", 96),
    "social": ("templates/poster-social.typ", 96),
    "square": ("templates/poster-square.typ", 96),
    "wide": ("templates/poster-wide.typ", 96),
    "banner": ("templates/poster-banner.typ", 48),
}


def parse_style_keys(root):
    p = os.path.join(root, "lib", "styles.typ")
    src = open(p, encoding="utf-8").read()
    return re.findall(r'"([a-z0-9\-]+)"\s*:\s*\(', src)


def main():
    ap = argparse.ArgumentParser(description="风格横向对比渲染")
    ap.add_argument("--root", default=None)
    ap.add_argument("--only", default="a4", choices=list(FMT))
    a = ap.parse_args()

    root = os.path.abspath(a.root or os.getcwd())
    template, ppi = FMT[a.only]
    keys = parse_style_keys(root)
    outdir = os.path.join(root, "out")
    os.makedirs(outdir, exist_ok=True)

    print(f"══ 风格对比：{a.only} × {len(keys)} 套配色 ══")
    for k in keys:
        out = os.path.join(outdir, f"style-{k}.png")
        r = subprocess.run(
            ["typst", "compile", "--root", root, "--input", f"style={k}",
             "--format", "png", "--ppi", str(ppi), template, out],
            cwd=root, capture_output=True)
        if r.returncode == 0:
            print(f"  ✅ style-{k}.png")
        else:
            print(f"  ❌ style-{k}："
                  + (r.stderr or b"").decode("utf-8", errors="replace")[:120])
    return 0


if __name__ == "__main__":
    sys.exit(main())
