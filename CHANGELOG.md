# 更新日志

本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [4.0.0] — 2026-10-14

> 主题：**补齐「可爱」方向 + 节气数据 + 照片格位**。起因是回到真实场景
> （邀请函 / 节气 / 朋友圈游玩 / 幼儿园可爱型）后发现：文档里一直写着「卡通 vs 正式」
> 两个方向，**示例却只有正式** —— 而真实需求里三个都偏可爱。

### 新增
- **可爱 / 亲子方向**：模板 `poster-cute`（3:4）——圆角卡片 + 序号圆牌 + 贴纸圆点 +
  圆体（幼圆 YouYuan）。新增 `FONTS_CUTE` 字体栈（跨平台回退到黑体，不会变豆腐块）。
- **风格库 18 → 24 套 / 4 组**（正式 / 文艺 / 活力 / **可爱**），新增 6 套可爱配色：
  糖果粉 / 奶油黄 / 马卡龙 / 薄荷 / 蜜桃 / 晴空（同样经对比度闸门自动校准）。
- **节气数据引擎 `scripts/solar_terms.py`**：按太阳视黄经（Meeus 低精度）**确定性计算**
  24 节气日期（北京时间），可复现。配套 `lib/terms.typ`（2026–2028 共 72 条）+
  `lib/term.typ`（当前节气）+ 模板 `poster-term`（1:1）。
- **照片集模板 `poster-photo`**（3:4）：`lib/photos.typ` 驱动，照片数量**自动适配版式**
  （1 大图 / 2 并排 / 3「1 大 2 小」/ 4+ 网格），圆角 + `cover` 裁切不拉伸。
- 每个格式支持**默认配色**（cute→candy-pink、term→teal），`--style` 可覆盖。

### 修复 / 加固
- **字体闸门升级**：从只查 `FONTS` 改为查**全部 `FONTS*` 字体栈**（含 `FONTS_CUTE`）。
- **底部净空检查改为「与页面底色一致」**：原来写死"必须纯白"，对整页浅色底的版式
  （如节气版用 TINT）会误报；现改为取**底部两角众数**为底色再比对
  （⚠️ 不能取四角：顶部通栏品牌带会让顶部两角是品牌色，与底部白角打平选错）。
- 记录两个 Typst 坑（已写进注释）：
  1. `.at(0, default: panic(...))` —— `default` **急切求值**，panic 无条件执行，守卫自己变炸弹；
  2. `image()` 的相对路径是相对**调用所在的 .typ 文件**，`--root .` 下需前导斜杠才是项目根相对。
- `ok_all.typ` 补可爱版配置（顺带验证了断言会拦住过窄的标签列）。

### 验证
**9 种格式**渲染 + 后检全过；回归 4/4；二维码 7/7；对比度 24×5 全达标；
可爱版 / 节气版 / 照片集均经目视验收；节气日期自检通过（2026 二分二至）。

## [3.2.0] — 2026-10-14

> 主题：**参考图 → 确定性复刻**。把竞品 poster-style-transfer 的「提取海报语法、不抄内容」
> 做成**可测量、可核验**的版本。

### 新增
- **`scripts/analyze_reference.py` 参考图结构化分析**：输入一张参考图，输出
  - `*-analysis.png`：**带标注的结构叠加图**（横带红框 + 竖栏蓝线 + 色卡）—— 可逐带目视核验；
  - `*-report.md`：比例 / 建议格式 / 色板表（含 WCAG 对比度）/ 横带竖栏结构表；
  - `*-palette.typ`：可直接粘进 `styles.typ` 的配色片段。
  做法是**量化 + 结构分析**（可复现），不是让模型"看图写提示词"。
- **`references/reference-extraction.md`**：完整流程 + 诚实边界（色板是启发式、小面积色会被合并，
  必须人工校订；只借语法不抄内容；肖像/logo/商标须替换）。

### 验证
- **往返测试**：拿本仓 `poster-social.png` 当参考图 → 比例 0.750 → 建议 `poster-social`；
  `brand` **精确还原** `#1B4F8C`；横带检测把标题两行 / 强调线 / 导语 / 亮点三条 / 信息两行 /
  报名区（并分出竖栏）/ 页脚全部正确圈出（叠加图目视验收）。

## [3.1.0] — 2026-10-14

> 主题：**一键导出 / 投递** —— 补齐竞品（html-anything 的 9 平台导出）目前明显强于我们的一块。

### 新增
- **`scripts/export_pack.py` 一键交付包**：`--pack` / `-Pack` 在渲染后自动打一个 `dist/<日期>/`：
  - `print/`（PDF 矢量 + PNG）、`social/`（PNG）、`web/`（平台友好 RGB JPEG）
  - `manifest.json`：每文件的尺寸 / 字节 / **sha256** / 用途 / 建议投放
  - `README.txt`：人读的交付清单
  - **体积预警 + 自动压缩版**：超过平台单张上限时报警，并另出 `*.compressed.jpg`
  - 打包 `.zip`
