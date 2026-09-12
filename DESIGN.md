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
    padding: "14px 16px"
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
- **Faint** (`{colors.faint}`): the smallest labels (sponsor eyebrows, fineprint)
  and inactive carousel dots. Deliberately as dark as "faint" gets: those uses
  are tiny text that needs the full 4.5:1, not the 3:1 large-text floor.
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
text, the portrait on a person page becomes full-width above the text, sponsor
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
  (`{components.chip-active}`) → oxblood fill, white label. Letters in the A–Z
  row are borderless 24px squares in muted, oxblood-filled when active,
  hairline-colored when no names start with them.

### Cards / Containers
- **Corner Style:** square (`{rounded.none}`).
- **Background:** paper white on the newsprint page.
- **Shadow Strategy:** none — a 1px rule border plus a 3px oxblood top edge.
- **Internal Padding:** 22–32px.
- **Featured card**: portrait (132×168, ruled frame) beside name / lifespan /
  three-line excerpt / "Read the full obituary →" in oxblood mono; fades in
  over 0.5s when it changes; hover to hover-wash with the name turning oxblood.
- **Sponsor card**: centered label ("OBITUARIES MADE POSSIBLE BY", tracked mono
  in muted) over 80px logos on the paper-white sheet.

### Inputs / Fields
- **Search** (`{components.input-search}`): the serif at 1rem in a paper-white
  box with a rule border, 14px 16px padding, italic placeholder in muted; the
  live count ("287 names") in mono beneath.
- **Form fields** (`{components.input-field}`): newsprint fill, rule border, 2px
  corners; labels above in mono caps.
- **Focus**: a 2px oxblood outline offset 2px (inputs also switch the border to
  oxblood). Never `outline: none` without this replacement. The caret and text
  selection are oxblood-tinted.

### Navigation
The masthead *is* the navigation: the flag (seal 52px beside the 34px
wordmark, one link home) over the tagline and the thick-over-thin ink rule,
then the surface's kicker and title. Static pages add a small mono "← All
obituaries" box top-left and a mono footer row ("← All obituaries · Browse the
full index →"), then the colophon. Browse controls on the register are the
chip rows (Month, A–Z) and two selects (Town, Funeral home) with mono labels.

### Register row (signature)
A 66px square portrait in a ruled frame (or a monogram tile: serif 700 initials
in oxblood on paper white with an inset hairline), beside the name in title
weight, the lifespan in mono, a one-line summary in body weight, and the
funeral home as a tracked mono caption. Rows divide with hairlines; the whole
row is one link that washes on hover and turns the name oxblood.

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
- **Do** honor reduced motion (the featured and mini fades are the only authored motion; all other transitions are 120–150ms and disable under `prefers-reduced-motion`).
- **Do** design the print state of a person page as a keepsake.

### Don't:
- **Don't** add a second accent, a gradient, a glow, or any drop shadow.
- **Don't** round a card; don't round a control past 2px; don't put an accent on a card's left or right edge.
- **Don't** use imagery from the funeral-products web — doves, candles, florals, soft-focus skies — or any decorative illustration around a notice.
- **Don't** set body copy or names in Oswald or Courier Prime; Oswald is the nameplate, Courier is for data.
- **Don't** put the tool's title above the newsroom's flag, and don't drop the colophon.
- **Don't** use pure black or pure white as text or ground; ink and newsprint are the poles.
- **Don't** let auto-advancing content run without a reachable pause; touch users get it by interacting.
