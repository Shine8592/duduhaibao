#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""改图 / 修图 CLI（duduhaibao 4.4.0）—— cn:hunyuan-image-alpha-edit。

定位：**画面语义级**重绘。覆盖技能自己承认的短板（README「不擅长把照片艺术化重构」）：
  - 照片艺术化 / 转绘本风
  - 底稿风格化（把随手拍变成卡通插画底图）
  - 去除底稿右下角的半透明 AI 水印（豆包AI生成 之类）
  - 局部重绘（器皿变形、轮子歪、物体粘连）
  - 插画微调（配色 / 描边统一）

⚠️⚠️ 硬边界 —— 改成品海报上的**错字 / 日期 / 活动流程 / 文字内容**，
   一律走 `python scripts/repair_raster.py ...`（像素级、确定性、字形不乱）。
   生图模型画中文字形不可靠（必乱码），所以文字必须由排版层或像素精修来画。
   注意：这不是说海报不带文字 —— 成品文字照常由排版层叠加，只是不交给生图模型画字形。
   本脚本的 prompt 会强制追加「不得改动/新增任何文字」约束，但仍不可用于改字。

用法：
  export DUDUHAIBAO_IMAGE_KEY="..."
  # 整图风格化
  python scripts/edit_image.py --in photo.jpg --out _wip/styled.png \
      --prompt "转成暖色扁平卡通插画，厚描边，无透视"

  # 裁局部再改（去水印 / 修某个物体）—— 先裁只送问题区域，改动面最小
  python scripts/edit_image.py --in draft.png --out _wip/fixed.png \
      --crop 1700,2690,2160,2880 --prompt "去掉右下角水印，保持纯色背景"

  # 检查输入图是否有文字（有则警告，提示应走 repair_raster）
  python scripts/edit_image.py --check-text --in poster.png
