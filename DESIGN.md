---
name: WPR Obituaries
description: A newspaper's obituary page, kept with care — newsprint, the paper's own flag, one line of oxblood.
colors:
  ink: "#1b1a18"
  newsprint: "#f6f2ea"
  paper-white: "#fffdf7"
  muted: "#6f6a61"
  faint: "#6d675f"
  rule: "#d9d3c6"
  hairline: "#e7e1d5"
  hover-wash: "#efe9dd"
  oxblood: "#7c2e36"
  oxblood-bright: "#9a3a43"
  on-oxblood: "#ffffff"
typography:
  display:
    fontFamily: "Oswald, 'Arial Narrow', system-ui, sans-serif"
    fontSize: "clamp(2.7rem, 9vw, 4rem)"
    fontWeight: 600
    lineHeight: 0.98
    letterSpacing: "0.02em"
  headline:
    fontFamily: "Merriweather, Georgia, 'Times New Roman', serif"
    fontSize: "clamp(2.1rem, 6vw, 3rem)"
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Merriweather, Georgia, 'Times New Roman', serif"
    fontSize: "1.32rem"
    fontWeight: 700
    lineHeight: 1.2
  body:
    fontFamily: "Merriweather, Georgia, 'Times New Roman', serif"
    fontSize: "1rem"
    fontWeight: 300
    lineHeight: 1.55
  lede:
    fontFamily: "Merriweather, Georgia, 'Times New Roman', serif"
    fontSize: "1.05rem"
    fontWeight: 300
    lineHeight: 1.6
  label:
    fontFamily: "'Courier Prime', 'Courier New', monospace"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.2em"
  meta:
    fontFamily: "'Courier Prime', 'Courier New', monospace"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0.02em"
rounded:
  none: "0"
  control: "2px"
  round: "50%"
spacing:
  xs: "8px"
  sm: "14px"
  md: "18px"
  lg: "22px"
  xl: "26px"
  2xl: "32px"
  3xl: "44px"
components:
  chip:
    backgroundColor: "{colors.newsprint}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "6px 9px"
  chip-hover:
    backgroundColor: "{colors.hover-wash}"
    textColor: "{colors.ink}"
  chip-active:
    backgroundColor: "{colors.oxblood}"
    textColor: "{colors.on-oxblood}"
  button-primary:
    backgroundColor: "{colors.oxblood}"
    textColor: "{colors.paper-white}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "10px 20px"
  button-secondary:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.oxblood}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "9px 18px"
  button-secondary-hover:
    backgroundColor: "{colors.hover-wash}"
    textColor: "{colors.oxblood}"
  button-more:
    backgroundColor: "{colors.newsprint}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "11px 12px"
    width: "100%"
  input-search:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "15px 16px 15px 46px"
  input-field:
    backgroundColor: "{colors.newsprint}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "9px 11px"
  card:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "22px 24px"
  sponsor-card:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "30px 28px 32px"
  mini-card:
    backgroundColor: "{colors.newsprint}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "16px 16px 14px"
    width: "380px"
  share-button:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.oxblood}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "6px 12px"
  share-button-hover:
    backgroundColor: "{colors.hover-wash}"
    textColor: "{colors.oxblood}"
---

# Design System: WPR Obituaries

## Overview

**Creative North Star: "The Memorial Page"**

This is a newspaper's obituary page done with care — Wausau Pilot & Review's
own page, not a memorial-products brand's. Everything sits on warm newsprint
under the paper's flag: the press seal beside the wordmark, the tagline, and a
thick-over-thin rule in ink. Names are set in the paper's reading serif;
datelines, labels, and lifespans in a typewriter face that echoes the
typewriter on WPR's badge; the nameplate in the condensed sans the site uses
for headings. One color speaks — oxblood — and it speaks rarely: the kicker,
the date headings, the active chip, the short rule beneath a name, the
three-pixel edge on a card. Portraits sit in hairline-ruled frames, very
slightly desaturated, like a photograph printed on paper.

The mood is **newsprint-honest** and **permanent**: the pages read as the
paper itself (rules, datelines, a flag, a colophon), and every page looks like
it will still be there in twenty years. Density is editorial rather than
app-like — generous leading, a single reading column, groups separated by
hairlines rather than boxes. The confirmed anti-reference is the
funeral-products web (Legacy.com and its kin): no pastel gradients, doves,
candles, stock florals, or upsell chrome around a notice.

