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


def _epub_css(css_text):
    """Strip @media print and @page blocks — irrelevant in EPUB readers."""
    result = []
    i = 0
    while i < len(css_text):
        m = re.search(r'@(?:media\s+print|page)\b', css_text[i:])
        if not m:
            result.append(css_text[i:])
            break
        result.append(css_text[i:i + m.start()])
        i += m.start()
        brace = css_text.find('{', i)
        if brace == -1:
            break
        depth, j = 0, brace
        while j < len(css_text):
            if css_text[j] == '{':
                depth += 1
            elif css_text[j] == '}':
                depth -= 1
                if depth == 0:
                    i = j + 1
                    break
            j += 1
        else:
            break
    return ''.join(result)


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

    # Stylesheet — strip print-only rules that EPUB readers don't need
    with open(CSS, encoding='utf-8') as f:
        css_text = f.read()
    css = epub.EpubItem(
        uid='style',
        file_name='style/main.css',
        media_type='text/css',
        content=_epub_css(css_text).encode('utf-8')
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