- **`references/delivery-guide.md`**：各平台投放规格（格式 / 尺寸 / 体积上限 / 二次压缩 / 常见坑），
  借鉴 web-asset-generator 的平台规格表 + 校验思路。

### 变更
- `build.sh` / `build.ps1` 新增 `--pack` / `-Pack`（一键：渲染 → 预检双闸 → 交付包）。
- `.gitignore` 排除 `dist/`、`*.zip`（产物不入库）。
- README：新增「一键交付包」章节；项目结构同步。

### 验证
6 格式渲染 + 后检全过；交付包 6 项全部核验（尺寸正确 / 非空白 / 体积正常）；回归 4/4；二维码 6/6。

> 为什么先转 JPEG：微信公众号 / 小红书 / 抖音会对上传的 PNG 二次压缩；先给 RGB JPEG（质量 88）更稳。

## [3.0.0] — 2026-10-14

> 主题：**目视质检 → 达到竞品 → 超越竞品**。本轮首次具备读图能力，所有版式改动都经目视验收。

### 新增
- **风格库 6 → 18 套**（新增 藏青金 / 青碧 / 樱粉 / 薰衣草 / 雾霾蓝 / 暖沙 / 科技青 / 深空 /
  鎏金 / 石墨 / 梅子 / 森林），全部经**对比度闸门自动校准**到达标。
- **`--styles` 升级为带标注的联系表**（`out/styles-sheet.jpg`）：一次看完 18 套配色并排效果，
  对齐 html-anything 的「多候选预览」。
- **新增格式：竖屏 Story（9:16，1080×1920）** —— 抖音 / 视频号 / 快手 / IG Story。
  并把**平台安全区编码成硬闸门**：`poster-story` 的底部净空设为 288px（=1920×15%），
  任何落进平台遮挡区的内容都会被 preflight 拦下。
- **间距阶梯 `SP` + `min_gap()` 断言**：纵向节奏统一从阶梯取值；间距过小在编译期报错。

### 修复（目视体检发现）
- **social / square / wide 纵向节奏失衡**：强调线被夹在标题与导语之间、导语贴住亮点列表、
  列表项之间间距被吞。
- **两个 Typst 静默坑**（已写进模板注释）：
  1. `v()` 默认是**弱间距**，放进大 block 会被吞掉 → 列表项间距凭空消失；需 `weak: false`。
  2. 在大 block 里设 `par(leading)` 会**压扁**嵌套 grid 的行高；而 grid 单元格是单行、
     行高由**字体度量**决定，**页面级 / 块级 leading 都改不动它** → 故列表、信息必须独立成块。
- square：亮点列表与信息贴死（间距仅 4px）→ 重新排布，列表与信息分开。

### 变更
- `preflight.py` 预检段落更名「数据 + 字体 + 风格 + 对比度」。
- README：六种格式、18 套风格表、联系表说明。
- `references/platform-specs.md`：标注 Story 已内置、且安全区已闸门化。

### 验证
6 种格式渲染 + 后检全过；回归 4/4；二维码 6/6；对比度 18×5 全达标；全部版式经目视验收。

## [2.2.0] — 2026-10-14

> 主题：第二轮竞品调研后的升级。分析与借鉴记录见
> [`competitive-analysis.md`](competitive-analysis.md) 的「第二轮补扫」。

### 新增
- **对比度闸门**：`preflight.py` 逐套配色算 WCAG 对比度（正文/小字 ≥ 4.5、大字 ≥ 3.0），
  不达标即报错。借鉴 huashu-design / html-anything 的「对比度 ≥ 4.5」硬约束，但把它从
  **提示词纪律**变成**可执行检查**。**当场查出并修好**两套配色的 muted 偏淡：
  `formal-blue` 4.26 → 4.65、`vivid-orange` 4.45 → 4.66（前者是默认配色，即所有成品的小字）。
- **`references/platform-specs.md`**：各平台画幅/像素尺寸 + **UI 遮挡安全区**
  （抖音/视频号底部 ~15%、小红书底部 ~12%、易拉宝底部 ~30cm、印刷出血/安全线）。
  借鉴 web-asset-generator 的平台规格表与 gbro-cover-design 的安全区定义。
- **`scripts/doctor.py`**：环境自检（Python / Typst / Pillow / 中文字体 / 二维码后端 / HTML 路线），
  **只报告、不静默安装**。借鉴 yingzao / web-asset-generator 的依赖检查纪律。

### 变更
- `SKILL.md` 新增「**程序做测量，模型做语义**」原则小节：代码负责测量与几何（尺寸 / 字形覆盖 /
  对比度 / 碰撞），模型负责语义（读图 / 定方向 / 判平衡）；并明确「**只读图一次、不自动重生成，
  把决定交回用户**」（借鉴 yingzao）。
- README：补 opencode / Claude Code / Codex / Hermes 四种安装路径；项目结构与闸门表同步。
- `references/qa-rubric.md`：新增对比度、doctor、平台安全区条目。

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
