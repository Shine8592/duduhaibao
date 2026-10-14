# Repairing text in a finished raster poster

For editing words in an existing poster, scan, or photo the user sends back (a typo fix on a delivered graphic). Do not rebuild the design. Change the fewest possible pixels.

## Tool: `scripts/repair_text.py`

The six steps below are now a script — no need to reassemble the snippets each time:

```bash
# 1) locate glyph boxes (projection; prints candidates + width warnings for you to check)
python scripts/repair_text.py --image p.png --find-in 1100,850,1500,950
# 2) identify the font (score candidate fonts on a known-clean glyph; advisory only)
python scripts/repair_text.py --image p.png --font-rank \
    --sample-box 1130,860,1210,940 --sample-char 路
# 3) replace (the box is auto-tightened to the real ink; writes a diff report + diff image)
python scripts/repair_text.py --image p.png --box 1130,860,1210,940 \
    --replace 安 --font 微软雅黑 --out fixed.png --report-json r.json
```

Outputs `fixed.png` + `fixed-diff.png` (difference ×8) + a report whose key number is
**changed pixels outside the box — it must be 0.**

### Measured behaviour and honest limits

Round-trip test (render a wrong-char image + a correct one, repair the first, pixel-compare):

- **changed pixels outside the box = 0** ✅ — the proof mechanism is reliable.
- The repaired glyph still differs from the true glyph by ~**0.45 % of the image**, concentrated
  on **stroke edges** (re-rasterisation antialiasing) plus a faint ghost of the old character.
  → Visible up close. **If you can get the source file, always edit the source, never the bitmap.**
- `--find-in` segmentation is **not perfect**: a CJK glyph's internal stroke gaps (~3 px) are
  close to the between-glyph gaps (~5 px), so no clean threshold exists. It therefore only
  *reports candidates and flags wide/narrow ones* for a human to pick.
- `--font-rank`'s IoU/NCC signal is weakened by the box normalisation — **advisory only**;
  render the top candidates side by side and look.

Dependencies: `opencv-python` + `numpy` + `Pillow`. `tesseract` is **optional** (auto-reading
the wrong character); without it the workflow degrades to projection + a human-supplied
replacement character.

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

Then run the normal `read` pass on the affected crops, asking about the new glyph specifically: whether it is complete, whether the colour and style match its neighbours, and whether the neighbouring glyphs were damaged.

## Block-level edits — whole lines, rows, or a table entry

> **Drive `scripts/repair_raster.py`; do not hand-write these scripts again.**
> `probe` = step 1-2 (bands + split column), `bg` = measure the background honestly,
> `erase` = blank a rectangle, `bands` = steps 1-5 end to end, `verify` = step 6.
> The command lines are in SKILL.md under "Revising an existing poster".
> Drawing the *new* text stays task-specific; the tool only does geometry, band moves and evidence.

Single glyphs are not the only request. "把这 10 行流程改成 6 行" / "去掉这一行" / "日期改成 X" are
**block edits**: a run of lines is removed, added, or re-timed. Same discipline (change only what was
asked, prove it with a diff), different mechanics — you move and delete *bands*, you do not inpaint a glyph.

1. **Map the bands with ink-row projection first.** For every few pixel rows print the ink-pixel count
   and its x-extent. Text lines appear as bands ~30-40 px tall separated by clean gaps; the pitch
   between band centres is the row rhythm you must preserve.
2. **Find where text ends and decoration begins.** For each band print the **max ink x**. Anything past
   it (a wheat spray, a leaf, a rule) is illustration and must not move. This one number gives you the
   split column `X_SPLIT` used in step 5.
3. **Snapshot every band you will move, including its bullet dot / number badge** — those sit at the
   left edge and are part of the band.
4. **Fill the whole list area, then re-paste the bands at their new centres.** Keep the *same overall
   block*: first and last band hold their old centres and the rest are spaced evenly between them.
   Otherwise a shorter list leaves a conspicuous empty tail inside the card.
   - **Redraw nothing the original does not already have.** Before adding a rule, divider, bullet or any
     other structural mark, profile the source for it. If the mark does exist (a vertical dashed divider,
     say), restore it column-wise out of the original rather than drawing a lookalike.
   - **Profile EVERY row when hunting for rules — a step of 5 will not find them.** These cards draw
     their row separators as **1 px hairlines only ~7-25 levels below the background**. Sampling
     `for y in range(y0, y1, 5)` steps straight over a single-row line, reports a smooth gradient, and
     the honest conclusion “this card has no separators” is wrong. It happened: the card *did* have one
     hairline per text row, and the miss led to five invented rules at the wrong pitch (100 px, 2 px thick,
     ~20 levels) which is exactly what “底纹背景有点乱” described.
   - **Tell a hairline from JPEG ringing by looking where there is no text.** Ringing hugs the glyphs;
     a drawn rule runs the full card width. Measure `ref − lum` against the rows 6 px above and below,
     then compare the median depth over a **blank** column range (left of the first column of text)
     against the depth under the text. A rule gives a ratio near 1; ringing gives near 0. Do not decide
     from a single x or a single row.
   - **If the rules were real, say what you did with them.** The per-row background profile that fills
     the vacated block will erase those hairlines along with the old text. That is a deliberate design
     decision, not a side effect to be silent about: either redraw them at the new row pitch and the
     measured weight, or state plainly that the block is now rule-less. Five times too heavy is worse
     than none; none is worse than matching the original.
