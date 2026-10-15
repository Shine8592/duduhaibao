#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════════
#  Releases 备份 / 还原
#
#  为什么需要：**git 里只有提交和 tag，Release 页（标题 + 正文）不在 git 里。**
#  删库重建会丢掉全部 Release 说明 —— 2026-10-14 本项目就踩过一次，只能从会话
#  记录里抢救。有这份备份，重建后一条命令就能还原。
#
#  用法：
#    python scripts/backup_releases.py export  [-o releases-backup.json]
#    python scripts/backup_releases.py restore [-i releases-backup.json] [--dry-run]
#
#  环境变量：GITHUB_TOKEN（export/restore 都需要）
# ═══════════════════════════════════════════════════════════════════

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_REPO = "Shine8592/duduhaibao"
DEFAULT_FILE = "releases-backup.json"
API = "https://api.github.com"


def api(repo, method, path, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(f"{API}/repos/{repo}{path}", data=data, method=method)
    tok = os.environ.get("GITHUB_TOKEN", "").strip()
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "duduhaibao-backup")
    if data:
        req.add_header("Content-Type", "application/json")
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req) as r:
        b = r.read().decode("utf-8")
        return json.loads(b) if b.strip() else {}


def do_export(repo, out):
    rels = api(repo, "GET", "/releases?per_page=100")
    if not rels:
        print("没有 Release 可备份")
        return 1
    data = {
        "_note": "Release 备份：git 里没有 Release 页，删库重建会丢，故单独备份。",
        "_repo": repo,
        "_exported": datetime.datetime.now().isoformat(timespec="seconds"),
        "releases": [
            {
                "tag": r["tag_name"],
                "name": r["name"],
                "body": r["body"],
                "prerelease": r["prerelease"],
                "published_at": r["published_at"],
            }
            for r in rels
        ],
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已备份 {len(rels)} 个 Release → {out}")
    for r in data["releases"]:
        print(f"  {r['tag']:<9} {len(r['body'] or ''):>5}字  {(r['name'] or '')[:50]}")
    return 0


def do_restore(repo, src, dry):
    data = json.load(open(src, encoding="utf-8"))
    rels = data.get("releases", [])
    existing = {}
    for r in api(repo, "GET", "/releases?per_page=100"):
        existing[r["tag_name"]] = r
    print(f"备份含 {len(rels)} 个 Release；远端已有 {len(existing)} 个")
    ok = 0
    for r in rels:
        tag, name, body = r["tag"], r.get("name") or tag, r.get("body") or ""
        act = "更新" if tag in existing else "新建"
        if dry:
            print(f"  [dry] {act} {tag}  {len(body)}字")
            continue
        try:
            if tag in existing:
                api(repo, "PATCH", f"/releases/{existing[tag]['id']}",
                    {"name": name, "body": body})
            else:
                api(repo, "POST", "/releases",
                    {"tag_name": tag, "name": name, "body": body,
                     "prerelease": r.get("prerelease", False)})
            print(f"  ✅ {act} {tag}")
            ok += 1
        except urllib.error.HTTPError as e:
            print(f"  ✗ {act} {tag} 失败：HTTP {e.code} {e.read().decode()[:120]}")
    print(f"\n完成 {ok}/{len(rels)}。"
          + ("（dry-run，未改动）" if dry else "标签必须在仓库里已存在，否则新建会失败。"))
    return 0


def main():
    ap = argparse.ArgumentParser(description="GitHub Releases 备份 / 还原")
    ap.add_argument("action", choices=["export", "restore"])
    ap.add_argument("-o", "--out", default=DEFAULT_FILE)
    ap.add_argument("-i", "--in", dest="src", default=DEFAULT_FILE)
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.action == "export":
        return do_export(a.repo, a.out)
    return do_restore(a.repo, a.src, a.dry_run)


if __name__ == "__main__":
    sys.exit(main())
