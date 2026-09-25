// netlify/functions/subscribe.js
// Server-side proxy for the site's own signup form → Beehiiv's Create
// Subscription API. Keeps the API key off the client. No external
// dependencies: uses Node's built-in fetch.
//
// Env vars (Netlify → Site configuration → Environment variables; locally in .env):
//   BEEHIIV_API_KEY          required
//   BEEHIIV_PUBLICATION_ID   required, starts with pub_
//   BEEHIIV_AUTOMATION_ID    optional, the welcome/ebook automation (aut_...)
//                            new subscribers get enrolled in

const API_BASE = 'https://api.beehiiv.com/v2';

// Must match the custom field names in Beehiiv exactly.
// TODO(dan): confirm against GET /v2/publications/{id}/custom_fields
const FIRST_NAME_FIELD = 'First Name';
const LAST_NAME_FIELD = 'Last Name';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function json(statusCode, body) {
  return {
    statusCode,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
    body: JSON.stringify(body),
  };
}

function clean(value, max) {
  return typeof value === 'string' ? value.trim().slice(0, max) : '';
}

exports.handler = async function handler(event) {
  if (event.httpMethod !== 'POST') return json(405, { error: 'Method not allowed' });

  const { BEEHIIV_API_KEY, BEEHIIV_PUBLICATION_ID, BEEHIIV_AUTOMATION_ID } = process.env;
  if (!BEEHIIV_API_KEY || !BEEHIIV_PUBLICATION_ID) {
    console.error('subscribe: BEEHIIV_API_KEY / BEEHIIV_PUBLICATION_ID not set');
    return json(500, { error: 'Signup is temporarily unavailable. Please try again later.' });
  }

  let data;
  try {
    data = JSON.parse(event.body || '{}');
  } catch (err) {
    return json(400, { error: 'Invalid request.' });
  }

  // Honeypot — real visitors never see or fill this field. Pretend it worked.
  if (clean(data.company, 200)) return json(200, { ok: true });

  const email = clean(data.email, 254).toLowerCase();
  const firstName = clean(data.first_name, 100);
  const lastName = clean(data.last_name, 100);

  if (!EMAIL_RE.test(email)) return json(400, { error: 'Please enter a valid email address.' });

  const customFields = [];
  if (firstName) customFields.push({ name: FIRST_NAME_FIELD, value: firstName });
  if (lastName) customFields.push({ name: LAST_NAME_FIELD, value: lastName });

  const payload = {
    email,
    reactivate_existing: false,
    send_welcome_email: false,
    utm_source: 'rebootcampcoaching.com',
    utm_medium: 'website',
    referring_site: clean(data.page, 500) || event.headers.referer || '',
    custom_fields: customFields,
  };
  if (BEEHIIV_AUTOMATION_ID) payload.automation_ids = [BEEHIIV_AUTOMATION_ID];

  try {
    const res = await fetch(`${API_BASE}/publications/${BEEHIIV_PUBLICATION_ID}/subscriptions`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${BEEHIIV_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      console.error(`subscribe: Beehiiv responded ${res.status}`, await res.text());
      return json(502, { error: 'Something went wrong. Please try again in a moment.' });
    }
    return json(200, { ok: true });
  } catch (err) {
    console.error('subscribe:', err);
    return json(502, { error: 'Something went wrong. Please try again in a moment.' });
  }
};
