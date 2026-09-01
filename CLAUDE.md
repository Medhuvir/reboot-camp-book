# Reboot Camp Coaching — Claude Code Project

## Project Overview
The marketing site at [rebootcampcoaching.com](https://rebootcampcoaching.com) (`site/`) is the primary deployed asset. The **Reboot Camp: 10 Life-Altering Steps** ebook by Bill McGlone (`book/`) is a secondary lead magnet, built from a single HTML source to PDF and EPUB.

## Repo Structure
```
site/                    ← primary marketing website
  index.html              (homepage)
  newsletter.html         (Beehiiv posts, latest 5 via Netlify Function)
  podcast.html            (coming soon — nav link disabled via .nav-coming-soon)
  radio.html              (playlist embed, placeholder until Bill sends the ID)
  style.css               (shared Blueprint design tokens)
  landing.css             (site-specific overrides, nav behavior)
  nav.js                  (shared hamburger-menu toggle, used by every page incl. book/)
  images/                 (marketing-only + assets shared with book/)

book/                     ← ebook builder, secondary
  index.html               (ebook web source — references ../site/style.css, ../site/landing.css)
  generate.py               (build script: HTML → PDF + EPUB)
  export_to_docx.py         (HTML → Word doc for author review)
  requirements.txt
  content/chapters.md       (raw chapter text for reference)
  images/                   (chapter-only + assets shared with site/)
  output/reboot-camp.pdf    (committed; .epub and .docx are gitignored build output)

netlify/functions/beehiiv-posts.js   ← proxies the Beehiiv RSS feed (CORS workaround)
netlify.toml               ← build command flattens site/ into publish root, nests book/ underneath
robots.txt / sitemap.xml   ← repo root, scoped to rebootcampcoaching.com
```

Images that appear on both site and book pages (logo, favicon, DN Creative credit mark, a couple of shared photos) are **duplicated** into both `site/images/` and `book/images/` rather than shared via a cross-level path — simpler and lower-risk for a static site using relative paths. `book/index.html` does **not** get its own copy of `style.css`/`landing.css` — it cross-references `site/`'s via `../site/style.css`.

## Site (`site/`)

### Preview
```bash
python -m http.server 3737
```
Open `http://localhost:3737/site/index.html`.

### Nav
Every page (`site/*.html` and `book/index.html`) shares the same nav markup inside `<nav id="landing-nav">`: standard inline links (`.landing-nav-link`) + the Book a Call CTA button on desktop, with a `.nav-toggle` hamburger button that's hidden until ≤640px, where it replaces the (now-hidden) inline links and opens the `.nav-menu` drawer + `.nav-overlay` backdrop. Behavior is driven by `site/nav.js` (adds/removes a `.nav-open` class; button click, close button, overlay click, and Escape all close it). The `.landing-nav-link:not(.cta-button) { display: none; }` rule in `landing.css` is what hides the inline links at ≤640px — the toggle's own visibility is gated the opposite way (`display: none` by default, `display: flex` only inside that same breakpoint).

To flag a nav link as not-yet-live, add `nav-coming-soon` to its class list plus `aria-disabled="true" tabindex="-1"` (see the Podcast link) — existing CSS dims it and disables clicks, with a "Coming Soon" tooltip on desktop hover.

### Adding a new page
1. Create `site/<name>.html`, copying the `<head>` and nav block from an existing page.
2. Add it as both a `.landing-nav-link` (inline) and a `.nav-menu-link` (drawer) in **every** page's nav (site pages + `book/index.html`).
3. Add a `sed` line for it to `netlify.toml`'s build command.
4. Add it to `sitemap.xml` if it should be indexed.

## Ebook (`book/`)

### Quick Commands
```bash
pip install -r book/requirements.txt
python book/generate.py          # both PDF + EPUB
python book/generate.py --pdf    # PDF only
python book/generate.py --epub   # EPUB only
python book/export_to_docx.py    # HTML → Word doc for author review
open book/index.html             # preview in browser
```

### Brand System — Blueprint Palette
Always use these exact values:

| Token        | Hex       | Usage                          |
|-------------|-----------|--------------------------------|
| Midnight    | `#0F172A` | Chapter headers, cover BG      |
| Cloud White | `#F8FAFC` | Body background                |
| Cyan        | `#06B6D4` | Accent, borders, badges, links |
| Slate       | `#475569` | Muted text, captions           |
| Dark Text   | `#0F172A` | Body copy                      |

Logo treatment: `REBOOT` (weight 900) + `CAMP` (weight 200, opacity 55%), thin cyan rule underneath.

Navigation elements are always uppercase (`text-transform: uppercase`, not hardcoded caps in the HTML) — `.landing-nav-link`, `.nav-menu-link`, `.nav-toggle-label`, `.nav-menu-title`, `.nav-menu-cta`, and CTA buttons (`.cta-button`, `.cta-button-secondary`) all carry it. Any new nav item or nav-adjacent label should follow the same pattern.

### How to Edit Content

**Swap a chapter image** — find the image tag in `book/index.html`:
```html
<img src="images/image5.jpg" alt="..." class="chapter-image">
```
Drop a new file into `book/images/` and update the `src` path.

**Edit chapter text** — each chapter is an `<article class="chapter">` following a `<section class="chapter-opener">`. Paragraphs are `<p>`, bold is `<strong>`, italics are `<em>`.

**Add a pull quote:**
```html
<blockquote class="pull-quote">
  Between stimulus and response there is a space.
  <cite>— Viktor Frankl</cite>
</blockquote>
```

### How Images Work
- Place any `.jpg`, `.png`, or `.svg` in `book/images/`
- Reference with `images/filename.jpg` from inside `book/index.html`
- WeasyPrint resolves relative paths correctly for PDF export (`base_url` is set to `book/` in `generate.py`)
- EPUB packaging rewrites `images/` → `../images/` internally (chapters live in `text/`, images in `images/`) — this is handled automatically by `generate.py`, no manual edits needed

### Chapters in Order
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

### PDF Notes
- Generated via WeasyPrint
- Page size: US Letter (8.5×11) — change `@page` in `site/style.css` for A4
- Print-ready: `generate.py`'s `strip_web_elements()` removes the nav, progress bar, nav overlay, download dropdown, and CTA buttons before rendering
- Images must be local files (no external URLs in PDF mode)

### EPUB Notes
- Generated via ebooklib
- Compatible with: Kindle, Apple Books, Kobo, Google Play Books
- Each chapter's `<article class="chapter">` becomes one EPUB chapter
- SVG illustrations are embedded inline

## Beehiiv / Spotify / Podcast Integration

- **Newsletter signup** (all pages): Beehiiv embed script with `data-beehiiv-form="f8115a3a-3103-4c8f-bd59-3f20fd999560"` — reuse this exact form ID for any new signup CTA.
- **Newsletter posts** (`site/newsletter.html`): client-side `fetch('/api/beehiiv-posts')`, proxied server-side by `netlify/functions/beehiiv-posts.js` (RSS feed `https://rss.beehiiv.com/feeds/UvfEUB9QlF.xml`, avoids CORS). The function returns `title`, `description` (RSS subhead), `excerpt` (first real paragraph scraped from `content:encoded`, HTML-stripped), `link`, `pubDate`, and `image` (from `<enclosure>`) per post. Cards show `excerpt` (falling back to `description`), the thumbnail if `image` is present, and paginate client-side at 10 posts per page (Previous/Next, hidden when there's only one page) — nothing sends users off to Beehiiv's own archive except the true fetch-failure fallback link to `https://rebootcamp.beehiiv.com/archive`.
- **Spotify playlists** (`site/radio.html`): rendered as a stack of cards (reusing `.process-grid`/`.process-card`), one official Spotify iframe embed per playlist. IDs live in the `PLAYLIST_IDS` array in the page's own `<script>` — add a new playlist by appending its ID or full `open.spotify.com/playlist/...` URL to that array. Currently live: `6Ijih7xZ0GKLVmbZYFnJN0` ("Summer Camp '26 Mix", Reboot Radio profile). If the array is emptied, the page falls back to a "coming soon" placeholder.
- **Podcast** (`site/podcast.html`): live, same pattern as the newsletter — client-side `fetch('/api/podcast-episodes')` proxied by `netlify/functions/podcast-episodes.js` (podcast RSS feed `https://rss.beehiiv.com/podcasts/019fede3-607b-7f64-bcbf-b101b95dc069.xml`). Each episode card gets its `itunes:image` artwork (falling back to the channel image), title, date, formatted duration, description, and a native `<audio controls>` player pointed at the `<enclosure>` URL — no third-party embed needed. Falls back to a "coming soon" placeholder if the feed is empty or the fetch fails. The nav's `.nav-coming-soon` gate on Podcast was removed sitewide once real episodes existed.

## Common Tasks for Claude Code

**"Add Bill's photo to the About page"**
→ Drop the file into `book/images/`, find the About section in `book/index.html`, add `<img src="images/filename.jpg"/>`

**"Change the accent color from cyan to orange"**
→ In `site/style.css`, find `:root` and change `--cyan: #06B6D4` to the new value

**"Add a new section inside Step 3"**
→ Find the Step 3 `<article class="chapter">` in `book/index.html`, add HTML inside it

**"Make the PDF output A4 instead of Letter"**
→ In `site/style.css`, change `@page { size: letter; }` to `@page { size: A4; }`

**"Rebuild after ebook changes"**
→ `python book/generate.py` — outputs to `book/output/`

**"Add a newsletter post card manually"**
→ Posts render from live Beehiiv RSS via the Netlify Function — no manual card-adding needed; new Beehiiv posts appear automatically on next page load.

**"Add a new Spotify playlist"**
→ In `site/radio.html`, append the playlist's ID (or full URL) to the `PLAYLIST_IDS` array — it renders as a new card automatically, no other markup changes needed.
