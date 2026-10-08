# Style directions — the cartoon kit and the formal kit

Two registers, one set of primitives. Pick the register from the occasion, then only
the **tokens** change: same block order, same geometry helpers, different palette,
type treatment, and corner language.

Picking wrong costs a full rebuild, because a warm event styled formally gets rejected
outright. When the occasion is genuinely ambiguous, render both and let the user choose.

| Occasion | Register |
|---|---|
| DIY, parent-child, festival, market, community fair, school activity, customer salon with families | **Cartoon** |
| Corporate report, board pack, consulting deliverable, bank-internal announcement, B2B, private-wealth salon | **Formal** |

> A **customer salon** flips by audience: an activity families *do together* is cartoon;
> a private-wealth briefing for clients is formal. Ask when it is not obvious.

## The shared primitive set

Both kits are assembled from the same seven blocks, in this order. Build them once as
tokens and the register is a parameter, not a rewrite.

| # | Block | Cartoon | Formal |
|---|---|---|---|
| 1 | Background wash | 2–3 blurred colour blobs bleeding off-page | one flat tint or plain white |
| 2 | Header chip | rounded pill, saturated fill, white text | thin rule + small caps label, no fill |
| 3 | Title block | display weight, drop shadow, side dots | restrained weight, generous whitespace, thin accent rule under |
| 4 | Subtitle | playful, accented colour | grey, small, tracked out |
| 5 | Hero / content | framed photo: rounded corners, tape or thick border, drop shadow | photo or none: square corners, hairline border, no shadow |
| 6 | Info rows | per-line cards with an emoji/icon chip | one left-aligned definition list, `label：value`, thin leader |
| 7 | Footer | centred, decorative | left brand line + right page/date, separated by a rule |

## Cartoon kit

**Palette** (warm, high-chroma accents on cream):

```
bg      #FFFDF7   cream page
accent  #F08A3C   orange     — titles, chips, QR tint
accent2 #FFC478   light orange — blobs, secondary chips
leaf    #78AF6E   green      — pills, doodles
pink    #F2A2B8   pink       — decorations only
ink     #4A362A   warm brown — body text (never pure black)
```

**Type**

- Title: 150–170 px on a 2480 px A4, weight bold, accent colour, with an offset duplicate
  in `accent2` behind it as a fake drop shadow.
- Subtitle: ~62 px, `ink`.
- Body: ~52 px, line height 1.7.
- Labels are full sentences, not fragments — this register reads as friendly.

**Geometry**

- Corners: 28–34 px radius on photos, 40–44 px on cards.
- Photos: `frame + rounded + drop shadow (blur 22, offset 0/14, alpha ~85)`.
- Add one small ornament per block (dots beside the title, a doodle in a corner). One —
  more than one reads as clutter.
- Illustrative doodles: inline SVG, 2–3 px stroke, accent colours, never overlapping text.

**What makes it read as cartoon**: high-chroma accents, rounded everything, warm (not
black) text, a visible drop shadow, and at least one hand-drawn element.

## Formal kit

**Palette** (restrained, one brand colour):

```
bg      #FFFFFF   white, or #FAFBFC for a very light grey page
brand   #1B4F8C   the brand colour — header band, titles, rules
brand2  #A8CBEA   tint of the brand — subtitles on the band
ink     #333333   body text
muted   #8899AA   labels, footers, metadata
rule    #DCE3EA   hairlines
```

Swap `brand` for the client's own colour (a brand's primary colour; a bank-internal doc → the
bank's corporate colour) and the whole kit follows.

**Type**

- Title: 24–30 pt (≈96–120 px on A4), weight bold, `brand`, left-aligned or centred.
  **No drop shadow, no outline.**
- Subtitle: grey, ~11–12 pt, tracked out slightly.
- Body: 11–11.5 pt, line height 1.8–1.9 (CJK wants the looser setting).
- Labels: `label：value` on one line, label in `muted`, value in `ink`.

**Geometry**

- Corners: **square**. Radius 0 on photos, cards, and bands. This single choice does most
  of the register work.
- No drop shadows. Use a hairline rule (`rule`, 1 px) or generous whitespace to separate.
- Header band, if used: full-bleed, 40–46 mm tall on A4, brand fill.
- Whitespace: at least 18 mm page margins, and noticeably more space above a block than
  below it.
- Accent rule under the title: 2–3 mm tall, 30–40 mm wide, `brand`. One is enough.

**What makes it read as formal**: square corners, no shadows, one restrained colour,
thin rules, and whitespace doing the separating instead of boxes.

## Register switcher

Keep the geometry and swap only these six values, and the same source produces both:

```python
KIT = {
  "cartoon": dict(bg="#FFFDF7", ink="#4A362A", accent="#F08A3C", tint="#FFC478",
                  radius=32, shadow=True,  title_px=160, body_px=52, lh=1.70),
  "formal":  dict(bg="#FFFFFF", ink="#333333", accent="#1B4F8C", tint="#A8CBEA",
                  radius=0,  shadow=False, title_px=104, body_px=46, lh=1.85),
}
```

`radius=0` + `shadow=False` + a single brand colour does ~80% of the formal/cartoon
distinction. Change those three first, then the type scale.

## Both registers: verification

The register is not visible to the code, only to the rendered pixels. A vision pass that
asks "does this read playful or formal, and is that right for the occasion?" catches the
mismatch before the user sees it. Also check that no decorative blob sits behind text
without enough contrast.
