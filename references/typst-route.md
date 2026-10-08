# Typst route — typographic posters without a browser

Third rendering route alongside the HTML route (SKILL.md) and the Pillow route
(`pillow-page-layout.md`). Use Typst when the artifact is **mostly type and rules**:
private-wealth salons, corporate briefings, invitations, certificates, price sheets,
multi-page or data-driven series.

## Why this route exists

| | Typst | HTML + WeasyPrint | Pillow |
|---|---|---|---|
| Install | one 47 MB static binary, zero deps | pip + libpango/cairo | already present |
| A4 @300 dpi render | **~0.2 s** | ~9 s | seconds |
| Output | PDF native, PNG at any ppi | PDF then rasterize | raster only |
| Type quality | real typesetting engine (kerning, justification, CJK line breaking) | good, browser-ish | manual, no shaping control |
| Photo collages | awkward | ok | **best** |
| Data-driven series | **excellent** (`#for` over a data file) | awkward | awkward |
| Learning cost | a markup language to learn | none (CSS) | none (Python) |

Pick by content, not by preference: **photos → Pillow, type → Typst, mixed/Web-looking →
WeasyPrint.**

## Install

```bash
curl -sL https://github.com/typst/typst/releases/latest/download/typst-aarch64-unknown-linux-musl.tar.xz \
  | tar xJ -C /tmp
install -m 755 /tmp/typst-aarch64-unknown-linux-musl/typst /usr/local/bin/typst
typst --version
```

Swap `aarch64` for `x86_64` on Intel. A `musl` build is statically linked and works on
glibc distros — prefer it over the gnu tarball.

## Compile

```bash
typst compile page.typ out.pdf                    # vector, what the user prints
typst compile --format png --ppi 300 page.typ out.png
typst watch page.typ out.pdf                      # live rebuild while iterating
```

`--ppi 300` on a 210×297 mm page yields exactly **2480×3508 px**. Typst rounds the same
way WeasyPrint does (210 mm @300 ppi = 2480.31), so accept ±1 px.

## A4 skeleton

```typst
#set page(width: 210mm, height: 297mm, margin: 0pt, fill: rgb("#FFFFFF"))
#set text(font: ("Noto Sans CJK SC",), lang: "zh", size: 11pt)
#set par(leading: 1.85em, spacing: 1.1em, justify: false)

// content is ABSOLUTELY placed — no flow layout to drift
#place(top + left, rect(width: 210mm, height: 44mm, fill: rgb("#1B4F8C")))
#place(top + left, dx: 18mm, dy: 14mm,
  text(fill: white, size: 26pt, weight: "bold")[新一代协作平台发布])
#place(top + left, dx: 18mm, dy: 30mm,
  text(fill: rgb("#A8CBEA"), size: 11pt)[云杉科技 × 山海设计 · 秋季产品发布会])

#place(top + left, dx: 18mm, dy: 62mm,
  text(size: 24pt, weight: "bold", fill: rgb("#1B4F8C"))[让复杂的工作变简单])

#place(top + left, dx: 18mm, dy: 88mm, block(width: 174mm)[
  #text(weight: "bold")[活动主题：]当工具越来越多、人却越来越累，问题出在哪里……
])
```

`#place(top + left, ...)` with explicit `dx`/`dy` is the equivalent of the HTML route's
absolute positioning: nothing reflows, so the block lands exactly where you put it.

## Data-driven series

The reason to prefer Typst for recurring work — one template, one data file, N variants:

```typst
#let event = (
  title: "让复杂的工作变简单",
  speaker: "林知远",
  date: "2026年12月5日 14:00",
  venue: "北京市朝阳区示例路 88 号",
  seats: 60,
)

#place(top + left, dx: 18mm, dy: 62mm,
  text(size: 24pt, weight: "bold", fill: rgb("#1B4F8C"))[#event.title])
```

Read the data with `#let d = json("data/session.json")` or `yaml("data/session.yaml")`
and loop with `#for row in d.rows [...]` — one invocation emits one PDF page per row.

## QR codes

Generate the PNG with `qrcode` (see `pillow-page-layout.md`), then place it:

```typst
#place(bottom + right, dx: -18mm, dy: -22mm,
  image("qr.png", width: 18mm, height: 18mm))
```

While the URL is unknown, place a `rect(... stroke: 1pt + rgb("#1B4F8C"))` of the exact
final footprint so swapping in the image is a one-line change.

## Pitfalls

- **Typst has no `px` unit.** Units are `pt`, `mm`, `cm`, `in`, `em`, `fr`, `%` — `1080px` is an
  "invalid number suffix" error. To port a pixel-based design (e.g. a 1080×1440 social canvas),
  define the conversion once and keep the design numbers verbatim:
  `#let px(v) = v * 0.75pt` (1 CSS px = 0.75 pt), then write `px(1080)`.
- **A grid column narrower than its content clips silently.** In the highlights helper the number
  column was fixed at `9mm`; at 52 pt the `01` did not fit and rendered as `0` — no error, exit 0,
  visible only in the pixels. **Column widths must scale with the font size** (`label_w: 68mm` for
  the banner-size variant). Same class of bug as the Pillow `draw`-handle trap: it fails silently.
- **A module-level `#let` cannot be reconfigured by the importing file.** Typst closures capture
  their *defining* scope, so `#import "tokens.typ": *` followed by `#let scale = 1.45` shadows the
  name locally while every function inside `tokens.typ` keeps using the original. Pass such values
  as function parameters instead of trying to override a module global.
- **Imports may not escape the project root.** `#import "../lib/data.typ"` from `templates/` fails
  with "path would escape the project root" unless you compile with `--root .`; the sandbox is the
  entry file's directory by default.
- **Relative paths resolve against the file that contains the call, not the project root.** A
  helper in `lib/tokens.typ` calling `image("qr.png")` looks for `lib/qr.png` — so putting the file
  at the project root fails with "file not found (searched at …/lib/qr.png)". Under `--root .` a
  leading slash is root-relative: normalise inside the helper
  (`let p = if img.starts-with("/") { img } else { "/" + img }`) so the data file can always say
  "put it in the project root" and any external checker agrees with Typst.
- **`leading` belongs to `par`, not `text`.** `#set text(leading: 1.9em)` is an
  "unexpected argument" error; write `#set par(leading: 1.9em)`.
- **Trailing `#` in markup mode is fine, but inside a code block it is not.** After
  `#place(...)` you are in code; a following `#place(...)` at the start of the next line
  can error with "the character `#` is not valid in code" if a bracket was left unclosed
  above. The real fault is usually the *previous* line's delimiter, not this one — fix
  the unclosed `(`, `[`, or `{` and the cascade disappears.
- **A parameter named `v` shadows the `v()` spacing function.** `#let row(k, v) = [ ... #v(3.6mm) ]`
  fails with "expected function, found content" — the parameter is content, not a function. Rename
  to `val`. Any one-letter parameter that collides with a builtin does this.
- **`block(width: 174mm)[...]` needs its closing bracket before the outer `)`.** Writing
  `block(width: 174mm, text(...)[...])` mis-nests and reports "unclosed delimiter".
- **`lang: "zh"` is not optional.** Without it Typst applies Western line-breaking and CJK
  punctuation lands at line starts (no 禁则処理). Set it in `#set text(...)`.
- **Name the family as `fc-list` reports it** — `"Noto Sans CJK SC"`. Naming
  `"Noto Sans"` silently falls back to a Latin face and every ideograph goes to tofu.
- **Don't trust automatic line breaking for headline copy.** CJK auto-wrap produces orphan
  characters ("交接。" alone on a line) and changes every time the text length changes. Put explicit
  breaks in the *data* (`"…如何穿越周期？\n本场活动…"`) so the layout is stable and controlled.
- **Typst errors are fail-fast and precise.** Unlike the Pillow route, a bad layout does
  not ship silently; but it also means a syntax error produces *no output at all*, so
  check the exit code before treating the PDF as fresh.

## Verify

Same loop as every other route: render, then `vision_analyze` the PNG with a prompt that
asks for a string-by-string read-back, overlap/clipping, and the register check. Typst
gets the geometry right; only the pixels tell you whether the *design* is right. Report
the exact output dimensions in the delivery message.
