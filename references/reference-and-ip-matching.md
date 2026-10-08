# Matching a Supplied Reference or a Named IP

Two different requests wear the same clothes, and both punish improvisation. Read this whenever the
user hands over a reference design, or names a character/brand the artifact must look like.

## The user sent a reference image ("I want it like this")

The reference **is** the spec. Do not interpret it — measure it.

1. Split the image into quadrants and crop regions; read each **crop** with `vision_analyze` and ask
   for numbers: the panel/side-column width split, band height fractions, cell aspect ratio, the
   header format, where the illustrations sit, what the footer contains.
2. One pass over the whole image returns a *description*. Only the crops return *proportions* — and
   proportions are what a template is actually built from.
3. Settle the structural ambiguities explicitly before writing any code. Typical ones: is this one
   sheet or two stacked sheets? which element is stacked vertically? what fraction of the width is
   the side column? how tall is the display numeral?
4. Only then build, and keep the reference's own vocabulary — its header wording, its weekday order,
   its colour logic — rather than substituting what you would have chosen.

Rebuilding from a remembered impression of the reference is the failure mode: the user rejects it and
the whole batch is wasted.

## The user named an existing IP or character brand

**Do not draw your own idea of it.** Naming an IP is a demand for that character's *actual,
recognisable* design. An invented approximation reads as **wrong** to the user even when it is well
drawn and cute — they will say so plainly and the work is discarded.

Sequence:

1. **Extract the concrete design features** — face and body colour, head-to-body ratio, eye and mouth
   construction, blush, ears / hood / hat, the signature accent, the overall silhouette. These are the
   features that make the character identifiable; everything else is decoration.
2. **Ground them on real product imagery, not on prose.** Description text tells you a character is
   "round and yellow"; only the image reveals that the *face* is skin-toned, that the hood is the
   coloured part, that the signature star sits on the hood tip, or that the eyes carry highlight dots.
   Official product and collection pages expose image URLs in the DOM: load the page, collect the
   `img` sources (filter to ones with a real `naturalWidth`), download a handful, and view them.
3. **Draw an original SVG in that style.** Never embed, trace, or bundle official assets. State in the
   delivery that the character is your own drawing in the style, so the copyright position is explicit
   and the user is not surprised later.
4. **Verify the character against the reference before scaling to N images.** Crop the drawn character
   out of one rendered page, view it, and confirm the recognisable features are present. Producing a
   full run of months (or products, or slides) before that check is how an unusable character gets
   multiplied by twelve.

## Build the character as a function

For any series driven by one character design, implement it once as a parameterised function — palette,
pose, flip, scale, plus a `shadow`/grounding flag — and compose every scene from it. Then a palette or
pose change is one argument rather than N edits, and the character cannot drift between pages.

Give the function a small set of named poses (standing, waving, sitting, eyes-closed) rather than free
parameters; the poses get reused and the names keep the scene table readable.

## Scene composition that fills the frame

The first attempt at any character illustration is almost always **too small with too much dead space**
— the reviewer will say so. Size the character from the container, not by eye:

```python
# character has a known local bounding box (CH_W, CH_H)
sc = min((W / n) / CH_W, H / CH_H) * 0.95   # n characters side by side
```

Then add a soft ground shadow ellipse under each character and two or three large, low-opacity
background circles. Those two cheap additions are what make a small character read as a placed scene
instead of a sticker floating in an empty box.