**Key Characteristics:**
- Warm newsprint ground, near-black ink, one oxblood accent used sparingly
- Three faces with fixed jobs: Oswald nameplate, Merriweather reading serif, Courier Prime typewriter labels
- Structure from hairlines and rules, never from shadows or boxes
- Square-cornered cards marked on the top edge; near-square (2px) controls
- Portraits in ink-ruled frames, lightly desaturated (`grayscale(0.15)`)
- One authored motion moment per surface (a 0.5s fade on the featured card); everything else is a 120–150ms state change
- Reads as WPR: flag, thick-over-thin rule, tagline, colophon with provenance and phone

## Colors

A newsprint palette — warm cream ground, near-black ink, a warm-grey scale for
secondary text and rules — with a single oxblood accent chosen for a memorial
surface in place of the site's teal.

### Primary
- **Oxblood** (`{colors.oxblood}`): the only voice color. Kickers ("In Memoriam"),
  date headings in the register, the active chip and letter, the 54px rule
  under a person's name, the 3px top edge on cards, links and share buttons,
  focus rings, the caret and text selection. It ties to the sponsors' crimson.
- **Oxblood, bright** (`{colors.oxblood-bright}`): hover state for oxblood text
  and links only. Never a fill.
- **On oxblood** (`{colors.on-oxblood}`): text on an oxblood fill (active chips,
  the primary button uses paper-white instead).

### Neutral
- **Ink** (`{colors.ink}`): all reading text, names, the flag rule, the OG card
  type. Never pure black.
- **Newsprint** (`{colors.newsprint}`): the page ground and the register's own
  surface (chips, the "show earlier" control, form fields).
- **Paper white** (`{colors.paper-white}`): the lighter sheet for things that sit
  *on* the page — the featured card, sponsor card, search input, secondary
  buttons, portrait placeholders.
- **Muted** (`{colors.muted}`): secondary text — lifespans, ledes, arrangements
  lines, the colophon, inactive letters. 4.8:1 on newsprint.
- **Faint** (`{colors.faint}`): the search placeholder, the smallest labels
  (sponsor eyebrows, fineprint), and inactive carousel dots. Deliberately as dark as "faint" gets: those uses are tiny text that needs the
  full 4.5:1, not the 3:1 large-text floor.
- **Rule** (`{colors.rule}`): borders on cards, controls, portrait frames, the
  hairline that closes the masthead, the archive's first-row rule.
- **Hairline** (`{colors.hairline}`): the lightest divider — between register
  rows, under the mini widget's sponsor line, the inset ring on monogram tiles.
- **Hover wash** (`{colors.hover-wash}`): background on hover for rows, chips,
  cards, and secondary buttons.

### Named Rules
**The One Voice Rule.** Oxblood is the only chromatic color on any surface and
appears on well under a tenth of it. Its rarity is what makes a kicker or a
date heading read as the paper's voice. A second accent is a redesign, not a
tweak.

**The Contrast-Is-Measured Rule.** Every text color is checked against the
surface it actually sits on (newsprint or paper white), never against white
by habit. `faint` exists because "lighter grey for small text" fails AA on
cream.

## Typography

**Display Font:** Oswald (with Arial Narrow, system-ui) — the WPR nameplate face
**Body Font:** Merriweather (with Georgia) — the WPR reading serif
**Label/Mono Font:** Courier Prime (with Courier New) — the typewriter accent

