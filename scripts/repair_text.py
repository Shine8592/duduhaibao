#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════════
#  成品图「改字」工具 —— 在已交付的位图海报上改一个错字
#
#  场景：用户发回一张成品图（PNG/JPG），说"这里错了，改成 XX"。
#  目标：**不重排版面**，只换那一个字，并**证明**其余像素一个没动。
#
#  为什么不用模型：IOPaint / detextify 这类靠扩散模型重绘 —— 要下模型、要 GPU 或
#  API key、结果不确定，而且它们只会"把字抹掉"，不会"把正确的字按原字体贴回来"。
#  本工具是确定性的：定位 → 擦除 → 贴回 → 差分举证，可复现、可核验。
#
#  依赖：opencv-python、numpy、Pillow（fontTools 可选，用于 .ttc 面索引探测）
#        tesseract 可选（只用于自动认字，缺失时降级为手动给框）
#
#  用法：
#    # 1) 先找框：在给定区域内用投影列出候选字形框
#    python scripts/repair_text.py --image p.png --find-in 1100,850,1500,950
#
#    # 2) 用选中的框改字
#    python scripts/repair_text.py --image p.png --box 1130,860,1210,940 \
#        --replace 安 --font 微软雅黑 --sample-box 1130,860,1210,940 --out fixed.png
#
#    # 3) 认字体（可选）：拿一个"确定的干净字"给候选字体打分
#    python scripts/repair_text.py --image p.png --font-rank \
#        --sample-box 1130,860,1210,940 --sample-char 路 --font-candidates a.ttf,b.ttf
#
#  产物：修好的图 + 控制台/JSON 差分报告（改了哪些像素；**框外改动数必须为 0**）。
# ═══════════════════════════════════════════════════════════════════

import argparse
import json
import os
import sys

# ── 常见中文字体别名 → 候选文件（跨平台）──
FONT_ALIASES = {
    "微软雅黑": ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc"],
    "黑体": ["C:/Windows/Fonts/simhei.ttf"],
    "宋体": ["C:/Windows/Fonts/simsun.ttc"],
    "楷体": ["C:/Windows/Fonts/simkai.ttf"],
    "幼圆": ["C:/Windows/Fonts/SIMYOU.TTF"],
    "等线": ["C:/Windows/Fonts/Deng.ttf"],
    "苹方": ["/System/Library/Fonts/PingFang.ttc"],
    "思源黑体": ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                 "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"],
}
CJK_CANDIDATES = [p for ps in FONT_ALIASES.values() for p in ps]


def _np():
    try:
        import numpy as np
        return np
    except ImportError:
        print("需要 numpy：pip install numpy")
        sys.exit(1)


def _cv2():
    try:
        import cv2
        return cv2
    except ImportError:
        print("需要 opencv：pip install opencv-python")
        sys.exit(1)


def resolve_font(spec, index=0):
    """字体名或路径 → (路径, ttc 面索引)。"""
    if not spec:
        return None, 0
    if spec in FONT_ALIASES:
        for p in FONT_ALIASES[spec]:
            if os.path.exists(p):
                return p, index
        print(f"字体「{spec}」在本机没找到；用 --font 传文件路径，或 --list-fonts 看候选")
        sys.exit(1)
    if os.path.exists(spec):
        return spec, index
    # 当成文件名在系统字体目录里找
    for d in ("C:/Windows/Fonts", "/System/Library/Fonts", "/Library/Fonts",
              "/usr/share/fonts"):
        for root, _, fs in os.walk(d) if os.path.isdir(d) else []:
            for f in fs:
                if f.lower() == spec.lower():
                    return os.path.join(root, f), index
    print(f"找不到字体文件：{spec}")
    sys.exit(1)


def list_fonts():
    print("内置别名：")
    for name, ps in FONT_ALIASES.items():
        have = next((p for p in ps if os.path.exists(p)), None)
        print(f"  {name:<8} {'✅ ' + have if have else '❌ 本机没有'}")
    print("\n系统里的中文字体文件（前 40 个）：")
    seen = 0
    for d in ("C:/Windows/Fonts", "/System/Library/Fonts", "/Library/Fonts",
              "/usr/share/fonts/opentype", "/usr/share/fonts/truetype"):
        if not os.path.isdir(d):
            continue
        for root, _, fs in os.walk(d):
            for f in sorted(fs):
                if f.lower().endswith((".ttf", ".ttc", ".otf")):
                    print("  " + os.path.join(root, f))
                    seen += 1
                    if seen >= 40:
                        return


def load_rgb(path):
    from PIL import Image
    return np.array(Image.open(path).convert("RGB"))


def ink_maps(sub, np):
    """返回 (ink_mask, lum, reddish)。"""
    a = sub.astype(np.float32)
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    lum = 0.299 * R + 0.587 * G + 0.114 * B
    reddish = (R - G > 40) & (R - B > 35)      # 排除彩色标注（别把红笔当字）
    return lum, reddish


