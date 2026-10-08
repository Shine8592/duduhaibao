// 回归测试：历史 bug —— 易拉宝字号塞进 9mm 序号列，
// "01" 溢出到正文列，成品上看着像 "0"。断言应当拦住。
#import "../lib/tokens.typ": *
#set page(width: 200mm, height: 80mm)
#highlights(("统一工作台的界面设计", "自动化流程的规则编排", "团队视图的权限模型"),
            num_size: 52pt, txt_size: 60pt, label_w: 9mm)   // ← 故意过窄
