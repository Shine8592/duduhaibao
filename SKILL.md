---
name: poster-design
description: "Use when making posters or invitations as print-ready PNG."
version: 1.3.0
---

# Poster Design — print-ready posters, in three routes

Use for a single-page visual deliverable: posters, invitations, event cards, promo/announcement graphics, flyers, share images.

Sibling skills: `visual-design-artifacts` covers diagrams, infographics, and browser mockups; `media-creation` covers video/audio pipelines and AI-generated imagery. This skill is for the poster/invitation/event-graphic class.

It also covers **revising an existing poster the user sends back** — typo fixes and small edits to a finished raster graphic. That path does not start from HTML: see `references/raster-text-repair.md`.

## Procedure

1. **Resolve the deliverable before building.** When the user sends an image, or an image plus a block of copy, with no explicit ask, it usually maps to several plausible outputs (poster, invitation PNG, deck, or written copy only). Inspect the image with `vision_analyze`, then use `clarify` with concrete options, recommended first. Building the wrong artifact burns the whole cycle.
2. **Harvest the source photo for design vocabulary.** Read the subject's own signage, labels, stickers, packaging words, and decorations with `vision_analyze`; that material is free, authentic vocabulary that ties the poster to the real event. Echo one or two motifs in the layout (bunting for a market, plant doodles for a gardening activity, the photo's label wording in the body copy).
3. **Choose the page size** per target channel (table below).
4. **Build one HTML file per size.** Absolutely position every element at an exact CSS page size on a same-sized canvas; embed the photo as a base64 data URI so the HTML stays self-contained. Flow layout drifts and cannot be tuned precisely; absolute coordinates put each block exactly where intended.
5. **Render.** HTML route: `scripts/render_html_to_png.py` (WeasyPrint + PyMuPDF, no browser — run it with the interpreter that has those packages, e.g. `/path/to/venv/bin/python`, and pass `--expect WxH` so a wrong page size fails loudly rather than shipping). Typst route: `typst compile --format png --ppi 300`. Pillow route: direct `save()`.
6. **Verify the PNG with `vision_analyze`** (see loop below), fix the HTML, re-render. Do not sign off by re-reading your own HTML or trusting a prior successful run.
7. **Report exact output dimensions** and deliver the files.

## Page sizes

Build the CSS page at 1x and render at `--scale 2`; the artifact is the 2x PNG.

| Channel | CSS px | 2x output | Ratio |
|---|---|---|---|
| Print / 公众号 / group large image | 1240 × 1754 | 2480 × 3508 | ~3:4 (A4) |
| 朋友圈 / WeChat Moments / single-send | 1080 × 1440 | 2160 × 2880 | 3:4 |

Deliver both when the poster will be both shared and printed — it costs one extra render job.

## Three rendering routes

Pick by **content**, not preference: photos → Pillow, type → Typst, mixed/web-looking → HTML.

The procedure above is the **HTML route**: absolutely-positioned HTML on a fixed-size CSS page, rendered headless. Use it when the layout is mostly type and rules — headings, cards, info rows, simple inline SVG.

Switch to the **Pillow route** when the artifact is a photo collage: several photographs that each need cropping to a ratio, rounded corners and a drop shadow, plus a heading, body copy and a QR code. Embedding and ratio-cropping half a dozen photos through base64 data URIs is more work than compositing them directly, and no browser is involved at all. Keep the same discipline either way: exact page geometry, a named font handle, and the `vision_analyze` verification loop.

Full recipe — A4 geometry, rounded-photo and shadow helpers, ratio-crop, CJK font handle, QR embedding, 300-dpi PDF export — is in `references/pillow-page-layout.md`.

Use the **Typst route** for type-heavy and recurring work: private-wealth salons, corporate briefings, invitations, certificates, price sheets, data-driven series. It renders A4 @300 dpi in ~0.2 s from a single 47 MB static binary with no browser, produces a vector PDF natively, and its `#for` over a data file is the cleanest way to emit the same poster for N sessions. Full cookbook — install, A4 skeleton, `#place` positioning, data binding, QR, and the syntax traps — is in `references/typst-route.md`.

