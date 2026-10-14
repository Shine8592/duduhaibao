// ═══════════════════════════════════════════════════════════════════
//  活动海报 · 横版头图（16:9，文章头图 / 公众号横版 / 视频封面）
//  页面 1920×1080 px → 渲染 --ppi 96 → 1920×1080 px
//  横版特征：左文右码，标题压在左列，报名二维码作为右侧独立模块
//  注：Typst 无 px 单位，统一用 lib/tokens.typ 的 px() 转换（1px = 0.75pt）
// ═══════════════════════════════════════════════════════════════════

#import "../lib/data.typ": salon, legal, company
#import "../lib/tokens.typ": *

#set page(width: px(1920), height: px(1080), margin: 0pt, fill: rgb("#FFFFFF"))
#set text(font: FONTS, lang: "zh", size: px(30), fill: INK)
#set par(leading: 1.7em, spacing: 1em, justify: false)

#let M    = px(96)
#let LW   = px(1040)                 // 左列（标题/导语/亮点）宽度
#let RX   = px(1176)                 // 右列（报名模块）起点
#let RW   = px(1920) - M - RX        // 右列宽度 = 648

// ── 品牌带（通栏）──
#place(top + left, rect(width: px(1920), height: px(160), fill: BRAND))
#place(top + left, dx: M, dy: px(42),
  text(fill: white, size: px(46), weight: "bold")[#salon.org])
#place(top + left, dx: M, dy: px(104),
  text(fill: BRAND2, size: px(24), tracking: 0.25em)[#salon.kicker])

// ── 左列：主标题 ──
#place(top + left, dx: M, dy: px(210), block(width: LW)[
  #set par(leading: 1.3em, spacing: 0pt)
  #text(size: px(66), weight: "bold", fill: BRAND)[#salon.title]
])

// ── 强调线 ──
#place(top + left, dx: M, dy: px(400), rect(width: px(96), height: px(6), fill: BRAND))

// ── 左列：导语（短版）──
#place(top + left, dx: M, dy: px(432), block(width: LW - px(20))[
  #set text(size: px(30), fill: MUTED)
  #set par(leading: 1.7em)
  #salon.lead_short
])

// ── 左列：亮点 ──
// 用 highlights 而非手写 grid：列宽不够会编译期报错
#place(top + left, dx: M, dy: px(576), block(width: LW)[
  #highlights(salon.highlights, gap: px(10), num_size: px(24), txt_size: px(27))
])

// ── 左列：时间 / 地点 ──
#place(top + left, dx: M, dy: px(742), block(width: LW)[
  #set text(size: px(28))
  #info_row("活动时间", salon.date,  label_w: px(160), size: px(28), gap: px(12))
  #info_row("活动地点", salon.venue, label_w: px(160), size: px(28), gap: px(12))
])

// ── 右列：报名模块 ──
#place(top + left, dx: RX, dy: px(210), rect(width: RW, height: px(540), fill: TINT))
#place(top + left, dx: RX + px(40), dy: px(252), block(width: RW - px(80))[
  #set par(leading: 1.7em, spacing: 0.4em)
  #text(fill: BRAND, weight: "bold", size: px(34))[报名通道]
  #v(px(12))
  #text(size: px(28))[#salon.enroll]
])
#place(top + left, dx: px(1920) - M - px(40) - px(210), dy: px(470), qr_slot(px(210), salon.qr_image))
#place(top + left, dx: px(1920) - M - px(40) - px(210), dy: px(694), block(width: px(210))[
  #set align(center)
  #text(size: px(19), fill: BRAND)[#salon.qr_note]
])

// ── 页脚合规声明（底部留安全区）──
#place(bottom + left, dx: M, dy: px(-40), block(width: px(1920) - M * 2)[
  #set text(size: px(20), fill: MUTED)
  #set par(leading: 1.5em, spacing: 0.4em)
  #legal　|　#company
])
