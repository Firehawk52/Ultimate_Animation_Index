import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';

process.env.UAI_SKIP_WARM = '1';

const { estimateContentRatings, server, startServer } = await import('../server.mjs');
let baseUrl;

before(async () => {
  await new Promise((resolve, reject) => {
    startServer(0);
    server.once('listening', resolve);
    server.once('error', reject);
  });

  const address = server.address();
  assert.equal(typeof address, 'object');
  baseUrl = `http://127.0.0.1:${address.port}`;
});

after(async () => {
  if (server.listening) {
    await new Promise((resolve, reject) => server.close((error) => (error ? reject(error) : resolve())));
  }
});

test('health endpoint reports a ready signing service', async () => {
  const response = await fetch(`${baseUrl}/api/health`);
  const body = await response.json();

  assert.equal(response.status, 200);
  assert.equal(body.ok, true);
  assert.equal(body.format, 'UWL1');
  assert.match(body.keyId, /^[a-f0-9]{16}$/);
});

test('home page is served with security headers', async () => {
  const response = await fetch(`${baseUrl}/`);
  const html = await response.text();

  assert.equal(response.status, 200);
  assert.match(response.headers.get('content-security-policy') ?? '', /default-src/);
  assert.match(html, /Ultimate Animation Index/);
});

test('readable catalog JSON is served to the browser', async () => {
  const response = await fetch(`${baseUrl}/catalog.json`);
  const raw = await response.text();
  const catalog = JSON.parse(raw);

  assert.equal(response.status, 200);
  assert.match(raw, /\r?\n  "items": \[\r?\n/);
  assert.ok(catalog.items.length > 0);
});

test('unknown API routes return structured JSON', async () => {
  const response = await fetch(`${baseUrl}/api/does-not-exist`);
  const body = await response.json();

  assert.equal(response.status, 404);
  assert.deepEqual(body, { error: 'unknown-api' });
});

test('provider metadata is converted into conservative content-rating estimates', () => {
  assert.deepEqual(
    estimateContentRatings({
      rating: 'R - 17+',
      genres: ['Action', 'Horror'],
      tags: [
        { name: 'Gore', rank: 82 },
        { name: 'Torture', rank: 70 },
        { name: 'Bisexual', rank: 90 },
      ],
    }),
    {
      sex: 2,
      nudity: 0,
      violence: 4,
      gore: 4,
      disturbing: 3,
      tags: ['Horror', 'Gore', 'Torture'],
    },
  );
});

test('signed UserLists preserve editable custom-title metadata', async () => {
  const payload = {
    v: 1,
    created: '2026-08-17T00:00:00.000Z',
    opinions: [{ id: 'c:example:123456', verdict: 'recommend' }],
    titles: [
      {
        id: 'c:example:123456',
        title: 'Example Animation',
        year: 2026,
        type: 'Film',
        origin: 'Denmark',
        api: 'none',
        lookupTitle: 'Example Animation',
        externalId: '',
        genres: 'Fantasy, Adventure',
        content: {
          sex: 1,
          nudity: 2,
          violence: 4,
          gore: 3,
          disturbing: 2,
          tags: ['Fantasy violence', 'Mild nudity'],
        },
      },
    ],
  };

  const signResponse = await fetch(`${baseUrl}/api/userlist/sign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const signed = await signResponse.json();
  assert.equal(signResponse.status, 200);

  const verifyResponse = await fetch(`${baseUrl}/api/userlist/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: signed.code }),
  });
  const verified = await verifyResponse.json();

  assert.equal(verifyResponse.status, 200);
  assert.equal(verified.payload.titles[0].genres, 'Fantasy, Adventure');
  assert.deepEqual(verified.payload.titles[0].content, payload.titles[0].content);
});

test('legacy UserLists remain valid without optional custom metadata', async () => {
  const response = await fetch(`${baseUrl}/api/userlist/sign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      v: 1,
      created: '2026-08-17T00:00:00.000Z',
      opinions: [],
      titles: [
        {
          id: 'c:legacy:123456',
          title: 'Legacy Title',
          year: 0,
          type: 'Series',
          origin: 'Unknown',
          api: 'none',
          lookupTitle: 'Legacy Title',
          externalId: '',
        },
      ],
    }),
  });
  const body = await response.json();

  assert.equal(response.status, 200);
  assert.ok(body.code.startsWith('UWL1.'));
});

test('UserList signing rejects out-of-range content ratings', async () => {
  const response = await fetch(`${baseUrl}/api/userlist/sign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      v: 1,
      created: '2026-08-17T00:00:00.000Z',
      opinions: [],
      titles: [
        {
          id: 'c:invalid:123456',
          title: 'Invalid Title',
          year: 2026,
          type: 'Series',
          origin: 'Unknown',
          api: 'none',
          lookupTitle: 'Invalid Title',
          externalId: '',
          genres: '',
          content: { sex: 6, nudity: 0, violence: 0, gore: 0, disturbing: 0, tags: [] },
        },
      ],
    }),
  });
  const body = await response.json();

  assert.equal(response.status, 400);
  assert.equal(body.error, 'invalid-title');
});
