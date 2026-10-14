#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════════
#  场景 → 版式 / 配色 推荐
#
#  动机：本仓有 9 种版式、24 套配色，但"该用哪个"全靠人记。这个脚本把选择
#  变成**可解释的确定性规则**：命中哪些关键词、为什么推荐它，一条条列出来。
#  刻意不用模型"猜口味" —— 规则可审计、可修正，说错了改一行就行。
#
#  用法：
#    python scripts/suggest.py "幼儿园家长会"
#    python scripts/suggest.py "立冬节气海报"
#    python scripts/suggest.py --list
#    python scripts/suggest.py "公司产品发布会" --json
# ═══════════════════════════════════════════════════════════════════

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from solar_terms import TERM_INFO          # 复用节气→季节的唯一真源
except Exception:
    TERM_INFO = {}

# ── 版式规则：(模板, 一句话用途, [关键词], [默认配色(有序)]) ──
RULES = [
    ("poster-cute", "可爱 / 亲子方向：圆角卡 + 序号圆牌 + 贴纸点 + 圆体",
     ["幼儿园", "亲子", "儿童", "小朋友", "宝宝", "生日", "家长会", "兴趣班",
      "早教", "托班", "六一", "萌", "绘本", "手工", "小班", "大班", "中班"],
     ["candy-pink", "macaron", "sky", "peach", "mint"]),

    ("poster-term", "节气 / 节日：日期自动算（不问模型）",
     list(TERM_INFO.keys()) +
     ["节气", "节日", "新年", "元旦", "春节", "元宵", "端午", "中秋", "重阳",
      "七夕", "国庆", "除夕", "腊八", "问候"],
     ["（按季节自动选）"]),

    ("poster-photo", "照片集：1 / 2 / 3 / 4+ 张照片自动适配版式",
     ["游玩", "旅行", "旅游", "出游", "踏青", "露营", "徒步", "郊游", "打卡",
      "记录", "照片", "合影", "自拍", "毕业", "纪念", "日常", "vlog", "相册"],
     ["mist-blue", "warm-sand", "forest", "sky"]),

    ("poster-banner", "易拉宝 / 展架（80×200cm，远距观看）",
     ["易拉宝", "展架", "展板", "签到墙", "背景板", "x展架"],
     ["formal-blue", "navy-gold", "graphite"]),

    ("poster-a4", "A4 打印：张贴 / 公告 / 通知",
     ["打印", "张贴", "公告", "通知", "招生", "招聘", "讲座", "沙龙", "发布会",
      "峰会", "论坛", "会议", "报名", "课程", "年会", "推介", "培训", "研讨会"],
     ["formal-blue", "ink-green", "navy-gold", "festival-gold"]),

    ("poster-square", "方形封面（公众号首图 / 小红书封面）",
     ["公众号首图", "封面", "头像", "方图", "方形", "小红书封面", "app图标"],
     ["vivid-orange", "sakura", "formal-blue"]),

    ("poster-social", "朋友圈 / 小红书竖图（3:4）",
     ["朋友圈", "微信", "小红书", "分享", "配图", "群发", "动态"],
     ["sakura", "vivid-orange", "warm-sand"]),

    ("poster-story", "竖屏 Story（抖音 / 视频号 / 快手）",
     ["抖音", "视频号", "快手", "story", "竖屏", "短视频", "探店", "直播"],
     ["tech-cyan", "vivid-orange", "deep-space"]),

    ("poster-wide", "横版头图（文章头图 / 视频封面 / 微博 / 知乎）",
     ["文章头图", "视频封面", "微博", "知乎", "16:9", "横版", "og", "朋友圈封面"],
     ["mist-blue", "mono-slate", "formal-blue"]),
]

# ── 配色线索：命中即把该配色提到前面（可解释）──
STYLE_HINTS = [
    ("candy-pink", ["幼儿园", "儿童", "宝宝", "生日"]),
    ("macaron", ["亲子", "手工", "兴趣班"]),
    ("sky", ["运动会", "户外", "夏令营", "暑期"]),
    ("peach", ["生日", "烘焙", "市集"]),
    ("sakura", ["女性", "美妆", "花", "婚礼", "求婚", "节日赠礼"]),
    ("lavender", ["文艺", "诗会", "心理", "疗愈", "阅读", "花艺", "冥想"]),
    ("plum", ["国潮", "传统", "东方", "汉服", "茶", "艺术展"]),
    ("warm-sand", ["咖啡", "手作", "市集", "烘焙", "下午茶", "陶艺"]),
    ("mist-blue", ["摄影", "设计", "简约", "展览", "建筑"]),
    ("forest", ["自然", "环保", "户外", "露营", "徒步", "植树", "绿色"]),
    ("mint", ["自然课堂", "春游", "清新", "环保"]),
    ("teal", ["健康", "医疗", "瑜伽", "生活方式", "养生"]),
    ("tech-cyan", ["科技", "产品", "ai", "数据", "编程", "智能", "数字经济"]),
    ("deep-space", ["游戏", "未来", "宇宙", "电竞", "科幻", "元宇宙"]),
    ("mono-slate", ["极简", "数据报告", "内部", "季度"]),
    ("ink-green", ["学术", "讲座", "论坛", "答辩", "研讨", "读书", "文化"]),
    ("navy-gold", ["峰会", "颁奖", "高端", "招商", "答谢", "周年"]),
    ("festival-gold", ["年会", "庆典", "答谢", "颁奖", "周年", "店庆"]),
    ("crimson", ["节庆", "春节", "店庆", "开业", "促销", "庆典"]),
    ("formal-blue", ["企业", "发布", "开业", "招聘", "商务", "培训", "政府"]),
    ("vivid-orange", ["招生", "社群", "市集", "推广", "报名"]),
    ("royal-purple", ["品牌", "设计", "女性向"]),
    ("graphite", ["工业", "极简", "建筑", "制造"]),
]