5. **Restore the illustration column from the original, then re-overlay the text that crosses the
   split.** Rows move; illustrations do not. After filling and re-pasting, copy `[X_SPLIT+1 : ]`
   straight back out of the untouched original over the whole block height, and restore the few columns
   between the longest text and `X_SPLIT` per row **except** where the old text sat. Skipping this
   chops the decoration into disjoint bands.
   - **The restore on its own silently halves the last glyph.** Any band whose text runs past the split
     has the tail of its final character overwritten by the illustration. Restoring the columns is step
     one; step two is overlaying that band's own ink back on top.
   - **Overlay only the bands whose text actually crosses the split — test it, do not eyeball it.**
     Count ink pixels in the columns immediately left of `X_SPLIT`; a count near zero means that row
     ends well before the illustration and must be left restored-and-untouched. Overlaying a band that
     has no text there pastes illustration in from the wrong row and mangles the decoration.
   - **Make the overlay mask discriminate text from illustration by luminance, per pixel.** Text ink
     runs far darker than a wheat/leaf fill, so a threshold loose enough to catch anti-aliased stroke
     edges also catches the illustration. Take a source pixel only where it is darker than the pixel
     already there.
   - **Keep the restore and the overlay in separate passes.** A `continue` that skips the overlay must
     not also skip the restore, or those bands keep the illustration copied in at the wrong y.
6. **Make each edit script start from the clean base.** A script that reads and writes the same path is
   not idempotent; applying the same fix twice destroys the file. Regenerate the base (re-run the
   upstream generator, or `cp` the original aside) before every further edit — and keep that copy until
   the poster is delivered.

### Filling a background honestly

A block edit needs a background for the vacated area, and a wrong fill is the defect that survives every
other check.

- **Sample inside the card, clear of text and decoration.** Taking the reference from `x0-24 : x0-4`
  (just left of the edit) put the sample *outside* the card's left border, so the filled band came out a
  darker shade than the card.
- **Never sample from a strip that might carry illustration.** A per-row `median(a[y, 470:515])` looked
  safe and was not — the wheat spray lived at x≈500-620, so the sample tracked the decoration and
  printed dark horizontal bars across the entire fill.
- **"Inside the border" is not "in the interior".** A strip hugging the card's left edge is inside the
  card and still wrong: these cards carry a lighter inner highlight band just inside the border, roughly
  11 levels off the interior, so the fill comes out visibly darker than everything around it.
- **Build a per-row background profile, not a fixed strip.** For each row take the median of the
  interior pixels whose luminance clears the ink threshold — that excludes text and decoration
  automatically — then interpolate the all-ink rows and smooth the series. This reproduces the card's
  real vertical gradient and lands within ~1-2 levels of the true colour, where a strip sample cannot.

  ```python
  good = row[row.mean(axis=1) > 205]                       # ink + decoration rejected
  prof[i] = np.median(good, axis=0) if len(good) >= 20 else np.nan
  # then np.interp the NaNs per channel, and convolve with a ~11 px box to smooth
  ```
- **Measure the background's spread before choosing flat vs copied fill.** If `std` over a clean gap is
  ≲5/255 the background is effectively flat and one mid-tone fill is invisible (it differs from the real
  texture by ~2%). If it is higher, copy real pixels instead.
- **Do not tile a short clean strip.** Repeating a 34 px strip to cover a 46 px gap puts a visible seam
  every 34 px. One copy, or a flat fill from the measured mean — never a repeat.
- **Verify with pixel statistics, not another vision pass.** `std` of the filled region (0.00 means it is
  genuinely flat), its mean against the measured background, and a `|current − original|` map to confirm
  every large delta sits where content actually moved. Re-inspecting the same crop by vision reports
  escalating, contradictory defects — one unchanged region scored 6, then 6, then 5, then "no problem"
  as the file got objectively cleaner. A number does not move.
- **Pick verification rows that are clean in the FINAL image, not the original.** A row chosen off the
  original's band rhythm can land under text you have just drawn; its mean then reports a large error
  that is entirely the new text, and a correct fill gets "fixed" twice for a fault it never had.
- **Cross-check every mask and metric a second way before acting on it.** When two measurements of the
  same region disagree, suspect the measuring code before the image — and confirm with an independent
  count (a histogram over the raw crop) rather than a second run of the same expression.
