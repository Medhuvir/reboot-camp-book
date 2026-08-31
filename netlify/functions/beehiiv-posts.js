// netlify/functions/beehiiv-posts.js
// Server-side proxy for the Beehiiv RSS feed — browsers can't fetch it
// directly due to CORS. No external dependencies: parses the small,
// well-known RSS <item> shape with regex, using Node's built-in fetch.

const FEED_URL = 'https://rss.beehiiv.com/feeds/UvfEUB9QlF.xml';
const CACHE_SECONDS = 900; // 15 min

function decodeEntities(str) {
  return str
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

function extractTag(block, tag) {
  const m = block.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`, 'i'));
  if (!m) return '';
  return decodeEntities(m[1].replace(/^<!\[CDATA\[|\]\]>$/g, '').trim());
}

function extractEnclosure(block) {
  const m = block.match(/<enclosure[^>]*\burl="([^"]+)"/i);
  return m ? decodeEntities(m[1]) : '';
}

// Beehiiv's post body (content:encoded) wraps real paragraphs in
// <p class="paragraph">; other <p> tags (e.g. photo credit captions) don't
// carry that class. Some issues also open with an empty spacer paragraph,
// so skip near-empty matches and return the first one with real text.
function extractFirstParagraph(block) {
  const contentMatch = block.match(/<content:encoded>([\s\S]*?)<\/content:encoded>/i);
  if (!contentMatch) return '';
  const html = contentMatch[1].replace(/^\s*<!\[CDATA\[|\]\]>\s*$/g, '');
  for (const m of html.matchAll(/<p class="paragraph"[^>]*>([\s\S]*?)<\/p>/gi)) {
    const text = decodeEntities(m[1].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim());
    if (text.length > 15) return text;
  }
  return '';
}

exports.handler = async function handler() {
  try {
    const res = await fetch(FEED_URL, {
      headers: { 'User-Agent': 'RebootCampCoaching/1.0 (+https://rebootcampcoaching.com)' },
    });
    if (!res.ok) throw new Error(`Beehiiv feed responded ${res.status}`);
    const xml = await res.text();

    const items = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].map((m) => {
      const block = m[1];
      return {
        title: extractTag(block, 'title'),
        description: extractTag(block, 'description'),
        excerpt: extractFirstParagraph(block),
        link: extractTag(block, 'link'),
        pubDate: extractTag(block, 'pubDate'),
        image: extractEnclosure(block),
      };
    });

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': `public, max-age=${CACHE_SECONDS}`,
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({ posts: items }),
    };
  } catch (err) {
    return {
      statusCode: 502,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Failed to load newsletter feed', detail: String(err) }),
    };
  }
};
