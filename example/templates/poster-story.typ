// ═══════════════════════════════════════════════════════════════════
//  活动海报 · 竖屏 Story（9:16，抖音 / 视频号 / 快手 / IG Story）
//  页面 1080×1920 px → 渲染 --ppi 96 → 1080×1920 px
//
//  ⚠️ 竖屏平台顶部 ~10%、底部 ~15% 会被 UI 遮挡（标题栏/按钮）。
//     本模板把内容限制在安全区内；preflight 的 FORMATS 里 poster-story 的
//     底部净空设为 288px（=1920×15%），任何落进底部遮挡区的内容都会被闸门拦下。
//  注：Typst 无 px 单位，统一用 lib/tokens.typ 的 px() 转换（1px = 0.75pt）
// ═══════════════════════════════════════════════════════════════════

#import "../lib/data.typ": salon, legal, company
#import "../lib/tokens.typ": *

#set page(width: px(1080), height: px(1920), margin: 0pt, fill: rgb("#FFFFFF"))
#set text(font: FONTS, lang: "zh", size: px(32), fill: INK)
#set par(leading: 1.7em, spacing: 1em, justify: false)

#let M  = px(72)
#let CW = px(1080) - M * 2

// ── 品牌带（通栏；文字压到顶部遮挡区之下）──
#place(top + left, rect(width: px(1080), height: px(300), fill: BRAND))
#place(top + left, dx: M, dy: px(150),
  text(fill: white, size: px(56), weight: "bold")[#salon.org])
#place(top + left, dx: M, dy: px(226),
  text(fill: BRAND2, size: px(26), tracking: 0.25em)[#salon.kicker])

// ── 标题 + 强调线 + 导语（同一个块内流式排布，见 social 注释）──
#place(top + left, dx: M, dy: px(400), block(width: CW)[
  #set par(leading: 1.34em, spacing: 0pt)
  #text(size: px(76), weight: "bold", fill: BRAND)[#salon.title]
  #v(min_gap(SP.md))
  #block(width: px(108), height: px(6), fill: BRAND)
  #v(min_gap(SP.lg))
  #set par(leading: 1.7em)
  #text(size: px(32), fill: MUTED)[#salon.lead_short]
])

// ── 亮点（独立块：行距用页面级设定）──
#place(top + left, dx: M, dy: px(850), block(width: CW)[
  #highlights(salon.highlights, gap: px(12), num_size: px(28), txt_size: px(33))
])

// ── 信息 ──
#place(top + left, dx: M, dy: px(1090), block(width: CW)[
  #set text(size: px(32))
  #info_row("活动时间", salon.date,  label_w: px(172), size: px(32), gap: px(14))
  #info_row("活动地点", salon.venue, label_w: px(172), size: px(32), gap: px(14))
])

// ── 报名模块（竖屏二维码放大，便于扫码）──
#place(top + left, dx: M, dy: px(1256), rect(width: CW, height: px(296), fill: TINT))
#place(top + left, dx: M + px(32), dy: px(1298), block(width: CW - px(280))[
  #set par(leading: 1.7em, spacing: 0.4em)
  #text(fill: BRAND, weight: "bold", size: px(36))[报名通道]
  #v(px(14))
  #text(size: px(28))[#salon.enroll]
])
#place(top + left, dx: px(1080) - M - px(32) - px(200), dy: px(1294), qr_slot(px(200), salon.qr_image))
#place(top + left, dx: px(1080) - M - px(32) - px(200), dy: px(1502), block(width: px(200))[
  #set align(center)
  #text(size: px(19), fill: BRAND)[#salon.qr_note]
])

// ── 页脚（抬高到平台底部遮挡区之上：距下沿 288px 安全线内）──
#place(bottom + left, dx: M, dy: px(-320), block(width: CW)[
  #set text(size: px(20), fill: MUTED)
  #set par(leading: 1.5em, spacing: 0.4em)
  #legal　|　#company
])