| Route | Best for | Render |
|---|---|---|
| HTML (`scripts/render_html_to_png.py`) | type + rules, card/row layouts, web look | WeasyPrint → PDF → PyMuPDF, no browser |
| Typst (`typst compile`) | formal/editorial type, recurring series | one static binary, PDF-native |
| Pillow (`references/pillow-page-layout.md`) | photo collages, QR, rounded frames | already installed |

## Recurring posters: one data file, N formats

**Before building a line, look for the user's existing one.** Rebuilding a pipeline that already
exists is the expensive failure in this class — search for a project directory shaped like
`lib/data.*` + `templates/` + `build.sh` (see `example/` in this repo) and extend it
rather than writing fresh templates. One data file + one command is the whole interface.

When the same poster class comes back monthly (a salon series, a term of school notices), do not
rebuild it — build the **line**. Separate three layers so only the first one changes per issue:

```
lib/data.typ      ← the ONLY file edited per issue: copy, speaker, date, venue, QR path
lib/tokens.typ    ← palette, type scale, shared components (info_row / highlights / brand band)
templates/*.typ   ← one file per physical format, all importing the two libs
build.sh          ← one command renders every format
```

- Keep the **data** free of layout decisions, except deliberate line breaks in headline copy
  (auto-wrap produces orphans and shifts whenever the text length changes).
- Make the QR a **data field** (`qr_image: none` → placeholder rect; a filename → real image), so
  "add the QR later" is one line, not a layout edit.
- A format is a **page geometry + a type scale**, not a redesign: the A4 print, the 3:4 phone
  version and a banner share the same components at different sizes.
- Give every format a **physical sanity check** before shipping: 18 mm print margins, and for a
  roll-up banner leave the bottom ~30 cm clear (the stand and roll-up edge cover it).
- Verify by **changing one data field and confirming every format's output hash changes** — that is
  what proves the line is actually wired, rather than three hand-maintained copies.
- **Reach for the engine directly; do not wrap it in an MCP server.** The value lives in Typst /
  WeasyPrint / Pillow, not in a protocol layer, and a schema between you and the renderer taxes every
  layout iteration — each tweak becomes a server edit, a schema change and a restart, where editing
  the template and re-running the build is seconds with nothing to restart. Rendering is stateless
  and sub-second, which removes the usual reason for a persistent process. Only two signals would
  justify a service layer: a **second client** (another agent or app needs the same capability), or
  **heavy warm-up** (a model taking tens of seconds to load). Neither holds for print layout. Put the
  validation and output gates in a plain script (`preflight.py`) invoked by the build command.
- **The tool layer is not where knowledge lives.** An engine called directly teaches you the
  pitfalls, and those lessons go back into this skill; a wrapped tool hides them, so the same
  failure is rediscovered every few months.

## Guarding a render pipeline

Rendering fails in two very different ways, and only one of them makes noise. Typst **errors** on a
syntax problem; it **silently clips** content that lands outside the page or overflows a grid cell.
Guard both, in the layer that owns the constraint:

- **Assert at the point of failure, not in a generic linter.** The helper that takes a label width
  and a font size is the only code that knows the two are related — so that is where the check
  belongs. Estimate the text width (CJK ≈ 1.0 em, Latin/digit ≈ 0.55 em) and `panic` with the
  *symptom* when the column is too narrow. A separate lint pass cannot know the relationship, and a
  check placed far from the bug gets ignored.
- **Write the failure message for a future reader.** Name the symptom ("`01` renders as `0`") and
  the fix ("raise `label_w`") — a bare "assertion failed" costs more time than it saves.
- **Two gates, two audiences.** *Before* rendering, validate the **data**: explicit `draft` flag
  (never guess which values "look like" placeholders), required fields, referenced files actually
  existing. *After* rendering, validate the **artifact by pixel**: expected dimensions, not blank,
  and a declared bottom-safety strip still white. Exit codes and "compile succeeded" prove nothing
  about whether the page looks right.
- **The bottom-safety-strip check is the cheapest clipping detector.** Declare a band that must be
  empty (print margin, the part of a banner a stand covers) and assert it is; any element pushed off
  the page lands there and is caught. It needs no model, no diff, and one pass over the bytes.
