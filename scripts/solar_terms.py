#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════════
#  二十四节气 —— 确定性计算（不联网、不问模型）
#
#  为什么自己做：节气日期**每年都变**（清明 4/4 或 4/5、冬至 12/21 或 12/22…）。
#  这正是本仓「日期绝不交给模型」铁律的适用场景：用太阳视黄经算，可复现、可核验。
#
#  方法：太阳视黄经（Meeus 低精度公式，~0.01°）→ 求 λ = 15°×k 的时刻
#       → 转北京时间（UTC+8）→ 取日期。精度对"出海报"绰绰有余。
#
#  用法：
#    python scripts/solar_terms.py                      # 打印 2026-2028 全部节气
#    python scripts/solar_terms.py --year 2026          # 只打印某年
#    python scripts/solar_terms.py --year 2026 2027 2028 --emit   # 生成 lib/terms.typ
# ═══════════════════════════════════════════════════════════════════

import argparse
import math
import os
import sys

# 节气顺序与对应太阳黄经（度）：从小寒(285°)起，每 15°
TERMS = [
    ("小寒", 285), ("大寒", 300), ("立春", 315), ("雨水", 330),
    ("惊蛰", 345), ("春分", 0),   ("清明", 15),  ("谷雨", 30),
    ("立夏", 45),  ("小满", 60),  ("芒种", 75),  ("夏至", 90),
    ("小暑", 105), ("大暑", 120), ("立秋", 135), ("处暑", 150),
    ("白露", 165), ("秋分", 180), ("寒露", 195), ("霜降", 210),
    ("立冬", 225), ("小雪", 240), ("大雪", 255), ("冬至", 270),
]

# 季节 + 一句释义（安全、通用；不含具体"三候"以免出错）
TERM_INFO = {
    "小寒": ("冬", "天寒地冻，进入严寒"),
    "大寒": ("冬", "一年最冷，冬去春来"),
    "立春": ("春", "春回大地，万物始生"),
    "雨水": ("春", "降雨渐多，冰雪消融"),
    "惊蛰": ("春", "春雷始鸣，蛰虫惊醒"),
    "春分": ("春", "昼夜均分，春暖花开"),
    "清明": ("春", "天清地明，踏青祭扫"),
    "谷雨": ("春", "雨生百谷，播种时节"),
    "立夏": ("夏", "万物繁茂，夏日伊始"),
    "小满": ("夏", "麦粒渐满，雨水丰盈"),
    "芒种": ("夏", "有芒麦收，忙种忙收"),
    "夏至": ("夏", "白昼最长，盛夏将至"),
    "小暑": ("夏", "暑气渐盛，热浪初起"),
    "大暑": ("夏", "一年最热，防暑降温"),
    "立秋": ("秋", "暑去凉来，秋意渐生"),
    "处暑": ("秋", "暑气止息，秋凉渐显"),
    "白露": ("秋", "昼夜温差，露凝而白"),
    "秋分": ("秋", "昼夜均分，秋色平分"),
    "寒露": ("秋", "露水更凉，秋意渐深"),
    "霜降": ("秋", "天气渐冷，初霜出现"),
    "立冬": ("冬", "万物收藏，冬季伊始"),
    "小雪": ("冬", "初雪飘落，寒意渐浓"),
    "大雪": ("冬", "雪盛冰封，天寒地冻"),
    "冬至": ("冬", "白昼最短，数九开始"),
}


def jd_from_ymd(y, m, d, h=0.0):
    if m <= 2:
        y -= 1; m += 12
    A = y // 100
    B = 2 - A + A // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5 + h / 24.0


def ymd_from_jd(jd, tz=8.0):
    """JD → (年,月,日,时,分)，默认北京时间 UTC+8。"""
    jd = jd + tz / 24.0
    Z = int(jd + 0.5); F = (jd + 0.5) - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - alpha // 4
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)
    day = B - D - int(30.6001 * E) + F
    month = E - 1 if E < 14 else E - 13
    year = C - 4716 if month > 2 else C - 4715
    di = int(day); frac = day - di
    hh = frac * 24.0; mm = (hh - int(hh)) * 60.0
    return year, month, di, int(hh), int(mm)


