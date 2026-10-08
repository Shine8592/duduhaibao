# CJK fonts — sourcing, binding, and the index trap

Chinese output fails in three different ways and they look identical in a rendered image
(missing glyphs, tofu boxes, or silent fallback to a Latin face). Work through this file
before laying out any CJK text.

## The one rule that matters

**Rasterized output may use any font. Editable output may not.**

- A PNG/PDF bakes the glyphs into pixels. Ship a decorative display face and the viewer
  installs nothing. The cross-platform constraint does **not** apply.
- A `.pptx` / `.docx` stores *font names* and relies on the reader's machine. A face the
  reader lacks is silently substituted and the layout collapses. Here the constraint is
  absolute: **Microsoft YaHei (微软雅黑) for CJK, Arial/Calibri for Latin.**

Getting this backwards is the most common CJK failure: either refusing a nice display
font for a PNG, or embedding a Linux-only face into a PowerPoint.

## What is on this box

```
/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc   黑体  Regular
/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc      黑体  Bold
/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc  宋体  Regular
/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc     宋体  Bold
```

`fc-list :lang=zh` lists what fontconfig can actually resolve.

WeasyPrint and Typst both resolve CJK through **fontconfig**, so the family name you
write in CSS/Typst must match `fc-list` output — `"Noto Sans CJK SC"`, not `"Noto Sans"`.

Microsoft YaHei is normally **absent** on Linux. That is fine: use it only when the
deliverable is an editable Office file, and note in the hand-off that the reader's
machine supplies it.

## The `.ttc` index trap

A `.ttc` is a *collection* of faces in one file. `NotoSansCJK-*.ttc` holds SC/TC/JP/KR/HK
at different indices, and **`Noto Sans CJK SC` is `index=2`**. The wrong index gives JP
glyphs (looks Chinese but is wrong for 简体) or raises only at draw time.

```python
from PIL import ImageFont
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def nf(path, size, idx=2):          # idx=2 -> the SC face
    return ImageFont.truetype(path, size, index=idx)
assert nf(FB, 40).getbbox("我")[2] > 0     # assert coverage BEFORE the layout
```

Assert with a real ideograph, not `"A"`. A Latin glyph exists in every face.

In CSS and Typst you name the family instead of indexing, so the trap only bites the
Pillow route — but assert there every time, because a wrong index fails *late*.

## Sourcing a face that is not installed

```bash
# Debian/Ubuntu, packaged
apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra

# A single face, no package: drop it in the user font dir and refresh the cache
mkdir -p ~/.local/share/fonts && cp MyFace.ttf ~/.local/share/fonts/
fc-cache -f && fc-list | grep -i myface      # verify BEFORE using the name
```

Always `fc-cache -f` and verify with `fc-list`; a font copied but not cached is invisible
to fontconfig and every engine silently falls back.

For a display face used only in a rasterized poster, downloading a single `.ttf` is fine.
For anything that ships inside a document, stay on the packaged Noto set.

## CSS / Typst font stacks

CSS (WeasyPrint, headless Chrome):

```css
font-family: "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", sans-serif;
```

Typst:

```typst
#set text(font: ("Noto Sans CJK SC", "Microsoft YaHei", "Arial"), lang: "zh")
```

Set `lang: "zh"` in Typst (and `<html lang="zh">` in HTML). Without it, the engine uses
Western line-breaking rules, and CJK punctuation ends up at the start of a line
(禁则処理 does not run).

## Editable files: binding the East Asian face

In `python-docx` a run has two font slots. Setting only `font.name` writes the Latin
slot, so the CJK characters keep the theme font and the reader sees a substitution:

```python
run.font.name = "Microsoft YaHei"
run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")   # the one that matters
```

For `pptx`, `python-pptx` exposes `run.font.name` only; also set the East Asian slot on
the `a:rPr` element the same way. Without it, `微软雅黑` in the XML is not what renders.

## Emoji

Emoji are **not** in the CJK fonts. If the design uses them and the render shows tofu,
install a colour emoji font (`fonts-noto-color-emoji`) or replace them with inline SVG.
Check this in the vision pass — a missing emoji is easy to miss at thumbnail size.

## Sizing and subsetting

- Body CJK at print size: **9–12 pt**; below 9 pt the strokes crowd at 300 dpi.
- Line height for CJK wants **1.7–1.9**, noticeably looser than Latin's 1.4–1.5.
- A full Noto CJK face is large; if a rasterized PDF must be small, subset it
  (`pyftsubset`) — never subset a font that goes into an editable file.