- **Prefer `tobytes()` over `getdata()`** when walking pixels in Pillow — `getdata()` is deprecated
  (removal in Pillow 14) and `tobytes()` needs no numpy.
- **One regression fixture per incident, and no more.** A guard is only worth having if it is
  exercised both ways: assert the historical bug now *fails loudly*, and assert the correct
  configuration still *passes* (a guard that fires on valid input gets deleted within a week).
- **In shell wrappers, `set -e` swallows exit codes.** `check || RC=$?` — a bare `check` followed by
  `RC=$?` never reaches the second line, because the script has already exited.

## Style direction

Match the register of the occasion. Choosing wrong here costs a full rebuild, because the user rejects formal styling for warm events outright.

| Occasion | Direction |
|---|---|
| Social, DIY, parent-child, festival, customer salon, community, market | **Playful cartoon** — display font, saturated accents, stickers, rounded corners, small illustrated doodles |
| Corporate report, board, consulting, bank-internal formal, B2B | Formal — restrained palette, thin rules, serif or plain sans, generous whitespace |

Default to the warm/cartoon direction for any event built around an activity people *do together*, and when the direction is genuinely unclear, render both and let the user choose rather than defaulting to formal.

Build both kits from the same primitives so only tokens change: background wash + accent blobs, a header chip row, a framed photo with tape or border accents, a title block with a small ornament, info cards per line item, and a footer line. Full element vocabulary, palettes, and the complete cartoon kit specification are in `references/style-directions.md`.

## Fonts

- **Rasterized output may use any font. Editable output may not.** PNG output bakes glyphs into pixels, so a decorative CJK display font ships fine and the viewer installs nothing. The cross-platform constraint (Microsoft YaHei / 微软雅黑 for editable CJK, Arial/Calibri for Latin) applies only to files the user opens and edits in PowerPoint/Word. Do not refuse a display font for a PNG, and do not put one inside an editable file.
- For English/Latin in any output, stay on the common set (Arial, Calibri, DejaVu, Liberation) and avoid obscure faces.
- Sourcing, installation, and the editable-file binding rule (including the `python-docx` `w:eastAsia` requirement) are in `references/cjk-fonts.md`.

## Verification loop

1. Render.
2. `vision_analyze` the PNG with an inspection prompt that asks it to: read back **every** string, report overlap or clipping, report whether icons and emoji rendered (not tofu boxes), and name spacing/balance defects.
3. Fix, re-render, re-verify. Two passes is normal; the first pass almost always finds a real spacing or balance issue.
4. Only then deliver.

**Calibrate the reviewer; do not chase its score.** The number is directional and noisy on an
unchanged file — one poster scored 6, 6.5, 7 and 9 across separate passes on identical pixels. The
model also invents defects: it reported the two lines of a single `text()` call at different sizes,
and read full-width CJK punctuation as half-width. Act only on a defect that is **named and
checkable** — a specific string in a specific place ("『经理』断成两行", "`01` 被裁成 `0`") — and
crop that region to confirm it yourself. Ignore the score and any claim you cannot reproduce. Keep
iterating while a concrete defect remains; stop once the rest is cosmetic and ship with an honest
note, because a pass that only moves the number is wasted cycle time.

**A downscaled preview lies about type size.** Chat previews are capped at ~1400 px on the longest
edge, so an 80×200 cm banner is shown ~14× smaller and every label looks too small — the reviewer
then reports "字号偏小" regardless of the real size. Judge type size against the physical page, or
crop a region at full resolution and review that crop instead.

## Revising an existing poster

When the user sends a finished poster (photo, screenshot, or scan) and asks for a wording fix, the deliverable is the *same image* with the minimum number of pixels changed — not a redesign. Full recipe in `references/raster-text-repair.md`; the shape is:

1. Establish the true text before touching anything (verify every suspected error — see pitfalls).
2. Locate exact glyph bounding boxes programmatically (column segmentation on the ink mask), not by eye.
3. Identify the poster's own font, then sample its ink colour from clean glyphs.
4. Erase and inpaint **only the target glyph's box**.
5. Render the replacement in the matched font, stretch it to the original box, paste with feathered alpha.
6. Prove it: pixel-diff against the original and report how many pixels changed, plus the vision pass on the affected crops.

