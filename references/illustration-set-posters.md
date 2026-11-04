# 卡通插画集海报（AI 生成配图 + HTML 排版）

适用：客户沙龙 / 亲子 / 节日 / 市集这类「要插画、要卡通感」的竖版海报。
上游生图走 `agnes-image`；本文件只管**成套一致性**与**排版验收**。

## 0. 收到底稿图就先查 AI 水印

用户发来一张「看着挺完整」的成品图当底稿时，**先放大看右下角**。这类图常带半透明描边水印（`豆包AI生成` 之类），缩略图里几乎看不见，原尺寸下清清楚楚。

- 裁 `(W-420, H-190, W, H)` 放大 4 倍看右下角，比肉眼扫缩略图可靠。
- 水印是`裁掉/覆盖`就能解决的，但**不能带着它发给客户**——尤其保险公司、银行这类要过合规的客户物料。
- 顺手自查这张底稿缺什么：年份、完整地址、联系人、主办方落款。AI 生成的「完整海报」常年缺这四样。

## 1. 一次生成整套，再开始排版

**不要先写 HTML 再补图**——缺图会逼你在布局里留占位，补齐后必然重排一次。

一套通常 4 张：1 张主视觉 + 3 个亮点图标。每张共用同一条 STYLE LOCK 前缀，只换 SUBJECT 段：

```text
Flat vector cartoon illustration for a warm children's picture book poster.
STYLE: clean thick uniform outlines, flat solid colors with subtle paper grain,
warm autumn palette of golden yellow, cream white, soft orange and warm brown,
cute rounded simple shapes, minimal detail, no gradients,
generous empty margins, centered composition.
STRICT: absolutely no text, no letters, no numbers, no watermark, no signature, no logo.
No human faces, no photorealistic rendering, no 3D shading.
```

- **主视觉最容易跑偏**：其余三张是扁平图标，主视觉却渲染成「有透视、有纹理的风景画」，线条系统直接对不上。风景类要额外写死 `no perspective lines, no texture, sticker-like, icon style`。
- 模型用 `agnes-image-2.5-flash`（本机可用，细节比 2.1 稳）；`GET /models` 拿实际 id，别照抄旧文档。
- **图内绝不出文字**：AI 中文必乱码。标题、时间、地址全部由 HTML 层叠加。

## 2. 接触表验收（一次调用看整套）

```python
from PIL import Image
names = ['hero', 'cake', 'basket', 'bus']; cell = 520
sheet = Image.new('RGB', (cell*2, cell*2), 'white')
for i, n in enumerate(names):
    im = Image.open(f'{n}.png').convert('RGB'); im.thumbnail((cell, cell), Image.LANCZOS)
    sheet.paste(im, ((i % 2) * cell + (cell - im.width) // 2,
                     (i // 2) * cell + (cell - im.height) // 2))
sheet.save('_sheet.png')
```

把拼图交给视觉，问四件事：**是否同一套 / 有无文字乱码 / 有无器皿或轮子畸变 / 哪张最该重画**。

**逐张看会漏掉对比**——同套一致性只在拼图里看得出来。

## 3. 不统一时：先改容器，再考虑重画

判据只有一条：**差在哪一层**。

| 差异 | 处理 |
|---|---|
| 描边粗细、细节密度、有没有投影 | **改容器**。统一规格的圆形贴纸（等宽深色描边 + 白底）或同一个圆角画框。框住之后差异不可见，比重画快一个数量级 |
| 构图类型不同（透视风景 vs 纯图标） | **只能重画**，并补 `no perspective lines, sticker-like` |
| 器皿变形、轮子歪、物体粘连 | 重画该张 |

视觉评审对成套插画会反复报「没有完全统一」并拒绝说「可以成套」，即使差异只有一档细节密度。**这是过度挑刺，不是缺陷**——按上表自行决断，别为它反复重画（重画往往还是差，因为漂移是模型固有的）。

## 4. 排版（HTML + Chromium，1080×1440 @2x）

- 所有元素绝对定位在固定 CSS 页面上；图片 base64 内嵌（4 张插画 ≈ 4 MB HTML，Chromium 无压力）。
- 卡通版字体：标题 **ZCOOL KuaiLe（站酷快乐体）**，数字用 **Fredoka / Baloo 2**，正文 Noto Sans CJK SC。写进 CSS 前先 `fc-list : family | grep -i <name>` 确认——未注册的字体会**静默回落**，整体气质就错了且不报错。
- 统一视觉语言：粗深棕描边（`border: 6–8px solid #6B4A2F`）+ 圆角 36–44px + 贴纸投影（`box-shadow: 0 5px 0 rgba(107,74,47,.15)`）。
- 页脚小字**不低于 26px、不用浅灰**——浅色小字手机和印刷上都糊。
- 日期行右侧容易留一大块空白：加一个虚线小标签（`诚邀莅临` 之类）平衡，比强行拉宽日期条好。

```bash
CHROME=$(ls ~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome | head -1)
"$CHROME" --headless --no-sandbox --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=2 --window-size=1080,1440 \
  --screenshot=/abs/out.png "file:///abs/page.html"
```

## 5. 验收顺序：先量，再看

```bash
# (a) 全文回读：文字到底有没有渲染（缺字/方框在这里暴露）
tesseract out.png - -l chi_sim --psm 6
```

```python
# (b) 探边：最下墨迹离页底多远、底部安全区是否干净
import numpy as np
from PIL import Image
im = np.array(Image.open('out.png').convert('RGB'), dtype=int)
H, W, _ = im.shape
bg  = im[H-35:H-5, 5:60].reshape(-1, 3).mean(axis=0)   # 左下角空白作背景
ink = (np.abs(im - bg).sum(axis=2) > 60)
rows = np.where(ink.any(axis=1))[0]
print('最下墨迹 y =', rows.max(), '距页底 =', H-1-rows.max())
print('底部 40 行墨迹 =', int(ink[H-40:].sum()))       # 应为 0
```

- **OCR 跳过 ≠ 没渲染**：低对比度文字（浅黄压绿底）会被 tesseract 整段漏读。把那一块裁出来放大 2–3 倍做一次视觉确认，再决定是否调色——不要因为 OCR 没读到就重画。
- 视觉只判版式（重叠 / 越界 / 间距节奏 / 画风），**不判字**。分数（同一张图 6→9 漂移）不看，只采纳能命名且可复现的缺陷。
- 上下间距按「块与块的间隙」均分，不要按「元素中心」均分：日期条→图标行、图标标签→卡片、卡片→绿条，三段间隙应接近，差值超过约 10px 就能看出来。

## 6. 交付

PNG（无损母版）+ JPG（`quality=93, subsampling=1, optimize`）。
报告里必须包含：输出尺寸、文件大小、**改掉的原文问题**（缺年份 / 缺地址 / 简称未写全称 / AI 水印）。
其余渠道（A4 印刷 2480×3508、9:16 竖屏）同一套 HTML 换 `--window-size` 与字号即可，不要重新设计。
