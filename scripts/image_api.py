#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生图 / 改图的统一 API 封装（duduhaibao 4.4.0）。

模型由供应商 yaner 提供，挂在 OpenAI-compatible 端点 `token.yaner.fun/v1`：

    cn:hunyuan-image-alpha        文生图  (text -> image)
    cn:hunyuan-image-alpha-edit   图生图  (text+image -> image, 改图/修图)

两端都走 `POST /images/generations`，返回 `data[0].url`（远程图片，需下载）。
图生图额外接受 `image`: <base64> 字段；实测该字段会被消费（把纯绿底图改成紫色，
输出中心像素确为紫色），不是被忽略的占位参数。

设计原则：
  - 只依赖标准库（urllib），不引入 requests —— 与技能「零额外依赖」一致。
  - 密钥只从环境变量读，绝不硬编码、绝不写进公开仓库。
  - 每次调用落一行成本记录（JSONL），供「免费额度用尽就停」的判断与交付回显。
  - 失败不静默：HTTP 非 200 / 无 url / 下载失败一律抛异常。
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# ── .env 兜底加载 ──
# Hermes 的 gateway 进程不加载 ~/.hermes/.env（实测进程环境里一个 API key 都没有），
# 只把 .env 当工具运行时配置，不会 export 给子进程。所以技能脚本直接读 os.environ
# 会拿不到 key —— 症状是脚本报「缺 key」而 .env 里明明写着。
# 这里做兜底：仅在环境变量缺失时读文件，已存在的环境变量一律不覆盖。
def _load_env_fallback():
    if os.environ.get("DUDUHAIBAO_IMAGE_KEY") or os.environ.get("YANER_API_KEY"):
        return
    env_path = Path.home() / ".hermes" / ".env"
    if not env_path.is_file():
        return
    try:
        text = env_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


_load_env_fallback()

# ── 端点与模型（可用环境变量覆盖，便于换供应商 / 灰度）──
API_BASE = os.environ.get("DUDUHAIBAO_IMAGE_API", "https://token.yaner.fun/v1")
API_KEY = os.environ.get("DUDUHAIBAO_IMAGE_KEY") or os.environ.get("YANER_API_KEY") or ""
T2I_MODEL = os.environ.get("DUDUHAIBAO_T2I_MODEL", "cn:hunyuan-image-alpha")
I2I_MODEL = os.environ.get("DUDUHAIBAO_I2I_MODEL", "cn:hunyuan-image-alpha-edit")
# 兼容旧后端（需求书 4.3.1 用的 Agnes 2.5 flash）
AGNES_BASE = os.environ.get("AGNES_API_BASE", "https://apihub.agnes-ai.com/v1")
AGNES_KEY = os.environ.get("AGNES_API_KEY", "")
AGNES_MODEL = os.environ.get("AGNES_MODEL", "agnes-image-2.5-flash")

COST_LOG = Path(os.environ.get("DUDUHAIBAO_COST_LOG", "image_cost.jsonl"))
TIMEOUT = 180


def _opener():
    # 不走系统代理（与项目其它脚本一致）
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _post_json(url, payload, key, timeout=TIMEOUT):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "User-Agent": "duduhaibao-image/4.4.0"})
    with _opener().open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _download(url, timeout=TIMEOUT):
    with _opener().open(urllib.request.Request(url, headers={"User-Agent": "duduhaibao-image/4.4.0"}),
                        timeout=timeout) as r:
        return r.read()


