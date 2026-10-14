// ═══════════════════════════════════════════════════════════════════
//  活动海报 · 方形封面版（1:1，公众号首图 / 小红书封面）
//  页面 1080×1080 px → 渲染 --ppi 192 → 2160×2160 px
//  1:1 特征：进信息流常被裁切展示，标题与亮点要压在中心区、信息要少
//  注：Typst 无 px 单位，统一用 lib/tokens.typ 的 px() 转换（1px = 0.75pt）
// ═══════════════════════════════════════════════════════════════════

#import "../lib/data.typ": salon, legal, company
#import "../lib/tokens.typ": *

#set page(width: px(1080), height: px(1080), margin: 0pt, fill: rgb("#FFFFFF"))
#set text(font: FONTS, lang: "zh", size: px(30), fill: INK)
#set par(leading: 1.7em, spacing: 1em, justify: false)

#let M  = px(72)
#let CW = px(1080) - M * 2

// ── 品牌带 ──
#place(top + left, rect(width: px(1080), height: px(170), fill: BRAND))
#place(top + left, dx: M, dy: px(44),
  text(fill: white, size: px(52), weight: "bold")[#salon.org])
#place(top + left, dx: M, dy: px(108),
  text(fill: BRAND2, size: px(26), tracking: 0.25em)[#salon.kicker])

// ── 主标题 + 强调线 + 导语（同一个块内流式排布，见 social 注释）──
#place(top + left, dx: M, dy: px(198), block(width: CW)[
  #set par(leading: 1.32em, spacing: 0pt)
  #text(size: px(64), weight: "bold", fill: BRAND)[#salon.title]
  #v(px(13))
  #block(width: px(96), height: px(6), fill: BRAND)
  #v(px(24))
  #set par(leading: 1.7em)
  #text(size: px(30), fill: MUTED)[#salon.lead_short]
])

// ── 亮点 ──
// 用 highlights 而非手写 grid：列宽不够会编译期报错
#place(top + left, dx: M, dy: px(534), block(width: CW)[
  #highlights(salon.highlights, gap: px(10), num_size: px(24), txt_size: px(30))
])

// ── 信息（只留时间地点，封面信息要少）──
#place(top + left, dx: M, dy: px(690), block(width: CW)[
  #set text(size: px(29))
  #info_row("活动时间", salon.date,  label_w: px(160), size: px(29), gap: px(14))
  #info_row("活动地点", salon.venue, label_w: px(160), size: px(29), gap: px(14))
])

// ── 报名模块 ──
#place(top + left, dx: M, dy: px(806), rect(width: CW, height: px(200), fill: TINT))
#place(top + left, dx: M + px(28), dy: px(840), block(width: CW - px(230))[
  #set par(leading: 1.7em, spacing: 0.4em)
  #text(fill: BRAND, weight: "bold", size: px(34))[报名通道]
  #v(px(12))
  #text(size: px(29))[#salon.enroll]
])
#place(top + left, dx: px(1080) - M - px(28) - px(132), dy: px(840), qr_slot(px(132), salon.qr_image))
#place(top + left, dx: px(1080) - M - px(28) - px(132), dy: px(978), block(width: px(132))[
  #set align(center)
  #text(size: px(18), fill: BRAND)[#salon.qr_note]
])

// ── 页脚合规声明（底部留安全区，距下沿 ≥40px）──
// 底部净空若被内容侵入，preflight 的闸门 2 会报错 —— 这是有意的
#place(bottom + left, dx: M, dy: px(-36), block(width: CW)[
  #set text(size: px(18), fill: MUTED)
  #set par(leading: 1.5em, spacing: 0.4em)
  #legal　|　#company
])