**Character:** The Newspack "Joseph" pairing the newsroom's own site uses,
with the typewriter face added for everything that would have been typed on a
dateline: labels, lifespans, counts, the tagline. Oswald appears exactly once
per surface (the OBITUARIES nameplate or the OG card's newsroom name); names
and reading text are always the serif, weight-contrasted (700 names over 300
body) rather than size-contrasted.

### Hierarchy
- **Display** (`{typography.display}`): the register's OBITUARIES nameplate only —
  uppercase Oswald at `clamp(2.7rem, 9vw, 4rem)`, line-height 0.98.
- **Headline** (`{typography.headline}`): a person's name atop their page —
  Merriweather 700 at `clamp(2.1rem, 6vw, 3rem)`, tracked in slightly. Also the
  funeral-home and archive page titles.
- **Title** (`{typography.title}`): names in the register (1.32rem) and on the
  featured card (1.5rem); Merriweather 700, line-height 1.15–1.2,
  `overflow-wrap: anywhere` so a long surname can never overflow a row.
- **Body** (`{typography.body}`): summaries and obituary text — Merriweather 300,
  1rem in the register, 1.06rem on a person page, leading 1.55–1.7. Reading
  columns are 680–720px wide (~70ch).
- **Lede** (`{typography.lede}`): the italic 300 line under the nameplate and the
  arrangements line — muted, never more than 44ch.
- **Label** (`{typography.label}`): Courier Prime, 11–12px, uppercase, tracked
  0.2–0.32em — kickers, section labels, chips, buttons, date headings. Wider
  tracking for shorter lines (the "In Memoriam" eyebrow at 0.32em, the tagline
  at 0.28em, the sponsor label at 0.24em).
- **Meta** (`{typography.meta}`): Courier Prime at 12.5px with light tracking —
  lifespans ("1957 – 2026"), counts, the colophon.

### Named Rules
**The Weight-Not-Size Rule.** In the register a name and its summary sit two
weights apart (700 / 300) at nearly the same size; hierarchy comes from
weight and the mono/serif contrast, not from a big type step.

**The Typewriter-Means-Data Rule.** Courier Prime is for things that would be
typed on a form: dates, labels, counts, lifespans, the tagline. It is never a
"technical" costume for body copy.

## Layout

A single reading column, centered: 720px for the register (`.page`, padding
44px 24px 80px), 680px for a person page (`.wrap`, same padding). The masthead
is centered; everything below it is left-aligned. Sections separate with
hairlines and whitespace rather than boxes — a register group is a mono date
heading in oxblood over rows divided by `hairline` lines; a person page is
name, lifespan, a 54px oxblood rule, then text with the portrait floated right
at 184px (max 42%).

Spacing follows a loose 4px rhythm with the observed steps 8 / 14 / 18 / 22 /
26 / 32 / 44. Tight inside a group (3–8px between a name and its lifespan,
10–12px between rows), generous between groups (26–48px). Cards use 22–32px of
internal padding; controls 6–14px.

Responsive behavior at one breakpoint, 480px: the flag scales down (seal 44px,
wordmark 27px, tagline tracking 0.2em), the featured card stacks portrait over
text, the browse selects go full-width with their labels stacked, the portrait
on a person page becomes full-width above the text, sponsor
logos shrink (72px), and control padding tightens. Both embeds post their own
height to the WordPress parent so the iframe never scrolls; the register is
paginated 60 rows at a time to keep that height bounded.

Print is a designed state on person pages: a centered nameplate, the portrait
above the text, chrome hidden (navigation, share, sponsor card, related links),
the colophon kept — a keepsake, not a screenshot.

## Elevation & Depth

Flat. There are no drop shadows anywhere in the system; depth is conveyed by
tone (paper white sitting on newsprint), by hairlines and rules, and by the
3px oxblood edge that marks a card as a thing placed on the page. The one
`box-shadow` in use is an inset 1px hairline ring on monogram tiles (portrait
placeholders), which is a border, not elevation. The featured card and the
mini widget are the "raised" objects and they achieve it entirely with the
lighter sheet plus a 1px rule border.

### Named Rules
**The No-Shadow Rule.** Nothing floats. If an element needs to read as on top
of the page, give it the paper-white sheet and a rule; never a shadow.

**The Edge-On-Top Rule.** Cards mark themselves with a 3px oxblood border on
the top edge only — the WPR house convention. No side accents, no full
oxblood outlines.

## Shapes

Print geometry. Cards and sheets are square-cornered (0). Controls — chips,
buttons, inputs — carry a near-square 2px radius that reads as a printed box
rather than a pill. The only true rounds are the press seal, portrait
placeholders' monogram tiles, carousel dots, and the prev/next arrows (50%).
Portraits are rectangles in a 1px `rule` frame with a light `grayscale(0.15)`,
never circles. Rules are horizontal and thin (1px hairline, 1px rule) except
two deliberate heavy strokes: the 3px-over-1px ink flag rule under the
masthead, and the 3px oxblood card edge / 54px name rule.

## Components

### Buttons
Set in type, not drawn: a Courier Prime label inside a 1px `rule` box, 2px
corners, no shadow, a 120–150ms background/border change on hover, a 2px
oxblood outline (offset 2px) on keyboard focus.
- **Primary** (`{components.button-primary}`): oxblood fill, paper-white label,
  used once per flow ("Open email to send").
- **Secondary** (`{components.button-secondary}`): paper-white fill, oxblood
  label ("Submit an obituary", share buttons on a page); hover to hover-wash.
- **Show earlier** (`{components.button-more}`): full-width, newsprint fill, ink
  label with a hairline-divided count ("227 more").
- **Arrows**: 34px round paper-white buttons with a rule border for the
  carousel, 85% opacity at rest.

### Chips
- **Style** (`{components.chip}`): mono 12px label, newsprint fill, 1px rule
  border, 2px corners, 6px 9px padding. A count sits after a hairline divider
  inside the chip ("June 2026 | 148").
- **State**: hover → hover-wash with a muted border; active
  (`{components.chip-active}`) → oxblood fill, paper-white label (every chip
  carries `aria-pressed`). Letters in the last-name row are borderless 24px
  squares in muted, oxblood-filled when active; only letters that begin a
  surname are rendered — a shorter row reads as the index it is, an A–Z row
  with invisible gaps reads as broken.

### Cards / Containers
- **Corner Style:** square (`{rounded.none}`).
- **Background:** paper white on the newsprint page.
- **Shadow Strategy:** none — a 1px rule border plus a 3px oxblood top edge.
- **Internal Padding:** 22–32px.
- **Featured card**: portrait (132×168, ruled frame) beside name / lifespan /
  three-line excerpt / "Read the full obituary →" in oxblood mono; fades in
  over 0.5s when it changes; hover to hover-wash with the name turning oxblood.
  The strip holds **five** of this week's portraits, newest death first (the
  same set on every visit — not a shuffle), and it follows the newest day's
  names rather than standing between the search and its results. The dots are
  one keyboard stop with a roving tabindex (arrow keys move between them), so
  the strip costs a keyboard reader five stops, not fourteen. Beside the dots
  sits a visible mono **Pause / Play** control (28px tall, labelled "Pause
  auto-advance" / "Resume auto-advance"; auto-advance also stops for good
  after any arrow or dot choice). The live region carries a name only after a
  change the reader asked for — someone reading the register is never
  interrupted every 6.5 seconds. **Not rendered on phones at all** (the
  component unmounts, so nothing advances or announces behind a hidden
  section): there the first name must land within a screen of the search, and
  the mini widget already puts a face in the article.
