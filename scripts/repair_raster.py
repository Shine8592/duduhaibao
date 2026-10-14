#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repair_raster.py — 成品海报栅格修订工具箱 (duduhaibao v4.1.0)

把 references/raster-text-repair.md 的流程做成可直接调用的工具，
免得每次现场重写脚本、把坑再踩一遍。

子命令
  probe   墨迹行投影 → 文本条带表 + 文字/插画分界列 X_SPLIT
  bg      量卡片内部底色剖面，判"平铺"还是"复制"
  erase   用逐行底色剖面清空一块矩形（诚实的填充）
  rules   逐行找结构线（分隔线/横线）—— 步长 5 会跳过 1px 发丝线
  bands   块级编辑：搬移/删除整条带，还原插画列并回叠墨迹
  verify  证明改动 + 证明克制（改动像素 / 目标区外像素）

编码成硬性守卫的坑（每条都来自 references/raster-text-repair.md）：
  * 单一亮度助手 lum() → 消灭 mean(axis=) 行/块混淆
  * 底色只能采卡片内部：同时拒绝文字与插画；贴边条带会被检出并告警
  * 逐行剖面 + 插值 + 平滑；不固定条带、不平铺（34px 条带铺 46px 必留缝）
  * "还原插画列"与"回叠墨迹"必须是两遍独立 pass
  * 回叠只对"文字确实越过分界"的条带生效 —— 用墨迹计数判定，不靠肉眼
  * 回叠遮罩逐像素判明暗：源像素比当前位置深才覆盖
  * 校验行必须在最终图上干净，不能在原图节奏上取

