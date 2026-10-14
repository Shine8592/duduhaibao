# 更新日志

本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [2.1.1] — 2026-10-14

### 修复
- **强调线压到标题字底**（`poster-social` / `poster-square` / `poster-wide` 三个模板）：
  强调线的位置原是硬编码的 `dy`，隐含假设标题只有 1 行；而示例数据是 **2 行标题**，
  线就落到第二行字底上，看着像给首字加了下划线 —— 不裁切、不溢出、编译器不报错、
  尺寸/溢出护栏也抓不到的**静默版式 bug**。改为把「标题 + 强调线 + 导语」放进同一个
  `place` 块内**流式排布**，间距由 `#v()` 保证，与标题实际行数解耦（1 行 / 2 行都不撞）；
  外层仍是绝对定位，不违背项目的锚定原则。
- 修复后实测墨迹间距：social 19px / square 15px / wide 13px（修复前为 0，贴字）。

> 注：`poster-a4` 不受影响（强调线离标题约 12mm，间隔充足）。
> 附带发现并修好：opencode 桌面版对**自定义 provider 模型**默认 `capabilities.input.image=false`，
> 需在模型配置里显式声明 `modalities.input` 才能读图（与本仓无关，属本地客户端配置）。

## [2.1.0] — 2026-10-14

> 主题：对标同类项目，补齐「风格 / 比例 / 质检」三块短板。分析与借鉴记录见
> [`competitive-analysis.md`](competitive-analysis.md)。

### 新增
- **风格预设库 `lib/styles.typ`**：6 套做过对比度校准的配色方案（商务蓝 / 墨绿 / 雅紫 /
  活力橙 / 中国红 / 极简墨）。`--input style=<名>`（build 脚本 `--style`）一键换色，
  模板一行不改。（借鉴乔木 Mondo 1271★ 的「风格库 + 按需选」思路）
- **风格横向对比**：`scripts/render_styles.py` + `build.sh --styles` / `build.ps1 -Styles`，
  同一版式并排渲染全部配色，挑一套。
- **新增格式：横版头图（16:9，1920×1080）** `templates/poster-wide.typ`，用于文章头图 /
  视频封面。（借鉴竞品的平台比例矩阵）
- **交付质检清单 `references/qa-rubric.md`**：机器可验项绑定本仓护栏，人眼判断项 +
  反「通用 AI 观感」清单。（借鉴 Skill2Poster 的 layout QA、poster-style-transfer 的 fidelity rubric）
- **`competitive-analysis.md`**：与 11 个同类项目的对比、优劣与借鉴记录。

### 变更
- `preflight.py` 新增**样式闸门**：未知风格名**报错**，而不是让 Typst 静默回退到默认色；
  并新增 `--list-styles`。
- `SKILL.md` 增补：「先定形态再定风格」分类步（借鉴 victor-design）、平台比例矩阵、
  风格预设、反通用 AI 观感、QA 清单引用。
- README：五种格式、风格预设表、与同类工具对照表、FAQ。
- **项目中文名由「嘟嘟海报」改为「海报」。**

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
