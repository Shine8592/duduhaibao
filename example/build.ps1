# ═══════════════════════════════════════════════════════════════════
#  活动海报生产线 —— 一键渲染全部格式（Windows / PowerShell 版）
#
#  与 build.sh 等价，供没有 bash 的 Windows 环境使用。
#  改 lib/data.typ 里的数据，跑这个脚本，各格式同时出新稿。
#  渲染前后各有一道预检闸门（..\scripts\preflight.py）。
#
#  用法：  .\build.ps1              全部渲染
#          .\build.ps1 a4           只渲染 A4
#          .\build.ps1 social       只渲染朋友圈版
#          .\build.ps1 square       只渲染方形封面版
#          .\build.ps1 wide         只渲染横版头图
#          .\build.ps1 banner       只渲染易拉宝版
#          .\build.ps1 all -Force   预检报错也强制渲染
#          .\build.ps1 -Style vivid-orange   换配色（列全部：preflight.py --list-styles）
#          .\build.ps1 -Styles               同一版式横向对比全部配色
#          .\build.ps1 -Pack                 渲染后再打一个交付包 dist/
#
#  依赖：  typst >= 0.13           https://typst.app
#          python + pillow         pip install pillow
#
#  环境变量：
#          PYTHON             指定 python 解释器（默认 python）
#          SKIP_PREFLIGHT=1   跳过预检
# ═══════════════════════════════════════════════════════════════════
[CmdletBinding()]
param(
  [Parameter(Position = 0)][string]$Only = "all",
  [switch]$Force,
  [string]$Style = "",
  [switch]$Styles,
  [switch]$Pack
)

$ErrorActionPreference = "Stop"

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Here
New-Item -ItemType Directory -Path "out" -Force | Out-Null

$Python = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$Preflight = Join-Path $Here "..\scripts\preflight.py"

if (-not (Get-Command typst -ErrorAction SilentlyContinue)) {
  Write-Host "🔴 找不到 typst。安装见 https://typst.app"
  Write-Host "   （winget install Typst.Typst ｜ 或下载 typst.exe 放进 PATH）"
  exit 1
}

Write-Host "════════ 活动海报渲染 ════════"

# ── 风格横向对比（-Styles）：渲染同一版式的全部配色 ──
if ($Styles) {
  $s = if ($Only -in @("a4", "social", "square", "banner")) { $Only } else { "a4" }
  & $Python (Join-Path $Here "..\scripts\render_styles.py") --root $Here --only $s
  exit $LASTEXITCODE
}

# 换配色：导出给预检校验（typst 侧由 Render 传 --input）
if ($Style) { $env:POSTER_STYLE = $Style }

# ─────────────────────────────────────────────────────────────────
#  闸门 1：渲染前查数据 + 字体可用性
# ─────────────────────────────────────────────────────────────────
if ($env:SKIP_PREFLIGHT -ne "1" -and (Test-Path -LiteralPath $Preflight)) {
  & $Python $Preflight --root $Here
  if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    if ($Force) {
      Write-Host "  ⚠️  预检有错误，但指定了 -Force，继续渲染"
    }
    else {
      Write-Host "  🔴 预检发现错误，已中止渲染 —— 修好再跑，或加 -Force 强制继续"
      exit 1
    }
  }
}
elseif ($env:SKIP_PREFLIGHT -eq "1") {
  Write-Host "  （SKIP_PREFLIGHT=1，已跳过预检）"
}

# ─────────────────────────────────────────────────────────────────
#  渲染
# ─────────────────────────────────────────────────────────────────
$t0 = Get-Date

function Render($name, $template, $ppi, $desc) {
  $extra = @()
  if ($Style) { $extra = @("--input", "style=$Style") }
  $pngArgs = @("compile", "--root", ".", "--format", "png", "--ppi", "$ppi") + $extra + @($template, "out/$name.png")
  typst @pngArgs
  if ($LASTEXITCODE -ne 0) { throw "typst 渲染 $name.png 失败" }
  $pdfArgs = @("compile", "--root", ".") + $extra + @($template, "out/$name.pdf")
  typst @pdfArgs
  if ($LASTEXITCODE -ne 0) { throw "typst 渲染 $name.pdf 失败" }
  Write-Host "  ✅ $name  —  $desc"
}

if ($Only -eq "all" -or $Only -eq "a4") { Render "poster-a4" "templates/poster-a4.typ" 300 "A4 打印版   2480x3508px (210x297mm)" }
if ($Only -eq "all" -or $Only -eq "social") { Render "poster-social" "templates/poster-social.typ" 192 "朋友圈版    2160x2880px (3:4)" }
if ($Only -eq "all" -or $Only -eq "square") { Render "poster-square" "templates/poster-square.typ" 192 "方形封面版  2160x2160px (1:1)" }
if ($Only -eq "all" -or $Only -eq "story") { Render "poster-story" "templates/poster-story.typ" 96 "竖屏 Story  1080x1920px (9:16)" }
if ($Only -eq "all" -or $Only -eq "wide") { Render "poster-wide" "templates/poster-wide.typ" 96 "横版头图    1920x1080px (16:9)" }
if ($Only -eq "all" -or $Only -eq "banner") { Render "poster-banner" "templates/poster-banner.typ" 100 "易拉宝版    3150x7874px (80x200cm)" }

# ─────────────────────────────────────────────────────────────────
#  预览图（聊天/网页里看，不用下大图）
# ─────────────────────────────────────────────────────────────────
& $Python (Join-Path $Here "..\scripts\make_preview.py") --root $Here --only $Only

# ─────────────────────────────────────────────────────────────────
#  闸门 2：渲染后查成品（尺寸 / 空白图 / 底部被裁）
# ─────────────────────────────────────────────────────────────────
$PostRC = 0
if ($env:SKIP_PREFLIGHT -ne "1" -and (Test-Path -LiteralPath $Preflight)) {
  Write-Host ""
  & $Python $Preflight --root $Here --output
  $PostRC = $LASTEXITCODE
}

$elapsed = [int]((Get-Date) - $t0).TotalMilliseconds
Write-Host "════════ 完成，用时 $elapsed ms ════════"
if ($PostRC -ne 0) {
  Write-Host "🔴 后检未通过：成品有问题，别发印"
  exit 1
}

# ── 一键交付包（-Pack）：分类 + 平台友好 JPEG + 清单 + zip ──
if ($Pack) {
  & $Python (Join-Path $Here "..\scripts\export_pack.py") --root $Here
}
exit 0
