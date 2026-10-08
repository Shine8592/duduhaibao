// 回归测试：内容被排到页面外，Typst 静默裁掉不报错 —— 后检应通过
// 底部净空区的非白像素抓到它
#import "../lib/data.typ": salon
#import "../lib/tokens.typ": *
#set page(width: 210mm, height: 297mm, margin: 0pt, fill: white)
#set text(font: ("Noto Sans CJK SC",), lang: "zh", size: 10pt)
#place(top + left, rect(width: 210mm, height: 44mm, fill: BRAND))
// 故意放到页面底部边缘 —— 真实场景里就是元素溢出被裁
#place(top + left, dx: 18mm, dy: 295mm, text(size: 12pt, fill: black)[这一行被排到了页面最底部])
