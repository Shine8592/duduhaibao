#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════════
#  环境自检 —— 装完先跑这个
#
#  检查渲染所需的依赖是否齐全，缺什么、怎么装，一目了然。
#  ⚠️ 本脚本【只报告，不安装】—— 借鉴同类项目的纪律：不向全局 Python 静默装包。
#
#  用法：python doctor.py
#  退出码：0 = 必需依赖齐全；1 = 缺必需项
# ═══════════════════════════════════════════════════════════════════

import importlib
import shutil
import subprocess
import sys

GREEN, RED, YELLOW, DIM, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
fails = 0


def ok(m):   print(f"  {GREEN}✅{OFF} {m}")
def warn(m): print(f"  {YELLOW}⚠️ {OFF} {m}")
def bad(m):
    global fails
    fails += 1
    print(f"  {RED}❌{OFF} {m}")


def have_mod(name):
    try:
        m = importlib.import_module(name)
        return getattr(m, "__version__", "?")
    except Exception:
        return None


def main():
    print("═══ 海报环境自检 ═══")

    # Python
    v = sys.version_info
    if v >= (3, 9):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        bad(f"Python {v.major}.{v.minor} 太旧，需要 ≥ 3.9")

    # Typst（必需）
    typst = shutil.which("typst")
    if typst:
        try:
            r = subprocess.run(["typst", "--version"], capture_output=True, timeout=15)
            ver = (r.stdout or b"").decode("utf-8", "replace").strip()
            ok(f"Typst —— {ver}  ({typst})")
        except Exception as e:
            bad(f"typst 存在但执行失败：{e}")
    else:
        bad("找不到 typst（必需）。装法见 README：winget install Typst.Typst / brew install typst")

    # Pillow（必需）
    pil = have_mod("PIL")
    if pil:
        ok(f"Pillow {pil}")
    else:
        bad("缺 Pillow（必需）：pip install pillow")

    # 中文字体（必需，否则中文变豆腐块）
    if typst:
        try:
            r = subprocess.run(["typst", "fonts"], capture_output=True, timeout=30)
            fonts = (r.stdout or b"").decode("utf-8", "replace")
            cjk = [f for f in ("Noto Sans CJK SC", "Noto Sans SC", "Microsoft YaHei") if f in fonts]
            if cjk:
                ok(f"中文字体可用：{'、'.join(cjk)}")
            else:
                bad("没有可用中文字体（需 Noto Sans CJK / Noto Sans SC / 微软雅黑）")
        except Exception:
            warn("无法执行 `typst fonts`，跳过字体检查")

    # 可选：二维码解码后端（check_qr.py 用）
    if have_mod("pyzbar") or have_mod("cv2"):
        ok("二维码解码后端（pyzbar / opencv）就绪")
    else:
        warn("无 pyzbar / opencv —— `tests/check_qr.py` 会跳过二维码检查（可选）")

    # 可选：HTML 路线
    if have_mod("weasyprint") and have_mod("fitz"):
        ok("HTML 路线依赖（weasyprint + pymupdf）就绪")
    else:
        warn("HTML 路线未就绪（weasyprint / pymupdf）—— 不用 HTML 路线可忽略（可选）")

    print()
    if fails:
        print(f"{RED}✗ 缺 {fails} 个必需项，先装好再跑 build{OFF}")
        return 1
    print(f"{GREEN}✓ 必需项齐全，可以渲染{OFF}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
