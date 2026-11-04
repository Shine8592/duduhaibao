# AI 生图 / 改图模型（duduhaibao 4.4.0）

> 两个模型由供应商 **yaner** 提供，挂在 OpenAI-compatible 端点 `token.yaner.fun/v1`。
> 它们把海报技能从「只能确定性排版」扩展到「能生成/重绘画面」，是本次升级的**质的提升**。
>
> **先说清一个常识**：海报当然要带文字——标题、时间、地点、主办方绝大多数是海报的核心。
> 本文约束的**不是「海报有没有文字」，而是「文字由哪一层渲染」**：
>
> - **文字永远在**：由 HTML / Typst / Pillow 的**真文字层**排版叠加，清晰、可改数据重出、永不乱码。
> - **AI 生成的插画/背景图里不烧字**：生图模型画中文字形不可靠（必乱码），所以它只出画面；
>   文字由排版层盖在画面之上。
>
> 一句话：**文字照常有，只是不交给生图模型去画字形。**

## 一、两个模型的分工

| 模型 id | 名称 | 能力 | 在技能里负责 |
|---|---|---|---|
| `cn:hunyuan-image-alpha` | Hunyuan Image Alpha | 文生图 (text→image) | **卡通插画集**：一次生成整套插画（主视觉 + 亮点图标） |
| `cn:hunyuan-image-alpha-edit` | Hunyuan Image Alpha Edit | 图生图 / 改图 / 修图 (text+image→image) | **画面级重绘**：照片艺术化、底稿风格化、去 AI 水印、局部重绘、插画微调 |

## 二、硬边界（三条，违反即倒退）

1. **AI 生成的插画 / 背景图里不烧文字**（`STRICT` 段写死 `no text/letters/numbers`）；
   **成品海报的文字照常要有**——标题、时间、地址、主办方全部由 HTML 层以真文字叠加在画面之上。
   理由不是「文字不许存在」，而是「生图模型画中文字形不可靠（必乱码）」，文字必须由能保证
   字形正确的排版层来画。
2. **改成品上的错字 / 日期 / 活动流程 / 任何文字内容 → 走 `repair_raster.py`**，
   不要用 edit 模型。`scripts/edit_image.py` 内置了「改文字类指令」拒绝逻辑；
   `repair_raster.py` 是像素级、确定性、留验证报告的（见 `--report`）。
   > 口诀：**edit 管画面，repair_raster 管文字；文字本身一直由排版层负责。**
3. **零 API 仍是默认路线**。两个模型是*可选增强*，没配 key 时技能照常纯本地出图。
   不要因为接了模型，就把所有海报都改成生图路线 —— 正式/文字密集/数据驱动版式仍走 Typst/HTML。

## 三、调用协议（实测坐实）

`GET /models` 返回两个模型都标 `image_generation: true`，一个 tag `text-to-image`、一个 `image-to-image`。
两端都走 `POST /images/generations`，返回 `data[0].url`（COS 签名 URL，需下载）：

```
文生图： {model, prompt, n:1, size}                       → data[0].url
图生图： {model, prompt, n:1, size, image: <base64>}     → data[0].url
```

图生图的 `image` 字段**确会被消费**（实测：纯绿底图 + 「改成紫色」→ 输出中心像素 `(139,81,154)` 紫色），不是被忽略的占位参数。

封装在 `scripts/image_api.py`（纯标准库，密钥只从环境变量读），两个 CLI 复用：

| 脚本 | 用途 |
|---|---|
| `scripts/generate_illustration.py` | 成套插画（文生图），含 STYLE LOCK + 接触表 |
| `scripts/edit_image.py` | 画面级改图/修图（图生图），含改字指令拦截 |

### 配置

```bash
export DUDUHAIBAO_IMAGE_KEY="..."        # 或 YANER_API_KEY
export DUDUHAIBAO_IMAGE_API="https://token.yaner.fun/v1"   # 可选，默认值即此
export DUDUHAIBAO_COST_LOG="_wip/image_cost.jsonl"          # 成本记录路径
```

**密钥绝不硬编码、绝不写进公开仓库**（2026-10-14 曾因本机路径/凭据误入公开镜像删库重建过一次，见 `publishing-publicly.md`）。

### 回退到旧后端

4.3.1 的插画 recipe 是按 `agnes-image-2.5-flash` 调的。STYLE LOCK 抽成了**后端无关**的通用风格约束，所以换后端不必重调整套 prompt：

```bash
python scripts/generate_illustration.py --backend agnes --subjects ...
# 需 AGNES_API_KEY / AGNES_API_BASE / AGNES_MODEL
```

## 四、成套插画流程（卡通插画集）

完整排版/验收 recipe 在 `illustration-set-posters.md`，这里只补模型侧：

```bash
# 1) 一次生成整套（第 1 个是主视觉，自动加锁「无透视/贴纸感」）
python scripts/generate_illustration.py \
    --subjects "秋日稻田主视觉" "蛋糕" "野餐篮" "大巴车" \
    --out-dir _wip/illustrations --size 1024x1024 --contact

# 2) 把 _sheet.png（接触表）缩到 ≤1024 送视觉，一次判「是否同一套 / 有无文字乱码 / 哪张该重画」
# 3) 不统一时：先改容器（统一圆形贴纸/画框），再考虑重画该张
```

- 主视觉最容易跑偏成「有透视的风景」→ 脚本自动给第 1 张追加 `no perspective lines, sticker-like`。
- **接触表验整套**，别逐张看（同套一致性只在拼图里看得出来）。
- 视觉评审会反复报「没完全统一」—— 差在描边/细节密度是过度挑刺，按 `illustration-set-posters.md §3` 自行决断，别为它反复重画。

## 五、改图 / 修图流程

```bash
# 整图风格化
python scripts/edit_image.py --in photo.jpg --out _wip/styled.png \
    --prompt "转成暖色扁平卡通插画，厚描边，无透视"

# 只改问题区域（去水印 / 修某个变形物体）—— 先裁局部，改动面最小
python scripts/edit_image.py --in draft.png --out _wip/fixed.png \
    --crop 1700,2690,2160,2880 --prompt "去掉右下角水印，保持纯色背景"

# 交付前粗查输入图有无文字（有则提醒：改字走 repair_raster.py）
python scripts/edit_image.py --check-text --in poster.png
```

**允许**：照片艺术化、底稿风格化、去 AI 水印（豆包/即梦类半透明描边）、器皿/轮子变形修复、配色描边统一。
**禁止**：改错字、改日期、改时间、改活动流程、改任何文字 —— 一律 `repair_raster.py`。

> 边界判定用**保守策略**：指令里出现「文字对象词」（日期/标题/text/title…）即拒绝，
> 不猜意图（词表猜法实测两头漏）。若确为画面指令只是措辞提到这些词，加 `--allow-text`
> 显式放行；例如 `--prompt "平衡一下日期条附近的配色" --allow-text`。
> `scripts/edit_image.py` 内置该逻辑，CI 冒烟会断言改字指令返回码 = 2。

## 六、成本记录（P2-1）

每次 API 调用在 `DUDUHAIBAO_COST_LOG` 落一行 JSONL（kind / model / ok / elapsed_s / credit，不记图片内容）。
交付消息回显一行，满足「免费额度用尽就停」的可判断性：

```
生成成本：插画 5 次调用（4 用 1 弃）· 改图 1 次 · 渲染 3 次 · 总耗时 21 分钟
```

`image_api.cost_summary()` 给出累计统计；`doctor.py` 会探测后端可用性（缺 key 只提示、不阻断本地渲染）。
