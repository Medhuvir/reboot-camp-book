// netlify/functions/podcast-episodes.js
// Server-side proxy for the Reboot Camp podcast RSS feed — browsers can't
// fetch it directly due to CORS. No external dependencies: parses the
// well-known iTunes-style RSS <item> shape with regex, using Node's
// built-in fetch (same pattern as beehiiv-posts.js).

const FEED_URL = 'https://rss.beehiiv.com/podcasts/019fede3-607b-7f64-bcbf-b101b95dc069.xml';
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

function extractEnclosureUrl(block) {
  const m = block.match(/<enclosure[^>]*\burl="([^"]+)"/i);
  return m ? decodeEntities(m[1]) : '';
}

function extractImageHref(block) {
  const m = block.match(/<itunes:image[^>]*\bhref="([^"]+)"/i);
  return m ? decodeEntities(m[1]) : '';
}

exports.handler = async function handler() {
  try {
    const res = await fetch(FEED_URL, {
      headers: { 'User-Agent': 'RebootCampCoaching/1.0 (+https://rebootcampcoaching.com)' },
    });
    if (!res.ok) throw new Error(`Podcast feed responded ${res.status}`);
    const xml = await res.text();

    // Channel-level artwork, used as a fallback for episodes with no
    // itunes:image of their own.
    const channelBlock = xml.split('<item>')[0];
    const channelImage = extractImageHref(channelBlock);

    const items = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].map((m) => {
      const block = m[1];
      return {
        title: extractTag(block, 'title'),
        description: extractTag(block, 'description'),
        link: extractTag(block, 'link'),
        pubDate: extractTag(block, 'pubDate'),
        duration: extractTag(block, 'itunes:duration'),
        audioUrl: extractEnclosureUrl(block),
        image: extractImageHref(block) || channelImage,
      };
    });

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': `public, max-age=${CACHE_SECONDS}`,
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({ episodes: items }),
    };
  } catch (err) {
    return {
      statusCode: 502,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Failed to load podcast feed', detail: String(err) }),
    };
  }
};
