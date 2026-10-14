#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════
#  海报预检 —— 渲染前后各一道闸
#
#    渲染前：查数据（示例数据 / 必填为空 / 二维码文件缺失）
#    渲染后：查成品（尺寸 / 空白图 / 底部被裁）
#
#  用法：  ./preflight.py --root <项目目录>            渲染前检查数据
#          ./preflight.py --root <项目目录> --output   渲染后检查成品
#          ./preflight.py --root <项目目录> --all      两个都查
#
#  默认的项目目录是当前工作目录（即含 lib/data.typ 的那个目录）。
#
#  退出码：0 = 通过（可能有警告）   1 = 有错误，不该发印
# ═══════════════════════════════════════════════════════════════════

import argparse
import os
import re
import subprocess
import sys

# 项目根：默认当前工作目录，可用 --root 覆盖。
# （不默认脚本所在目录：这个脚本放在项目外的 scripts/ 里，
#   是要被复用的，项目目录必须由调用方指定。）
ROOT = os.path.abspath(os.environ.get("POSTER_ROOT") or os.getcwd())
DATA = os.path.join(ROOT, "lib", "data.typ")

# 每种格式的期望产物：文件名 → (宽, 高, 底部净空px, 说明)
# 底部净空 = 最底部这么高的像素带必须是纯白（防内容被静默裁掉 / 溢出页面）
FORMATS = {
    "poster-a4":     (2480, 3508, 60,  "A4 打印版"),
    "poster-social": (2160, 2880, 60,  "朋友圈版"),
    "poster-square": (2160, 2160, 60,  "方形封面版"),
    "poster-story":  (1080, 1920, 288, "竖屏 Story"),
    "poster-wide":   (1920, 1080, 30,  "横版头图"),
    "poster-banner": (3150, 7874, 240, "易拉宝版"),
}

REQUIRED = [
    "org", "kicker", "title", "lead", "lead_short",
    "speaker", "date", "venue", "seats", "enroll", "qr_note",
]

GREEN, RED, YELLOW, DIM, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"

errors: list[str] = []
warns: list[str] = []
oks: list[str] = []


def err(m):  errors.append(m)
def warn(m): warns.append(m)
def ok(m):   oks.append(m)


# ─────────────────────────────────────────────────────────────────
#  渲染前：数据检查
# ─────────────────────────────────────────────────────────────────
def parse_data(path: str) -> dict:
    """从 Typst 数据文件里抠出顶层字段。够用即可，不做完整语法解析。"""
    if not os.path.exists(path):
        err(f"找不到数据文件：{path}")
        return {}
    src = open(path, encoding="utf-8").read()
    fields: dict[str, str] = {}

    # 简单标量：  key:  "值",   或   key: none,
    for m in re.finditer(r'^\s+(\w+)\s*:\s*(.+?)\s*,?\s*(?://.*)?$', src, re.M):
        k, v = m.group(1), m.group(2).strip().rstrip(",")
        fields.setdefault(k, v)

    # 多值字段 highlights: ( "a", "b", ... )
    m = re.search(r'highlights\s*:\s*\((.*?)\)\s*,?\s*\n', src, re.S)
    if m:
        fields["highlights_count"] = str(len(re.findall(r'"[^"]*"', m.group(1))))

    # draft 标志：显式开关，比"猜哪些像示例值"可靠
    m = re.search(r'^\s+draft\s*:\s*(true|false)', src, re.M)
    fields["draft"] = m.group(1) if m else "<未设置>"

    return fields


def strip_typst(v: str) -> str:
    """把 Typst 字面量还原成纯文本用于长度估算。"""
    v = v.strip()
    v = re.sub(r'^"(.*)"$', r"\1", v, flags=re.S)
    v = v.replace("\\n", "\n")
    return v


