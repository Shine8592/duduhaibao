// ═══════════════════════════════════════════════════════════════
//  设计 token + 共用组件（正式版规格：方角、无阴影、单一品牌色）
// ═══════════════════════════════════════════════════════════════

// ── 颜色 ──────────────────────────────────────────────────────
#let BRAND  = rgb("#1B4F8C")   // 主品牌色（换银行/换活动只改这一行）
#let BRAND2 = rgb("#A8CBEA")   // 品牌浅色
#let TINT   = rgb("#F4F8FC")   // 极浅品牌底
#let INK    = rgb("#2B2B2B")   // 正文
#let MUTED  = rgb("#6E7C8C")   // 次要文字（对比度够小字阅读）
#let RULE   = rgb("#DCE3EA")   // 细线

// ── 二维码：有图用图，无图用占位框 ────────────────────────────
// 这样"补二维码"始终是改一行数据（data.typ 的 qr_image），不是改版式
//
// ⚠️ 路径坑：Typst 的相对路径是相对于「调用所在的 .typ 文件」，
// 不是项目根 —— 在本文件里写 image("qr.png") 会去找 lib/qr.png。
// 所以这里统一转成根相对路径（"--root ." 下的 "/qr.png"），
// 数据里就永远按「放在项目根」写，且与 preflight.py 的检查口径一致。
#let qr_slot(s, img) = if img == none {
  rect(width: s, height: s, stroke: 0.6pt + BRAND)
} else {
  let p = if img.starts-with("/") { img } else { "/" + img }
  image(p, width: s, height: s)
}

// ── px 转换：Typst 没有 px 单位，1 CSS px = 0.75pt ──────────────
// 这样设计稿上的 px 数字可以原样搬过来：px(1080) 就是 1080 CSS px
#let px(v) = v * 0.75pt

// ── 字号 ──────────────────────────────────────────────────────
// 不设全局 scale：Typst 的闭包捕获定义处作用域，模块级变量改了也不会影响
// 已导入的函数。各格式直接写字号更清楚，也避免这类隐性 bug。
#let fs(base, s) = base * s * 1pt

// ── 编号（01/02/03）──────────────────────────────────────────
#let num2(n) = if n < 10 { "0" + str(n) } else { str(n) }

// ── 文本宽度估算（用于断言：列宽够不够）───────────────────────
// Typst 布局时会静默让内容溢出网格单元，不做任何提示 —— 所以只能自己估。
// CJK 按 1.0 em、西文/数字按 0.55 em 估。这是护栏不是精密测量：
// 宁可略微高估（早报错），也不要低估（放过真问题）。
#let est_width(s, size) = {
  let cl = s.clusters()
  let cjk = cl.filter(c => c.to-unicode() > 0x2E80).len()
  let other = cl.len() - cjk
  (cjk * 1.0 + other * 0.55) * size
}

// 断言失败时的统一提示格式
#let _fail(where, need, have, symptom) = panic(
  "❌ " + where + " 空间不够：需要约 " + need + "，只有 " + have
  + "\n   症状：" + symptom + "\n   修法：加大该组件的 label_w / 缩小字号 / 缩短文案"
)

// ── 亮点列表（序号 + 文案）────────────────────────────────────
// label_w 必须随 num_size 放大：小格式 9mm 够，易拉宝大号数字要 68mm，
// 否则 "01" 会溢出到正文列 —— 渲染不报错，只在成品上看起来像 "0"。
// 这个 bug 真实发生过，所以这里加断言把它变成编译期报错。
#let highlights(items, gap: 2.4mm, num_size: 9pt, txt_size: 10.5pt, label_w: 9mm) = {
  let widest = if items.len() == 0 { "01" } else { num2(items.len()) }
  let need = est_width(widest, num_size)
  if need > label_w {
    _fail("highlights", repr(need), repr(label_w),
          "序号 \"" + widest + "\" 被裁成 \"" + widest.first() + "\"，看着像少了位数字")
  }
  for (i, h) in items.enumerate() {
    grid(
      columns: (label_w, 1fr),
      gutter: 1mm,
      text(fill: BRAND, size: num_size, weight: "bold")[#num2(i + 1)],
      text(size: txt_size)[#h],
    )
    v(gap)
  }
}

// ── 信息行（固定宽度标签列，保证左列严格对齐）───────────────────
// 标签列放不下就会折行（"活动时间" → "活动时 / 间"），比裁字更难看。
#let info_row(k, val, label_w: 24mm, size: 10.5pt, gap: 3.2mm) = {
  let need = est_width(k, size)
  if need > label_w {
    _fail("info_row 的标签列", repr(need), repr(label_w),
          "\"" + k + "\" 会折行 / 被裁；窄屏上尤其明显")
  }
  grid(
    columns: (label_w, 1fr),
    gutter: 5mm,
    text(fill: MUTED, size: size)[#k],
    text(fill: INK, weight: "medium", size: size)[#val],
  )
  v(gap)
}

// ── 品牌带 ────────────────────────────────────────────────────
#let brand_band(w, h, org, kicker, dx: 18mm, dy1: 12mm, dy2: 24mm,
                org_size: 21pt, kicker_size: 10pt, accent: true) = {
  place(top + left, rect(width: w, height: h, fill: BRAND))
  place(top + left, dx: dx, dy: dy1,
    text(fill: white, size: org_size, weight: "bold")[#org])
  place(top + left, dx: dx, dy: dy2,
    text(fill: BRAND2, size: kicker_size, tracking: 0.25em)[#kicker])
  if accent {
    place(top + left, dx: w - dx - 0.5mm, dy: dy1,
      rect(width: 0.5mm, height: h - dy1 - 10mm, fill: BRAND2))
  }
}
