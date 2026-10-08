#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════
#  二维码回归测试 —— 验证成品里的二维码真的能扫出来
#
#  为什么需要它：二维码放错位置、尺寸太小、静默区被吃掉、对比度不足，
#  在屏幕预览上完全看不出问题，但打印出来就是扫不出。这类失败是静默的。
#
#  做法：不硬编码坐标 —— 让解码器全图搜索，所以它同样能发现
#  「二维码被挪到版面外」这类版式回归。
#
#  依赖（二选一，自动适配）：
#    A) pyzbar      —— pip install pyzbar     + apt install libzbar0
#    B) opencv      —— pip install opencv-python-headless
#
#  用法：python3 tests/check_qr.py
# ═══════════════════════════════════════════════════════════════════

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # 示例项目目录
sys.path.insert(0, ROOT)

GREEN, RED, DIM, OFF = "\033[32m", "\033[31m", "\033[2m", "\033[0m"

from PIL import Image


# ── 解码后端 ──────────────────────────────────────────────────────
def _backend():
    try:
        from pyzbar.pyzbar import decode as _d
        return "pyzbar", lambda im: [r.data.decode() for r in _d(im)]
    except Exception:
        pass
    try:
        import cv2
        import numpy as np

        def _d(im):
            arr = cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2BGR)
            data, _, _ = cv2.QRCodeDetector().detectAndDecode(arr)
            return [data] if data else []

        return "opencv", _d
    except Exception:
        return None, None


def expected_payload():
    """从 lib/data.typ 读出 qr_image 指向的源图，解码它作为期望值。

    这样就不用在测试里硬编码 URL —— 数据改了测试自动跟随。
    """
    import re
    src = open(os.path.join(ROOT, "lib", "data.typ"), encoding="utf-8").read()
    m = re.search(r'qr_image\s*:\s*"([^"]+)"', src)
    if not m:
        return None, None          # qr_image: none → 无期望值
    name = m.group(1)
    path = name if os.path.isabs(name) else os.path.join(ROOT, name)
    if not os.path.exists(path):
        return None, None
    _, decode = _backend()
    got = decode(Image.open(path))
    return (got[0] if got else None), name


def main():
    name, decode = _backend()
    if not decode:
        print(f"  {DIM}（无 pyzbar / opencv，跳过二维码检查）{OFF}")
        return 0

    print(f"  {DIM}解码后端：{name}{OFF}")

    want, srcfile = expected_payload()
    if want is None:
        print(f"  {DIM}（data.typ 的 qr_image 为 none，成品上是占位框，跳过）{OFF}")
        return 0
    print(f"  {DIM}期望值（来自 {srcfile}）：{want}{OFF}")

    outputs = ["poster-a4", "poster-social", "poster-banner"]
    checked = failed = 0

    for n in outputs:
        p = os.path.join(ROOT, "out", f"{n}.png")
        if not os.path.exists(p):
            print(f"  {RED}✗{OFF} {n}：缺少成品（先跑 build.sh）")
            failed += 1
            continue

        got = decode(Image.open(p))
        checked += 1
        if not got:
            print(f"  {RED}✗{OFF} {n}：成品里没找到二维码 —— 可能被挪出画面/尺寸过小/对比度不足")
            failed += 1
        elif got[0] != want:
            print(f"  {RED}✗{OFF} {n}：解码内容不符\n      期望 {want}\n      实际 {got[0]}")
            failed += 1
        elif len(got) > 1:
            print(f"  {RED}✗{OFF} {n}：找到 {len(got)} 个二维码，预期只有 1 个")
            failed += 1
        else:
            print(f"  {GREEN}✓{OFF} {n} {DIM}— 二维码可扫，内容正确{OFF}")

    if failed:
        print(f"\n  {RED}✗ 二维码检查未通过：{failed} 个问题{OFF}")
        return 1
    print(f"\n  {GREEN}✓ 二维码检查通过（{checked} 个格式）{OFF}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
