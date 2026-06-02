# Reboot Camp Rules — Ebook Builder

**Bill M · Reboot Camp Coaching**

Builds the Reboot Camp Rules ebook from a single HTML source to both PDF and EPUB.

## Setup

```bash
pip install -r requirements.txt
```

## Generate

```bash
python generate.py
```

Outputs to `output/`:
- `reboot-camp.pdf` — print-ready PDF
- `reboot-camp.epub` — Kindle/Apple Books compatible

## Edit Content

All content lives in `src/index.html`. Each chapter is clearly marked with comments.

## Swap Images

Drop images into the `images/` folder. Update `src` paths in `src/index.html`.

## Brand

Blueprint palette — see `CLAUDE.md` for full spec.