依赖：numpy + PIL。cv2 仅 glyph 路径需要（可选）。
"""
import argparse
import sys
import numpy as np
from PIL import Image


def load(path):
    return np.array(Image.open(path).convert('RGB'), dtype=np.float64)


def lum(arr):
    """逐像素亮度。对 (N,3) 单行、(M,N,3) 块、(H,W,3) 全图都成立。
    这是唯一一处算亮度的地方 —— 消灭 axis 混淆。"""
    a = arr[..., :3]
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def region(s):
    v = [int(t) for t in s.replace(':', ',').split(',')]
    if len(v) != 4:
        raise argparse.ArgumentTypeError('区域格式 x0,y0,x1,y1')
    return tuple(v)


def bg_profile(a, y0, y1, sx0, sx1, ink=205, need=20, smooth=11):
    """逐行底色剖面：每行取"亮度越过墨迹阈值"的像素中值（自动排除文字+插画），
    全墨迹行插值，再平滑。复现卡片真实竖向渐变，误差 ~1-2 级。"""
    n = y1 - y0
    p = np.full((n, 3), np.nan)
    for i, y in enumerate(range(y0, y1)):
        row = a[y, sx0:sx1]
        good = row[lum(row) > ink]
        if len(good) >= need:
            p[i] = np.median(good, axis=0)
    idx = np.arange(n)
    for c in range(3):
        v = p[:, c]
        ok = ~np.isnan(v)
        if ok.sum() < 2:
            raise SystemExit('底色采样失败：参考窗 x%d:%d 内几乎没有干净像素' % (sx0, sx1))
        v[~ok] = np.interp(idx[~ok], idx[ok], v[ok])
        pad = np.r_[np.full(smooth, v[0]), v, np.full(smooth, v[-1])]
        p[:, c] = np.convolve(pad, np.ones(smooth) / smooth, 'same')[smooth:-smooth]
    return p


def guard_sample(a, y0, y1, sx0, sx1, wide=(0, None)):
    """采样条带自检：与更宽的卡内参考窗对比，差异大 = 采到边缘高光或插画。"""
    prof = bg_profile(a, y0, y1, sx0, sx1)
    wx0, wx1 = wide
    if wx1 is None:
        wx1 = a.shape[1]
        wx0 = min(sx0, 660) if sx0 > 200 else 100
    try:
        big = bg_profile(a, y0, y1, wx0, wx1)
        d = np.abs(prof - big).mean()
        if d > 5:
            print('  ⚠ 采样窗 x%d:%d 与宽窗 x%d:%d 平均差 %.1f 级 —— '
                  '可能采到了边框内侧高光带或插画，请换窗'
                  % (sx0, sx1, wx0, wx1, d))
        else:
            print('  ✓ 采样窗自检通过（与宽窗差 %.1f 级）' % d)
    except SystemExit:
        pass
    return prof


def cmd_probe(args):
    a = load(args.image)
    x0, y0, x1, y1 = args.region
    L = lum(a[y0:y1, x0:x1])
    rows = (L < args.ink).sum(axis=1)
    runs, s = [], None
    for i, v in enumerate(rows):
        if v > 0 and s is None:
            s = i
        elif v == 0 and s is not None:
            runs.append([s, i]); s = None
    if s is not None:
        runs.append([s, len(rows)])
    bands = []
    for r in runs:
        if bands and r[0] - bands[-1][1] < args.min_gap:
            bands[-1][1] = r[1]
        else:
            bands.append(r)
    bands = [b for b in bands if b[1] - b[0] >= args.min_height]
    if not bands:
        print('区域内未找到墨迹条带（阈值 %d）' % args.ink); return
    med = float(np.median([b[1] - b[0] for b in bands])) if bands else 0
    if any((b[1] - b[0]) > max(3 * med, 60) for b in bands):
        print('  ⚠ 有条带高度远超中位数（%.0f px）—— 行间空隙被填满，条带粘连。\n'
              '    先看下面两行：左/右边界列若几乎整列有墨，那是卡片虚线边框或竖分隔线，\n'
              '    它会把所有行连成一块 —— 把区域收窄到边框内侧重跑。' % med)
    # 边界列自检：卡片虚线边框 / 竖分隔线会让某整列几乎全有墨
    Lall = lum(a[y0:y1, x0:x1]) < args.ink
    for side, cols in (('左', range(0, min(10, Lall.shape[1]))),
                       ('右', range(max(0, Lall.shape[1] - 10), Lall.shape[1]))):
        hit = [int(Lall[:, c].sum()) for c in cols]
        if hit and max(hit) > 0.8 * Lall.shape[0]:
            print('  ⚠ %s边界列 x=%d 有 %d/%d 行有墨 —— 看起来是卡片虚线边框/竖分隔线，'
                  '不是文字。把区域收窄到它内侧。'
                  % (side, x0 + (cols[0] + int(np.argmax(hit))), max(hit), Lall.shape[0]))
    print('区域 x%d~%d y%d~%d   条带 %d 个  (阈值 lum<%d)' % (x0, x1, y0, y1, len(bands), args.ink))
    print('  #   y0    y1    中心  高   墨迹px  文字最右x')
    smax = 0
    for i, (b0, b1) in enumerate(bands):
        sub = L[b0:b1]
        mx = int(np.nonzero((sub < args.ink).any(axis=0))[0].max()) + x0
        smax = max(smax, mx)
        print('  %-3d %-5d %-5d %-5d %-4d %-7d %d' %
              (i + 1, b0 + y0, b1 + y0, (b0 + b1) // 2 + y0, b1 - b0,
               int((sub < args.ink).sum()), mx))
    cs = [(bands[i][0] + bands[i][1]) // 2 + y0 for i in range(len(bands))]
    if len(cs) > 1:
        print('  中心序列 %s   节距 %s'
              % (cs, [cs[i + 1] - cs[i] for i in range(len(cs) - 1)]))
    print('  → X_SPLIT 建议 ≈ %d（所有条带文字最右；再往右是插画）' % (smax + 1))


def cmd_bg(args):
    a = load(args.image)
    x0, y0, x1, y1 = args.region
    sx0, sx1 = args.sample_x
    print('卡片底色剖面 x%d:%d  y%d~%d' % (sx0, sx1, y0, y1))
    prof = guard_sample(a, y0, y1, sx0, sx1)
    print('  剖面均值 %s' % prof.mean(axis=0).round(1))
    print('  剖面极差 %.1f 级（卡片真实竖向渐变）'
          % float((prof.max(axis=0) - prof.min(axis=0)).max()))
    jit = float(np.abs(np.diff(prof, axis=0)).mean())
    print('  相邻行抖动 %.2f 级' % jit)
    # 独立第二法：干净行间带 std
    d = a[y0:y1, sx0:sx1]
    g = d[lum(d) > 205]
    print('  干净像素 std = %s  → %s'
          % (g.std(axis=0).round(2),
             '底近乎纯色，可平铺/单色填充' if g.std() < 5 else
             '底有纹理，用逐行剖面（勿平铺）'))


def cmd_erase(args):
    a = load(args.image)
    x0, y0, x1, y1 = args.region
    sx0, sx1 = args.sample_x
    prof = bg_profile(a, y0, y1, sx0, sx1)
    for y in range(y0, y1):
        a[y, x0:x1] = prof[y - y0]
    Image.fromarray(a.astype(np.uint8)).save(args.out)
    print('已清空 x%d:%d y%d:%d → %s' % (x0, x1, y0, y1, args.out))


def cmd_bands(args):
    base = load(args.image)
    a = base.copy()
    x0, y0, x1, y1 = args.area
    src = [int(v) for v in args.src.split(',')]
    H = args.band_h
    if args.dst:
        dst = [int(v) for v in args.dst.split(',')]
    else:
        c0, c1 = src[0] + H / 2, src[-1] + H / 2
        n = args.count
        dst = [int(round(c0 + i * (c1 - c0) / (n - 1) - H / 2)) for i in range(n)]
        print('  自动均分：首末条带中心保持 %d / %d，均分 %d 条' % (c0, c1, n))
    if args.dst and len(dst) != args.count:
        pass
    sx0, sx1 = args.sample_x
    deco = args.deco

    # ---- pass 1: 快照条带 → 整块填底 → 还原插画列 ----
    bands = [base[s:s + H, x0:x1].copy() for s in src]
    prof = bg_profile(base, y0, y1, sx0, sx1)
    for y in range(y0, y1):
        a[y, x0:x1] = prof[y - y0]
    if deco:
        a[y0:y1, deco[0]:deco[1]] = base[y0:y1, deco[0]:deco[1]]
        print('  插画列 x%d:%d 已从原图还原（pass 1）' % (deco[0], deco[1]))
    for d, b in zip(dst, bands):
        a[d:d + H, x0:x1] = b
    if deco:
        a[y0:y1, deco[0]:deco[1]] = base[y0:y1, deco[0]:deco[1]]

    # ---- pass 2: 只对"文字确实越过分界"的条带回叠墨迹 ----
    # 分开的 pass —— 还原绝不能因为"不需回叠"而被跳过
    if deco:
        probe0 = deco[0] - args.cross_w
        for s, d in zip(src, dst):
            sub = base[s:s + H, probe0:deco[0]]
            n_ink = int((lum(sub) < args.ink).sum())
            if n_ink <= args.cross_min:
                print('  条带 y%d→%d：分界左侧仅 %d 墨迹像素（≤%d），跳过回叠'
                      % (s, d, n_ink, args.cross_min))
                continue
            for y in range(d, d + H):
                seg = a[y, deco[0]:deco[1]].copy()
                srow = base[y + (s - d), deco[0]:deco[1]]
                ls, lg = lum(srow), lum(seg)
                ap = (ls < args.ink) & (ls < lg - 4)   # 源更深才覆盖
                seg[ap] = srow[ap]
                a[y, deco[0]:deco[1]] = seg
            print('  条带 y%d→%d：已回叠墨迹（%d 像素越过分界）' % (s, d, n_ink))

    Image.fromarray(a.astype(np.uint8)).save(args.out)
    print('已写出', args.out)

    # 自证：每条带源 vs 新的墨迹缺口 —— 只在【文字列】内量，
    # 插画列（deco 起）本来就该保留原位置的插画，拿它算缺口是假警报
    gx1 = deco[0] if deco else x1
    fin = load(args.out)
    for s, d in zip(src, dst):
        si = lum(base[s:s + H, x0:gx1]) < 175
        sn = lum(fin[d:d + H, x0:gx1]) < 175
        gap = int((si & ~sn).sum())
        flag = 'OK' if gap < 40 else '⚠ 缺口偏大：检查回叠阈值/是否该回叠'
        print('  条带 y%d→%d  文字列(x%d~%d) 源墨迹%5d 新%5d 缺%3d  %s'
              % (s, d, x0, gx1, int(si.sum()), int(sn.sum()), gap, flag))


def cmd_rules(args):
    """逐行找结构线（分隔线/横线）。必须逐行 —— 步长 5 会跳过 1px 的发丝线。"""
    a = load(args.image)
    x0, y0, x1, y1 = args.region
    bx0, bx1 = args.blank_x if args.blank_x else (x0, x1)
    tx0, tx1 = args.text_x if args.text_x else (x0, x1)
    prof = np.array([np.median(lum(a[y, bx0:bx1])) for y in range(y0, y1)])
    k = args.win
    base = np.array([np.median(prof[max(0, i - k):i + k + 1]) for i in range(len(prof))])
    dep = base - prof
    groups = []
    for i in range(len(dep)):
        if dep[i] > args.min_depth:
            if groups and i - groups[-1][-1] <= 1:
                groups[-1].append(i)
            else:
                groups.append([i])
    print('逐行扫描 y%d~%d   空白参考列 x%d:%d   阈值 >%.1f 级'
          % (y0, y1, bx0, bx1, args.min_depth))
    if not groups:
        print('  未发现结构线（仅在本 x 窗 + 步长 1 下成立，换窗再确认）')
        return
    print('  #   y    深(级)   文字列深  比    判定')
    cs = []
    for g in groups:
        y = y0 + int(np.mean(g))
        d_blank = float(np.median([dep[i] for i in g]))
        d_text = float(base[y - y0] - np.median(lum(a[y, tx0:tx1])))
        ratio = d_blank / d_text if d_text else float('nan')
        cs.append(y)
        print('  %-3d %-5d %-8.1f %-9.1f %-5.2f  %s'
              % (len(cs), y, d_blank, d_text, ratio,
                 '结构线' if ratio > 0.6 else '疑 JPEG 振铃'))
    if len(cs) > 1:
        print('  节距: %s' % [cs[i + 1] - cs[i] for i in range(len(cs) - 1)])
    print('  提醒：填充会把这些线一并抹掉 —— 要么按新行距与实测权重重画，'
          '要么明说这一块现在无线。五倍粗比没有更糟，没有比不匹配更糟。')


def cmd_verify(args):
    o = load(args.original)
    f = load(args.final)
    if o.shape != f.shape:
        raise SystemExit('尺寸不同 %s vs %s' % (o.shape, f.shape))
    d = np.abs(o - f).sum(axis=2)
    ch = d > 40
    tot = d.size
    m = np.zeros_like(ch)
    print('尺寸 %dx%d  总像素 %d' % (f.shape[1], f.shape[0], tot))
    for spec in args.region:
        name, r = spec.split(':', 1)
        x0, y0, x1, y1 = region(r)
        m[y0:y1, x0:x1] = True
        print('  %-16s 改 %7d px' % (name, int(ch[y0:y1, x0:x1].sum())))
    out = ch & ~m
    print('  变化合计 %d = %.3f%%' % (int(ch.sum()), ch.sum() / tot * 100))
    print('  ★ 目标区外 %d px = %.4f%%' % (int(out.sum()), out.sum() / tot * 100))
    if out.sum():
        ys, xs = np.nonzero(out)
        print('    范围 x%d~%d y%d~%d（正常来源：擦字/描边的抗锯齿外溢）'
              % (xs.min(), xs.max(), ys.min(), ys.max()))
    if args.clean_rows:
        x0, y0, x1, y1 = args.clean_rows
        print('  填充区校验（自动跳过最终图上有文字的行）：')
        e, n = [], 0
        for y in range(y0, y1):
            rowf = f[y, x0:x1]
            # 文档铁律：校验行必须在【最终图】上干净 —— 取到新画的字会报
            # 一个完全属于新文字的假误差，把正确的填充"修"第二遍
            if (lum(rowf) > 205).mean() < 0.9:
                continue
            rowo = o[y, x0:x1]
            go = rowo[lum(rowo) > 205]
            if len(go) < 30:
                continue
            e.append(float(np.abs(rowf.mean(axis=0) - np.median(go, axis=0)).max()))
            n += 1
        if not n:
            print('    区间内没有同时在两图上都干净的行 —— 请把范围指到行间空白带')
        else:
            print('    用 %d 个干净行  |最终−原底| 平均 %.2f 最大 %.1f 级  → %s'
                  % (n, np.mean(e), max(e),
                     '不可见' if max(e) <= 3 else
                     ('轻微，可接受' if max(e) <= 6 else '需复查')))


def main():
    ap = argparse.ArgumentParser(description='成品海报栅格修订工具箱')
    sub = ap.add_subparsers(dest='cmd', required=True)

    for name, fn, helptext in [('probe', cmd_probe, '墨迹行投影 → 条带表 + X_SPLIT'),
                               ('bg', cmd_bg, '量卡片内部底色剖面'),
                               ('erase', cmd_erase, '用逐行剖面清空矩形'),
                               ('rules', cmd_rules, '逐行找结构线（分隔线/横线）'),
                               ('bands', cmd_bands, '块级编辑：搬移/删除条带'),
                               ('verify', cmd_verify, '证明改动 + 证明克制')]:
        p = sub.add_parser(name, help=helptext)
        p.set_defaults(fn=fn)

    p = sub.choices['probe']
    p.add_argument('image'); p.add_argument('--region', type=region, required=True)
    p.add_argument('--ink', type=int, default=150)
    p.add_argument('--min-gap', type=int, default=6)
    p.add_argument('--min-height', type=int, default=8)

    p = sub.choices['bg']
    p.add_argument('image'); p.add_argument('--region', type=region, required=True)
    p.add_argument('--sample-x', type=lambda s: [int(v) for v in s.split(',')], required=True)

    p = sub.choices['erase']
    p.add_argument('image'); p.add_argument('out')
    p.add_argument('--region', type=region, required=True)
    p.add_argument('--sample-x', type=lambda s: [int(v) for v in s.split(',')], required=True)

    p = sub.choices['rules']
    p.add_argument('image'); p.add_argument('--region', type=region, required=True,
                   help='待查的行范围；x 用整张卡宽度')
    p.add_argument('--blank-x', type=lambda s: [int(v) for v in s.split(',')],
                   help='无文字空白列范围（分开结构线与 JPEG 振铃的关键）')
    p.add_argument('--text-x', type=lambda s: [int(v) for v in s.split(',')],
                   help='文字列范围，用于比对')
    p.add_argument('--min-depth', type=float, default=6.0)
    p.add_argument('--win', type=int, default=6, help='基准窗半宽')

    p = sub.choices['bands']
    p.add_argument('image'); p.add_argument('out')
    p.add_argument('--area', type=region, required=True, help='填充块 x0,y0,x1,y1')
    p.add_argument('--sample-x', type=lambda s: [int(v) for v in s.split(',')], required=True)
    p.add_argument('--deco', type=lambda s: [int(v) for v in s.split(',')],
                   help='插画列 S,E：从原图还原并回叠墨迹')
    p.add_argument('--src', required=True, help='源条带 y，逗号分隔')
    p.add_argument('--dst', help='目标条带 y；省略则按 --count 在首末中心间均分')
    p.add_argument('--count', type=int, help='结果条带数（配 --dst 省略时用）')
    p.add_argument('--band-h', type=int, default=56)
    p.add_argument('--ink', type=int, default=150, help='墨迹亮度阈值（文字远深于插画）')
    p.add_argument('--cross-w', type=int, default=20, help='分界左侧探针宽度')
    p.add_argument('--cross-min', type=int, default=20, help='墨迹数超此值才回叠')

    p = sub.choices['verify']
    p.add_argument('original'); p.add_argument('final')
    p.add_argument('--region', action='append', default=[],
                   help='name:x0,y0,x1,y1，可重复')
    p.add_argument('--clean-rows', type=region, help='填充区抽样 x0,y0,x1,y1')

    args = ap.parse_args()
    if args.cmd == 'bands' and not args.dst and not args.count:
        raise SystemExit('bands：需给 --dst 或 --count')
    args.fn(args)


if __name__ == '__main__':
    main()
