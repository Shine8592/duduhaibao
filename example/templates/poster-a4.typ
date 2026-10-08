// ═══════════════════════════════════════════════════════════════════
//  活动海报 · A4 打印版
//  数据在 lib/data.typ，样式在 lib/tokens.typ —— 本文件只管版式
//  渲染：typst compile --format png --ppi 300 templates/poster-a4.typ out/a4.png
//  产出：2480×3508 px = 210×297 mm @300dpi，页边距 18mm，方角无阴影
// ═══════════════════════════════════════════════════════════════════

#import "../lib/data.typ": salon, legal, company
#import "../lib/tokens.typ": *

#set page(width: 210mm, height: 297mm, margin: 0pt, fill: rgb("#FFFFFF"))
#set text(font: ("Noto Sans CJK SC",), lang: "zh", size: 10pt, fill: INK)
#set par(leading: 1.85em, spacing: 1.2em, justify: false)

#let M  = 18mm
#let CW = 210mm - M * 2

// ── 品牌带 ──
#brand_band(210mm, 44mm, salon.org, salon.kicker)

// ── 主标题 ──
#place(top + left, dx: M, dy: 56mm, block(width: CW)[
  #set par(leading: 1.36em, spacing: 0pt)
  #text(size: 24pt, weight: "bold", fill: BRAND)[#salon.title]
])

// ── 强调线 ──
#place(top + left, dx: M, dy: 91mm, rect(width: 34mm, height: 1.6mm, fill: BRAND))

// ── 导语 ──
#place(top + left, dx: M, dy: 99mm, block(width: CW - 8mm)[
  #set text(size: 10.5pt)
  #set par(leading: 1.9em)
  #salon.lead
])

// ── 活动亮点 ──
#place(top + left, dx: M, dy: 122mm, block(width: CW)[
  #text(size: 9pt, fill: MUTED, tracking: 0.2em)[活动亮点]
  #v(4mm)
  #highlights(salon.highlights)
])

// ── 活动信息 ──
#place(top + left, dx: M, dy: 172mm, block(width: CW)[
  #info_row("主讲嘉宾", [#salon.speaker（#salon.speaker2）])
  #info_row("活动时间", salon.date)
  #info_row("活动地点", salon.venue)
  #info_row("参会席位", salon.seats)
])

// ── 报名通道（整体成模块）──
#place(top + left, dx: M, dy: 226mm, rect(width: CW, height: 36mm, fill: TINT))
#place(top + left, dx: M + 8mm, dy: 235mm, block(width: CW - 52mm)[
  #set text(size: 10.5pt)
  #set par(leading: 1.75em, spacing: 0.4em)
  #text(fill: BRAND, weight: "bold", size: 11pt)[报名通道]
  #v(2mm)
  #salon.enroll
])
#place(top + left, dx: 210mm - M - 8mm - 26mm, dy: 230mm, qr_slot(26mm, salon.qr_image))
#place(top + left, dx: 210mm - M - 8mm - 26mm, dy: 257.5mm, block(width: 24mm)[
  #set align(center)
  #text(size: 8pt, fill: BRAND)[#salon.qr_note]
])

// ── 页脚合规声明 ──
#place(bottom + left, dx: M, dy: -17mm, block(width: CW)[
  #set text(size: 7.5pt, fill: MUTED)
  #set par(leading: 1.6em, spacing: 0.45em)
  #legal　|　#company
])
