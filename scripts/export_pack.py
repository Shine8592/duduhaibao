#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════════
#  一键交付包 —— 把渲染产物整理成可直接投放的 dist/ 目录
#
#  为什么需要：渲染完拿到一堆 png/pdf 只是半成品。"投放到公众号 / 小红书 /
#  抖音"还要求：对的格式（平台会重压缩 PNG → 先转 JPEG）、对的体积（超限会被
#  拒或被压糊）、对的清单（谁是谁、放哪、多少 MB）。这些全是"确定性"工作，
#  交给脚本，不交给模型。
#
#  用法：python scripts/export_pack.py --root <项目目录> [--out dist] [--no-zip]
#  产物：dist/<日期>/
#         ├── print/    A4、易拉宝（PDF + PNG，用于印刷）
#         ├── social/   朋友圈 / 方形 / 竖屏 / 横版（PNG）
#         ├── web/      全格式的平台友好 JPEG（≤2048 长边，含超限压缩版）
#         ├── manifest.json   每个文件的尺寸 / 字节 / sha256 / 用途 / 投放建议
#         ├── README.txt      交付清单（人读）
#         └── duduhaibao-<日期>.zip
# ═══════════════════════════════════════════════════════════════════

import argparse
import datetime
import glob
import hashlib
import json
import os
import shutil
import sys

# 格式 → (分类, 用途, 建议投放)
PURPOSE = {
    "poster-a4":     ("print",  "A4 打印版",   "打印 / 张贴 / 会议现场"),
    "poster-banner": ("print",  "易拉宝版",    "展架 / 易拉宝印刷"),
    "poster-social": ("social", "朋友圈版",    "朋友圈 / 小红书（3:4）"),
    "poster-square": ("social", "方形封面版",  "公众号首图 / 小红书封面（1:1）"),
    "poster-story":  ("social", "竖屏 Story",  "抖音 / 视频号 / 快手 / IG Story（9:16）"),
    "poster-cute":   ("social", "可爱版",      "幼儿园 / 亲子 / 儿童（3:4）"),
    "poster-term":   ("social", "节气版",      "节气 / 节日问候（1:1）"),
    "poster-photo":  ("social", "照片集",      "朋友圈游玩 / 旅行记录（3:4）"),
    "poster-wide":   ("social", "横版头图",    "文章头图 / 视频封面 / 微博（16:9）"),
}