def check_data(strict_sample: bool):
    f = parse_data(DATA)
    if not f:
        return

    print(f"  {DIM}数据文件：lib/data.typ{OFF}")

    # ① 草稿开关 —— 防把示例数据当正式稿发出去
    if f.get("draft") == "true":
        (err if strict_sample else warn)(
            'data.typ 是 draft: true（示例数据）。确认内容后把 draft 改成 false'
        )
    elif f.get("draft") == "<未设置>":
        warn("data.typ 没有 draft 字段，无法判断是否仍为示例数据")
    else:
        ok("draft: false（已确认为正式数据）")

    # ② 必填字段不能空
    empty = [k for k in REQUIRED
             if k in f and strip_typst(f[k]) in ("", "none", '""')]
    missing = [k for k in REQUIRED if k not in f]
    if empty:
        err("字段为空：" + "、".join(empty))
    if missing:
        err("字段缺失：" + "、".join(missing))
    if not empty and not missing:
        ok(f"必填字段齐全（{len(REQUIRED)} 项）")

    # ③ 二维码：占位框 / 文件是否存在
    qr = f.get("qr_image", "none")
    if qr in ("none", "<未设置>"):
        warn("qr_image 仍是 none —— 成品上二维码位置是空的占位框，不能发印")
    else:
        name = strip_typst(qr)
        p = name if os.path.isabs(name) else os.path.join(ROOT, name)
        if os.path.exists(p):
            ok(f"二维码文件存在：{name}")
        else:
            err(f'qr_image 指向 "{name}"，但文件不存在（渲染会失败）')

    # ④ 亮点条数
    n = int(f.get("highlights_count", "0") or 0)
    if n == 0:
        err("highlights 为空，成品上会缺一块")
    elif n > 4:
        warn(f"highlights 有 {n} 条，建议 3–4 条（多了版面会被挤）")
    else:
        ok(f"亮点 {n} 条")

    # ⑤ 标题行长 —— 单行太长会折行，把精心排的版面毁掉
    title = strip_typst(f.get("title", ""))
    if title:
        lines = title.split("\n")
        longest = max((len(l) for l in lines), default=0)
        # A4 主标题 24pt / 174mm 栏宽 ≈ 每行 24 全角字；留安全余量按 18
        if longest > 18:
            warn(
                f"标题最长一行 {longest} 字（上限约 18）——"
                f"可能在 A4 上折行；请手动加 \\n 断开"
            )
        else:
            ok(f"标题 {len(lines)} 行，最长 {longest} 字")


# ─────────────────────────────────────────────────────────────────
#  渲染前：字体可用性检查（把「静默回退」变成闸门）
#
#  模板只写字体名（取自 tokens.typ 的 FONTS 字体栈）。若本机一个都
#  没有，Typst 不会报错，而是【静默回退】到默认字体，版式悄悄走样 ——
#  这正是本项目要消灭的那类静默失败。这里用 `typst fonts` 核对。
# ─────────────────────────────────────────────────────────────────
def parse_font_stack(tokens_path: str) -> list:
    """从 tokens.typ 抠出 FONTS 字体栈里的字体名（按优先级）。"""
    if not os.path.exists(tokens_path):
        return []
    src = open(tokens_path, encoding="utf-8").read()
    m = re.search(r'FONTS\s*=\s*\((.*?)\)', src, re.S)
    return re.findall(r'"([^"]+)"', m.group(1)) if m else []


def check_fonts():
    stack = parse_font_stack(os.path.join(ROOT, "lib", "tokens.typ"))
    if not stack:
        warn("未在 lib/tokens.typ 找到 FONTS 字体栈，跳过字体可用性检查")
        return
    try:
        # 不用 text=True：Windows 上会按 GBK 解码 Typst 的 UTF-8 输出而崩溃
        r = subprocess.run(["typst", "fonts"], capture_output=True, timeout=60)
    except Exception as e:
        warn(f"无法执行 `typst fonts`（{e.__class__.__name__}），跳过字体检查")
        return
    if r.returncode != 0:
        warn("`typst fonts` 执行失败，跳过字体检查")
        return

    out = (r.stdout or b"").decode("utf-8", errors="replace")
    have = {ln.strip() for ln in out.splitlines() if ln.strip()}
    available = [f for f in stack if f in have]
    if not available:
        err("字体栈在本机一个都不可用：" + " / ".join(stack)
            + " —— 渲染会【静默回退】到默认字体，版式会变！")
    elif available[0] != stack[0]:
        warn(f'首选字体 "{stack[0]}" 本机没有，回退到 "{available[0]}"'
             f'（跨平台正常，但要确认版式未走样）')
    else:
        ok(f"首选字体可用：{stack[0]}")


