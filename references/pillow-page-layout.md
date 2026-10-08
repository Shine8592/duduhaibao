# Pillow route — single-page layout built directly with Pillow

Use when the deliverable is a photo collage (several photos needing ratio-crop, rounded
corners and shadows) plus heading, body copy and a QR code. Companion to the HTML route in
SKILL.md; the verification loop and delivery rules are the same.

## Page geometry

| | px @ 300 dpi |
|---|---|
| A4 | 2480 × 3508 |

- Work at **300 dpi** for print. 2480 px / 210 mm is exactly 300 dpi.
- Set the page margin `M ≈ 160` (≈ 13.5 mm) and place the outermost frame at `M-42`, giving a
  ~10 mm safe border. Closer than ~10 mm and home printers clip or rescale.
- Keep type and rules well inside the frame; only decorative blobs may bleed off the page.

## Canvas and the `draw` handle

```python
canvas = Image.new("RGB", (A4W, A4H), BG)
# background wash: draw blobs on a separate RGBA layer, blur, composite
canvas = Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGBA")
draw = ImageDraw.Draw(canvas)          # MUST come after the last canvas re-binding
draw.rounded_rectangle([...], outline=ACCENT, width=9)
```

**The `draw` handle is bound to one image object.** Every `canvas = ...` reassignment produces a
new object; a handle taken earlier writes into the discarded one and its text/lines never appear
in the saved file — with no error and exit code 0. Re-bind after every reassignment. Photos pasted
via `canvas.alpha_composite(...)` use the new object and *do* appear, so the symptom looks like
"only the text vanished".

## Fonts

```python
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
def nf(path, size, idx=2):                 # idx=2 -> the SC face
    return ImageFont.truetype(path, size, index=idx)
assert nf(FB, 40).getbbox("我")[2] > 0      # assert coverage before laying out
```

`WenQuanYi` is Linux-only and must never go in an *editable* deliverable; for rasterized output any
font is fine (see the Fonts section in SKILL.md).

Measure before centring — `bbox = draw.textbbox((0, 0), s, font=f)` then centre on `bbox[2]-bbox[0]`.

## Photo helper — ratio crop + rounded corners

```python
def fit_photo(path, tw, th, cy_ratio=0.40, radius=30):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    ar = tw / th
    if W / H > ar: nw, nh = int(H * ar), H
    else:          nw, nh = W, int(W / ar)
    cx, cy = W / 2, H * cy_ratio          # cy_ratio biases what stays in frame
    l = int(max(0, min(W - nw, cx - nw / 2)))
    t = int(max(0, min(H - nh, cy - nh / 2)))
    im = im.crop((l, t, l + nw, t + nh)).resize((tw, th), Image.LANCZOS)
    m = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, tw - 1, th - 1], radius=radius, fill=255)
    out = im.convert("RGBA"); out.putalpha(m)
    return out
```

Crop to the container ratio first; never rely on the paste step to trim. Tune `cy_ratio` per photo so
heads are not clipped — inspect the rendered sheet, do not assume the default is right.

## Shadow helper

```python
def paste_shadow(canvas, img, x, y, radius=30, blur=22, off=(0, 14), alpha=85):
    sh = Image.new("RGBA", (img.width + off[0] + 80, img.height + off[1] + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [40 + off[0], 40 + off[1], 40 + img.width - 1 + off[0], 40 + img.height - 1 + off[1]],
        radius=radius, fill=(0, 0, 0, alpha))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)), (x - 40, y - 40))
    canvas.alpha_composite(img, (x, y))
```

## QR code

Generate with the highest error-correction level and tint it to the palette — it still scans and it
stops the code from looking pasted on:

```python
import qrcode
from qrcode.constants import ERROR_CORRECT_H
qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=20, border=2)
qr.add_data(url); qr.make(fit=True)
img = qr.make_image(fill_color="#F08A3C", back_color="white").convert("RGB")
```

While the target URL is not yet known, render a **dashed rounded placeholder box** with the words
"二维码 / 扫码观看" in the same footprint, so the layout is final and swapping in the code is a
one-line change. Reserving the exact final size is what makes that swap safe.

## Export

```python
out.save("a4.jpg", quality=97, dpi=(300, 300))
out.save("a4.pdf", resolution=300.0)                 # pdf is what the user prints
out.resize((out.width // 3, out.height // 3), Image.LANCZOS).save("_preview.jpg", quality=94)
```

Deliver the PDF and the full-size JPG, and send the downscaled preview into the chat so the user can
check the layout without downloading the full-resolution file.

## A4 skeleton that held up

Margins 160, content width 2160:

| Block | y range |
|---|---|
| tag chip (pill, centred) | 150 – 236 |
| title + drop shadow + side dots | 286 – 480 |
| subtitle | 480 – 545 |
| hero photo 2160 × 1215 | 560 – 1775 |
| three-up row, 690 × 920 each, gap 45 | 1827 – 2747 |
| caption card (left) + QR 396 × 396 (right) | 2803 – 3191 |
| footer line, centred | bottom inside `M` |

## Print-readiness checks

- Measure the bottom band and the top band: they must be pure white (or pure background).
- Confirm outer frame-to-edge distance ≥ ~10 mm.
- Read every string back off the rendered image with `vision_analyze` — the Pillow route can drop an
  entire text layer silently, so "script exited 0" is not evidence anything was drawn.
