// 回归测试：历史 bug —— 朋友圈版手写 grid 用了 px(120)，
// "活动时间" 被折成 "活动时 / 间"。断言应当拦住。
#import "../lib/tokens.typ": *
#set page(width: 200mm, height: 80mm)
#info_row("活动时间", "2026年12月5日（周六）14:00", label_w: px(120), size: px(32))
