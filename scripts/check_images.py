#!/usr/bin/env python3
"""图片资产完整性检查（2026-10-27 新增）。

背景：仓库里的图片资产曾因「二进制 → 文本 → 二进制」往返，
所有非法 UTF-8 字节被替换为 U+FFFD（EF BF BD），PNG/JPEG 文件头即损坏，
Typst 渲染直接失败（Invalid PNG signature / Illegal start bytes）。

本脚本做两件事：
  1. 扫描所有图片，检测 U+FFFD 污染（字节层面）
  2. 用 Pillow 实际解码一次，检测「文件头正常但内容损坏」

用法：
    python scripts/check_images.py              # 检查全仓库
    python scripts/check_images.py --quiet      # 只在有问题时输出
退出码：0 = 全部完好；1 = 发现问题
"""
import argparse
import sys
from pathlib import Path

# U+FFFD 在 UTF-8 下的字节序列
REPLACEMENT = b"\xef\xbf\xbd"
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist"}


def iter_images(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in IMAGE_EXT:
            yield p


def check_one(p: Path) -> list:
    """返回该文件的问题列表（空 = 完好）。"""
    problems = []
    try:
        data = p.read_bytes()
    except Exception as e:
        return [f"读取失败: {e}"]

    n = data.count(REPLACEMENT)
    if n:
        problems.append(f"含 {n} 个 U+FFFD 替换字符（文本往返损坏）")

    # 用 Pillow 实际解码（能发现文件头正常但内容坏的情况）
    try:
        from PIL import Image
        with Image.open(p) as im:
            im.verify()
    except ImportError:
        pass  # 没装 Pillow 就只做字节检查
    except Exception as e:
        problems.append(f"解码失败: {type(e).__name__}: {str(e)[:80]}")

    # 文件头快检（不解码也能发现的）
    if data[:3] == REPLACEMENT[:3] or data[:2] == b"\xef\xbf":
        problems.append("文件头已被替换字符污染")
    elif data[:8] == b"\x89PNG\r\n\x1a\n":
        pass
    elif data[:2] == b"\xff\xd8":
        pass
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        pass
    elif data[:6] in (b"GIF87a", b"GIF89a"):
        pass
    else:
        problems.append(f"文件头异常: {data[:6].hex(' ')}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="仓库根目录")
    ap.add_argument("--quiet", action="store_true", help="只在有问题时输出")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    images = list(iter_images(root))
    bad = []
    for p in images:
        problems = check_one(p)
        if problems:
            bad.append((p.relative_to(root), problems))

    if not bad:
        if not args.quiet:
            print(f"✅ 图片资产完好（{len(images)} 个文件）")
        return 0

    print(f"❌ {len(bad)}/{len(images)} 个图片文件有问题：")
    for rel, problems in bad:
        print(f"   - {rel}")
        for pr in problems:
            print(f"       · {pr}")
    print("\n处置：用二进制方式重新上传原图（勿经文本编辑器/文本管道），")
    print("     随后跑 python scripts/check_images.py 复检。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