Deliver PNG (lossless master) and JPG (chat-sized) together; state the changed regions, the changed-pixel count, and explicitly what was left untouched.

## Pitfalls

- **Change only what was asked.** When the user says "just fix the typo" or "nothing else", touch nothing else — do not also strip annotations, re-crop, re-typeset, or tidy adjacent areas. A hand-drawn circle, highlighter mark, or margin note in the source is not yours to remove unless the user asks; keep it and say in the report that you kept it. Rebuilding more than was requested reproduces the very defect the user is asking you to fix.
- **Never assert a typo you have not verified at magnification.** Vision models and OCR both return a *plausible* word for a blurry region, so a confident-sounding read is not evidence. Confirm at 12-16x against side-by-side reference glyphs, and compare the candidate against the character actually printed, not against the word you expect. Rebuilding a correct glyph into a wrong one is worse than the original defect.
- **Deliver the minimal fix promptly; do not hold the artifact hostage to polish.** When a residual imperfection remains, ship the corrected image with an honest note about what is still imperfect and offer a follow-up pass — stalling to perfect a cosmetic detail is the failure mode here.
- **Size the image to the container's exact aspect before embedding.** A fixed-size container plus `object-fit: cover` makes the browser re-crop, silently cutting background subjects; the crop is invisible in the code and only shows in the rendered pixels. Crop the photo to the container ratio first (Pillow), then embed.
- **Re-create the Pillow `ImageDraw` handle after every canvas re-binding.** `canvas = canvas.convert("RGBA")`, `alpha_composite(...)` and `Image.new(...)` all return a *new* image object. A `draw = ImageDraw.Draw(canvas)` created before that line keeps writing to the discarded object, so every string and line drawn through it is **silently absent from the output — no exception, exit code 0**. It is doubly deceptive because elements composited through the other path (`alpha_composite` for photos) still appear, so the failure reads as "only the text disappeared". Re-bind `draw` immediately after any statement that reassigns `canvas`.
- **Assert glyph coverage before laying out CJK text.** A `.ttc` collection needs the right face index — `Noto Sans CJK SC` is `index=2` in `NotoSansCJK-*.ttc`; the wrong index gives tofu or raises only at draw time. Assert `font.getbbox("中")[2] > 0` for the exact font + index you will use, before building anything.
- **Never let CJK headline or lead copy auto-wrap.** Automatic wrapping leaves an orphan tail ("交接。" alone on a line) and the break point moves every time the copy length changes, so a one-word edit silently breaks the layout. Put the break in the **content**, not the layout: store the headline with an explicit break (Typst `"…穿越周期？\n本场活动…"`, HTML `<br>`, Pillow a two-line draw) and keep each line within the column width. Then verify the rendered line count matches what you intended.
- **Keep the outermost frame at least ~10 mm inside the page edge.** Home printers have a non-printable margin; a border closer than that gets clipped, or triggers "scale to fit" and shrinks the whole layout.
- **Always confirm the calendar.** Never print a weekday or date claim from memory — compute it and verify against real output before it goes on a deliverable.
- **Quote exact output dimensions in the delivery message.** It is checkable evidence the render happened at the intended page size.
- **Check the page size actually matches the viewport.** If the HTML declares a page size different from the screenshot viewport or clip, the PNG silently reflows or truncates. Assert the returned image dimensions equal width × scale.
- **Verify the final artifact, not the HTML.** Typography and balance defects surface only in the rendered PNG.
- **Keep decorative SVG inline in the HTML.** Inline `<svg>` is reliable in headless Chromium and needs no asset files.
- **Keep color blobs and borders behind the text layer.** Re-check contrast in the vision pass.

## Verification checklist

- [ ] Deliverable type confirmed with the user when the request was ambiguous.
- [ ] Style direction matches the occasion's register.
- [ ] Page size matches the target channel; both sizes produced when needed.
- [ ] Photo cropped to the container ratio before embedding.
- [ ] Fonts appropriate to rasterized vs editable output.
- [ ] PNG inspected with `vision_analyze`: all text read back, no overlap, no clipping, icons rendered.
- [ ] Output dimensions and file paths stated in the reply.
- [ ] For revisions: every asserted error verified at magnification; changed-pixel count reported; untouched regions explicitly named.