# ─────────────────────────────────────────────────────────────────
#  渲染前：风格预设校验（--input style=...）
#
#  模板颜色取自 lib/styles.typ 的命名方案。名字写错时 Typst 会静默回退到
#  默认色 —— 又是一类静默失败。这里核对请求的风格是否存在于方案库。
# ─────────────────────────────────────────────────────────────────
def parse_styles() -> dict:
    p = os.path.join(ROOT, "lib", "styles.typ")
    if not os.path.exists(p):
        return {}
    src = open(p, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'"([a-z0-9\-]+)"\s*:\s*\(([\s\S]*?)\n\s*\),', src):
        key, body = m.group(1), m.group(2)
        lm = re.search(r'label:\s*"([^"]*)"', body)
        if not lm:
            continue
        um = re.search(r'use:\s*"([^"]*)"', body)
        out[key] = {"label": lm.group(1), "use": um.group(1) if um else ""}
    return out


def check_style(requested):
    styles = parse_styles()
    if not styles:
        warn("未找到 lib/styles.typ，跳过风格检查")
        return
    if not requested:
        ok(f"风格库 {len(styles)} 套：{'、'.join(styles)}")
        return
    if requested in styles:
        s = styles[requested]
        ok(f'风格 "{requested}"（{s["label"]}）—— {s["use"]}')
    else:
        err(f'未知风格 "{requested}"，可选：' + "、".join(styles))


# ─────────────────────────────────────────────────────────────────
#  渲染前：对比度闸门
#
#  借鉴 huashu-design / html-anything 的「对比度 ≥ 4.5」硬约束 —— 但把它从
#  「写进提示词的纪律」变成**可执行检查**：逐套配色算 WCAG 对比度，不达标即报。
# ─────────────────────────────────────────────────────────────────
def parse_palette_colors() -> dict:
    p = os.path.join(ROOT, "lib", "styles.typ")
    if not os.path.exists(p):
        return {}
    src = open(p, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'"([a-z0-9\-]+)"\s*:\s*\(([\s\S]*?)\n\s*\),', src):
        key, body = m.group(1), m.group(2)
        cols = dict(re.findall(r'(\w+)\s*:\s*rgb\("#([0-9A-Fa-f]{6})"\)', body))
        if cols:
            out[key] = cols
    return out