def sun_lon(jd):
    """太阳视黄经（度），Meeus 低精度公式，精度约 0.01°。"""
    T = (jd - 2451545.0) / 36525.0
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
    Mr = math.radians(M % 360.0)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(Mr)
         + (0.019993 - 0.000101 * T) * math.sin(2 * Mr)
         + 0.000289 * math.sin(3 * Mr))
    true = L0 + C
    Om = 125.04 - 1934.136 * T
    return (true - 0.00569 - 0.00478 * math.sin(math.radians(Om))) % 360.0


def _diff(jd, target):
    return ((sun_lon(jd) - target + 180.0) % 360.0) - 180.0


def find_term_jd(year, target):
    """在给定公历年内找到太阳黄经 = target 的时刻（JD）。"""
    j0 = jd_from_ymd(year, 1, 1)
    j1 = jd_from_ymd(year + 1, 1, 1)
    prev = _diff(j0, target)
    j = j0
    while j < j1:
        jn = j + 0.5
        cur = _diff(jn, target)
        if prev < 0.0 <= cur:
            lo, hi = j, jn
            for _ in range(50):
                mid = (lo + hi) / 2.0
                if _diff(mid, target) < 0.0:
                    lo = mid
                else:
                    hi = mid
            return (lo + hi) / 2.0
        prev = cur
        j = jn
    return None


def terms_of_year(year):
    out = []
    for name, lam in TERMS:
        jd = find_term_jd(year, lam)
        if jd is None:
            continue
        y, m, d, hh, mm = ymd_from_jd(jd)
        out.append((name, y, m, d, hh, mm))
    out.sort(key=lambda t: (t[1], t[2], t[3], t[4], t[5]))
    return out


def self_check():
    """粗校验：二分/夏至/秋分/冬至应落在常识范围内。"""
    t = {n: (m, d) for n, _, m, d, _, _ in terms_of_year(2026)}
    ok = (3, 19) <= t["春分"] <= (3, 21) and \
         (6, 20) <= t["夏至"] <= (6, 22) and \
         (9, 21) <= t["秋分"] <= (9, 24) and \
         (12, 20) <= t["冬至"] <= (12, 23)
    return ok


def emit_typst(years, path):
    lines = ["// 二十四节气日期表 —— 由 scripts/solar_terms.py 生成（勿手改）",
             "// 太阳视黄经计算（Meeus 低精度）→ 北京时间；每年重跑生成。", "",
             "#let TERMS = ("]
    for y in years:
        for name, yy, m, d, hh, mm in terms_of_year(y):
            lines.append(f'  (year: {yy}, name: "{name}", m: {m}, d: {d}),')
    lines += (")", "", "#let TERM_INFO = (")
    for name, _ in TERMS:
        season, note = TERM_INFO[name]
        lines.append(f'  "{name}": (season: "{season}", note: "{note}"),')
    lines += (")", "")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return path


def main():
    ap = argparse.ArgumentParser(description="二十四节气确定性计算")
    ap.add_argument("--year", nargs="+", type=int, default=[2026, 2027, 2028])
    ap.add_argument("--root", default=None, help="项目 example 目录（生成 terms.typ 用）")
    ap.add_argument("--emit", action="store_true", help="生成 lib/terms.typ")
    a = ap.parse_args()

    for y in a.year:
        rows = terms_of_year(y)
        print(f"══ {y} 年二十四节气（北京时间）══")
        for i, (name, yy, m, d, hh, mm) in enumerate(rows):
            season, note = TERM_INFO[name]
            print(f"  {name}  {yy}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}  [{season}] {note}")
        print()

    print("自检（2026 二分二至）：", "通过 ✅" if self_check() else "异常 ❌")

    if a.emit:
        root = a.root or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "example")
        path = emit_typst(a.year, os.path.join(root, "lib", "terms.typ"))
        print("已生成：", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
