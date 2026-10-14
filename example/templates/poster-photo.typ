// ═══════════════════════════════════════════════════════════════════
//  照片集海报（3:4，1080×1440）—— 朋友圈游玩 / 旅行 / 活动记录
//  渲染：typst compile --root . --format png --ppi 96 templates/poster-photo.typ out/poster-photo.png
//
//  数据在 lib/photos.typ（地点 / 日期 / 一句话 / 照片列表）。
//  照片数量自动适配版式：1 大图 · 2 并排 · 3「1 大 2 小」· 4+ 网格。
//  圆角 + cover 裁切，保证每格比例一致、不拉伸。
// ═══════════════════════════════════════════════════════════════════

#import "../lib/data.typ": legal, company
#import "../lib/tokens.typ": *
#import "../lib/photos.typ": photos

#set page(width: px(1080), height: px(1440), margin: 0pt, fill: rgb("#FFFFFF"))
#set text(font: FONTS, lang: "zh", size: px(30), fill: INK)
#set par(leading: 1.6em, spacing: 1em, justify: false)

#let M  = px(56)
#let CW = px(1080) - M * 2
#let R  = px(28)

// 一格照片：圆角 + 裁切填满（cover），不拉伸
// ⚠️ image 的相对路径是相对「调用所在的 .typ 文件」；"--root ." 下前导斜杠才是项目根相对
#let ph(f, h) = block(radius: R, clip: true, width: 100%, height: h,
  image(if f.starts-with("/") { f } else { "/" + f },
        width: 100%, height: 100%, fit: "cover"))

// ── 顶部：地点 + 日期 ──
#place(top + left, dx: M, dy: px(72), block(width: CW)[
  #grid(columns: (1fr, auto), align: horizon,
    text(size: px(28), weight: "bold", fill: BRAND)[#photos.place],
    text(size: px(24), fill: MUTED)[#photos.date],
  )
])

// ── 照片区（按数量自适应）──
#place(top + left, dx: M, dy: px(146), block(width: CW)[
  #let fs = photos.files
  #let n = fs.len()
  #if n == 0 {
    block(width: 100%, height: px(700), radius: R, fill: TINT,
      align(center + horizon)[#text(fill: MUTED)[在 lib/photos.typ 里填照片路径]])
  } else if n == 1 {
    ph(fs.at(0), px(1012))
  } else if n == 2 {
    grid(columns: (1fr, 1fr), gutter: px(16),
      ph(fs.at(0), px(1000)), ph(fs.at(1), px(1000)))
  } else if n == 3 {
    grid(columns: (1fr, 1fr), rows: (px(640), px(370)), gutter: px(16),
      grid.cell(colspan: 2, ph(fs.at(0), px(640))),
      ph(fs.at(1), px(370)), ph(fs.at(2), px(370)))
  } else {
    grid(columns: (1fr, 1fr), gutter: px(16),
      ..fs.slice(0, 4).map(f => ph(f, px(498))))
  }
])

// ── 一句话 ──
#place(bottom + left, dx: M, dy: px(-150), block(width: CW)[
  #set par(leading: 1.3em, spacing: 0pt)
  #text(size: px(40), weight: "bold", fill: BRAND)[#photos.caption]
])

// ── 页脚 ──
#place(bottom + left, dx: M, dy: px(-66), block(width: CW)[
  #set text(size: px(20), fill: MUTED)
  #legal　|　#company
])
