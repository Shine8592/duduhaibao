#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""卡通插画集 · 成套生图 CLI（duduhaibao 4.4.0）。

一次生成整套插画（1 主视觉 + N 亮点图标），共用同一条 STYLE LOCK 前缀，
只换 SUBJECT 段；产出图片 + 接触表（contact sheet）供一次性成套验收。

后端：默认 cn:hunyuan-image-alpha（文生图，供应商 yaner）；
      --backend agnes 可回退到 4.3.1 的 agnes-image-2.5-flash。

分工边界（务必遵守）：
  - 成品海报的文字照常要有 —— 由 HTML / Typst 排版层以真文字叠加。
    本脚本生成的**插画素材图内不烧文字**（STYLE LOCK 的 STRICT 段写死 no text），
    因为生图模型画中文字形不可靠；文字由排版层盖在画面之上。
  - 本脚本只管「生成成套插画」。改图修图走 edit_image.py；改成品上的文字走 repair_raster.py。

用法：
  export DUDUHAIBAO_IMAGE_KEY="..."
  python scripts/generate_illustration.py \
      --subjects "秋日稻田主视觉" "蛋糕" "野餐篮" "大巴车" \
      --out-dir _wip/illustrations --size 1024x1024 --contact

  # 用自定义 STYLE LOCK（或覆盖主体前缀）
  python scripts/generate_illustration.py --style-file style.txt --subjects ...

环境变量见 scripts/image_api.py。
"""
import argparse
import sys
from pathlib import Path

import image_api

# 与 references/illustration-set-posters.md §1 完全一致的通用 STYLE LOCK。
# 这段是**后端无关**的：Agnes 2.5 与 hunyuan-image-alpha 都用同一套风格约束，
# 这样换后端不必重调整套 prompt（回应需求书「换了要全部重调」的顾虑）。
STYLE_LOCK = """Flat vector cartoon illustration for a warm children's picture book poster.
STYLE: clean thick uniform outlines, flat solid colors with subtle paper grain,
warm autumn palette of golden yellow, cream white, soft orange and warm brown,
cute rounded simple shapes, minimal detail, no gradients,
generous empty margins, centered composition.
STRICT: absolutely no text, no letters, no numbers, no watermark, no signature, no logo.
No human faces, no photorealistic rendering, no 3D shading."""

# 主视觉最容易跑偏成「有透视的风景」——额外锁死（reference §1）。
HERO_EXTRA = "no perspective lines, no texture, sticker-like, icon style, flat lay."


def build_prompt(subject, is_hero=False):
    parts = [STYLE_LOCK, f"SUBJECT: {subject}."]
    if is_hero:
        parts.append(HERO_EXTRA)
    return "\n".join(parts)


def make_contact_sheet(paths, out, cell=520):
    """接触表：一次调用看整套一致性（reference §2）。逐张看会漏掉对比。"""
    from PIL import Image
    n = len(paths)
    cols = 2
    rows = (n + cols - 1) // cols
    sheet = Image.new("RGB", (cell * cols, cell * rows), "white")
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGB")
        im.thumbnail((cell, cell), Image.LANCZOS)
        x = (i % cols) * cell + (cell - im.width) // 2
        y = (i // cols) * cell + (cell - im.height) // 2
        sheet.paste(im, (x, y))
    sheet.save(out)
    return out


def main():
    global STYLE_LOCK
    ap = argparse.ArgumentParser(description="卡通插画集成套生图")
    ap.add_argument("--subjects", nargs="+", required=True,
                    help="主体列表：第一个是主视觉，其余是亮点图标")
    ap.add_argument("--out-dir", default="_wip/illustrations")
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--backend", choices=["hunyuan", "agnes"], default="hunyuan")
    ap.add_argument("--style-file", help="覆盖默认 STYLE LOCK（整段文本）")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--contact", action="store_true", help="生成接触表 _sheet.png")
    ap.add_argument("--names", nargs="+", help="输出文件名（不含扩展名），默认 hero/icon1...")
    args = ap.parse_args()

    style = Path(args.style_file).read_text(encoding="utf-8").strip() if args.style_file else STYLE_LOCK
    STYLE_LOCK = style

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    names = args.names or (["hero"] + [f"icon{i}" for i in range(1, len(args.subjects))])
    if len(names) != len(args.subjects):
        print("❌ --names 数量与 --subjects 不一致", file=sys.stderr)
        return 1

    paths = []
    for i, (name, subj) in enumerate(zip(names, args.subjects)):
        prompt = build_prompt(subj, is_hero=(i == 0))
        out = outdir / f"{name}.png"
        print(f"[{i+1}/{len(names)}] {name}: {subj}  (backend={args.backend})")
        try:
            r = image_api.generate(prompt, str(out), size=args.size,
                                   backend=args.backend, seed=args.seed)
            print(f"    ✅ {out}  {r['bytes']//1024} KB")
            paths.append(out)
        except Exception as e:
            print(f"    ❌ 生成失败: {e}", file=sys.stderr)
            return 1

    if args.contact and paths:
        sheet = make_contact_sheet(paths, outdir / "_sheet.png")
        print(f"接触表: {sheet}")

    s = image_api.cost_summary()
    print(f"\n生成成本：插画 {s['t2i']} 次调用 · 累计 {s['calls']} 次 API · "
          f"总耗时 {s['elapsed_s']}s")
    print("交付前：放大生成图右下角查 AI 水印（reference §0）；"
          "若插画里混入了文字，重画该张（文字由排版层叠加，不烧进插画）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