def _log_cost(kind, model, ok, elapsed, credit=None, note=""):
    """每次调用落一行 JSONL —— 供成本回显与额度判断。只记元数据，不记图片内容。"""
    rec = {"ts": datetime.now().isoformat(timespec="seconds"),
           "kind": kind, "model": model, "ok": bool(ok),
           "elapsed_s": round(elapsed, 2)}
    if credit is not None:
        rec["credit"] = credit
    if note:
        rec["note"] = note
    try:
        COST_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(COST_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[warn] 成本记录写入失败: {e}", file=sys.stderr)
    return rec


def _extract_url(resp):
    data = resp.get("data") or []
    if not data or not isinstance(data[0], dict) or not data[0].get("url"):
        raise RuntimeError("生图响应缺少 data[0].url: " + json.dumps(resp, ensure_ascii=False)[:300])
    return data[0]["url"], (resp.get("usage") or {}).get("credit")


def generate(prompt, out_path, size="1024x1024", backend="hunyuan", seed=None):
    """文生图。返回成本记录 dict。

    backend:
      hunyuan —— cn:hunyuan-image-alpha（默认）
      agnes   —— agnes-image-2.5-flash（4.3.1 旧 recipe，保留可回退）
    """
    t0 = time.time()
    ok = False
    credit = None
    try:
        if backend == "agnes":
            key, base, model = AGNES_KEY, AGNES_BASE, AGNES_MODEL
            if not key:
                raise RuntimeError("backend=agnes 需要 AGNES_API_KEY 环境变量")
        else:
            key, base, model = API_KEY, API_BASE, T2I_MODEL
            if not key:
                raise RuntimeError("需要 DUDUHAIBAO_IMAGE_KEY 或 YANER_API_KEY 环境变量")
        payload = {"model": model, "prompt": prompt, "n": 1, "size": size}
        if seed is not None:
            payload["seed"] = int(seed)
        resp = _post_json(base.rstrip("/") + "/images/generations", payload, key)
        url, credit = _extract_url(resp)
        data = _download(url)
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(data)
        ok = True
        return {"out": str(out_path), "backend": backend, "model": model,
                "bytes": len(data), "url_host": url.split("/")[2] if "/" in url else "?"}
    finally:
        _log_cost("t2i", (locals().get("model") or T2I_MODEL), ok, time.time() - t0,
                  credit, note=f"backend={backend} size={size}")


def edit(prompt, image_bytes, out_path, size="1024x1024", seed=None):
    """图生图 / 改图 / 修图（画面语义级）。

    ⚠️ 边界：本函数负责「画面重绘」—— 照片艺术化、底稿风格化、去 AI 水印、
       局部重绘、插画微调。**改成品海报上的错字 / 日期 / 流程请走 repair_raster.py**，
       生图模型画中文字形不可靠（必乱码），文字须由能保证字形正确的层来渲染。
       （成品海报的文字照常由排版层叠加，不受此限。）

    image_bytes: 输入图片的原始字节（PNG/JPG 均可）。
    """
    t0 = time.time()
    ok = False
    credit = None
    try:
        if not API_KEY:
            raise RuntimeError("需要 DUDUHAIBAO_IMAGE_KEY 或 YANER_API_KEY 环境变量")
        b64 = base64.b64encode(image_bytes).decode("ascii")
        payload = {"model": I2I_MODEL, "prompt": prompt, "n": 1,
                   "size": size, "image": b64}
        if seed is not None:
            payload["seed"] = int(seed)
        resp = _post_json(API_BASE.rstrip("/") + "/images/generations", payload, API_KEY)
        url, credit = _extract_url(resp)
        data = _download(url)
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(data)
        ok = True
        return {"out": str(out_path), "model": I2I_MODEL, "bytes": len(data),
                "input_bytes": len(image_bytes)}
    finally:
        _log_cost("i2i", I2I_MODEL, ok, time.time() - t0, credit,
                  note=f"in={len(image_bytes)}B size={size}")


def list_models():
    """GET /models，返回可用模型 id 列表（供 doctor.py 自检）。"""
    if not API_KEY:
        return []
    req = urllib.request.Request(API_BASE.rstrip("/") + "/models",
                                 headers={"Authorization": "Bearer " + API_KEY,
                                          "User-Agent": "duduhaibao-image/4.4.0"})
    with _opener().open(req, timeout=30) as r:
        d = json.loads(r.read().decode("utf-8", "replace"))
    return [m.get("id") for m in d.get("data", [])]


def cost_summary():
    """汇总成本日志，供交付消息回显：调用次数 / 成功 / 总耗时。"""
    if not COST_LOG.exists():
        return {"calls": 0, "ok": 0, "t2i": 0, "i2i": 0, "elapsed_s": 0}
    recs = [json.loads(l) for l in COST_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {"calls": len(recs),
            "ok": sum(1 for r in recs if r.get("ok")),
            "t2i": sum(1 for r in recs if r.get("kind") == "t2i"),
            "i2i": sum(1 for r in recs if r.get("kind") == "i2i"),
            "elapsed_s": round(sum(r.get("elapsed_s", 0) for r in recs), 1)}