# 平台体积上限（单张，近似值）——超限会预警并生成压缩版
LIMITS = {
    "微信公众号正文图": 10 * 1024 * 1024,
    "小红书": 20 * 1024 * 1024,
    "抖音 / 视频号封面": 10 * 1024 * 1024,
    "Open Graph (Facebook)": 8 * 1024 * 1024,
    "X / Twitter": 5 * 1024 * 1024,
    "微信朋友圈（建议）": 1 * 1024 * 1024,
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description="一键交付包")
    ap.add_argument("--root", default=None, help="示例项目目录（含 out/），默认当前目录")
    ap.add_argument("--out", default="dist", help="输出根目录名（相对项目根）")
    ap.add_argument("--no-zip", action="store_true")
    ap.add_argument("--web-edge", type=int, default=2048, help="web/ JPEG 最长边")
    a = ap.parse_args()

    root = os.path.abspath(a.root or os.getcwd())
    outdir = os.path.join(root, "out")
    if not os.path.isdir(outdir):
        print("找不到 out/ —— 先跑一次 build")
        return 1

    try:
        from PIL import Image
    except ImportError:
        print("需要 Pillow：pip install pillow")
        return 1

    stamp = datetime.datetime.now().strftime("%Y%m%d")
    pack = os.path.join(root, a.out, stamp)
    if os.path.exists(pack):
        shutil.rmtree(pack)
    for sub in ("print", "social", "web"):
        os.makedirs(os.path.join(pack, sub), exist_ok=True)

    manifest = {"generated": datetime.datetime.now().isoformat(timespec="seconds"),
                "source": root, "items": [], "warnings": []}

    names = [n for n in PURPOSE]
    for name in names:
        png = os.path.join(outdir, f"{name}.png")
        if not os.path.exists(png):
            manifest["warnings"].append(f"缺少 {name}.png（先跑 build）")
            continue
        cat, title, where = PURPOSE[name]
        png_dst = os.path.join(pack, cat, f"{name}.png")
        shutil.copy2(png, png_dst)

        im = Image.open(png)
        w, h = im.size
        entry = {
            "name": name, "title": title, "purpose": where, "category": cat,
            "png": os.path.relpath(png_dst, pack).replace("\\", "/"),
            "width": w, "height": h, "png_bytes": os.path.getsize(png_dst),
            "sha256": sha256(png_dst),
        }

        # PDF（印刷类必有；其它有则一并带上）
        pdf = os.path.join(outdir, f"{name}.pdf")
        if os.path.exists(pdf):
            pdf_dst = os.path.join(pack, cat, f"{name}.pdf")
            shutil.copy2(pdf, pdf_dst)
            entry["pdf"] = os.path.relpath(pdf_dst, pack).replace("\\", "/")

        # 平台友好 JPEG（平台多会重压缩 PNG；先转 RGB JPEG 更稳）
        rgb = im.convert("RGB") if im.mode != "RGB" else im
        k = min(1.0, a.web_edge / max(w, h))
        web = rgb.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS) if k < 1 else rgb
        jpg = os.path.join(pack, "web", f"{name}.jpg")
        web.save(jpg, quality=88, optimize=True)
        entry["web_jpg"] = os.path.relpath(jpg, pack).replace("\\", "/")
        entry["web_bytes"] = os.path.getsize(jpg)

        # 体积预警 + 压缩版
        for platform, cap in LIMITS.items():
            if entry["web_bytes"] > cap:
                tiny = os.path.join(pack, "web", f"{name}.compressed.jpg")
                web.save(tiny, quality=70, optimize=True)
                entry["compressed_jpg"] = os.path.relpath(tiny, pack).replace("\\", "/")
                entry["compressed_bytes"] = os.path.getsize(tiny)
                manifest["warnings"].append(
                    f"{title}：JPEG {entry['web_bytes']/1e6:.1f}MB 超过「{platform}」上限 "
                    f"{cap/1e6:.0f}MB —— 已生成 {name}.compressed.jpg "
                    f"({entry['compressed_bytes']/1e6:.1f}MB)")
                break

        manifest["items"].append(entry)
        print(f"  ✅ {title:<12} {w}×{h}  png {entry['png_bytes']/1e6:.1f}MB  "
              f"jpg {entry['web_bytes']/1e6:.1f}MB")

    # 清单
    with open(os.path.join(pack, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    lines = [f"海报交付包  {stamp}", "=" * 46, ""]
    for it in manifest["items"]:
        lines.append(f"[{it['category']}] {it['title']}  ({it['name']})")
        lines.append(f"    尺寸 {it['width']}×{it['height']}   投放：{it['purpose']}")
        lines.append(f"    印刷/原图：{it['png']}" + (f" / {it['pdf']}" if it.get("pdf") else ""))
        lines.append(f"    平台用图  ：{it['web_jpg']}  ({it['web_bytes']/1e6:.1f} MB)")
        lines.append("")
    lines.append("提示：")
    lines.append("  - 公众号/小红书/抖音对图片会二次压缩；web/ 里的 JPEG 已转好 RGB，优先用它。")
    lines.append("  - 印刷用 print/ 里的 PDF（矢量）或 PNG。")
    lines.append("  - 二维码请用解码器扫一遍再发（tests/check_qr.py 已验）。")
    if manifest["warnings"]:
        lines += ["", "⚠ 预警："] + ["  - " + w for w in manifest["warnings"]]
    with open(os.path.join(pack, "README.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if not a.no_zip:
        zi = shutil.make_archive(os.path.join(root, a.out, f"duduhaibao-{stamp}"),
                                 "zip", pack)
        print(f"  📦 {os.path.relpath(zi, root)}")

    print(f"\n交付包：{os.path.relpath(pack, root)}")
    if manifest["warnings"]:
        print("预警：")
        for w in manifest["warnings"]:
            print("  ⚠ " + w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
