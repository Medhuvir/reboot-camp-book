#!/usr/bin/env python3
"""
generate.py - Reboot Camp book builder
Usage:
  python generate.py          -> both PDF + EPUB
  python generate.py --pdf    -> PDF only
  python generate.py --epub   -> EPUB only
"""

import argparse
import os
import re
import sys
from pathlib import Path

ROOT     = Path(__file__).parent
SRC      = ROOT / 'src' / 'book'
CSS      = ROOT / 'src' / 'style.css'
IMAGES   = ROOT / 'images'
OUTPUT   = ROOT / 'output'
HTML     = SRC / 'index.html'

OUTPUT.mkdir(exist_ok=True)


# ─── Helpers ────────────────────────────────────────────────────────────────

def read_html():
    with open(HTML, encoding='utf-8') as f:
        return f.read()

def log(msg):
    print(f'  {msg}')

# Patterns for elements that only make sense on the web
_WEB_ONLY = [
    # progress bar
    re.compile(r'<div[^>]*\bid="progress-bar"[^>]*>.*?</div>', re.DOTALL | re.IGNORECASE),
    # site navigation
    re.compile(r'<nav\b[^>]*>.*?</nav>', re.DOTALL | re.IGNORECASE),
    # nav overlay backdrop
    re.compile(r'<div[^>]*\bid="nav-overlay"[^>]*>.*?</div>', re.DOTALL | re.IGNORECASE),
    # download dropdown on cover
    re.compile(r'<div[^>]*\bclass="download-dropdown"[^>]*>.*?</div>', re.DOTALL | re.IGNORECASE),
    # CTA button (external call-booking link)
    re.compile(r'<a[^>]*\bclass="cta-button"[^>]*>.*?</a>', re.DOTALL | re.IGNORECASE),
    # all inline scripts
    re.compile(r'<script\b[^>]*>.*?</script>', re.DOTALL | re.IGNORECASE),
]

def strip_web_elements(html):
    for pattern in _WEB_ONLY:
        html = pattern.sub('', html)
    return html


# ─── PDF ────────────────────────────────────────────────────────────────────

def build_pdf():
    try:
        from weasyprint import HTML as WP
    except ImportError:
        print('WeasyPrint not found. Run: pip install weasyprint')
        sys.exit(1)

    out = OUTPUT / 'reboot-camp.pdf'
    log('Building PDF...')

    clean = strip_web_elements(read_html())
    WP(string=clean, base_url=str(SRC)).write_pdf(str(out))
    size_kb = out.stat().st_size // 1024
    log(f'Done -> output/reboot-camp.pdf  ({size_kb} KB)')


# ─── EPUB ────────────────────────────────────────────────────────────────────

CHAPTERS = [
    ('toc',     'Contents',                           ''),
    ('note',    'A Quick Note From Me',               ''),
    ('step1',   'Own It',                             'Step 1'),
    ('step2',   "Don't Look Back",                    'Step 2'),
    ('step3',   'Start Now',                          'Step 3'),
    ('step4',   'Strip Down',                         'Step 4'),
    ('step5',   'Get Off the Grid',                   'Step 5'),
    ('step6',   "Strive for 'F#$k You' Shape",        'Step 6'),
    ('step7',   'Scare Yourself on the Regular',      'Step 7'),
    ('step8',   'Emotions: Be a Master, Not a Slave', 'Step 8'),
    ('step9',   'Be Grateful',                        'Step 9'),
    ('step10',  'Help Others',                        'Step 10'),
    ('about',   'About the Author',                   ''),
]

# Title page XHTML — shown right after the cover image in EPUB readers
_TITLE_PAGE = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<!DOCTYPE html>'
    '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">'
    '<head><title>Reboot Camp</title><meta charset="utf-8"/>'
    '<link rel="stylesheet" href="../style/main.css" type="text/css"/></head>'
    '<body>'
    '<section epub:type="titlepage" style="'
    'background:#0F172A;min-height:100vh;display:flex;flex-direction:column;'
    'justify-content:center;align-items:flex-start;padding:60px 48px;">'
    '<span style="font-size:9px;font-weight:900;letter-spacing:0.4em;'
    'text-transform:uppercase;color:#06B6D4;display:block;margin-bottom:16px;">'
    'Bill McGlone</span>'
    '<h1 style="font-size:48px;font-weight:900;letter-spacing:-0.03em;'
    'text-transform:uppercase;color:#F8FAFC;line-height:1.05;margin-bottom:16px;">'
    'Reboot Camp</h1>'
    '<p style="font-size:18px;font-weight:300;color:rgba(248,250,252,0.75);'
    'line-height:1.5;max-width:480px;margin-bottom:32px;">'
    '10 Life-Altering Steps to Take You From <em>Surviving</em> to <em>Thriving</em> After 40'
    '</p>'
    '<div style="width:48px;height:2px;background:#06B6D4;"></div>'
    '</section>'
    '</body></html>'
)


