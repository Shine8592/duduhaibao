# Repairing text in a finished raster poster

For editing words in an existing poster, scan, or photo the user sends back (a typo fix on a delivered graphic). Do not rebuild the design. Change the fewest possible pixels.

## Dependencies

```bash
apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
pip install opencv-python-headless numpy fonttools
```

## Step 1 — Establish the truth before touching anything

Never edit on an unverified read. Three independent methods, cheapest first:

1. **Tesseract on the region.** For clean print, OCR is far more reliable than asking a vision model to read. It returns the *actual* character rather than the plausible word. Run with a size boost and a binarised copy:

   ```bash
   tesseract crop.png - -l chi_sim --psm 6        # block of lines
   tesseract crop.png - -l chi_sim --psm 7        # single line
   ```

   TSV mode gives per-character boxes, which doubles as glyph localisation:

   ```bash
   tesseract full2x.png out -l chi_sim --psm 6 tsv
   ```

   Iterate the binarisation threshold (100/120/140/160/180) — ragged display fonts read cleanly at one threshold and garrble at another.

2. **Percentile band segmentation** to split a line into individual glyphs without OCR (see Step 2).

3. **Side-by-side glyph comparison.** Build one image: the target crop magnified 12-16x, and each candidate character rendered large via PIL in a known font, side by side with labels. Ask the vision model a *structural* question — "is the right half `身` or `又`?", "is the radical `木` or `扌`?" — never "which character is this?".

   Crop tight enough that the *component* under dispute fills the frame. A too-wide crop buries the discriminating stroke in noise; a too-narrow or too-tall strip makes the model misread the whole line.

## Step 2 — Locate glyphs programmatically

Find the text lines by ink-row projection, then segment each line by column projection with a gap threshold; print each segment's width and vertical extent.

```python
lum   = 0.299*R + 0.587*G + 0.114*B
reddish = (R-G > 40) & (R-B > 35)        # see pitfall below
ink   = (lum < 150) & (~reddish)
```

Print per-segment columns and extents and sanity-check them before trusting a box — a segment that is 2-3x the width of its neighbours is several glyphs merged; a very short one is an accent or a stray mark.

## Step 3 — Identify the source font

**Rank, do not assume.** Render the poster's own correct glyphs (the ones you have confirmed are right) in every candidate font and in the matching aspect ratio, score them against the extracted glyphs by IoU, and take the winner. Restrict the candidate set to display/CJK fonts to keep the comparison meaningful.

Two independent metrics agreeing on the same winner is the confidence bar — a single metric can be fooled by a font that differs in weight but matches in skeleton. Cross-check with normalised cross-correlation on the raw grayscale.

Measured prior from display-CJK fonts (use as a starting shortlist, re-rank per poster): an expression brush face (`ZhiMangXing`) scored IoU 0.459 / NCC 0.306, above the cartoon face (`ZCOOLKuaiLe`, 0.441 / 0.062), the calligraphic serif (`MaShanZheng`, 0.420 / 0.050), and `NotoSerifCJK` (0.335 / 0.000). Note the NCC column separates far more cleanly than IoU — a high IoU with near-zero NCC means the shape mass matches but the stroke structure does not.

Face under dispute? Render a candidate grid of the *candidate characters* in the winning font and read the winner straight off the comparison, rather than trying to describe both in prose.

## Step 4 — Erase only the target glyph

Build the erase mask **from the original image's ink pixels inside the target box only** — do not carry a mask in from a wider region:

```python
m = (lum[y0:y1, x0:x1] < 170).astype('uint8') * 255
m = cv2.dilate(m, np.ones((3,3), np.uint8), iterations=2)
work[y0:y1, x0:x1] = cv2.inpaint(work[y0:y1, x0:x1].copy(), m, 9, cv2.INPAINT_TELEA)
```

- `INPAINT_TELEA` suits the paper/watercolour textures these posters use.
- Keep the dilation kernel small (3x3, 1-2 iterations). A 7x7 with more iterations spreads the mask into the neighbouring glyph's box, which is exactly the damage described under pitfalls.

## Step 5 — Paste the replacement

1. **Sample the ink colour from the poster's own clean glyphs** — median of the pixels darker than ~120 L inside a clean char's box. Never hardcode a colour, and never sample after inpainting (the region is now background).
2. Render the character with PIL, crop to the ink bbox.
3. **Stretch to the original glyph's box dimensions** (`resize((W, H))`). Do not rely on the font's natural aspect: a display font's natural width/height for the replacement can be far off the poster's (a brush face gave 0.845 where the poster's glyph box was 1.30), and a narrow paste is instantly visible.
4. Paste with a Gaussian-feathered alpha (3x3, sigma ~0.5) so the edges melt into the paper texture.

```python
al = cv2.GaussianBlur(g.astype(np.float32)/255.0, (3,3), 0.5)
for c in range(3):
    reg = work[top:top+h, left:left+w, c].astype(np.float32)
    work[top:top+h, left:left+w, c] = np.clip(reg*(1-al) + ink_bgr[c]*al, 0, 255).astype('uint8')
```

## Step 6 — Prove the edit, and prove the restraint

Diff the finished image against the original and report the result:

```python
d = np.array(ImageChops.difference(orig, fixed)).sum(axis=2)
changed = (d > 40).sum()
```

Report the changed-pixel count, the percentage of the image, and the per-region breakdown, then explicitly state **how many pixels changed outside the intended edit regions**. That number being zero is the evidence that nothing else moved, and it is what a "just fix the typo" request is actually asking to see.

Then run the normal `vision_analyze` pass on the affected crops, asking about the new glyph specifically: whether it is complete, whether the colour and style match its neighbours, and whether the neighbouring glyphs were damaged.

## Pitfalls

- **`cv2.imread` returns BGR.** A colour sampled as RGB and written into a BGR array comes out with the channels swapped — a brown glyph turns blue. Convert once at load (`cv2.cvtColor(img, cv2.COLOR_BGR2RGB)`) and reverse at paste time (`ink_rgb[::-1]`). Always eyeball one paste before batching the rest.
- **A coloured annotation over a glyph lands in the ink mask.** Erase masks thresholded on luminance treat saturated red marker as ink. Exclude reddish pixels (`R-G > 40` and `R-B > 35`) — but if the poster legitimately contains red-orange element text, a luminance threshold already drops most of it, and the red-exclusion should stay scoped to the erase decision, not the display pipeline.
- **Do not erase annotations the user did not ask you to remove.** A hand-drawn circle over the corrected word is often the user's own mark. Inpainting around a tight, irregular hand-drawn stroke has to reconstruct background in a narrow channel and readily drags the stroke's colour into the adjacent glyph — visibly smearing the letters you were told not to touch. When the request is "only fix the typo", leave the annotation in the delivered file and say so; offer the cleaned version as a separate follow-up. If you genuinely need a clean base image, paint matching background texture over the stroke rather than inpainting across it.
- **Small pastes are the only well-behaved pastes.** Keep the paste to a single glyph (or a tight multi-glyph run) sized to an error well under a pixel. Repainting a wider area that overlaps decoys, separators, and decorative marks accumulates visible blur faster than it fixes anything.
- **Re-verify the neighbour after a multi-glyph rebuild.** When a word contains an unrecognised character in one slot, rebuild only the confirming slot. If you rebuild the whole word, confirm via the vision pass that the characters you were *not* asked about survived intact — a multi-glyph paste is the common way to damage the adjacent correct character.