"""
import argparse
import io
import sys
from pathlib import Path

import image_api

NO_TEXT_CLAUSE = (
    "Keep the overall composition. Do NOT add, remove, or alter any TEXT, letters, "
    "numbers, dates, or signs — if text exists it must remain untouched. "
    "No watermark, no signature."
)


def _crop_bytes(image_bytes, box):
    from PIL import Image
    im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    x0, y0, x1, y1 = box
    cropped = im.crop((x0, y0, x1, y1))
    buf = io.BytesIO()
    cropped.save(buf, "PNG")
    return buf.getvalue(), cropped.size


def check_text_hint(image_bytes):
    """轻量提醒：用 tesseract（若装了）粗查输入里是否有文字。
    有文字 ≠ 禁止（可能是插画里的招牌），但交付前必须人工确认没把字改乱。
    """
    try:
        import subprocess
        from PIL import Image
        im = Image.open(io.BytesIO(image_bytes))
        p = subprocess.run(["tesseract", "stdin", "stdout", "-l", "chi_sim+eng"],
                           input=image_bytes, capture_output=True, timeout=30)
        txt = (p.stdout or b"").decode("utf-8", "replace").strip()
        return txt[:200]
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description="画面级改图/修图（hunyuan-image-alpha-edit）")
    ap.add_argument("--in", dest="inp", help="输入图片路径")
    ap.add_argument("--out", help="输出图片路径")
    ap.add_argument("--prompt", help="改图指令（画面级，不要写改字要求）")
    ap.add_argument("--crop", help="先裁局部 x0,y0,x1,y1 再改（改动面最小）")
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--check-text", action="store_true",
                    help="只检查输入图文字并提示边界，不调用模型")
    ap.add_argument("--allow-text", action="store_true",
                    help="显式放行：确认指令只改画面（措辞里提到文字对象词时用）")
    args = ap.parse_args()

    if not args.inp:
        print("❌ 需要 --in", file=sys.stderr)
        return 1
    raw = Path(args.inp).read_bytes()

    if args.check_text:
        t = check_text_hint(raw)
        if t:
            print("⚠️ 输入图检测到文字（tesseract 粗读）：", t)
            print("   若要改这些文字 → 用 repair_raster.py（确定性，字不乱）。")
            print("   本 edit 模型只管画面重绘，禁止用于改字。")
        else:
            print("✅ 未检测到文字（或 tesseract 未安装）—— 仍需人工确认改动后文字完好。")
        return 0

    if not args.out or not args.prompt:
        print("❌ 需要 --out 和 --prompt", file=sys.stderr)
        return 1

    # 边界防护：edit 模型只管画面，绝不该处理文字。
    # 设计取舍（实测踩坑后定的）：不猜「改字意图」—— 词表/正则两边都会漏
    # （漏 rename the text / 误伤 update the color）。改为保守策略：
    #   指令里出现任何「文字对象词」→ 一律拒绝，除非用户显式 --allow-text。
    # 宁可误拒（画面指令里若恰好提到"日期条"，加 --allow-text 即可），也不漏放改字指令。
    # 真正改字请走 repair_raster.py；误拒时的 escape hatch 让意图显式，比隐式猜测可靠。
    # 中文按子串（"日期条"也算），英文按词边界（避免 update 里的 date / rename 里的 name 误伤）
    import re as _re
    _TEXT_OBJECTS_CN = ["字", "日期", "时间", "文字", "文案", "标题", "标点", "数字",
                        "年份", "月份", "落款", "署名"]
    _TEXT_OBJECTS_EN = ["text", "date", "time", "title", "word", "wording", "heading",
                        "label", "caption", "number", "digit", "letter", "typo", "name"]
    low = args.prompt.lower()
    hit_words = [w for w in _TEXT_OBJECTS_CN if w in args.prompt]
    hit_words += [w for w in _TEXT_OBJECTS_EN
                  if _re.search(r"\b" + _re.escape(w) + r"\b", low)]
    # 「把 <数字串> 改成/换成 <数字串>」= 改年份/日期/门牌，也属改字
    if _re.search(r"(把|将)\s*\d{2,4}\s*(改成|换成|改为|改掉)", args.prompt):
        hit_words.append("数字年份")
    _KEEP_PATTERNS = ["保留文字", "文字不变", "不要改字", "不改字", "keep the text",
                      "text unchanged", "leave the text"]
    intent_keep = any(k in args.prompt for k in _KEEP_PATTERNS)
    if hit_words and not intent_keep and not getattr(args, "allow_text", False):
        print("❌ 指令涉及文字对象（%s）。改成品上的文字请走 repair_raster.py。"
              % "、".join(hit_words[:4]), file=sys.stderr)
        print("   生图模型画中文字形不可靠（必乱码），文字须由排版层或像素精修来画。", file=sys.stderr)
        print("   若确为画面指令只是措辞里提到这些词，可加 --allow-text 显式放行。", file=sys.stderr)
        return 2

    if args.crop:
        try:
            box = [int(v) for v in args.crop.split(",")]
            assert len(box) == 4
        except Exception:
            print("❌ --crop 需为 x0,y0,x1,y1", file=sys.stderr)
            return 1
        raw, sz = _crop_bytes(raw, box)
        print(f"已裁局部 {box} → {sz}")

    full_prompt = args.prompt.strip() + "\n" + NO_TEXT_CLAUSE
    print(f"改图指令: {args.prompt}")
    print("后端:", image_api.I2I_MODEL, "(图生图/改图/修图)")
    try:
        r = image_api.edit(full_prompt, raw, args.out, size=args.size, seed=args.seed)
        print(f"✅ {args.out}  {r['bytes']//1024} KB  (输入 {r['input_bytes']//1024} KB)")
    except Exception as e:
        print(f"❌ 改图失败: {e}", file=sys.stderr)
        return 1

    s = image_api.cost_summary()
    print(f"\n生成成本：改图 {s['i2i']} 次调用 · 累计 {s['calls']} 次 API · "
          f"总耗时 {s['elapsed_s']}s")
    print("交付前：确认画面里原有文字（若有）没被改乱；改字需求永远走 repair_raster.py。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
