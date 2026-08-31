# Reboot Camp Coaching — Website + Ebook Builder

**Bill McGlone · Reboot Camp Coaching**

The primary deployed asset is the marketing site at [rebootcampcoaching.com](https://rebootcampcoaching.com) (`site/`). The ebook (`book/`) is a secondary lead magnet built from a single HTML source to PDF and EPUB.

## Site

```bash
python -m http.server 3737
```

Then open `http://localhost:3737/site/index.html`. Pages: `index.html`, `newsletter.html`, `podcast.html`, `spotify.html`. Shared nav behavior lives in `site/nav.js`.

## Ebook

```bash
pip install -r book/requirements.txt
python book/generate.py
```

Outputs to `book/output/`:
- `reboot-camp.pdf` — print-ready PDF
- `reboot-camp.epub` — Kindle/Apple Books compatible

Edit content in `book/index.html`; images live in `book/images/`.

## Deploy

Netlify builds from `netlify.toml` on push to `main`. The build flattens `site/` into the publish root and nests `book/` underneath it. A Netlify Function (`netlify/functions/beehiiv-posts.js`) proxies the Beehiiv newsletter RSS feed for `site/newsletter.html`.

## Brand

Blueprint palette — see `CLAUDE.md` for full spec.