- **A sampled scan has a resolution, and it is not the image's.** "I profiled the card and it is a smooth
  gradient" is only true of the **stride you chose**. At a step of 5 rows a 1 px hairline is invisible in
  every stride; at a step of 1 it is 7-25 levels deep and unmistakable. When a conclusion is of the form
  "the source does not contain X", state the stride that produced it — and before contradicting the user
  about something they can see, re-measure at full resolution over a window narrow enough to catch a
  one-row feature. A wrong "there is nothing there" is more expensive than a slow scan: it produced an
  invented design element, a user complaint, and a second round of edits.
- **Map the bands from inside the card's border.** These posters frame the text block in a *dashed*
  rounded border. A probe region whose left or right edge lands on that border has ink in essentially
  every row (the dashes are near-continuous vertically), so all the text bands merge into one tall blob
  and the pitch — the one number the whole procedure rests on — is lost. `probe` warns when a band is
  tall against the median *and* when an edge column has ink in >80% of the region's rows; take the
  region inward until both are silent. The same trap applies to a vertical dashed divider between a
  time column and a description column.
- **Measure the band-move's ink gap over the TEXT columns only.** After a move, comparing the source
  and destination bands across the full block width reports a large "missing ink" count for every row
  that ends before the illustration column — but that count is the illustration, which is *supposed* to
  stay at its own y. Measuring over `[x0 : X_SPLIT]` gives 0 for every band and is the only number that
  means anything; a self-check that lumps the illustration in cries wolf on every correct edit.

## Pitfalls

- **`arr[y, x0:x1]` and `arr[y0:y1, x0:x1]` need different `mean` axes.** A single-row slice is
  `(N, 3)` → `axis=1`; a block slice is `(M, N, 3)` → `axis=2`. The wrong axis does not raise, it
  reduces over the wrong dimension and returns a plausibility-shaped number: the same crop reported 2
  ink pixels and then 69, minutes apart, and conclusions were drawn from both. Reduce, then print
  `mask.sum()` beside an independent count from the raw crop before trusting it.
- **`cv2.imread` returns BGR.** A colour sampled as RGB and written into a BGR array comes out with the channels swapped — a brown glyph turns blue. Convert once at load (`cv2.cvtColor(img, cv2.COLOR_BGR2RGB)`) and reverse at paste time (`ink_rgb[::-1]`). Always eyeball one paste before batching the rest.
- **A coloured annotation over a glyph lands in the ink mask.** Erase masks thresholded on luminance treat saturated red marker as ink. Exclude reddish pixels (`R-G > 40` and `R-B > 35`) — but if the poster legitimately contains red-orange element text, a luminance threshold already drops most of it, and the red-exclusion should stay scoped to the erase decision, not the display pipeline.
- **Do not erase annotations the user did not ask you to remove.** A hand-drawn circle over the corrected word is often the user's own mark. Inpainting around a tight, irregular hand-drawn stroke has to reconstruct background in a narrow channel and readily drags the stroke's colour into the adjacent glyph — visibly smearing the letters you were told not to touch. When the request is "only fix the typo", leave the annotation in the delivered file and say so; offer the cleaned version as a separate follow-up. If you genuinely need a clean base image, paint matching background texture over the stroke rather than inpainting across it.
- **Small pastes are the only well-behaved pastes.** Keep the paste to a single glyph (or a tight multi-glyph run) sized to an error well under a pixel. Repainting a wider area that overlaps decoys, separators, and decorative marks accumulates visible blur faster than it fixes anything.
- **Take the ink-run that contains the target x; never hand-guess an x-window.** A fixed window
  silently spans the neighbouring glyph, and erasing it deletes a character the user never mentioned
  (a window chosen for one glyph swallowed the next one and wiped it). Segment the line into runs
  first, then pick the run whose range contains the target x.
- **Size the replacement from the neighbours' median ink size, not from the target's own box.** The
  target's bounding box is contaminated: it may include a decoration above or below (a 69 px box for a
  44 px glyph), and when the target run has merged with a neighbour its width is ~2x the glyph (88 px
  where the neighbours are 37-39 px). Take the median ink width and height of the neighbouring glyphs,
  pick the font size whose ink matches that, and centre it on their midline.
- **Match stroke weight, then check the gap.** A replacement at the right size but a heavier weight
  than its neighbours still reads as pasted. Redraw with a light outline in the surrounding paper tone
  if the poster's own glyphs carry one, and keep the inter-glyph gap equal to the neighbours' — a
  centred paste can end up tighter than every other pair.
- **If the user points at something you cannot see, look in the image cache before asking.** A
  message that says "这两个" / "the one on the left" while only one attachment reached you usually
  means a second file landed and was not surfaced. List the cache newest-first
  (`ls -lt --time-style='+%m-%d %H:%M' ~/.hermes/image_cache/`) and read the sibling from the same
  timestamp — one listing is cheaper than a round-trip, and the other image often carries the whole
  comparison the request depends on.
- **Re-verify the neighbour after a multi-glyph rebuild.** When a word contains an unrecognised character in one slot, rebuild only the confirming slot. If you rebuild the whole word, confirm via the vision pass that the characters you were *not* asked about survived intact — a multi-glyph paste is the common way to damage the adjacent correct character.
