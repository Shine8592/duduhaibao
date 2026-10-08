#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════
#  海报生产线 · 回归测试
#
#  每个用例都对应一个【真实发生过的故障】，防止改版时重新踩坑：
#    bug_01_truncated  易拉宝序号 "01" 被挤成 "0"（静默，只在成品上可见）
#    bug_label_wrap    朋友圈 "活动时间" 折成 "活动时 / 间"
#    bug_overflow      内容排到页面外被 Typst 静默裁掉
#    ok_all            三种格式的正确配置（防断言误报）
#
#  用法：python3 tests/run_tests.py     （需先 pip install pillow）
# ═══════════════════════════════════════════════════════════════════

import os
import subprocess
import sys

# ROOT = 示例项目目录（本文件的上一级），Typst 编译以它为根
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# preflight.py 在项目外的 scripts/ 里，复用它的像素检查函数
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "scripts"))

GREEN, RED, DIM, OFF = "\033[32m", "\033[31m", "\033[2m", "\033[0m"
passed, failed = 0, 0


def typst(src, out, ppi=None):
    """编译，返回 (成功?, 输出)"""
    cmd = ["typst", "compile", "--root", ROOT]
    if ppi:
        cmd += ["--format", "png", "--ppi", str(ppi)]
    cmd += [src, out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, (r.stderr or "") + (r.stdout or "")


def case(name, desc, expect_ok, src, ppi=None, must_mention=None):
    global passed, failed
    ok, out = typst(src, "/tmp/rt-out.png" if ppi else "/tmp/rt-out.pdf", ppi)
    problems = []
    if ok != expect_ok:
        problems.append(
            "编译" + ("通过了" if ok else "失败了") + "，但期望" + ("通过" if expect_ok else "失败")
        )
    if must_mention and must_mention not in out:
        problems.append(f'错误信息里没提到 "{must_mention}"')

    if problems:
        failed += 1
        print(f"  {RED}✗{OFF} {name}")
        for p in problems:
            print(f"      {p}")
        if out:
            print(f"      {DIM}{out.strip().splitlines()[0] if out.strip() else ''}{OFF}")
    else:
        passed += 1
        note = "如预期报错" if not expect_ok else "通过"
        print(f"  {GREEN}✓{OFF} {name} {DIM}— {desc}（{note}）{OFF}")


def case_pixel(name, desc, src, safe_bottom_px):
    """渲染后跑与 preflight 相同的底部净空检查"""
    global passed, failed
    png = "/tmp/rt-ovf.png"
    ok, out = typst(src, png, ppi=150)
    if not ok:
        failed += 1
        print(f"  {RED}✗{OFF} {name} —— 渲染就失败了")
        print(f"      {DIM}{out.strip().splitlines()[0] if out.strip() else ''}{OFF}")
        return
    import preflight
    from PIL import Image
    im = Image.open(png).convert("RGB")
    w, h = im.size
    sb = max(1, int(safe_bottom_px * h / 3508))       # 按 A4 口径等比缩放
    dirty, total = preflight._ink_and_dirty(im, region=(0, h - sb, w, h))
    if dirty > 0:
        passed += 1
        print(f"  {GREEN}✓{OFF} {name} {DIM}— {desc}（检出 {dirty/total*100:.2f}% 越界像素）{OFF}")
    else:
        failed += 1
        print(f"  {RED}✗{OFF} {name} —— 底部净空干净，越界内容被漏过")


print("════════ 海报生产线 · 回归测试 ════════\n")

print(f"  {DIM}断言类：应当编译失败（把静默 bug 变成大声报错）{OFF}")
case("01 被裁成 0", "易拉宝字号塞进 9mm 序号列",
     expect_ok=False, src=f"{ROOT}/tests/bug_01_truncated.typ",
     must_mention="highlights")
case("标签折行", "px(32) 字号塞进 px(120) 标签列",
     expect_ok=False, src=f"{ROOT}/tests/bug_label_wrap.typ",
     must_mention="info_row")

print(f"\n  {DIM}防误报类：应当编译通过{OFF}")
case("正确配置不误报", "A4 + 朋友圈 + 易拉宝三种真实配置",
     expect_ok=True, src=f"{ROOT}/tests/ok_all.typ")

print(f"\n  {DIM}成品后检：越界内容应当被像素检查抓住{OFF}")
case_pixel("内容溢出页面", "元素被排到页面底部之外（Typst 静默裁掉）",
           src=f"{ROOT}/tests/bug_overflow.typ", safe_bottom_px=60)

print()
total = passed + failed
if failed:
    print(f"{RED}✗ {failed}/{total} 个用例失败{OFF}")
    sys.exit(1)
print(f"{GREEN}✓ 全部 {total} 个用例通过{OFF}")
