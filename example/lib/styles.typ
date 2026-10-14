// ═══════════════════════════════════════════════════════════════════
//  命名配色方案库（风格预设）· 18 套
//
//  动机：竞品（乔木 Mondo 1271★ / 大羽海报 / html-anything）都有「风格库 + 按需选」。
//  我们不堆艺术家风格（那是提示词生图的路子），而是给**确定性渲染**提供一组经过
//  WCAG 对比度校准的配色主题：换一个名字，全篇同步换色。
//
//  用法（不改模板）：
//      typst compile --input style=vivid-orange ...
//    build 脚本： ./build.sh --style vivid-orange   /   .\build.ps1 -Style vivid-orange
//    列出全部：   python scripts/preflight.py --list-styles
//
//  ⚠️ 每套都经 preflight 的「对比度闸门」校验：正文/小字 ≥ 4.5、大字 ≥ 3.0、
//     白字于品牌带 ≥ 4.5。改色后务必重跑 preflight。
// ═══════════════════════════════════════════════════════════════════

#let DEFAULT_STYLE = "formal-blue"

#let PALETTES = (
  "formal-blue": (
    label: "商务蓝", use: "企业发布会 / 公开课 / 正式活动",
    brand: rgb("#1B4F8C"), brand2: rgb("#A8CBEA"), tint: rgb("#F4F8FC"),
    ink: rgb("#2B2B2B"), muted: rgb("#687685"), rule: rgb("#DCE3EA"),
  ),
  "ink-green": (
    label: "墨绿", use: "学术讲座 / 文化沙龙 / 自然环保",
    brand: rgb("#1F5C4A"), brand2: rgb("#A9D6C6"), tint: rgb("#F1F7F4"),
    ink: rgb("#23282B"), muted: rgb("#68786F"), rule: rgb("#D6E4DE"),
  ),
  "royal-purple": (
    label: "雅紫", use: "品牌发布 / 设计 / 女性向活动",
    brand: rgb("#4B3B8F"), brand2: rgb("#C6BEE8"), tint: rgb("#F5F3FB"),
    ink: rgb("#2A2833"), muted: rgb("#76708B"), rule: rgb("#E0DCEF"),
  ),
  "vivid-orange": (
    label: "活力橙", use: "社群 / 亲子 / 市集 / 招生活动",
    brand: rgb("#C2410C"), brand2: rgb("#FBD3B4"), tint: rgb("#FFF6EF"),
    ink: rgb("#2C2420"), muted: rgb("#867061"), rule: rgb("#F0DFD2"),
  ),
  "crimson": (
    label: "中国红", use: "节庆 / 年会 / 典礼 / 内购",
    brand: rgb("#9E1B1B"), brand2: rgb("#E8B4B4"), tint: rgb("#FCF3F2"),
    ink: rgb("#2A2020"), muted: rgb("#8B6E6E"), rule: rgb("#EFD9D7"),
  ),
  "mono-slate": (
    label: "极简墨", use: "极简 / 数据报告 / 内部分享",
    brand: rgb("#334155"), brand2: rgb("#CBD5E1"), tint: rgb("#F5F7FA"),
    ink: rgb("#1E293B"), muted: rgb("#5E6B7C"), rule: rgb("#E2E8F0"),
  ),
  "navy-gold": (
    label: "藏青金", use: "峰会 / 颁奖 / 高端活动",
    brand: rgb("#1F3A5F"), brand2: rgb("#D9B34A"), tint: rgb("#F5F7FA"),
    ink: rgb("#2A2F36"), muted: rgb("#65717C"), rule: rgb("#DDE3EA"),
  ),
  "teal": (
    label: "青碧", use: "健康 / 环保 / 生活方式",
    brand: rgb("#0F6E6E"), brand2: rgb("#A7D9D9"), tint: rgb("#F0F8F8"),
    ink: rgb("#1F2A2A"), muted: rgb("#5F7A7A"), rule: rgb("#D5E7E7"),
  ),
  "sakura": (
    label: "樱粉", use: "女性向 / 亲子 / 节日赠礼",
    brand: rgb("#B03A5B"), brand2: rgb("#F3C3CE"), tint: rgb("#FDF2F4"),
    ink: rgb("#2E2226"), muted: rgb("#7E6670"), rule: rgb("#F0D8DE"),
  ),
  "lavender": (
    label: "薰衣草", use: "文艺 / 疗愈 / 心理成长",
    brand: rgb("#6A4C93"), brand2: rgb("#D5C6E8"), tint: rgb("#F7F3FB"),
    ink: rgb("#2A2733"), muted: rgb("#74688A"), rule: rgb("#E4DBF0"),
  ),
  "mist-blue": (
    label: "雾霾蓝", use: "简约 / 设计 / 摄影展",
    brand: rgb("#3E5C76"), brand2: rgb("#C3D2DF"), tint: rgb("#F4F7FA"),
    ink: rgb("#26313B"), muted: rgb("#64737F"), rule: rgb("#DCE5ED"),
  ),
  "warm-sand": (
    label: "暖沙", use: "手作 / 咖啡 / 市集",
    brand: rgb("#8C6239"), brand2: rgb("#E7CFB3"), tint: rgb("#FBF6EF"),
    ink: rgb("#2B241D"), muted: rgb("#7C6A57"), rule: rgb("#EFE0CE"),
  ),
  "tech-cyan": (
    label: "科技青", use: "科技 / 产品发布 / 数据",
    brand: rgb("#0E7490"), brand2: rgb("#A5E3F0"), tint: rgb("#EFF9FC"),
    ink: rgb("#1E2A2E"), muted: rgb("#5C7883"), rule: rgb("#D3E9F0"),
  ),
  "deep-space": (
    label: "深空", use: "科技 / 游戏 / 未来主题",
    brand: rgb("#1E2A78"), brand2: rgb("#B9C2F0"), tint: rgb("#F2F3FC"),
    ink: rgb("#20222E"), muted: rgb("#6E7291"), rule: rgb("#DCDEEF"),
  ),
  "festival-gold": (
    label: "鎏金", use: "年会 / 庆典 / 答谢",
    brand: rgb("#8A6A1F"), brand2: rgb("#EBD79A"), tint: rgb("#FBF7EA"),
    ink: rgb("#2C2718"), muted: rgb("#7E7048"), rule: rgb("#EEE1BE"),
  ),
  "graphite": (
    label: "石墨", use: "工业 / 极简 / 建筑",
    brand: rgb("#37474F"), brand2: rgb("#CFD8DC"), tint: rgb("#F5F7F8"),
    ink: rgb("#212A2E"), muted: rgb("#62737C"), rule: rgb("#DEE5E8"),
  ),
  "plum": (
    label: "梅子", use: "东方 / 文化 / 艺术展",
    brand: rgb("#7B2E59"), brand2: rgb("#E3B7CE"), tint: rgb("#FBF3F7"),
    ink: rgb("#2B2026"), muted: rgb("#7C6470"), rule: rgb("#EFDCE6"),
  ),
  "forest": (
    label: "森林", use: "自然 / 户外 / 可持续",
    brand: rgb("#2E5E3A"), brand2: rgb("#B7D9BF"), tint: rgb("#F2F8F3"),
    ink: rgb("#1F2A22"), muted: rgb("#607B67"), rule: rgb("#D8E8DC"),
  ),
)

// 取一个方案；名字不存在时回退到默认（并由 preflight 的样式闸门报错拦住）
#let palette(name) = PALETTES.at(name, default: PALETTES.at(DEFAULT_STYLE))
