// ═══════════════════════════════════════════════════════════════════
//  活动海报 · 朋友圈版（3:4 竖版，手机屏观看）
//  页面 1080×1440 px → 渲染 --ppi 192 → 2160×2880 px
//  手机屏特征：字要大、信息要少、二维码要突出
//  注：Typst 无 px 单位，统一用 lib/tokens.typ 的 px() 转换（1px = 0.75pt）
// ═══════════════════════════════════════════════════════════════════

#import "../lib/data.typ": salon, legal, company
#import "../lib/tokens.typ": *

#set page(width: px(1080), height: px(1440), margin: 0pt, fill: rgb("#FFFFFF"))
#set text(font: ("Noto Sans CJK SC",), lang: "zh", size: px(34), fill: INK)
#set par(leading: 1.7em, spacing: 1em, justify: false)

#let M  = px(72)
#let CW = px(1080) - M * 2

// ── 品牌带（更高，手机屏第一眼）──
#place(top + left, rect(width: px(1080), height: px(200), fill: BRAND))
#place(top + left, dx: M, dy: px(52),
  text(fill: white, size: px(60), weight: "bold")[#salon.org])
#place(top + left, dx: M, dy: px(128),
  text(fill: BRAND2, size: px(30), tracking: 0.25em)[#salon.kicker])

// ── 主标题（字号大，两行）──
#place(top + left, dx: M, dy: px(238), block(width: CW)[
  #set par(leading: 1.34em, spacing: 0pt)
  #text(size: px(76), weight: "bold", fill: BRAND)[#salon.title]
])

// ── 强调线 ──
#place(top + left, dx: M, dy: px(436), rect(width: px(108), height: px(6), fill: BRAND))

// ── 导语（短版）──
#place(top + left, dx: M, dy: px(472), block(width: CW - px(20))[
  #set text(size: px(33), fill: MUTED)
  #set par(leading: 1.75em)
  #salon.lead_short
])

// ── 亮点 ──
#place(top + left, dx: M, dy: px(606), block(width: CW)[
  #highlights(salon.highlights, gap: px(10), num_size: px(28), txt_size: px(33))
])

// ── 信息（只留时间地点，手机屏信息要少）──
// 用 info_row 而非手写 grid：这样列宽不够会编译期报错
// （上次手写 grid 用了 px(120)，"活动时间" 被折成 "活动时 / 间"）
#place(top + left, dx: M, dy: px(866), block(width: CW)[
  #set text(size: px(32))
  #info_row("活动时间", salon.date,   label_w: px(172), size: px(32), gap: px(14))
  #info_row("活动地点", salon.venue,  label_w: px(172), size: px(32), gap: px(14))
])

// ── 报名模块（二维码放大，手机屏要易扫）──
#place(top + left, dx: M, dy: px(1006), rect(width: CW, height: px(304), fill: TINT))
#place(top + left, dx: M + px(34), dy: px(1078), block(width: CW - px(300))[
  #set par(leading: 1.7em, spacing: 0.4em)
  #text(fill: BRAND, weight: "bold", size: px(38))[报名通道]
  #v(px(14))
  #text(size: px(31))[#salon.enroll]
])
#place(top + left, dx: px(1080) - M - px(34) - px(200), dy: px(1058), qr_slot(px(200), salon.qr_image))
#place(top + left, dx: px(1080) - M - px(34) - px(200), dy: px(1272), block(width: px(200))[
  #set align(center)
  #text(size: px(24), fill: BRAND)[#salon.qr_note]
])

// ── 页脚 ──
#place(bottom + left, dx: M, dy: px(-40), block(width: CW)[
  #set text(size: px(23), fill: MUTED)
  #set par(leading: 1.5em, spacing: 0.4em)
  #legal　|　#company
])
