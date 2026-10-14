# 更新日志

本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [2.0.0] — 2026-10-14

### 新增
- **方形封面版（1:1，2160×2160 px）**：面向公众号首图 / 小红书封面，新增
  `example/templates/poster-square.typ`，并已纳入 `build.sh`、`preflight.py`、`check_qr.py`
  与回归用例。
- **Windows 原生渲染脚本 `example/build.ps1`**：无需 bash，一键渲染四种格式 + 预检双闸，
  行为与 `build.sh` 对齐。
- **字体可用性闸门**：`preflight.py` 用 `typst fonts` 核对字体栈 —— 一个都不可用直接报错、
  首选缺失则警告，把「字体静默回退」变成大声提示。
- **跨平台预览脚本 `scripts/make_preview.py`**：生成最长边 1400px 的预览 JPG
  （原先内联在 build 脚本的 heredoc 里，换 shell 就崩）。

### 修复
- **模板硬编码字体名 → Windows 静默回退**：`Noto Sans CJK SC` 在 Windows 上不存在，Typst
  不报错、无声回退，版式走样。改为引用 `lib/tokens.typ` 的 `FONTS` 跨平台字体栈
  （`Noto Sans CJK SC` → `Noto Sans SC` → `Microsoft YaHei`），并配字体闸门兜底。
- **`run_tests.py` 在 Windows 上不可用**：临时产物路径由写死的 `/tmp` 改为
  `tempfile.gettempdir()`。
- **`subprocess` 在 Windows 按 GBK 解码 Typst 的 UTF-8 输出而崩溃**：`preflight.py` /
  `run_tests.py` 改为显式 UTF-8 解码（`errors="replace"`）。

### 变更
- **技能名 `poster-design` → `duduhaibao`**，frontmatter 描述改为中文触发词，适配 opencode。
- **工具引用改为跨 Agent 中立**：`vision_analyze` → `read`（看图），`clarify` → `question`
  （向用户确认）；文档开头附 opencode / Hermes 映射说明。
- README 同步：四种格式、`build.ps1`、字体栈与字体闸门说明、opencode 部署步骤。

## [1.3.0] — 2026-10-08（首次发布）

- 一套数据出 **A4 打印版 / 朋友圈版 / 易拉宝版** 三种格式，Typst 渲染，无浏览器、无服务、无 MCP。
- 三层护栏：编译期断言（把静默裁切变成大声报错）+ 双闸预检（渲染前查数据 / 渲染后查成品）
  + 回归测试（每个用例对应一个真实故障，双向断言）。
- CI：每次 push / PR 跑测试 + 完整渲染 + 二维码可扫性检查，产物作为 artifact 上传。