_EPUB_CSS = """
/* ============================================
   REBOOT CAMP — EPUB STYLESHEET
   Hardcoded values only; no CSS variables.
   Dark-on-light for universal reader compat.
   ============================================ */

body {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 1em;
  line-height: 1.75;
  color: #1a1a1a;
  background: #ffffff;
  margin: 0;
  padding: 0;
}

/* ── Layout ─────────────────────────────── */
.ebook-body {
  max-width: 100%;
  margin: 0 auto;
  padding: 0 1.2em;
}

/* ── Cover (title page fallback) ─────────── */
.cover, .cover-content { display: none; }

/* ── TOC ─────────────────────────────────── */
.toc-section {
  background: #f8fafc;
  padding: 2em 1.2em;
  border-bottom: 2px solid #06B6D4;
}
.toc-inner { max-width: 100%; }
.toc-overline {
  display: block;
  font-size: 0.65em;
  font-weight: bold;
  letter-spacing: 0.35em;
  text-transform: uppercase;
  color: #06B6D4;
  margin-bottom: 0.5em;
}
.toc-heading {
  font-size: 1.8em;
  font-weight: bold;
  text-transform: uppercase;
  color: #0F172A;
  margin-bottom: 1.2em;
  letter-spacing: -0.02em;
}
.toc-list {
  list-style: none;
  padding: 0;
  margin: 0;
  border-top: 1px solid #cbd5e1;
}
.toc-list li {
  border-bottom: 1px solid #cbd5e1;
}
.toc-list a {
  display: flex;
  gap: 0.75em;
  padding: 0.75em 0;
  text-decoration: none;
  color: #1a1a1a;
  font-size: 0.9em;
}
.toc-num {
  font-size: 0.65em;
  font-weight: bold;
  letter-spacing: 0.2em;
  color: #06B6D4;
  text-transform: uppercase;
  min-width: 2.4em;
  flex-shrink: 0;
  padding-top: 0.15em;
}
.toc-title { flex: 1; }

/* ── Chapter opener ──────────────────────── */
.chapter-opener {
  background: #f1f5f9;
  padding: 2.5em 1.2em 2em;
  border-left: 4px solid #06B6D4;
  margin-bottom: 0;
}
.step-number {
  display: block;
  font-size: 4em;
  font-weight: bold;
  color: #cbd5e1;
  line-height: 1;
  margin-bottom: 0.1em;
  letter-spacing: -0.04em;
}
.step-label {
  display: block;
  font-size: 0.65em;
  font-weight: bold;
  letter-spacing: 0.35em;
  text-transform: uppercase;
  color: #06B6D4;
  margin-bottom: 0.6em;
}
.chapter-title {
  font-size: 1.9em;
  font-weight: bold;
  text-transform: uppercase;
  color: #0F172A;
  line-height: 1.1;
  letter-spacing: -0.02em;
  margin-bottom: 1em;
}

/* ── Section opener (non-step) ───────────── */
.section-opener {
  background: #f8fafc;
  padding: 2em 1.2em 1.5em;
  border-left: 4px solid #06B6D4;
}
.accent-rule {
  width: 3em;
  height: 2px;
  background: #06B6D4;
  margin-bottom: 1em;
}
.section-title {
  font-size: 1.7em;
  font-weight: bold;
  text-transform: uppercase;
  color: #0F172A;
  letter-spacing: -0.02em;
  margin-bottom: 0.5em;
}

/* ── Chapter body ────────────────────────── */
.chapter {
  padding: 1.8em 1.2em;
}
.body-text p {
  margin-bottom: 1em;
  color: #1a1a1a;
}

/* ── Pull quote ──────────────────────────── */
.pull-quote {
  border-left: 3px solid #06B6D4;
  margin: 1.5em 0;
  padding: 0.8em 1.2em;
  background: #f8fafc;
}
.pull-quote p {
  font-style: italic;
  font-size: 1.05em;
  color: #1e293b;
  margin-bottom: 0.4em;
}
.pull-quote cite {
  font-size: 0.8em;
  color: #475569;
  font-style: normal;
}

/* ── Affirmation ─────────────────────────── */
.affirmation {
  border: 2px solid #06B6D4;
  padding: 1em 1.2em;
  margin: 1.5em 0;
  text-align: center;
  font-style: italic;
  font-size: 1.05em;
  color: #0F172A;
  background: #f0fafe;
}

/* ── Statement ───────────────────────────── */
.statement {
  font-size: 1.15em;
  font-weight: bold;
  color: #0F172A;
  margin: 1.2em 0;
  line-height: 1.5;
}

/* ── The Action ──────────────────────────── */
.the-action {
  border-top: 2px solid #06B6D4;
  border-bottom: 2px solid #06B6D4;
  padding: 1.2em;
  margin: 1.8em 0;
  background: #f8fafc;
}
.action-label {
  display: block;
  font-size: 0.65em;
  font-weight: bold;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: #06B6D4;
  margin-bottom: 0.5em;
}
.action-text {
  color: #1a1a1a;
  font-size: 0.95em;
}

/* ── Callout ─────────────────────────────── */
.callout {
  border-left: 3px solid #94a3b8;
  padding: 0.8em 1em;
  margin: 1.2em 0;
  background: #f8fafc;
  color: #1e293b;
  font-size: 0.95em;
}
.callout.cyan { border-left-color: #06B6D4; }

/* ── Stats ───────────────────────────────── */
.stat-block {
  display: block;
  margin: 1.5em 0;
}
.stat-item {
  display: block;
  margin-bottom: 1em;
  padding-bottom: 1em;
  border-bottom: 1px solid #e2e8f0;
}
.stat-number {
  display: block;
  font-size: 2em;
  font-weight: bold;
  color: #06B6D4;
  line-height: 1;
}
.stat-label {
  font-size: 0.85em;
  color: #475569;
}

/* ── Formula ─────────────────────────────── */
.formula {
  font-size: 1.1em;
  font-weight: bold;
  text-align: center;
  color: #0F172A;
  margin: 1.5em 0;
  padding: 1em;
  border: 1px solid #e2e8f0;
}

/* ── Sign-off ────────────────────────────── */
.sign-off {
  border-top: 1px solid #06B6D4;
  margin-top: 2em;
  padding-top: 1em;
  color: #475569;
  font-style: italic;
}

/* ── Images ──────────────────────────────── */
.image-wrap {
  margin: 1.5em 0;
  text-align: center;
}
.chapter-image {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
}
.image-caption {
  font-size: 0.75em;
  color: #475569;
  margin-top: 0.4em;
  font-style: italic;
}

/* ── About section ───────────────────────── */
.about-section {
  padding: 2em 1.2em;
  background: #f8fafc;
  border-top: 3px solid #06B6D4;
}
.about-inner { max-width: 100%; }
.author-2col { display: block; }
.author-photo {
  max-width: 160px;
  height: auto;
  border: 2px solid #06B6D4;
  display: block;
  margin-bottom: 1em;
}
.author-name {
  font-size: 1.6em;
  font-weight: bold;
  color: #0F172A;
  margin-bottom: 0.2em;
}
.author-role {
  display: block;
  font-size: 0.65em;
  font-weight: bold;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: #06B6D4;
  margin-bottom: 1em;
}
.about-text { color: #1a1a1a; font-size: 0.95em; }
.about-text p { margin-bottom: 0.9em; }

/* ── Footer ──────────────────────────────── */
.ebook-footer {
  text-align: center;
  padding: 1.5em 1em;
  border-top: 1px solid #e2e8f0;
  margin-top: 2em;
}
.footer-signoff {
  font-style: italic;
  color: #475569;
  margin-bottom: 0.5em;
}
.footer-legal {
  font-size: 0.75em;
  color: #94a3b8;
}
.footer-producer, .dn-credit, .dn-produced, .dn-name, .dn-icon {
  display: none;
}
"""


