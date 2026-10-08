// 回归测试：三种格式的真实配置，断言不应误报
#import "../lib/tokens.typ": *
#set page(width: 200mm, height: 200mm)
// A4 配置
#highlights(("统一工作台：把散落的工具收进一处", "自动化流程：重复动作交给规则去做",
             "团队视图：每个人的进度一眼可见"), num_size: 9pt, txt_size: 10.5pt)
#info_row("主讲嘉宾", "示例主讲人（产品负责人）")
// 朋友圈配置
#highlights(("a","b","c"), num_size: px(28), txt_size: px(33))
#info_row("活动时间", "2026年12月5日（周六）14:00", label_w: px(172), size: px(32))
// 易拉宝配置
#highlights(("a","b","c"), num_size: 56pt, txt_size: 66pt, label_w: 68mm)
#info_row("活动时间", "2026年12月5日（周六）14:00", label_w: 190mm, size: 64pt)
