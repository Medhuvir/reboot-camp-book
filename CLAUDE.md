# Reboot Camp Book — Claude Code Project

## Project Overview
This project builds the **Reboot Camp: 10 Life-Altering Steps** ebook by Bill McGlone.
Single HTML source → publishes to both **PDF** and **EPUB** with one command.

## Quick Commands
```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Generate both PDF and EPUB
python generate.py

# Generate PDF only
python generate.py --pdf

# Generate EPUB only  
python generate.py --epub

# Preview in browser (open src/index.html directly)
open src/index.html
```

## Project Structure
```
reboot-camp-book/
├── CLAUDE.md          ← You are here
├── README.md          ← Human docs
├── generate.py        ← Build script: HTML → PDF + EPUB (Blueprint v1.3)
├── requirements.txt   ← Python deps
├── src/
│   ├── index.html     ← Master document (all content lives here)
│   └── style.css      ← Blueprint design system
├── content/
│   └── chapters.md    ← Raw chapter text for reference
├── images/            ← Drop images here, reference in index.html
│   ├── cover.jpg      ← Cover photo (recommended: 1200x1600px)
│   ├── step1.jpg      ← Per-chapter images (optional)
│   └── ...
└── output/            ← Generated files land here
    ├── reboot-camp.pdf
    └── reboot-camp.epub
```

## Brand System — Blueprint Palette
Always use these exact values:

| Token        | Hex       | Usage                          |
|-------------|-----------|--------------------------------|
| Midnight    | `#0F172A` | Chapter headers, cover BG      |
| Cloud White | `#F8FAFC` | Body background                |
| Cyan        | `#06B6D4` | Accent, borders, badges, links |
| Slate       | `#475569` | Muted text, captions           |
| Dark Text   | `#0F172A` | Body copy                      |

Logo treatment: `REBOOT` (weight 900) + `CAMP` (weight 200, opacity 55%), thin cyan rule underneath.

## How to Edit Content

### Swap a chapter image
Find the image tag in `src/index.html`:
```html
<!-- CHAPTER: Step 1 -->
<section class="chapter" id="step1">
  <img src="../images/step1.jpg" alt="Own It" class="chapter-img"/>
```
Drop a new file into `images/` and update the `src` path. That's it.

### Edit chapter text
Each chapter is wrapped in a clear comment block:
```html
<!-- ══════════════════════════════════
     STEP 1: OWN IT
     ══════════════════════════════════ -->
<section class="chapter" id="step1">
```
Edit the HTML inside that section. Paragraphs are `<p>`, bold is `<strong>`, italics are `<em>`.

### Add a pull quote
```html
<blockquote class="pull-quote">
  Between stimulus and response there is a space.
  <cite>— Viktor Frankl</cite>
</blockquote>
```

### Add a new image anywhere
```html
<figure class="book-image">
  <img src="../images/my-photo.jpg" alt="Description"/>
  <figcaption>Optional caption here</figcaption>
</figure>
```

## How Images Work
- Place any `.jpg`, `.png`, or `.svg` in the `images/` folder
- Reference with `../images/filename.jpg` from inside `src/index.html`
- WeasyPrint resolves relative paths correctly for PDF export
- EPUB packages all images automatically

## Chapters in Order
1. Cover
2. Table of Contents
3. A Quick Note From Me (intro)
4. How to Get the Most Out of This Guide
5. Step 1: Own It
6. Step 2: Don't Look Back
7. Step 3: Start Now
8. Step 4: Strip Down
9. Step 5: Get Off the Grid
10. Step 6: Get in F#$k You Shape
11. Step 7: Scare Yourself on the Regular
12. Step 8: Emotions: Be a Master, Not a Slave
13. Step 9: Be Grateful
14. Step 10: Help Others
15. About the Author

## PDF Notes
- Generated via WeasyPrint
- Page size: US Letter (8.5×11) — change `@page` in style.css for A4
- Print-ready: no screen-only effects
- Images must be local files (no external URLs in PDF mode)

## EPUB Notes
- Generated via ebooklib
- Compatible with: Kindle, Apple Books, Kobo, Google Play Books
- Each `<section class="chapter">` becomes one EPUB chapter
- SVG illustrations are embedded inline

## Common Tasks for Claude Code

**"Add Bill's photo to the About page"**
→ Drop `bill-headshot.jpg` into `images/`, find `<!-- ABOUT THE AUTHOR -->` in index.html, add `<img src="../images/bill-headshot.jpg"/>`

**"Change the accent color from cyan to orange"**
→ In `src/style.css`, find `:root` and change `--accent: #06B6D4` to the new value

**"Add a new section inside Step 3"**
→ Find `<!-- STEP 3 -->` in index.html, add HTML inside that `<section>` block

**"Make the PDF output A4 instead of Letter"**
→ In `src/style.css`, change `@page { size: letter; }` to `@page { size: A4; }`

**"Rebuild after changes"**
→ `python generate.py` — outputs to `output/`