SEASON_STYLE = {
    "春": ["mint", "forest", "teal"],
    "夏": ["teal", "sky", "tech-cyan"],
    "秋": ["warm-sand", "festival-gold", "crimson"],
    "冬": ["mist-blue", "navy-gold", "deep-space"],
}

FESTIVAL_SEASON = {
    "春节": "冬", "除夕": "冬", "新年": "冬", "元旦": "冬", "腊八": "冬", "元宵": "春",
    "清明": "春", "端午": "夏", "中秋": "秋", "重阳": "秋", "国庆": "秋", "七夕": "夏",
}

# 版式 → build 脚本的选择子
BUILD_ARG = {
    "poster-a4": "a4", "poster-social": "social", "poster-square": "square",
    "poster-story": "story", "poster-cute": "cute", "poster-term": "term",
    "poster-photo": "photo", "poster-wide": "wide", "poster-banner": "banner",
}


def match(scene):
    low = scene.lower()
    scored = []
    for tpl, desc, kws, styles in RULES:
        hit = [k for k in kws if k.lower() in low]
        # 长关键词更具体，权重更高
        score = sum(len(k) for k in hit)
        if hit:
            scored.append((score, tpl, desc, hit, styles))
    scored.sort(key=lambda x: -x[0])

    # 配色线索（按命中关键词长度排序）
    hints = []
    for style, kws in STYLE_HINTS:
        hit = [k for k in kws if k.lower() in low]
        if hit:
            hints.append((sum(len(k) for k in hit), style, hit))
    hints.sort(key=lambda x: -x[0])
    return scored, hints


def term_season(scene):
    """若场景含节气/节日，返回对应季节，用于给节气版选季节配色。"""
    for name, (season, _) in TERM_INFO.items():
        if name in scene:
            return season, name
    for name, season in FESTIVAL_SEASON.items():
        if name in scene:
            return season, name
    return None, None


def main():
    ap = argparse.ArgumentParser(description="场景 → 版式/配色 推荐")
    ap.add_argument("scene", nargs="*", help="场景描述，如「幼儿园家长会」")
    ap.add_argument("--list", action="store_true", help="列出全部规则")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()

    if a.list:
        print("版式规则：")
        for tpl, desc, kws, styles in RULES:
            print(f"  {tpl:<15} {desc}")
            print(f"     关键词：{'、'.join(kws)}")
        print("\n配色线索（命中即前置）：")
        for st, kws in STYLE_HINTS:
            print(f"  {st:<15} {'、'.join(kws)}")
        return 0

    scene = " ".join(a.scene).strip()
    if not scene:
        print("给个场景，例如：python scripts/suggest.py \"幼儿园家长会\"")
        return 2

    scored, hints = match(scene)
    if not scored:
        print(f"场景「{scene}」没命中任何规则。用 --list 看关键词；")
        print("或直接指定：python scripts/suggest.py \"<加上 打印/朋友圈/抖音 等字样>\"")
        return 1

    score, tpl, desc, hit, base_styles = scored[0]
    season, which = term_season(scene)
    if tpl == "poster-term" and season:
        base_styles = SEASON_STYLE[season]

    # 合并配色：线索优先，其次规则默认
    styles = []
    for _, st, _ in hints:
        if st not in styles:
            styles.append(st)
    for st in base_styles:
        if st not in styles:
            styles.append(st)
    styles = styles[:4]

    alt = [s[1] for s in scored[1:3]]
    arg = BUILD_ARG.get(tpl, tpl)

    if a.json:
        print(json.dumps({
            "scene": scene, "template": tpl, "template_desc": desc,
            "matched": hit, "styles": styles,
            "styles_matched": [{"style": s, "keywords": k} for _, s, k in hints],
            "term": which, "season": season, "alternatives": alt,
            "command": f"./build.sh {arg} --style {styles[0] if styles else 'formal-blue'}",
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"场景：{scene}")
    print()
    print(f"▎版式 → {tpl}")
    print(f"  {desc}")
    print(f"  命中关键词：{'、'.join(hit)}")
    if tpl == "poster-term" and which:
        print(f"  识别为「{which}」（{season}季）→ 配色按季节选")
    if alt:
        print(f"  备选版式：{'、'.join(alt)}")
    print()
    if styles:
        print(f"▎配色 → {styles[0]}")
        why = next((k for _, s, k in hints if s == styles[0]), None)
        if why:
            print(f"  命中关键词：{'、'.join(why)}")
        if len(styles) > 1:
            print(f"  备选：{'、'.join(styles[1:])}")
    print()
    print("▎执行")
    print(f"  ./build.sh {arg} --style {styles[0] if styles else 'formal-blue'}")
    print(f"  .\\build.ps1 {arg} -Style {styles[0] if styles else 'formal-blue'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