def _find_tag_end(html, start):
    """Find the position after the closing tag that matches the opening tag at start."""
    # Determine the tag name
    m = re.match(r'<(\w+)', html[start:])
    if not m:
        return start
    tag = m.group(1)

    depth = 0
    pos = start
    pattern = re.compile(rf'</?{tag}[\s>]', re.IGNORECASE)
    while pos < len(html):
        hit = pattern.search(html, pos)
        if not hit:
            break
        if html[hit.start():hit.start()+2] == '</':
            depth -= 1
            if depth == 0:
                # Find the actual end of this closing tag
                close_end = html.index('>', hit.end()) + 1
                return close_end
        else:
            depth += 1
        pos = hit.end()
    return len(html)


def extract_chapters(html_src):
    """
    Extract chapter content by ID.
    For each chapter ID, finds the section/article with that id=,
    then includes any immediately following <article class="chapter">.
    """
    found = {}

    for ch_id, _, _ in CHAPTERS:
        id_attr = f'id="{ch_id}"'
        idx = html_src.find(id_attr)
        if idx == -1:
            continue

        # Walk back to the opening < of this tag
        tag_start = html_src.rfind('<', 0, idx)
        if tag_start == -1:
            continue

        # Find end of this section/article element
        section_end = _find_tag_end(html_src, tag_start)
        content = html_src[tag_start:section_end]

        # Check if an <article class="chapter"> immediately follows
        remainder = html_src[section_end:]
        article_m = re.match(
            r'(\s*<article[^>]*class="chapter"[^>]*>.*?</article>)',
            remainder,
            re.DOTALL
        )
        if article_m:
            content += article_m.group(1)

        found[ch_id] = content

    return found


