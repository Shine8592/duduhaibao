# Calendar & Date-Grid Artifacts

Use when the artifact's core content is **dates** rather than copy: a 12-month calendar series, a
wall/desk calendar, a date grid, a term or campaign schedule, a planner spread.

The whole risk profile is different from a poster. A poster is judged on style; a calendar is judged
on **correctness**, and one wrong weekday destroys the deliverable. Treat every date as data to be
computed and asserted, never as text to be written.

## Rule 0 — the model never produces a date

Compute every date with the stdlib and assert the result programmatically before rendering.
`calendar.monthrange(y, m)` for day counts, `datetime.date(y, m, d).weekday()` for the column
(Monday = 0). Never transcribe a weekday, a day count, or a solar-term date from memory or from a
model's guess — the whole artifact is wrong if one cell is off, and it will not be obvious by eye.

## Chinese lunar dates, solar terms and festivals

`pip install cnlunar` (pure Python, no build step). Per day:

```python
import cnlunar, datetime as dt
o = cnlunar.Lunar(dt.datetime(y, m, d), godType='8char')
o.lunarMonthCn   # '正月大' / '八月小' — ALWAYS carries a 大/小 suffix; strip it for display
o.lunarDayCn     # '初一', '十五', '廿三'
o.todaySolarTerms  # '立春' … or the literal '无' on ordinary days
```

- `todaySolarTerms` returns the string `'无'` (not empty, not None) when there is no term that day —
test for both falsy and `'无'` or you will print 「无」 into cells.
- Derive the lunar festivals by **scanning the lunar day names** for the year and matching against a
map of `(month, day)` → name (春节 = 正月初一, 元宵 = 正月十五, 端午 = 五月初五, 七夕 = 七月初七,
中元 = 七月十五, 中秋 = 八月十五, 重阳 = 九月初九, 腊八 = 十二月初八). Do not hardcode Gregorian dates
for them — 除夕 and 春节 move every year and the scan is what keeps them right.
- 除夕 is the day before 春节, not a lunar-day name — compute it as `春节 - 1 day`.
- `sxtwl` is the usual companion package but is a compiled extension and **fails to build** on some
interpreters; `cnlunar` covers the same ground. Reach for `cnlunar` first.

**Build the year's data once into a JSON file and have every page read it.** Scanning 365 days per
page × 12 pages is 12× the work for identical output, and it makes the 12 pages capable of drifting
apart. One `data<year>.json` holding `{terms, lunar, fests}` is the contract between the compute step
and the layout step.

## Statutory holidays for a future year

**The State Council publishes the next year's 放假安排 only around November–December of the prior
year.** Before that date the 调休 (make-up workdays) genuinely do not exist yet, and any arrangement
you print is fabrication.

Correct handling for an unpublished year:

1. Mark only the dates fixed by law and by the calendar — 元旦 1/1, 春节 初一–初三, 清明, 劳动节 5/1,
   端午, 中秋, 国庆 10/1–10/3. These do not depend on the notice.
2. **Do not invent 调休 days.** Omit them rather than guess.
3. Print the limitation **on the artifact**: a small line stating the year's 放假调休 arrangement is
   pending the State Council notice and that make-up workdays are not marked. This is the difference
   between an honest deliverable and a wrong one.
4. Say the same thing in the delivery message, and offer to patch the 调休 in once the notice drops.

## Label a holiday run once

A statutory holiday spanning consecutive days (春节 初一–初三, 国庆 1–3) must not repeat its name in
every cell — 「春节」 three cells in a row reads as a mistake. Compute the runs and label only each
run's **first** day with the festival name; the remaining days fall back to their lunar day name
(初二, 初三). Keep the *number* colour on all days of the run so the holiday still reads as a block.

```python
sd = sorted(statutory_days); first_of_run = set()
for i, d in enumerate(sd):
    if i == 0 or (dt.date.fromisoformat(d) - dt.date.fromisoformat(sd[i-1])).days != 1:
        first_of_run.add(d)
```

## Layout geometry

- Monday-first (`MON…SUN` / `一二三四五六日`) unless the user's reference or locale says otherwise —
  the supplied reference's own header row is the authority, not a default.
- CSS `grid-template-columns: repeat(7, 1fr)` for the grid; one cell per day, blanks for the lead-in.
- **A month has 4–6 grid rows, so never fix the cell height.** Resolve it per month against a fixed
  grid band so every month's grid occupies the same area and the page below never shifts:
  `ch = (GRID_H - (nrows - 1) * gap) / nrows`.
- Cell priority for the small line under the number: solar term → festival → lunar 初一/十五 →
  lunar day. Terms and festivals in colour, ordinary lunar days muted.
- Encode weekday/weekend/holiday/term as distinct number colours **and print the legend on the art**,
  and make the legend swatches use the *same* classes/colours as the cells. A legend that says
  "red = holiday" next to a blue holiday chip is a defect the reviewer will catch every time.
- Weekend-colour collision: a Saturday that is also a statutory holiday takes the holiday colour.
  Say so in the legend, or the two rules look inconsistent.

## Verification (do this before rendering, and report it)

Re-parse the generated HTML and assert, per month: the extracted day list equals
`range(1, ndays+1)`, the first day lands in the correct column, the year's term count is 24, and a
handful of key festival dates resolve to the expected Gregorian dates. Print a per-month table. A
passing render proves nothing about the dates; the re-parse is the check that actually catches a bad
column offset or a hardcoded 31.

Then run the normal `vision_analyze` pass on the rendered image for layout — but **never** use it to
confirm a date, a year, or a weekday. See the SKILL.md pitfall on rendered digits.

## Multi-month delivery

One file per month. Convert the rendered PNGs to JPEG with `quality=88, subsampling=1,
progressive=True` to land each page around ≤ 500 KB — a full-size PNG of a dense calendar page runs
several hundred KB to several MB and a 12-file delivery becomes an uncomfortable upload without it.
State the total count and the page dimensions in the delivery message.

## Year facts worth not getting wrong

- `calendar.isleap(y)` — do not assume February has 28 days, and do not hardcode 31 for month 12 in
  the next-month lookup; use `((date(y, m % 12 + 1, 1) - first).days)`.
- Week starts Monday in the Python `weekday()` convention; a Sunday-first display needs an explicit
  shift, and mixing the two silently moves every date by one column.