- **Featured card** ("Recently Remembered"): portrait (132×168, ruled frame)
  beside name / lifespan / three-line excerpt / "Read the full obituary →" in
  oxblood mono; fades in over 0.5s when it changes; hover to hover-wash with
  the name turning oxblood. It opens the default view, under the search, and
  stands down the moment the reader searches or browses. The strip holds
  **five** faces drawn at random from the past month's notices, so a different
  handful gets its moment on each visit; the draw happens once per visit, so the
  strip stays put while the reader is on the page. The dots are one keyboard
  stop with a roving tabindex
  (arrow keys move between them), so the strip costs a keyboard reader five
  stops, not fourteen. Beside them sits a visible mono **Pause / Resume**
  control (28px tall, its visible word contained in its accessible name;
  auto-advance also stops for good after any arrow or dot choice). The live
  region carries a name only after a change the reader asked for, so someone
  reading the register is never interrupted every 6.5 seconds. On phones the
  card stacks portrait over text.
- **Sponsor card**: centered label ("OBITUARIES MADE POSSIBLE BY", tracked mono
  in muted) over 80px logos on the paper-white sheet — the sponsors' full-size
  placement, in the footer.
- **Presented-by line**: the sponsors' second placement rides in the nameplate,
  between the tagline and the ink rule, the way a newspaper section credits its
  underwriter: the 11px tracked label beside 28px logos (24px on phones) on one
  wrapping line. Nothing sits between the search and its results.

