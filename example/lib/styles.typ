// ═══════════════════════════════════════════════════════════════════
//  命名配色方案库（风格预设）
//
//  动机：竞品（乔木 Mondo 1271★ / 大羽海报）都有「一套风格库 + 按需选风格」，
//  我们不堆叠 33 个艺术家风格（那是提示词生图的路子），而是给**确定性渲染**
//  提供一组经过对比度校准的**配色主题**：换一个名字，全篇同步换色。
//
//  用法（不改模板）：
//      typst compile --input style=vivid-orange ...
//    build 脚本： ./build.sh --style vivid-orange   /   .\build.ps1 -Style vivid-orange
//    列出全部：  python scripts/preflight.py --list-styles
//
//  每个方案字段：brand（主色）/ brand2（浅点缀）/ tint（极浅底）/ ink（正文）
//  / muted（次要文字）/ rule（细线）。
//  ⚠️ muted 必须保证小字在白底上可读（对比度 ≥ 4.5:1 左右）。
// ═══════════════════════════════════════════════════════════════════

#let DEFAULT_STYLE = "formal-blue"

#let PALETTES = (
  // ── 商务蓝（默认，正式/企业/公开课）───────────────────────────
  "formal-blue": (
    label: "商务蓝", use: "企业发布会 / 公开课 / 正式活动",
    brand: rgb("#1B4F8C"), brand2: rgb("#A8CBEA"), tint: rgb("#F4F8FC"),
    ink: rgb("#2B2B2B"), muted: rgb("#6E7C8C"), rule: rgb("#DCE3EA"),
  ),
  // ── 墨绿（学术 / 文化 / 自然）─────────────────────────────────
  "ink-green": (
    label: "墨绿", use: "学术讲座 / 文化沙龙 / 自然环保",
    brand: rgb("#1F5C4A"), brand2: rgb("#A9D6C6"), tint: rgb("#F1F7F4"),
    ink: rgb("#23282B"), muted: rgb("#68786F"), rule: rgb("#D6E4DE"),
  ),
  // ── 雅紫（品牌 / 女性向 / 设计）───────────────────────────────
  "royal-purple": (
    label: "雅紫", use: "品牌发布 / 设计 / 女性向活动",
    brand: rgb("#4B3B8F"), brand2: rgb("#C6BEE8"), tint: rgb("#F5F3FB"),
    ink: rgb("#2A2833"), muted: rgb("#76708B"), rule: rgb("#E0DCEF"),
  ),
  // ── 活力橙（社群 / 亲子 / 市集）───────────────────────────────
  "vivid-orange": (
    label: "活力橙", use: "社群 / 亲子 / 市集 / 招生活动",
    brand: rgb("#C2410C"), brand2: rgb("#FBD3B4"), tint: rgb("#FFF6EF"),
    ink: rgb("#2C2420"), muted: rgb("#8A7364"), rule: rgb("#F0DFD2"),
  ),
  // ── 中国红（节庆 / 年会 / 开业内购）───────────────────────────
  "crimson": (
    label: "中国红", use: "节庆 / 年会 / 典礼 / 内购",
    brand: rgb("#9E1B1B"), brand2: rgb("#E8B4B4"), tint: rgb("#FCF3F2"),
    ink: rgb("#2A2020"), muted: rgb("#8C6F6F"), rule: rgb("#EFD9D7"),
  ),
  // ── 极简墨（极简 / 数据 / 报告）───────────────────────────────
  "mono-slate": (
    label: "极简墨", use: "极简 / 数据报告 / 内部分享",
    brand: rgb("#334155"), brand2: rgb("#CBD5E1"), tint: rgb("#F5F7FA"),
    ink: rgb("#1E293B"), muted: rgb("#5E6B7C"), rule: rgb("#E2E8F0"),
  ),
)

// 取一个方案；名字不存在时回退到默认（并由 preflight 的样式闸门报错拦住）
#let palette(name) = PALETTES.at(name, default: PALETTES.at(DEFAULT_STYLE))
