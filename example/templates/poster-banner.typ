// ═══════════════════════════════════════════════════════════════════
//  活动海报 · 易拉宝版（80×200cm 竖幅，远距 3–5m 观看）
//  远距设计要求：字号极大、长句砍短、中段不留大片空白
//  安全区：最底部约 30cm 常被展架/卷边遮挡 —— 关键信息一律不放那里
//  ⚠️ 大幅面 100dpi 足够（3150×7874px），或直接出 PDF 矢量
// ═══════════════════════════════════════════════════════════════════

#import "../lib/data.typ": salon, legal, company
#import "../lib/tokens.typ": *

#set page(width: 800mm, height: 2000mm, margin: 0pt, fill: rgb("#FFFFFF"))
#set text(font: ("Noto Sans CJK SC",), lang: "zh", size: 52pt, fill: INK)
#set par(leading: 1.6em, spacing: 1em, justify: false)

#let M  = 80mm
#let CW = 800mm - M * 2

// ── 品牌带 ──
#place(top + left, rect(width: 800mm, height: 320mm, fill: BRAND))
#place(top + left, dx: M, dy: 100mm,
  text(fill: white, size: 96pt, weight: "bold")[#salon.org])
#place(top + left, dx: M, dy: 222mm,
  text(fill: BRAND2, size: 48pt, tracking: 0.25em)[#salon.kicker])

// ── 主标题（超大，3–5m 外的主视觉）──
#place(top + left, dx: M, dy: 400mm, block(width: CW)[
  #set par(leading: 1.28em, spacing: 0pt)
  #text(size: 150pt, weight: "bold", fill: BRAND)[#salon.title]
])

// ── 强调线 ──
#place(top + left, dx: M, dy: 610mm, rect(width: 200mm, height: 10mm, fill: BRAND))

// ── 导语（远距 → 精简一版）──
#place(top + left, dx: M, dy: 680mm, block(width: CW - 40mm)[
  #set text(size: 56pt, fill: MUTED)
  #set par(leading: 1.7em)
  #salon.lead_short
])

// ── 亮点（label_w 60mm 才不会把 "01" 裁成 "0"）──
#place(top + left, dx: M, dy: 850mm, block(width: CW)[
  #set text(size: 48pt)
  #text(fill: MUTED, tracking: 0.2em)[活动亮点]
  #v(34mm)
  #highlights(salon.highlights, gap: 30mm, num_size: 56pt, txt_size: 66pt, label_w: 68mm)
])

// ── 活动信息（远距核心决策信息，字号加大）──
#place(top + left, dx: M, dy: 1210mm, block(width: CW)[
  #info_row("主讲嘉宾", [#salon.speaker（#salon.speaker2）],
            label_w: 190mm, size: 64pt, gap: 22mm)
  #info_row("活动时间", salon.date, label_w: 190mm, size: 64pt, gap: 22mm)
  #info_row("活动地点", salon.venue, label_w: 190mm, size: 64pt, gap: 22mm)
  #info_row("参会席位", salon.seats, label_w: 190mm, size: 64pt, gap: 22mm)
])

// ── 报名：二维码放大到 300mm ──
#place(top + left, dx: M, dy: 1450mm, rect(width: CW, height: 340mm, fill: TINT))
#place(top + left, dx: M + 44mm, dy: 1536mm, block(width: CW - 400mm)[
  #set par(leading: 1.65em, spacing: 0.4em)
  #text(fill: BRAND, weight: "bold", size: 68pt)[报名通道]
  #v(24mm)
  #text(size: 52pt)[#salon.enroll]
])
#place(top + left, dx: 800mm - M - 44mm - 300mm, dy: 1462mm, qr_slot(300mm, salon.qr_image))
#place(top + left, dx: 800mm - M - 44mm - 300mm, dy: 1780mm, block(width: 300mm)[
  #set align(center)
  #text(size: 38pt, fill: BRAND)[#salon.qr_note]
])

// ── 合规声明（上方留足安全区，不放最底部）──
#place(top + left, dx: M, dy: 1840mm, block(width: CW)[
  #set text(size: 32pt, fill: MUTED)
  #set par(leading: 1.5em, spacing: 0.4em)
  #legal　|　#company
])
