#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  公开仓库泄漏扫描 —— 发布前去标识化流程的最后一道闸
#
#  为什么需要它：一轮只查中文业务词的扫描漏掉了英文措辞
#  「the user's real series ... carries client material」，
#  它既暴露了本机私有路径，又暴露了私有材料的存在。
#  **规则不够狠 = 等于没扫。**
#
#  用法：bash audit_public_release.sh [目录]
#  说明：这是「标记待人工复核」的工具，不是自动判定器 ——
#        它一定会误报（用户名在 clone URL 里、~/.hermes 是文档化安装路径），
#        目的只是让你逐条看一眼，而不是替你做决定。
# ═══════════════════════════════════════════════════════════════════
set -uo pipefail
DIR="${1:-.}"
cd "$DIR"
HIT=0

EXCL='--exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=out --exclude-dir=node_modules'

scan() {  # 描述  正则
  local desc="$1" pat="$2" r n
  r=$(grep -rn $EXCL -E "$pat" . 2>/dev/null \
        | grep -v "$(basename "${BASH_SOURCE[0]}")")
  if [ -n "$r" ]; then
    HIT=1
    printf "\n  [!] %s\n" "$desc"
    echo "$r" | head -8 | sed 's/^/       /'
    n=$(echo "$r" | wc -l)
    [ "$n" -gt 8 ] && echo "       ...还有 $((n-8)) 处"
  fi
}

echo "════════ 公开仓库泄漏扫描 ════════"

if [ -n "${AUDIT_CLIENT_TERMS:-}" ]; then
  echo
echo "── ① 客户业务词（用 AUDIT_CLIENT_TERMS 传，逗号分隔）──"
  scan "客户业务词" "$AUDIT_CLIENT_TERMS"
fi

echo
echo "── ② 身份 / 账号标识 ──"
scan "其他项目名" "cyber-nyx|Moltbook|duduppt|internal-agent"

echo
echo "── ③ 本机路径 / 环境（最易漏）──"
scan "绝对路径"       "/(root|home|Users|opt|srv)/[a-zA-Z0-9_.-]"
scan "本机缓存路径"   "\\.cache/|ms-playwright|img-env|\\.hermes"
scan "内网 / 本机服务" "localhost|127\\.0\\.0\\.1|192\\.168\\.|\\.internal"

echo
echo "── ④ 内部 / 私有措辞（英文，最常被漏掉的一类）──"
scan "私有措辞" "client material|private pipeline|internal only|do not publish|confidential|proprietary"
scan "内部引用" "the user's real|real series|the private copy|production secrets"

echo
echo "── ⑤ 凭据 ──"
scan "密钥"   "ghp_|gho_|ghs_|sk-[A-Za-z0-9]|AKIA|BEGIN [A-Z ]*PRIVATE KEY"
scan "口令"   "password\\s*[:=]|passwd|api[_-]?key\\s*[:=]|secret\\s*[:=]"
scan "手机/身份证" "1[3-9][0-9]{9}|[0-9]{17}[0-9Xx]"

echo
echo "── ⑥ 个人邮箱（放行 noreply 与示例域）──"
e=$(grep -rn $EXCL -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-z]{2,}" . 2>/dev/null \
     | grep -v "$(basename "${BASH_SOURCE[0]}")" \
     | grep -vE "users\\.noreply\\.github\\.com|example\\.(com|org)|noreply")
if [ -n "$e" ]; then HIT=1; echo "$e" | sed 's/^/  [!] /'; fi

echo
if [ $HIT -eq 0 ]; then
  echo "  OK  全部规则通过"
  exit 0
fi
echo "  [!] 发现潜在泄漏 —— 逐条人工确认后再发布"
echo "      （用户名在 clone URL 里、~/.hermes 是文档化安装路径，这类属正常误报）"
exit 1
