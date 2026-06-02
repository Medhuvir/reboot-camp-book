#!/usr/bin/env python3
"""
generate.py — Reboot Camp book builder
Usage:
  python generate.py          → both PDF + EPUB
  python generate.py --pdf    → PDF only
  python generate.py --epub   → EPUB only
"""

import argparse
import os
import re
import sys
from pathlib import Path

ROOT     = Path(__file__).parent
SRC      = ROOT / 'src'
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


# ─── PDF ────────────────────────────────────────────────────────────────────

def build_pdf():
    try:
        from weasyprint import HTML as WP
    except ImportError:
        print('WeasyPrint not found. Run: pip install weasyprint')
        sys.exit(1)

    out = OUTPUT / 'reboot-camp.pdf'
    log('Building PDF...')

    # base_url must point to src/ so WeasyPrint resolves relative image paths
    WP(filename=str(HTML), base_url=str(SRC)).write_pdf(str(out))
    size_kb = out.stat().st_size // 1024
    log(f'Done → output/reboot-camp.pdf  ({size_kb} KB)')


# ─── EPUB ────────────────────────────────────────────────────────────────────

CHAPTERS = [
    ('note',    'A Quick Note From Me',               ''),
    ('how-to',  'How to Get the Most Out of This',    ''),
    ('origin',  'How Did I Get Here?',                ''),
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
    # Fix image paths for EPUB packaging (images live at images/ in EPUB)
    body = content.replace('src="../images/', 'src="../images/')
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<!DOCTYPE html>'
        '<html xmlns="http://www.w3.org/1999/xhtml">'
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
    html_src = read_html()
    log('Building EPUB...')

    book = epub.EpubBook()
    book.set_identifier('reboot-camp-2026')
    book.set_title('Reboot Camp: 10 Life-Altering Steps')
    book.set_language('en')
    book.add_author('Bill McGlone')

    # Stylesheet
    with open(SRC / 'style.css', encoding='utf-8') as f:
        css_text = f.read()
    css = epub.EpubItem(
        uid='style',
        file_name='style/main.css',
        media_type='text/css',
        content=css_text.encode('utf-8')
    )
    book.add_item(css)

    # Package images
    for img_path in IMAGES.glob('*'):
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

    # Extract chapters from HTML
    sections = extract_chapters(html_src)

    spine  = ['nav']
    toc    = []
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
    log(f'Done → output/reboot-camp.epub  ({size_kb} KB)')


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Build Reboot Camp ebook')
    parser.add_argument('--pdf',  action='store_true', help='PDF only')
    parser.add_argument('--epub', action='store_true', help='EPUB only')
    args = parser.parse_args()

    both = not args.pdf and not args.epub

    print('\nReboot Camp — Book Builder')
    print('─' * 36)

    if args.pdf or both:
        build_pdf()

    if args.epub or both:
        build_epub()

    print('─' * 36)
    print('  All done. Check the output/ folder.\n')


if __name__ == '__main__':
    main()
