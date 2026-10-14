# 竞品分析 · 海报生成工具（2026-10）

> 目的：看清同类项目在做什么、强在哪、弱在哪，据此决定本项目的**差异化定位**与
> **可借鉴点**。结论直接落到 v2.1.0 的改动上（见文末「本次借鉴落实」）。

## 一、方法论

- GitHub 检索（`poster generator` / `typst poster` / `海报 生成` / `poster design skill`
  / `poster mcp` / `ai poster design`），按 star 排序取头部。
- 逐个读 README，重点看：**它交付什么**、**靠什么生成**、**怎么保证正确**、**怎么被安装**。
- 只对比与「把内容变成一张海报」这件事直接相关的项目；纯线上设计工具（Canva 类）
  只作背景。

## 二、同赛道项目（按 star 降序）

| 项目 | ★ | 类型 | 交付物 | 生成方式 |
|---|---|---|---|---|
| [palxiao/poster-design](https://github.com/palxiao/poster-design) | 4914 | Web 应用 | 可在浏览器编辑的图片 | Vue + fabric.js 在线画布 |
| [joeseesun/qiaomu-mondo-poster-design](https://github.com/joeseesun/qiaomu-mondo-poster-design) | 1271 | Agent Skill | **图片模型的提示词** | 33+ 艺术家风格 → 文生图 / 图生图 |
| [Anil-matcha/Open-AI-Design-Agent](https://github.com/Anil-matcha/Open-AI-Design-Agent) | 450 | AI Agent | 设计图 | 多模型编排 |
| [jiji262/claude-design-skill](https://github.com/jiji262/claude-design-skill) | 204 | Claude Skill | HTML 设计稿 | HTML 工件 |
| [pncnmnp/typst-poster](https://github.com/pncnmnp/typst-poster) | 156 | Typst 模板 | A0 学术海报 PDF | Typst，参数化模板 |
| [jonaspleyer/peace-of-posters](https://github.com/jonaspleyer/peace-of-posters) | 123 | Typst 包 | 学术海报 | Typst 库 |
| [LEON-gittech/Skill2Poster](https://github.com/LEON-gittech/Skill2Poster) | 82 | Codex Skill ×2 | A0 HTML/PDF 学术海报 | 生图做**设计参考** + HTML 重建 |
| [victorzhang016-code/victor-design](https://github.com/victorzhang016-code/victor-design) | 69 | Agent Skill | 可编辑 Figma 帧 | 主题优先 + 三道交付闸 |
| [jiemianduan/poster-style-transfer](https://github.com/jiemianduan/poster-style-transfer) | 56 | Agent Skill | 风格规范 + 新海报概念 | 提取"海报语法"，提示词生成 |
| [AIPlayerDayu/dayu-poster-designer](https://github.com/AIPlayerDayu/dayu-poster-designer) | — | Agent Skill | 文生图提示词 | 18 份分类规则按需加载 |
| [WinterNova-X/design-poster](https://github.com/WinterNova-X/design-poster) | — | Agent Skill | 品牌提案板图 | 提示词生成 |
| **本项目 duduhaibao** | — | **Agent Skill** | **可直接印刷的 PDF/PNG** | **Typst 确定性渲染** |

## 三、关键洞察

### 1. 这个赛道 90% 是「提示词生成器」，不是「渲染器」

qiaomu、大羽、design-poster、poster-style-transfer 都只**产出提示词**，真正的图由
图片模型画。它们的 README 里反复出现同一句话的变体：

- design-poster：**「文字定稿防乱码：所有文案提前写死，宁可留白不造假字」**
- 大羽：**「标题、日期、价格等绝对不能出错时，先生成画面并预留文字区域，再用
  PS/Figma/Canva 正式排字」**
- Skill2Poster：**「AI 生图适合探索版式……但不应该作为最终事实来源」**

> **这正是本项目的护城河。** 我们用 Typst 确定性排版——**文字永远正确，书名号、
> 日期、价格不会变成错字或乱码**。竞品要靠"预留文字区域 + 手工排字"绕开的坑，
> 我们不存在。

### 2. 但竞品在「风格」和「发现性」上强于我们

| 维度 | 竞品做法 | 我们 v2.0 的状态 |
|---|---|---|
| 风格库 | qiaomu 内置 33+ 设计师风格，按题材**自动选风格** | 只有 2 个方向（卡通/正式），颜色写死 |
| 平台比例 | qiaomu 一张表覆盖 21:9 / 3:4 / 16:9 / 9:16 / 1:1 | 3 种（A4 / 3:4 / 1:1） |
| 反"AI 味" | victor「拒绝通用 AI 视觉与文案」；design-poster 有禁止清单 | 无 |
| 安装 | qiaomu `npx skills add`；大羽用自然语言安装 | 手动 `cp -r` |
| 包装 | 样张画廊 + FAQ + "和别的工具比"对照表 | 有徽章，无 FAQ / 对照表 |

### 3. 「护栏」我们独一档

victor-design 讲「三道交付闸」，但那是**提示词级的自我约束**；没人做**可执行的
自动检查**。我们的编译期断言 + 双闸 + 回归测试是**代码级、可复现**的，这是第二处
独有优势（Skill2Poster 的 QA 清单是纯人工 checklist）。

## 四、逐项优劣

### 我们比竞品强
1. **文字零错误**（确定性渲染）——直接消灭竞品的头号痛点。
2. **可执行的护栏**——断言/像素闸门/回归测试，竞品只有文字纪律。
3. **零依赖零成本**——无图片模型 API key、无浏览器、无常驻进程；竞品都要 API。
4. **一条产线出多格式**——改一个 `data.typ` 出全部规格；竞品是"一次一图"。
5. **矢量 PDF 原生**——印刷级，竞品给位图。

### 竞品比我们强
1. **风格丰富度与自动选风格**（qiaomu 1271★）——我们会渲染但"颜色只有一套"。
2. **平台比例更全**——缺 16:9 / 21:9 / 9:16。
3. **反 AI 通用观感的纪律**（victor / design-poster）。
4. **发现性与安装体验**——npx / 自然语言安装、样张画廊、FAQ。
5. **可按参考图提取"海报语法"**（poster-style-transfer 的 Style Spec）。

## 五、本次借鉴落实（v2.1.0）

| 借鉴点 | 来源 | 落实方式 |
|---|---|---|
| 命名风格库 | qiaomu / victor | `lib/styles.typ` **6 套配色方案**，`--input style=<名>` 一键换色，全篇同步；`preflight.py` 增样式闸门防静默回退 |
| 风格对比 | qiaomu「对比三种风格」 | `scripts/render_styles.py` + `build.sh --styles`，同一版式并排出全部配色 |
| 平台比例矩阵 | qiaomu | 新增 **16:9 横版头图**（`poster-wide.typ`，1920×1080） |
| 交付 QA 清单 | Skill2Poster / poster-style-transfer | 新增 `references/qa-rubric.md`（可勾选 + 与本仓护栏呼应） |
| 先定形态再定风格 | victor「form before styling」 | 写进 `SKILL.md` 流程第 1 步 |
| 反"AI 味"清单 | victor / design-poster | 写进 `SKILL.md`「反通用 AI 观感」小节 |
| 提"海报语法"不抄内容 | poster-style-transfer | 并入 `references/reference-and-ip-matching.md` 的硬锁/软锁/替换三分类 |

## 六、刻意**不**借鉴

- **文生图路线**：会引入"文字不可靠"这一原罪，与我们护城河冲突。我们反而要强调
  "要准确就渲染"。
- **33 个艺术家风格库**：那是提示词语境下的产物；确定性排版里堆风格 = 维护爆炸，
  用**校准过对比度的配色方案**替代更诚实。
- **上 MCP 服务**：渲染无状态、亚秒级、只有一个消费者，理由见 `SKILL.md` 架构决策。
