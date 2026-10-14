// ═══════════════════════════════════════════════════════════════════
//  活动海报 · 可爱版（3:4，1080×1440）—— 幼儿园 / 亲子 / 儿童生日 / 兴趣班
//  渲染：typst compile --root . --input style=candy-pink --format png --ppi 192 \
//          templates/poster-cute.typ out/poster-cute.png
//
//  方向：圆角卡片 + 贴纸圆点 + 高饱和大色块 + 圆体（YouYuan 幼圆）。
//  与 formal 方向共用同一套 data.typ / 组件，只换「语法」不换「内容」。
// ═══════════════════════════════════════════════════════════════════

#import "../lib/data.typ": salon, legal, company
#import "../lib/tokens.typ": *

#set page(width: px(1080), height: px(1440), margin: 0pt, fill: rgb("#FFFFFF"))
#set text(font: FONTS_CUTE, lang: "zh", size: px(30), fill: INK)
#set par(leading: 1.6em, spacing: 1em, justify: false)

#let M  = px(64)
#let CW = px(1080) - M * 2

// ── 背景装饰圆（超出页面被裁掉，营造柔和色块）──
#place(top + left, dx: px(-120), dy: px(-130),
  circle(radius: px(210), fill: BRAND2.transparentize(40%)))
#place(top + left, dx: px(880), dy: px(180),
  circle(radius: px(120), fill: BRAND2.transparentize(55%)))

// ── 主卡：活动类型 + 标题 + 机构 ──
#place(top + left, dx: M, dy: px(112), block(
  width: CW, radius: px(44), fill: TINT, inset: px(40),
  above: px(0),
)[
  #text(fill: BRAND, weight: "bold", size: px(28), tracking: 0.15em)[#salon.kicker]
  #v(px(16))
  #set par(leading: 1.2em, spacing: 0pt)
  #text(size: px(64), weight: "bold", fill: BRAND)[#salon.title]
  #v(px(18))
  #set par(leading: 1.5em)
  #text(size: px(28), fill: MUTED)[#salon.org]
])

// ── 亮点：圆角小卡 + 序号圆牌 ──
#place(top + left, dx: M, dy: px(486), block(width: CW)[
  #for (i, h) in salon.highlights.enumerate() {
    block(width: 100%, radius: px(26), fill: TINT, inset: (x: px(22), y: px(16)), above: px(16))[
      #grid(columns: (px(52), 1fr), gutter: px(16), align: horizon,
        badge(i + 1),
        text(size: px(30), fill: INK)[#h],
      )
    ]
  }
])

// ── 时间 / 地点：两张圆角卡并排 ──
#let cardinfo(label, val, above: px(0)) = block(
  width: 100%, radius: px(26), fill: TINT, inset: (x: px(26), y: px(18)), above: above,
  grid(columns: (px(96), 1fr), gutter: px(14), align: horizon,
    text(size: px(26), fill: BRAND, weight: "bold")[#label],
    text(size: px(28), fill: INK)[#val],
  ))

#place(top + left, dx: M, dy: px(790), block(width: CW)[
  #cardinfo("时间", salon.date, above: px(0))
  #cardinfo("地点", salon.venue, above: px(14))
])

// ── 报名：圆角大卡 + 二维码 ──
#place(top + left, dx: M, dy: px(1000), block(
  width: CW, radius: px(40), fill: TINT, inset: px(32),
)[
  #grid(columns: (1fr, auto), gutter: px(24), align: horizon,
    [
      #set par(leading: 1.6em, spacing: 0.4em)
      #text(fill: BRAND, weight: "bold", size: px(36))[报名通道]
      #v(px(10))
      #text(size: px(28))[#salon.enroll]
    ],
    qr_slot(px(200), salon.qr_image),
  )
])

// ── 贴纸点分隔 + 页脚 ──
#place(bottom + left, dx: M, dy: px(-70), block(width: CW)[
  #grid(columns: (auto, auto, auto, 1fr), gutter: px(10), align: horizon,
    dot(), dot(fill: BRAND), dot(),
    text(size: px(20), fill: MUTED)[#legal　|　#company],
  )
])