def _rel_lum(hexstr: str) -> float:
    r, g, b = (int(hexstr[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def f(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _contrast(a: str, b: str) -> float:
    la, lb = _rel_lum(a), _rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# (前景, 背景, 目标比, 级别, 说明)；"ffffff" 表示纯白
CONTRAST_RULES = [
    ("ink",     "ffffff", 4.5, "err",  "正文 ink 于白底"),
    ("muted",   "ffffff", 4.5, "err",  "次要文字 muted 于白底（小字）"),
    ("brand",   "ffffff", 3.0, "warn", "主色 brand 于白底（标题，大字）"),
    ("ffffff",  "brand",  4.5, "err",  "白字于品牌带"),
    ("brand2",  "brand",  3.0, "warn", "点缀色 brand2 于品牌带"),
]


def check_contrast():
    palettes = parse_palette_colors()
    if not palettes:
        warn("未找到 lib/styles.typ 配色，跳过对比度检查")
        return
    bad = 0
    for key, cols in palettes.items():
        for fg, bg, target, level, desc in CONTRAST_RULES:
            cf = "ffffff" if fg == "ffffff" else cols.get(fg)
            cb = "ffffff" if bg == "ffffff" else cols.get(bg)
            if not cf or not cb:
                continue
            r = _contrast(cf, cb)
            if r < target:
                bad += 1
                msg = f'{key}：{desc} = {r:.2f}:1 < {target}:1'
                (err if level == "err" else warn)(msg)
    if bad == 0:
        ok(f"对比度全部达标（{len(palettes)} 套配色 × {len(CONTRAST_RULES)} 条规则）")


def _ink_and_dirty(im, region=None):
    """统计墨迹占比与"脏像素"数。

    用 tobytes() 而不是 getdata()：后者在 Pillow 13+ 已弃用
    （2027-10 移除），而 tobytes() 各版本都在，也不依赖 numpy。
    """
    if region is not None:
        im = im.crop(region)
    data = im.tobytes()
    total = len(data) // 3
    dirty = 0
    for i in range(0, len(data), 3):
        if data[i] < 245 or data[i + 1] < 245 or data[i + 2] < 245:
            dirty += 1
    return dirty, total


# ─────────────────────────────────────────────────────────────────
#  渲染后：成品检查
# ─────────────────────────────────────────────────────────────────
def check_output():
    try:
        from PIL import Image
    except ImportError:
        warn("没装 Pillow，跳过成品像素检查")
        return

    for name, (w_exp, h_exp, safe_bottom, desc) in FORMATS.items():
        p = os.path.join(ROOT, "out", f"{name}.png")
        if not os.path.exists(p):
            err(f"{desc}：缺少 {name}.png")
            continue

        im = Image.open(p)
        w, h = im.size
        if (w, h) != (w_exp, h_exp):
            err(f"{desc}：尺寸 {w}×{h}，期望 {w_exp}×{h_exp}")
            continue

        if im.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            rgba = im.convert("RGBA")
            bg.paste(rgba, mask=rgba.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")

        # ① 不是空白图（缩到 200px 宽再统计，够快又够准）
        small = im.resize((200, max(1, int(200 * h / w))), Image.LANCZOS)
        dirty, total = _ink_and_dirty(small)
        ink = dirty / total
        if ink < 0.005:
            err(f"{desc}：几乎空白（墨迹 {ink*100:.2f}%），渲染可能失败")
            continue

        # ② 底部净空必须纯白 —— 抓"内容被静默裁到页面外"
        d2, t2 = _ink_and_dirty(im, region=(0, h - safe_bottom, w, h))
        if d2 > 0:
            err(
                f"{desc}：底部 {safe_bottom}px 净空区有内容（{d2/t2*100:.2f}%），"
                f"可能有元素被裁到页面外"
            )
        else:
            ok(f"{desc}：{w}×{h}，墨迹 {ink*100:.1f}%，底部净空干净")


# ─────────────────────────────────────────────────────────────────
def _print_section(title: str):
    print(f"\n══ {title} ══")
    for m in oks:    print(f"  {GREEN}✅{OFF} {m}")
    for m in warns:  print(f"  {YELLOW}⚠️ {OFF} {m}")
    for m in errors: print(f"  {RED}❌{OFF} {m}")


def main():
    ap = argparse.ArgumentParser(description="海报预检")
    ap.add_argument("--root", default=None,
                    help="项目目录（含 lib/data.typ），默认当前工作目录")
    ap.add_argument("--output", action="store_true", help="只检查渲染后的成品")
    ap.add_argument("--all", action="store_true", help="数据+成品都检查")
    ap.add_argument("--strict", action="store_true", help="把示例数据警告升级为错误")
    ap.add_argument("--style", default=None, help="校验指定风格名（styles.typ）")
    ap.add_argument("--list-styles", action="store_true", help="列出全部风格并退出")
    a = ap.parse_args()

    if a.root:
        global ROOT, DATA
        ROOT = os.path.abspath(a.root)
        DATA = os.path.join(ROOT, "lib", "data.typ")

    if a.list_styles:
        styles = parse_styles()
        print("可用风格（--input style=<名>）：")
        for k, v in styles.items():
            print(f"  {k:<16} {v['label']:<8} {v['use']}")
        return 0

    # 两段各跑各的，最后给一条总结论 —— 避免中间那条
    # "预检全部通过" 被误读成整体结论
    total_errors: list[str] = []
    total_warns: list[str] = []

    if not a.output:
        check_data(strict_sample=a.strict)
        check_fonts()
        check_style(a.style or os.environ.get("POSTER_STYLE"))
        check_contrast()
        _print_section("预检（渲染前 · 数据 + 字体 + 风格 + 对比度）")
        total_errors += errors
        total_warns += warns
        oks.clear(); warns.clear(); errors.clear()

    if a.output or a.all:
        check_output()
        _print_section("后检（渲染后 · 查成品）")
        total_errors += errors
        total_warns += warns
        oks.clear(); warns.clear(); errors.clear()

    print()
    if total_errors:
        print(f"{RED}✗ 未通过：{len(total_errors)} 个错误、{len(total_warns)} 个警告"
              f" —— 修好再发印{OFF}")
        return 1
    if total_warns:
        print(f"{YELLOW}△ 通过，但有 {len(total_warns)} 个警告需人工确认"
              f" —— 确认无误后可发印{OFF}")
        return 0
    print(f"{GREEN}✓ 全部通过，可发印{OFF}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