### Inputs / Fields
- **Search** (`{components.input-search}`): the product's one primary control,
  placed directly under the lede with nothing between it and its results. A
  serif label at body size ("Find a name"), a drawn search glyph inside the
  field, the serif at 1.1rem in a paper-white box with a **2px muted border**
  (5.3:1 — a boundary a low-vision reader can find on cream; the 1px rule was
  1.5:1), italic placeholder; the browser's clear glyph is redrawn in muted ink
  (oxblood on hover) so no off-palette pixel appears in the field. The live
  count in mono beneath always states what the number is *of* ("276 names ·
  the last 3 months", "36 names · last names beginning with J", "2 names · 3
  more mentions"). Matching is by name token prefix, so "Allan Jensen" finds
  Allan Guy Jensen; records that only *mention* the query list in a second
  tier; a hyphenated surname is two names to the searcher, so "Tugnoli"
  reaches "Latzig-Tugnoli". Enter dismisses the phone keyboard (results are
  already live). The
  search and any browse filter mirror into the URL (`?q=`, `?month=`,
  `?letter=`, `?town=`, `?home=`) so Back and a shared link reopen the list.
- **Form fields** (`{components.input-field}`): newsprint fill, rule border, 2px
  corners; labels above in mono caps.
- **Focus**: a 2px oxblood outline offset 2px (inputs also switch the border to
  oxblood). Never `outline: none` without this replacement. The caret and text
  selection are oxblood-tinted.

### Navigation
The masthead *is* the navigation: the flag (seal 52px beside the 34px
wordmark, one link home) over the tagline, the sponsors' presented-by line,
and the thick-over-thin ink rule, then the surface's kicker and title. Static pages add a small mono "← All
obituaries" box top-left and a mono footer row ("← All obituaries · Browse the
full index →"), then the colophon. Browse on the register is a secondary path
and lives behind **one disclosure** ("Browse by month or last name" — an
oxblood mono link with a small ruled +/– mark, naming what is immediately
inside rather than everything nested under it), closed
unless a filter is active; inside, two rows — Month (Last 3 months · All · up
to six month chips with three or more names, the rest in an "Earlier…"
select) and Last name — with 11px mono labels and no box around them, then a
second-tier line ("More ways to browse: town, funeral home") that reveals the
two selects, so the open panel is two rows, not a control deck. A letter
browse lists surnames alphabetically under one heading. On phones the selects
go full-width with their labels stacked above.

### Register row (signature)
A 66px square portrait in a ruled frame (or a monogram tile: serif 700 initials
in oxblood on paper white with an inset hairline), beside the name in title
weight, a mono **fact line** (lifespan · town — the confirming facts outside
the sentence — age joins them only where the years do not already carry it),
and the funeral home as a tracked mono caption. There is no summary line: the
extractor writes one sentence naming the person, their age and their town, and
every one of those facts is already on the row or in its date heading. Rows divide with hairlines; the whole
row is one link that washes on hover and turns the name oxblood. Groups are
headed by the **date of death** in oxblood mono ("Died September 2, 2026"; the
few records without one say "Published …") — the register is a calendar of
deaths, not of editions.

### Second tier (mentions and arrangements)
A row is a promise that this person is who you searched for, so anything that
is not a person of that name says what it is instead:
- **A funeral home's own name** ("Schmidt" is also Schmidt & Schulta) never
  becomes rows. One oxblood mono line above a rule — "68 notices arranged by
  Schmidt & Schulta Funeral Home →" — filters to that home.
- **A mention** (a maiden name, a surviving relative, a hall named for a
  family) keeps its row but replaces its summary with the **evidence line**:
  the phrase around the hit in 12px Courier muted, the matched word washed in
  hover-wash rather than highlighted, six words either side, ellipses outside.
  Ten at a time under "Also named in N other notices" (just "Named in N
  notices" when no name matched), then "Show the rest".

### Empty state
A dead end on a memorial page must offer a way forward and never end on the
sponsor card: "No one named “…” is listed yet." in ink, then a row of
secondary-style actions (Clear the search · Browse by last name · Not listed?
Submit an obituary), then a muted italic hint about spellings and notices
that haven't arrived yet. Each action hands focus to what it opened: the
search field after Clear, the first letter after Browse, the first field
after Submit — never to nothing.

### Failure state
The one state the reader cannot fix by typing differently, so it says so and
offers a way on: "Obituaries are unavailable right now. This is usually
temporary." in ink, a secondary **Try again** that refetches in place, and the
footer beneath it — the index link and the colophon, which is where the
newsroom's phone number is. Never a raw status code.

### Share buttons
A row on every person page — "SHARE" as a tracked mono label, then Facebook /
Copy link / Email / Save as PDF as four secondary-style boxes
(`{components.share-button}`): Courier Prime 12px in oxblood on paper white,
1px rule border, 2px corners, 6px 12px padding; hover to hover-wash. "Copy
link" confirms inline by swapping its own label to "Link copied" for 1.5s —
no toast, no icon. The row is hidden in print.

### Mini widget card (signature)
The compact article/sidebar embed (`{components.mini-card}`): a 380px-wide
newsprint sheet with a 1px rule border and the 3px oxblood top edge, 16px
padding. Inside, top to bottom: the "In Memoriam · WPR" kicker (10.5px mono,
tracked 0.22em, oxblood, centered); one card — a 72×90 ruled portrait (or a
monogram tile) beside the name (serif 700, 1.08rem), the lifespan in 11.5px
mono, and a two-line clamped summary in body weight; a centered nav row of
30px round paper-white arrows around 6px dots (faint, oxblood when active, in
22px hit areas); "View all obituaries →" in oxblood mono; and a hairline-topped
sponsor strip with a 9.5px tracked label over 26px logos. The card fades in
over 0.45s on change and auto-advances every 6s until hovered, focused, or
touched. Everything is scoped under `.mini` so it can never bleed into a host
page.

### Colophon (signature)
The 44px seal beside two mono lines in muted: the provenance sentence, then
"Wausau Pilot & Review · 715-301-5539 — <tagline>". Present at the foot of the
register and every static page; it survives print.

### Share card (OG image)
1200×630 on newsprint with the 8px oxblood bar across the top: the portrait
(360×424, ruled) at left, "I N   M E M O R I A M" spaced in oxblood mono, the
name in Merriweather Bold at 66px (shrinking to 42px, breaking after hyphens),
the lifespan in mono at 34px in muted, and the newsroom name in Oswald
SemiBold over the sponsor line at the foot.

## Do's and Don'ts

### Do:
- **Do** keep oxblood to labels, edges, rules, and one active state per row of controls; the page should read as ink on newsprint with one color speaking.
- **Do** separate groups with hairlines and whitespace; put the 3px oxblood edge on a card's top only.
- **Do** measure every text color against the surface it sits on (newsprint 4.5:1 for small text; muted and faint already pass, rule and hairline never do).
- **Do** set every control in Courier Prime caps inside a 1px rule box with 2px corners; primary actions get the single oxblood fill.
- **Do** keep portraits rectangular in a ruled frame with the light desaturation, and never crop them to circles.
- **Do** keep the flag intact on every surface: seal beside wordmark linking home, tagline, thick-over-thin ink rule, the surface's own title below it.
- **Do** honor reduced motion (the featured and mini fades are the only authored motion; the loading skeleton is a still hairline block, not a shimmer; all other transitions are 120–150ms and disable under `prefers-reduced-motion`).
- **Do** keep the smallest type on the register and the pages at 11px (the tagline, sponsor labels, funeral-home captions, the colophon — only the mini widget, at card scale, runs smaller) and every control at a 24px minimum target, even when its visible mark is smaller.
- **Do** design the print state of a person page as a keepsake.

### Don't:
- **Don't** add a second accent, a gradient, a glow, or any drop shadow.
- **Don't** round a card; don't round a control past 2px; don't put an accent on a card's left or right edge.
- **Don't** use imagery from the funeral-products web — doves, candles, florals, soft-focus skies — or any decorative illustration around a notice.
- **Don't** set body copy or names in Oswald or Courier Prime; Oswald is the nameplate, Courier is for data.
- **Don't** put the tool's title above the newsroom's flag, and don't drop the colophon.
- **Don't** use pure black or pure white as text or ground; ink and newsprint are the poles.
- **Don't** let auto-advancing content run without a reachable pause; touch users get it by interacting.