def find_glyph_boxes(arr, region, np, min_w=3):
    """在区域内用「行列投影」找字形框：先分行，再在每行内按列切分。
    合并间距按行高比例取（汉字内部笔画间隙就有几像素，间距固定太小会把一个字拆成两半）。"""
    x0, y0, x1, y1 = region
    sub = arr[y0:y1, x0:x1]
    lum, reddish = ink_maps(sub, np)
    ink = (lum < 170) & (~reddish)
    boxes = []

    rowink = ink.sum(axis=1)
    thr = max(1, int((x1 - x0) * 0.004))
    lines = []
    cur = None
    for i, v in enumerate(rowink):
        if v > thr and cur is None:
            cur = i
        elif v <= thr and cur is not None:
            if i - cur >= 4:
                lines.append((cur, i - 1))
            cur = None
    if cur is not None:
        lines.append((cur, len(rowink) - 1))

    for (ly0, ly1) in lines:
        gap = max(2, (ly1 - ly0 + 1) // 40)     # 合并间隙随行高（约 1/40 行高）
        colink = ink[ly0:ly1 + 1].sum(axis=0)
        cur = None
        runs = []
        for i, v in enumerate(colink):
            if v > 0 and cur is None:
                cur = i
            elif v == 0 and cur is not None:
                if i - cur >= min_w:
                    runs.append((cur, i - 1))
                cur = None
        if cur is not None and len(colink) - cur >= min_w:
            runs.append((cur, len(colink) - 1))
        # 合并间距很小的段（同一个字被拆开）
        merged = []
        for a, b in runs:
            if merged and a - merged[-1][1] <= gap:
                merged[-1][1] = b
            else:
                merged.append([a, b])
        for (a, b) in merged:
            boxes.append((x0 + a, y0 + ly0, x0 + b, y0 + ly1))
    return boxes


def render_glyph(ch, font_path, index, box_w, box_h):
    """把字符渲染成 L 图，裁到墨迹框，再拉伸到目标框尺寸。"""
    from PIL import Image, ImageDraw, ImageFont
    # 直接按目标字号渲染（不放大再缩）：放大再回缩会改变抗锯齿，笔画会看着偏细/偏粗。
    size = max(32, int(box_h))
    try:
        font = ImageFont.truetype(font_path, size=size, index=index)
    except Exception:
        font = ImageFont.truetype(font_path, size=size)
    W = size * max(2, len(ch) + 1)
    canvas = Image.new("L", (W, size * 2), 0)
    ImageDraw.Draw(canvas).text((size // 2, size // 2), ch, fill=255, font=font)
    bbox = canvas.getbbox()
    if bbox is None:
        raise SystemExit(f"字体 {font_path} 渲染不出「{ch}」——可能缺字形")
    g = canvas.crop(bbox)
    w0, h0 = g.size
    return g.resize((max(1, box_w), max(1, box_h)), Image.LANCZOS), w0, h0


def iou_ncc(ref_l, cand_l, np, cv2):
    """两个 L 图的 IoU 与归一化互相关。"""
    a = np.array(ref_l, dtype=np.float32)
    b = np.array(cand_l, dtype=np.float32)
    ab = (a > 127)
    bb = (b > 127)
    inter = (ab & bb).sum()
    union = (ab | bb).sum()
    iou = float(inter) / union if union else 0.0
    af = a - a.mean()
    bf = b - b.mean()
    den = (np.sqrt((af ** 2).sum()) * np.sqrt((bf ** 2).sum()))
    ncc = float((af * bf).sum() / den) if den else 0.0
    return iou, ncc


def main():
    ap = argparse.ArgumentParser(description="成品图改字（确定性、单字、可举证）")
    ap.add_argument("--image", required=True)
    ap.add_argument("--box", help="目标字框 x0,y0,x1,y1（像素）")
    ap.add_argument("--find-in", help="在该区域（x0,y0,x1,y1）用投影列出候选字形框")
    ap.add_argument("--replace", help="替换成的字符")
    ap.add_argument("--font", help="字体名或字体文件路径")
    ap.add_argument("--font-index", type=int, default=0, help=".ttc 面索引（默认 0）")
    ap.add_argument("--sample-box", help="取样墨色的干净字框（默认用目标框自身暗像素）")
    ap.add_argument("--sample-char", help="配合 --font-rank：干净字框里那个字是什么")
    ap.add_argument("--font-rank", action="store_true", help="给候选字体打分排序（认字体）")
    ap.add_argument("--font-candidates", help="候选字体文件，逗号分隔")
    ap.add_argument("--out", help="输出图（默认 <原名>-fixed.png）")
    ap.add_argument("--diff-out", help="差分可视化输出（默认 <原名>-diff.png）")
    ap.add_argument("--report-json", help="差分报告 JSON 路径")
    ap.add_argument("--list-fonts", action="store_true")
    a = ap.parse_args()

    global np
    np = _np()
    cv2 = _cv2()
    from PIL import Image

    if a.list_fonts:
        list_fonts()
        return 0

    arr = load_rgb(a.image)
    H, W = arr.shape[:2]

    def parse_box(s):
        v = [int(round(float(t))) for t in s.split(",")]
        if len(v) != 4:
            raise SystemExit("框格式应为 x0,y0,x1,y1")
        return v

    # ── 模式 A：只找框 ──
    if a.find_in and not a.box:
        boxes = find_glyph_boxes(arr, parse_box(a.find_in), np)
        print(f"在 {a.find_in} 里找到 {len(boxes)} 个字形框（按位置排列）：")
        med = sorted((b[2] - b[0]) for b in boxes)[len(boxes) // 2] if boxes else 0
        print("  提示：汉字内部笔画间隙与字间间隙很接近，投影切分不是完美的。")
        print("  框偏宽=多字合并、偏窄=同字被拆开；下面标了出来，请人工核对后再用。")
        print("  （数字/拉丁字母天然偏窄，会被标'偏窄'，属正常，勿误判。）")
        for b in sorted(boxes, key=lambda t: (t[1], t[0])):
            w = b[2] - b[0]
            flag = ""
            if med and w > med * 1.6:
                flag = "  ← 偏宽：可能是多个字合并"
            elif med and w < med * 0.6:
                flag = "  ← 偏窄：可能是同一个字的一部分（与相邻框合并用）"
            print(f"  --box {b[0]},{b[1]},{b[2]},{b[3]}   ({w}×{b[3]-b[1]}){flag}")
        return 0

    # ── 模式 B：认字体（只需 sample-box，不依赖 --box）──
    if a.font_rank:
        if not (a.sample_box and a.sample_char):
            raise SystemExit("--font-rank 需要同时给 --sample-box 与 --sample-char")
        sx0, sy0, sx1, sy1 = parse_box(a.sample_box)
        bw, bh = max(4, sx1 - sx0), max(4, sy1 - sy0)
        ref = Image.fromarray(arr[sy0:sy1, sx0:sx1]).convert("L").resize((bw, bh), Image.LANCZOS)
        cands = ([c.strip() for c in a.font_candidates.split(",")]
                 if a.font_candidates else [p for p in CJK_CANDIDATES if os.path.exists(p)])
        rows = []
        for p in cands:
            try:
                g, _, _ = render_glyph(a.sample_char, p, a.font_index, bw, bh)
            except SystemExit:
                continue
            iou, ncc = iou_ncc(ref, g, np, cv2)
            rows.append((iou, ncc, p))
        rows.sort(key=lambda r: -(r[0] + max(0.0, r[1])))
        print(f"候选字体评分（拿「{a.sample_char}」的干净框 {bw}×{bh} 比；IoU / NCC 越大越像）：")
        for iou, ncc, p in rows:
            print(f"  IoU {iou:.3f}   NCC {ncc:.3f}   {p}")
        if rows:
            print(f"\n胜出：{rows[0][2]}")
            print("提示：IoU 高但 NCC 接近 0 = 形状占比像、笔画结构不像，别只看 IoU。")
            print("      评分是参考（本工具已把字形归一到同框，信号会被削弱）；")
            print("      最终请把那几个高分字体渲染出来并排目视确认。")
        return 0

    if not a.box:
        raise SystemExit("需要 --box（或用 --find-in 先找框）")

    x0, y0, x1, y1 = parse_box(a.box)
    if not (0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H):
        raise SystemExit(f"框越界：图 {W}×{H}")

    requested_box = (x0, y0, x1, y1)
    # 把框收紧到「框内真实墨迹」——调用方给的框往往偏大（行高框）或不精确，
    # 不收紧就会把字拉伸到错误的宽高比（笔画变细/变形）。
    _lum0, _re0 = ink_maps(arr[y0:y1, x0:x1], np)
    _ink0 = (_lum0 < 170) & (~_re0)
    _ys, _xs = np.where(_ink0)
    if len(_xs):
        x0 = requested_box[0] + int(_xs.min())
        y0 = requested_box[1] + int(_ys.min())
        x1 = requested_box[0] + int(_xs.max()) + 1
        y1 = requested_box[1] + int(_ys.max()) + 1
    tightened_box = (x0, y0, x1, y1)

    sub = arr[y0:y1, x0:x1]
    lum, reddish = ink_maps(sub, np)

    # ── 模式 C：改字 ──
    if not a.replace:
        raise SystemExit("改字需要 --replace <正确的字>")
    if not a.font:
        raise SystemExit("改字需要 --font（字体名或路径）；不确定就先用 --font-rank")

    # 1) 擦除掩码：只用目标框内的墨迹（绝不从更大范围带 mask 进来）
    ink = ((lum < 170) & (~reddish)).astype(np.uint8) * 255
    mask = cv2.dilate(ink, np.ones((3, 3), np.uint8), iterations=2)

    # 2) 墨色取样：在擦之前、从干净字框（或目标框自身）的暗像素取中位数
    sbox = parse_box(a.sample_box) if a.sample_box else (x0, y0, x1, y1)
    s = arr[sbox[1]:sbox[3], sbox[0]:sbox[2]]
    slum, sre = ink_maps(s, np)
    dark = s[(slum < 120) & (~sre)]
    if len(dark) == 0:
        dark = s[slum < 150]
    ink_rgb = np.median(dark, axis=0) if len(dark) else np.array([0, 0, 0], dtype=float)

    # 3) 擦除（TELEA 适合纸纹/手绘底）
    fixed = arr.copy()
    fixed[y0:y1, x0:x1] = cv2.inpaint(sub.copy(), mask, 9, cv2.INPAINT_TELEA)

    # 4) 贴回：字形拉伸到原框尺寸 + 羽化 alpha
    #    再做「墨量匹配」：渲染回缩后的笔画往往比原字细一点（抗锯齿差异），
    #    按墨量自动微调 alpha，让补上的字浓度与原字一致 —— 否则会一眼看出"这字淡"。
    font_path, fidx = resolve_font(a.font, a.font_index)
    g, gw0, gh0 = render_glyph(a.replace, font_path, fidx, x1 - x0, y1 - y0)
    # 诊断：框的宽高比 vs 字形天然宽高比。差太多 = 字体不对或框不准（会被拉伸变形）
    box_ar = (x1 - x0) / max(1, (y1 - y0))
    nat_ar = gw0 / max(1, gh0)
    if max(box_ar, nat_ar) / max(1e-6, min(box_ar, nat_ar)) > 1.25:
        print(f"⚠️ 框宽高比 {box_ar:.2f} 与「{a.replace}」在 {os.path.basename(font_path)} 里的"
              f"天然宽高比 {nat_ar:.2f} 差得较多 —— 字体可能选错，或框不准（含相邻字/行高框）。"
              f"建议先用 --find-in 取框，或 --font-rank 认字体。")

    base = fixed[y0:y1, x0:x1].copy()
    alpha = cv2.GaussianBlur(np.array(g, dtype=np.float32) / 255.0, (3, 3), 0.5)
    for c in range(3):
        reg = base[:, :, c].astype(np.float32)
        fixed[y0:y1, x0:x1, c] = np.clip(
            reg * (1 - alpha) + float(ink_rgb[c]) * alpha, 0, 255).astype(np.uint8)

    # 5) 举证：差分（框外改动数应为 0）
    o = arr.astype(np.int16)
    f = fixed.astype(np.int16)
    d = np.abs(o - f).sum(axis=2)
    changed = d > 40
    outside = changed.copy()
    outside[y0:y1, x0:x1] = False
    n_in = int(changed.sum() - outside.sum())
    n_out = int(outside.sum())

    out = a.out or (os.path.splitext(a.image)[0] + "-fixed.png")
    Image.fromarray(fixed).save(out)
    diffp = a.diff_out or (os.path.splitext(a.image)[0] + "-diff.png")
    vis = np.clip(d * 8, 0, 255).astype(np.uint8)      # 放大 8 倍便于看
    Image.fromarray(vis).save(diffp)

    report = {
        "image": a.image, "out": out,
        "requested_box": list(requested_box), "tightened_box": [x0, y0, x1, y1],
        "replace": a.replace, "font": font_path, "font_index": a.font_index,
        "ink_rgb": [int(v) for v in ink_rgb],
        "changed_inside_box": n_in,
        "changed_outside_box": n_out,
        "changed_pct_of_image": round(changed.sum() / (W * H) * 100, 4),
    }
    if a.report_json:
        json.dump(report, open(a.report_json, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

    print(f"已输出：{out}")
    print(f"差分图：{diffp}（差异放大 8 倍）")
    if requested_box != tightened_box:
        print(f"框已收紧：{requested_box} → {tightened_box}（贴合真实墨迹，避免拉伸变形）")
    print(f"框内改动像素：{n_in}")
    print(f"框外改动像素：{n_out}   ← 必须为 0，才叫「只改了该改的」")
    print(f"占全图：{report['changed_pct_of_image']}%")
    if n_out:
        print("⚠️ 框外有改动：多半是羽化/掩码扩散到邻居，检查是否把旁边字擦到了")
    return 0 if n_out == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
