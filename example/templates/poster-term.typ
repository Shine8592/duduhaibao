// ═══════════════════════════════════════════════════════════════════
//  节气 / 节日海报（1:1，1080×1080）
//  渲染：typst compile --root . --input style=mint --input term=立冬 --format png --ppi 96 \
//          templates/poster-term.typ out/poster-term.png
//
//  日期来自 lib/terms.typ（由 scripts/solar_terms.py 确定性计算），**不问模型**。
//  不传 --input term 时，自动取「下一个未到的节气」。
//  换季配色：--input style=<mint/pale…>；不传时用当前风格。
// ═══════════════════════════════════════════════════════════════════

#import "../lib/data.typ": salon, legal, company
#import "../lib/tokens.typ": *
#import "../lib/terms.typ": TERMS, TERM_INFO
#import "../lib/term.typ": ACTIVE_TERM

// ── 选节气：默认读 lib/term.typ（改那个文件即可）；可用 --input year=<数字> 覆盖年份 ──
//  ⚠️ 不要用 --input term=中文 传节气名 —— Windows 控制台编码会弄坏它。
#let YEAR = int(sys.inputs.at("year", default: str(ACTIVE_TERM.year)))
#let _all = TERMS.filter(t => t.year == YEAR)
#let HIT = if _all.len() == 0 {
    panic("terms.typ 里没有 " + str(YEAR) + " 年的数据。先跑：python scripts/solar_terms.py --year " + str(YEAR) + " --emit")
  } else {
    // ⚠️ 不能写成 .at(0, default: panic(...))：default 会被【急切求值】，
    //    于是 panic 无条件执行、永远报错。必须先判空再取。
    let hit = _all.filter(t => t.name == ACTIVE_TERM.name)
    if hit.len() == 0 {
      panic("该年没有节气「" + ACTIVE_TERM.name + "」（见 lib/term.typ）")
    }
    hit.first()
  }
#let INFO = TERM_INFO.at(HIT.name)

#set page(width: px(1080), height: px(1080), margin: 0pt, fill: TINT)
#set text(font: FONTS_CUTE, lang: "zh", size: px(30), fill: INK)
#set par(leading: 1.6em, spacing: 1em, justify: false)

#let M = px(80)

// ── 背景装饰圆 ──
#place(top + left, dx: px(740), dy: px(-150),
  circle(radius: px(320), fill: BRAND2.transparentize(45%)))
#place(top + left, dx: px(-70), dy: px(690),
  circle(radius: px(150), fill: BRAND2.transparentize(60%)))

// ── 季节 + 节气名 ──
#place(top + left, dx: M, dy: px(120), block(
  radius: px(22), fill: BRAND, inset: (x: px(24), y: px(10)),
)[#text(fill: white, weight: "bold", size: px(28))[#INFO.season　季]])

#place(top + left, dx: M, dy: px(196), block(width: px(760))[
  #set par(leading: 1.0em, spacing: 0pt)
  #text(size: px(150), weight: "bold", fill: BRAND)[#HIT.name]
])

// ── 日期（来自确定性计算）──
#place(top + left, dx: M, dy: px(400), block(width: px(760))[
  #text(size: px(44), weight: "bold", fill: INK)[#HIT.year 年 #HIT.m 月 #HIT.d 日]
])

// ── 一句释义 ──
#place(top + left, dx: M, dy: px(480), block(width: px(720))[
  #text(size: px(32), fill: MUTED)[#INFO.note]
])

// ── 机构（活动方）──
#place(top + left, dx: M, dy: px(600), block(width: px(720))[
  #text(size: px(30), weight: "bold", fill: BRAND)[#salon.org]
  #v(px(10))
  #text(size: px(26), fill: MUTED)[#salon.kicker]
])

// ── 贴纸点 + 页脚 ──
#place(bottom + left, dx: M, dy: px(-80), block(width: px(920))[
  #grid(columns: (auto, auto, auto, 1fr), gutter: px(10), align: horizon,
    dot(), dot(fill: BRAND), dot(),
    text(size: px(20), fill: MUTED)[#legal　|　#company],
  )
])
