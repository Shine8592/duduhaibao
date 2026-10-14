#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  活动海报生产线 —— 一键渲染全部格式
#
#  改 lib/data.typ 里的数据，跑这个脚本，三个格式同时出新稿。
#  渲染前后各有一道预检闸门（../scripts/preflight.py）。
#
#  用法：  ./build.sh              全部渲染
#          ./build.sh a4           只渲染 A4
#          ./build.sh social       只渲染朋友圈版
#          ./build.sh square       只渲染方形封面版
#          ./build.sh wide         只渲染横版头图
#          ./build.sh banner       只渲染易拉宝版
#          ./build.sh all --force  预检报错也强制渲染
#          ./build.sh --style vivid-orange   换配色（列全部：preflight.py --list-styles）
#          ./build.sh --styles               同一版式横向对比全部配色
#
#  依赖：  typst >= 0.13           https://typst.app
#          python3 + pillow        pip install pillow
#
#  环境变量：
#          PYTHON   指定 python 解释器（默认 python3）
#                   例：PYTHON=/path/to/venv/bin/python ./build.sh
#          SKIP_PREFLIGHT=1       跳过预检
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
mkdir -p out

ONLY="all"; FORCE=""; STYLE=""; STYLES_CMP=0
while [ $# -gt 0 ]; do
  case "$1" in
    --force)   FORCE="--force" ;;
    --style)   STYLE="${2:-}"; shift ;;
    --style=*) STYLE="${1#*=}" ;;
    --styles)  STYLES_CMP=1 ;;
    -*)        echo "未知参数：$1"; exit 2 ;;
    *)         ONLY="$1" ;;
  esac
  shift
done

PYTHON="${PYTHON:-python3}"
PREFLIGHT="$HERE/../scripts/preflight.py"

# 换配色：--input style= 透传给每次 typst 调用；同时导出给预检校验
STYLE_INPUT=""
if [ -n "$STYLE" ]; then
  STYLE_INPUT="--input style=$STYLE"
  export POSTER_STYLE="$STYLE"
fi

if ! command -v typst >/dev/null 2>&1; then
  echo "🔴 找不到 typst。安装见 https://typst.app"
  echo "   （macOS: brew install typst ｜ Rust: cargo install typst-cli）"
  exit 1
fi

echo "════════ 活动海报渲染 ════════"

# ── 风格横向对比（--styles）：渲染同一版式的全部配色 ──
if [ "$STYLES_CMP" = "1" ]; then
  case "$ONLY" in a4|social|square|banner) S="$ONLY" ;; *) S="a4" ;; esac
  "$PYTHON" "$HERE/../scripts/render_styles.py" --root "$HERE" --only "$S"
  exit $?
fi

# ─────────────────────────────────────────────────────────────────
#  闸门 1：渲染前查数据（示例数据 / 必填为空 / 二维码文件缺失）
#
#  用 "|| RC=$?" 而非裸调用：脚本开头有 set -e，裸调用会在预检
#  失败时直接终止，后面的 $? 根本执行不到。
# ─────────────────────────────────────────────────────────────────
if [ "${SKIP_PREFLIGHT:-}" != "1" ] && [ -f "$PREFLIGHT" ]; then
  RC=0
  "$PYTHON" "$PREFLIGHT" --root "$HERE" || RC=$?
  if [ $RC -ne 0 ]; then
    echo ""
    if [ "$FORCE" = "--force" ] || [ "$ONLY" = "--force" ]; then
      echo "  ⚠️  预检有错误，但指定了 --force，继续渲染"
    else
      echo "  🔴 预检发现错误，已中止渲染 —— 修好再跑，或加 --force 强制继续"
      exit 1
    fi
  fi
elif [ "${SKIP_PREFLIGHT:-}" = "1" ]; then
  echo "  （SKIP_PREFLIGHT=1，已跳过预检）"
fi

# ─────────────────────────────────────────────────────────────────
#  渲染
# ─────────────────────────────────────────────────────────────────
t0=$(date +%s%N)

render() {  # name  template  ppi  desc
  local n="$1" t="$2" ppi="$3" desc="$4"
  typst compile --root . $STYLE_INPUT --format png --ppi "$ppi" "$t" "out/$n.png"
  typst compile --root . $STYLE_INPUT "$t" "out/$n.pdf"
  echo "  ✅ $n  —  $desc"
}

if [ "$ONLY" = "all" ] || [ "$ONLY" = "a4" ]; then
  render poster-a4      templates/poster-a4.typ      300 "A4 打印版   2480x3508px (210x297mm)"
fi
if [ "$ONLY" = "all" ] || [ "$ONLY" = "social" ]; then
  render poster-social  templates/poster-social.typ  192 "朋友圈版    2160x2880px (3:4)"
fi
if [ "$ONLY" = "all" ] || [ "$ONLY" = "square" ]; then
  render poster-square  templates/poster-square.typ  192 "方形封面版  2160x2160px (1:1)"
fi
if [ "$ONLY" = "all" ] || [ "$ONLY" = "story" ]; then
  render poster-story   templates/poster-story.typ   96  "竖屏 Story  1080x1920px (9:16)"
fi
if [ "$ONLY" = "all" ] || [ "$ONLY" = "wide" ]; then
  render poster-wide    templates/poster-wide.typ    96  "横版头图    1920x1080px (16:9)"
fi
if [ "$ONLY" = "all" ] || [ "$ONLY" = "banner" ]; then
  render poster-banner  templates/poster-banner.typ  100 "易拉宝版    3150x7874px (80x200cm)"
fi

# ─────────────────────────────────────────────────────────────────
#  预览图（聊天/网页里看，不用下大图）
# ─────────────────────────────────────────────────────────────────
"$PYTHON" "$HERE/../scripts/make_preview.py" --root "$HERE" --only "$ONLY"

# ─────────────────────────────────────────────────────────────────
#  闸门 2：渲染后查成品（尺寸 / 空白图 / 底部被裁）
# ─────────────────────────────────────────────────────────────────
POST=0
if [ "${SKIP_PREFLIGHT:-}" != "1" ] && [ -f "$PREFLIGHT" ]; then
  echo ""
  "$PYTHON" "$PREFLIGHT" --root "$HERE" --output || POST=$?
fi

t1=$(date +%s%N)
echo "════════ 完成，用时 $(( (t1 - t0) / 1000000 )) ms ════════"
if [ $POST -ne 0 ]; then
  echo "🔴 后检未通过：成品有问题，别发印"
  exit 1
fi
exit 0
