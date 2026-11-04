#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════════
#  未指定尺寸时的推荐速查（duduhaibao 4.4.2）
#
#  动机：用户说「做张海报/邀请函/分享图」却没给尺寸时，不该默默选一个。
#  先给一组带「比例 + 具体像素 + 适用场景」的推荐，让用户/模型显式选。
#
#  数据单一真源：references/platform-specs.md（本仓已沉淀、经 9 版式验证的
#  中文平台规格），并与国际通用规范交叉核对（Sprout Social / Hootsuite 2026：
#  1:1=1080×1080、竖版 3:4=1080×1350~1440、9:16=1080×1920、宽 1080 是通用基准）。
#
#  用法：
#    python scripts/suggest_size.py                 # 全表
#    python scripts/suggest_size.py --scenario 网络传播
#    python scripts/suggest_size.py --scenario 微信邀请函
#    python scripts/suggest_size.py --scenario 朋友圈 --json
#    python scripts/suggest_size.py --list-scenarios
# ═══════════════════════════════════════════════════════════════════

import argparse
import json

# (渠道, 比例, 建议像素, 本仓格式, 适用场景/说明)
SIZES = [
    ("朋友圈单图 / 微信转发海报·邀请函（单图）", "3:4", "1080 × 1440",
     "poster-social", "【网络传播首选】竖图在手机信息流占屏最大，微信单图转发/邀请函通用；信息流缩略图会裁成方形，主体压中心"),
    ("朋友圈九宫格（9 图）", "1:1", "1080 × 1080",
     "poster-square", "九宫格每格必须是正方形，否则被裁；常用于活动九连图/产品九图"),
    ("朋友圈方形单图 / 节气问候", "1:1", "1080 × 1080",
     "poster-square / poster-term", "方形单图、节气/节日问候卡；中心构图最稳"),
    ("小红书封面 / 配图", "3:4", "1242 × 1656（常用 1080 × 1440）",
     "poster-social", "竖图信息流展示最佳，底部 ~12% 会被标题/按钮遮挡"),
    ("公众号首图（超宽）", "2.35:1", "900 × 383",
     "poster-wide 改比例", "公众号头条封面，右下角可能被播放按钮压住，主体压中心"),
    ("公众号正文配图 / 文章头图", "16:9", "1080 × 608（或 1920 × 1080）",
     "poster-wide", "文章内横图、网站 hero、视频封面"),
    ("抖音 / 视频号 / 快手 / Story 竖屏", "9:16", "1080 × 1920",
     "poster-story", "全屏竖版；顶部 ~10%、底部 ~15%、右侧 ~15% 被 UI 遮挡（preflight 已闸门化）"),
    ("A4 打印 / 张贴", "A4 210×297mm", "2480 × 3508 @300dpi",
     "poster-a4", "线下张贴、公告、通知、报名表"),
    ("易拉宝 / 展架", "80×200cm", "3150 × 7874 @100dpi",
     "poster-banner", "远距观看，底部 ~30cm 被展架遮挡"),
]

# 场景词 → 推荐尺寸组（按优先级）。用于「用户给了场景但没给尺寸」。
SCENARIOS = {
    "网络传播": ["朋友圈单图", "朋友圈九宫格", "小红书封面", "公众号首图", "抖音竖屏"],
    "微信转发": ["朋友圈单图", "朋友圈方形单图"],
    "微信邀请函": ["朋友圈单图", "朋友圈方形单图"],
    "邀请函": ["朋友圈单图", "朋友圈方形单图", "A4 打印"],
    "朋友圈": ["朋友圈单图", "朋友圈九宫格", "朋友圈方形单图"],
    "九宫格": ["朋友圈九宫格"],
    "小红书": ["小红书封面"],
    "公众号": ["公众号首图", "公众号正文配图"],
    "抖音": ["抖音竖屏"], "视频号": ["抖音竖屏"], "story": ["抖音竖屏"],
    "打印": ["A4 打印"], "张贴": ["A4 打印"], "印刷": ["A4 打印"],
    "易拉宝": ["易拉宝"], "展架": ["易拉宝"],
}


def _match(label):
    for key in SCENARIOS:
        if key in label:
            return SCENARIOS[key]
    return None


def recommend(scenario=None):
    """返回推荐行（dict 列表）。scenario 为空 = 给「网络传播」默认组。"""
    if not scenario:
        picks = SCENARIOS["网络传播"]
    else:
        # 场景词匹配渠道名
        picks = None
        for key, val in SCENARIOS.items():
            if key in scenario or scenario in key:
                picks = val
                break
        if not picks:
            picks = SCENARIOS["网络传播"]
    order = {name: i for i, name in enumerate(picks)}
    rows = []
    for s in SIZES:
        for name in picks:
            if name in s[0]:
                rows.append({"channel": s[0], "ratio": s[1], "pixels": s[2],
                             "format": s[3], "why": s[4], "rank": order.get(name, 99)})
                break
    rows.sort(key=lambda r: r["rank"])
    return rows


def main():
    ap = argparse.ArgumentParser(description="未指定尺寸时的推荐速查")
    ap.add_argument("--scenario", help="场景词（网络传播/微信邀请函/朋友圈/小红书/打印…）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--list-scenarios", action="store_true", help="列出可识别场景词")
    args = ap.parse_args()

    if args.list_scenarios:
        print("可识别场景词：", "、".join(sorted(set(SCENARIOS))))
        return 0

    rows = recommend(args.scenario)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    if args.scenario:
        print(f"场景：{args.scenario}  →  推荐尺寸（未指定尺寸时按此提示用户选）\n")
    else:
        print("未指定尺寸 —— 网络传播常用尺寸推荐（用 question 摆给用户选，推荐项在前）\n")
    for i, r in enumerate(rows, 1):
        star = " ★推荐" if i == 1 else ""
        print(f"  {i}. {r['channel']}{star}")
        print(f"     比例 {r['ratio']} · 像素 {r['pixels']} · 本仓格式 {r['format']}")
        print(f"     {r['why']}")
    print("\n  完整规格/安全区见 references/platform-specs.md；投放体积/格式见 references/delivery-guide.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
