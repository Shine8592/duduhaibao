#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML -> print-ready PNG + PDF, without a browser.

Why not headless Chromium: it is a ~170 MB download and a second toolchain to keep
alive. WeasyPrint renders the same absolutely-positioned HTML to PDF in-process, and
PyMuPDF rasterizes that PDF at an exact DPI -- so the PNG dimensions are deterministic
(A4 @300 dpi is 2480x3508, every time) rather than dependent on a viewport guess.

Interpreter: this needs `weasyprint` + `pymupdf`, which usually live in a dedicated
venv, NOT the system python. Run it with that interpreter (e.g.
`/path/to/venv/bin/python render_html_to_png.py ...`). The script fails loudly with
the pip line if either import is missing.

System libs WeasyPrint needs: libpango-1.0-0, libpangoft2-1.0-0, libcairo2,
libgdk-pixbuf-2.0-0. Check with `python -c "import weasyprint"` before blaming the HTML.

Usage
-----
  render_html_to_png.py page.html out.png                 # A4 @300dpi (default)
  render_html_to_png.py page.html out.png --dpi 300
  render_html_to_png.py page.html out.png --scale 2       # 2x the CSS px page size
  render_html_to_png.py page.html out.png --expect 2480x3508
  render_html_to_png.py page.html out.png --transparent   # keep alpha (no page fill)

`--dpi` and `--scale` are mutually exclusive; `--scale` is for the px-canvas convention
in SKILL.md (build the page at 1240x1754 CSS px, ship the 2x PNG), `--dpi` is for
physical sizes (A4 poster at print resolution).

Always also writes `<out>.pdf` next to the PNG -- the PDF is what the user prints, and
it is vector, so it stays sharp at any size.
"""
from __future__ import annotations

import argparse
import os
import sys


def _fail(msg: str) -> None:
    sys.stderr.write("render_html_to_png: %s\n" % msg)
    raise SystemExit(2)


def main() -> int:
    ap = argparse.ArgumentParser(description="Render HTML to a print-ready PNG + PDF (no browser).")
    ap.add_argument("html", help="input .html file")
    ap.add_argument("png", help="output .png file")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dpi", type=float, default=None, help="rasterize the physical page at this dpi (default 300)")
    g.add_argument("--scale", type=float, default=None, help="output = N x the CSS px page size (2 = the 2x convention)")
    ap.add_argument("--expect", default=None, help="assert output is WxH, e.g. 2480x3508")
    ap.add_argument("--transparent", action="store_true", help="keep the PDF page's alpha in the PNG")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.html):
        _fail("no such html file: %s" % args.html)

    try:
        from weasyprint import HTML
    except Exception as exc:  # noqa: BLE001
        _fail("weasyprint not importable (%s).\n  pip install weasyprint\n"
              "  system libs: libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0" % exc)
    try:
        import pymupdf  # noqa: F401  (PyMuPDF >= 1.24 exposes this name)
    except Exception:  # noqa: BLE001
        try:
            import fitz as pymupdf  # older name
        except Exception as exc:  # noqa: BLE001
            _fail("PyMuPDF not importable (%s).\n  pip install pymupdf" % exc)

    # ---- render HTML -> PDF -------------------------------------------------
    pdf_path = os.path.splitext(args.png)[0] + ".pdf"
    doc = HTML(filename=args.html).render()
    doc.write_pdf(pdf_path)

    # ---- PDF -> PNG ---------------------------------------------------------
    pdf = pymupdf.open(pdf_path)
    if pdf.page_count < 1:
        _fail("rendered PDF has no pages -- check the HTML is non-empty")
    page = pdf[0]

    if args.scale is not None:
        # CSS px are 1/96", PDF user units are 1/72" -> zoom = scale * 96/72
        zoom = args.scale * (96.0 / 72.0)
    else:
        zoom = (args.dpi or 300.0) / 72.0

    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=bool(args.transparent))
    pix.save(args.png)
    # capture geometry BEFORE closing the document -- page objects die with it
    page_w_pt, page_h_pt = page.rect.width, page.rect.height
    pdf.close()

    from PIL import Image
    with Image.open(args.png) as im:
        w, h = im.size

    mm = page_w_pt / 72.0 * 25.4, page_h_pt / 72.0 * 25.4
    if not args.quiet:
        print("PNG  %s  %dx%d px  (page %.1f x %.1f mm)" % (args.png, w, h, mm[0], mm[1]))
        print("PDF  %s" % pdf_path)

    if args.expect:
        want = args.expect.lower().replace(" ", "")
        got = "%dx%d" % (w, h)
        # A mm-declared page lands on a non-integer pixel count at most DPIs
        # (210 mm @300 dpi = 2480.31 px), so allow +-1 px. Anything more is a real
        # mismatch -- the CSS page size does not match what was asked for.
        try:
            ew, eh = (int(v) for v in want.split("x"))
            off = max(abs(w - ew), abs(h - eh))
        except Exception:  # noqa: BLE001
            off = 999
        if off > 1:
            _fail("dimension mismatch: expected %s, got %s (off by %d px) -- the page size "
                  "in the CSS does not match what you asked for" % (want, got, off))
        if off == 1 and not args.quiet:
            sys.stderr.write("note: %s vs requested %s -- 1 px rounding on a mm-declared page, fine\n" % (got, want))

    # A page smaller than ~1 mm in either axis means the CSS size collapsed.
    if page_w_pt < 3 or page_h_pt < 3:
        _fail("rendered page is %.1f x %.1f pt -- the @page size did not apply" % (page_w_pt, page_h_pt))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
