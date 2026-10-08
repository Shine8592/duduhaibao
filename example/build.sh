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
#          ./build.sh banner       只渲染易拉宝版
#          ./build.sh all --force  预检报错也强制渲染
#
#  依赖：  typst >= 0.13           https://typst.app
#          python3 + pillow        pip install pillow
#
#  环境变量：
#          PYTHON   指定 python 解释器（默认 python3）
#                   例：PYTHON=/opt/venv/bin/python ./build.sh
#          SKIP_PREFLIGHT=1       跳过预检
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
mkdir -p out

ONLY="${1:-all}"
FORCE="${2:-}"
PYTHON="${PYTHON:-python3}"
PREFLIGHT="$HERE/../scripts/preflight.py"

if ! command -v typst >/dev/null 2>&1; then
  echo "🔴 找不到 typst。安装见 https://typst.app"
  echo "   （macOS: brew install typst ｜ Rust: cargo install typst-cli）"
  exit 1
fi

echo "════════ 活动海报渲染 ════════"

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
  typst compile --root . --format png --ppi "$ppi" "$t" "out/$n.png"
  typst compile --root . "$t" "out/$n.pdf"
  echo "  ✅ $n  —  $desc"
}

if [ "$ONLY" = "all" ] || [ "$ONLY" = "a4" ]; then
  render poster-a4      templates/poster-a4.typ      300 "A4 打印版   2480x3508px (210x297mm)"
fi
if [ "$ONLY" = "all" ] || [ "$ONLY" = "social" ]; then
  render poster-social  templates/poster-social.typ  192 "朋友圈版    2160x2880px (3:4)"
fi
if [ "$ONLY" = "all" ] || [ "$ONLY" = "banner" ]; then
  render poster-banner  templates/poster-banner.typ  100 "易拉宝版    3150x7874px (80x200cm)"
fi

# ─────────────────────────────────────────────────────────────────
#  预览图（聊天/网页里看，不用下大图）
# ─────────────────────────────────────────────────────────────────
"$PYTHON" - "$ONLY" <<'PY'
import sys, os
from PIL import Image
only = sys.argv[1] if len(sys.argv) > 1 else "all"
names = [n for n in ("poster-a4", "poster-social", "poster-banner")
         if only == "all" or only == n.replace("poster-", "")]
for n in names:
    p = f"out/{n}.png"
    if not os.path.exists(p):
        continue
    im = Image.open(p)
    if im.mode in ("RGBA", "LA", "P"):
        a = im.convert("RGBA"); bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(a, mask=a.split()[-1]); im = bg
    else:
        im = im.convert("RGB")
    w, h = im.size
    k = min(1.0, 1400 / max(w, h))          # 预览最长边 1400
    pv = im.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
    pv.save(f"out/{n}_preview.jpg", quality=93)
    print(f"  ✅ {n}_preview.jpg  {pv.size[0]}x{pv.size[1]}  (原图 {w}x{h})")
PY

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