def chapter_to_xhtml(ch_id, title, step_lbl, content, css):
    """Wrap chapter content in valid XHTML for EPUB."""
    display = f'{step_lbl}: {title}' if step_lbl else title
    # HTML source uses ../../images/ (relative to src/book/); EPUB needs ../images/
    body = content.replace('src="../../images/', 'src="../images/')
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<!DOCTYPE html>'
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">'
        '<head>'
        f'<title>{display}</title>'
        '<meta charset="utf-8"/>'
        '<link rel="stylesheet" href="../style/main.css" type="text/css"/>'
        '</head>'
        f'<body>{body}</body>'
        '</html>'
    )


def build_epub():
    try:
        import ebooklib
        from ebooklib import epub
    except ImportError:
        print('ebooklib not found. Run: pip install ebooklib')
        sys.exit(1)

    out      = OUTPUT / 'reboot-camp.epub'
    html_src = strip_web_elements(read_html())
    log('Building EPUB...')

    book = epub.EpubBook()
    book.set_identifier('reboot-camp-2026')
    book.set_title('Reboot Camp: 10 Life-Altering Steps')
    book.set_language('en')
    book.add_author('Bill McGlone')

    # Cover image (full-page image shown by EPUB readers before any content)
    cover_img = IMAGES / 'image6.jpg'
    if cover_img.exists():
        with open(cover_img, 'rb') as f:
            book.set_cover('images/image6.jpg', f.read())

    # Stylesheet — dedicated EPUB CSS with hardcoded values, no CSS variables
    css = epub.EpubItem(
        uid='style',
        file_name='style/main.css',
        media_type='text/css',
        content=_EPUB_CSS.encode('utf-8')
    )
    book.add_item(css)

    # Package images (skip cover — already added by set_cover above)
    for img_path in IMAGES.glob('*'):
        if img_path == cover_img:
            continue
        if img_path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.svg', '.gif', '.webp'):
            mt = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png',  '.svg': 'image/svg+xml',
                '.gif': 'image/gif',  '.webp': 'image/webp',
            }.get(img_path.suffix.lower(), 'image/jpeg')
            with open(img_path, 'rb') as f:
                img_item = epub.EpubItem(
                    uid=img_path.name,
                    file_name=f'images/{img_path.name}',
                    media_type=mt,
                    content=f.read()
                )
            book.add_item(img_item)

    # Title page (styled dark page with title + subtitle + author)
    title_page = epub.EpubHtml(
        title='Reboot Camp: 10 Life-Altering Steps',
        file_name='chapters/titlepage.xhtml',
        lang='en'
    )
    title_page.content = _TITLE_PAGE.encode('utf-8')
    title_page.add_item(css)
    book.add_item(title_page)

    # Extract chapters from HTML
    sections = extract_chapters(html_src)

    spine  = ['nav', title_page]
    toc    = [epub.Link('chapters/titlepage.xhtml', 'Title Page', 'titlepage')]
    pages  = []

    for ch_id, ch_title, step_lbl in CHAPTERS:
        content = sections.get(ch_id, f'<section><h1>{ch_title}</h1></section>')
        xhtml = chapter_to_xhtml(ch_id, ch_title, step_lbl, content, css)

        page = epub.EpubHtml(
            title=f'{step_lbl}: {ch_title}' if step_lbl else ch_title,
            file_name=f'chapters/{ch_id}.xhtml',
            lang='en'
        )
        page.content = xhtml.encode('utf-8')
        page.add_item(css)
        book.add_item(page)

        spine.append(page)
        toc.append(epub.Link(f'chapters/{ch_id}.xhtml', ch_title, ch_id))
        pages.append(page)

    book.toc    = toc
    book.spine  = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(str(out), book, {'epub3_pages': False})
    size_kb = out.stat().st_size // 1024
    log(f'Done -> output/reboot-camp.epub  ({size_kb} KB)')


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Build Reboot Camp ebook')
    parser.add_argument('--pdf',  action='store_true', help='PDF only')
    parser.add_argument('--epub', action='store_true', help='EPUB only')
    args = parser.parse_args()

    both = not args.pdf and not args.epub

    print('\nReboot Camp - Book Builder')
    print('-' * 36)

    if args.pdf or both:
        build_pdf()

    if args.epub or both:
        build_epub()

    print('-' * 36)
    print('  All done. Check the output/ folder.\n')


if __name__ == '__main__':
    main()
