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

    # 用 Pillow 实际解码一次（能发现文件头正常但内容坏的情况）
    decodes = None  # None=无 Pillow / True=可解码 / False=解码失败
    try:
        from PIL import Image
        with Image.open(p) as im:
            im.verify()
        decodes = True
    except ImportError:
        pass  # 没装 Pillow 就只做字节检查
    except Exception as e:
        decodes = False
        problems.append(f"解码失败: {type(e).__name__}: {str(e)[:80]}")

    # v4.4.3（交付物复验修复）：不能「出现任意 U+FFFD 字节就定罪」。
    # JPEG/PNG 是二进制压缩数据，像素里恰好出现 EF BF BD 三字节是合法且常见的
    # （实测一张正常导出的 poster-story.jpg 在压缩数据中间有 1 个，Pillow 能完整解码）。
    # 真正的「文本往返损坏」特征是：文件头即 EF BF BD，或替换字符成千上万成片出现。
    # 判据 = 头损坏 / 解码失败 / 「成片替换字符」——成片用绝对数 + 密度双门槛，
    # 避免小文件里 1 个孤立字节因密度虚高被误判（16x16 JPEG 插 1 个 = 0.16%）。
    # 真「文本往返损坏」是成千上万个（外部审计报告 5 万+），个位数是二进制巧合。
    n = data.count(REPLACEMENT)
    density = n / max(len(data), 1)
    head_corrupt = data[:2] == b"\xef\xbf" or data[:3] == REPLACEMENT[:3]
    mass_pollution = n >= 20 and density > 0.001
    if n and (head_corrupt or mass_pollution or decodes is False):
        problems.append(f"含 {n} 个 U+FFFD 替换字符（{density*100:.2f}%，"
                        f"文本往返损坏或疑似损坏）")

    # 文件头快检（不解码也能发现的）
    if head_corrupt:
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
