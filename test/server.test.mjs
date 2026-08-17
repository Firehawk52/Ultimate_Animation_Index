import assert from 'node:assert/strict';
import { createHash, generateKeyPairSync, sign as cryptoSign } from 'node:crypto';
import { after, before, test } from 'node:test';

process.env.UAI_SKIP_WARM = '1';

const {
  anilistSeriesNeedsRefresh,
  estimateContentRatings,
  fromAniListSeriesMedia,
  fromTVMazeSeries,
  isNewerVersion,
  server,
  startServer,
  tvMazeSeriesNeedsRefresh,
} = await import('../server.mjs');
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
  assert.equal(body.format, 'UWL');
  assert.match(body.version, /^\d+\.\d+\.\d+$/);
  assert.match(body.updateToken, /^[A-Za-z0-9_-]{32}$/);
  assert.equal(body.userListSchema, 3);
  assert.match(body.keyId, /^[a-f0-9]{16}$/);
});

test('update endpoint rejects requests without its same-origin token', async () => {
  const response = await fetch(`${baseUrl}/api/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  });
  const body = await response.json();

  assert.equal(response.status, 403);
  assert.equal(body.error, 'update-forbidden');
});

test('release versions are compared by semantic version components', () => {
  assert.equal(isNewerVersion('v2.0.5', '2.0.4'), true);
  assert.equal(isNewerVersion('2.1.0', '2.0.9'), true);
  assert.equal(isNewerVersion('3.0.0', '2.9.9'), true);
  assert.equal(isNewerVersion('2.0.4', '2.0.4'), false);
  assert.equal(isNewerVersion('2.0.3', '2.0.4'), false);
  assert.equal(isNewerVersion('latest', '2.0.4'), false);
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

test('AniList series entries retain episodes and only main sequence relations', () => {
  const entry = fromAniListSeriesMedia({
    id: 42,
    title: { english: 'Example Special', romaji: 'Example' },
    seasonYear: 2026,
    startDate: { year: 2026, month: 4, day: 9 },
    format: 'SPECIAL',
    episodes: null,
    relations: {
      edges: [
        { relationType: 'SEQUEL', node: { id: 43, type: 'ANIME' } },
        { relationType: 'SIDE_STORY', node: { id: 44, type: 'ANIME' } },
        { relationType: 'PREQUEL', node: { id: 45, type: 'MANGA' } },
      ],
    },
  });

  assert.equal(entry.id, '42');
  assert.equal(entry.episodes, 1);
  assert.equal(entry.startDate, '2026-04-09');
  assert.deepEqual(entry.relations, [{ id: '43', type: 'SEQUEL' }]);
});

test('only active AniList series groups refresh when their tracker opens', () => {
  assert.equal(
    anilistSeriesNeedsRefresh({ entries: [{ status: 'FINISHED' }, { status: 'CANCELLED' }] }),
    false,
  );
  assert.equal(
    anilistSeriesNeedsRefresh({ entries: [{ status: 'FINISHED' }, { status: 'RELEASING' }] }),
    true,
  );
  assert.equal(anilistSeriesNeedsRefresh({ entries: [{ status: 'NOT_YET_RELEASED' }] }), true);
  assert.equal(anilistSeriesNeedsRefresh({ entries: [{ status: 'HIATUS' }] }), true);
});

test('TVMaze episodes are grouped into seasons with status-aware refresh behavior', () => {
  const ended = fromTVMazeSeries({
    id: 99,
    name: 'Example Show',
    status: 'Ended',
    premiered: '2024-01-01',
    averageRuntime: 42,
    _embedded: {
      episodes: [
        { id: 1, season: 1, number: 1, airdate: '2024-01-01' },
        { id: 2, season: 1, number: 2, airdate: '2024-01-08' },
        { id: 3, season: 2, number: 1, airdate: '2025-02-01' },
      ],
    },
  });

  assert.equal(ended.entries.length, 2);
  assert.equal(ended.entries[0].title, 'Example Show Season 1');
  assert.equal(ended.entries[0].episodes, 2);
  assert.equal(ended.entries[1].startDate, '2025-02-01');
  assert.equal(tvMazeSeriesNeedsRefresh(ended), false);
  assert.equal(tvMazeSeriesNeedsRefresh({ ...ended, showStatus: 'Running' }), true);
});

test('series endpoint rejects unsupported providers without making an external request', async () => {
  const response = await fetch(`${baseUrl}/api/series?kind=wiki&title=Example`);
  const body = await response.json();

  assert.equal(response.status, 400);
  assert.equal(body.error, 'unsupported-metadata-kind');
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

test('portable UserLists verify when signed by another installation', async () => {
  const payload = {
    v: 1,
    created: '2026-08-17T00:00:00.000Z',
    opinions: [],
    titles: [],
  };
  const { privateKey, publicKey } = generateKeyPairSync('ed25519');
  const publicDer = publicKey.export({ type: 'spki', format: 'der' });
  const keyId = createHash('sha256').update(publicDer).digest('hex').slice(0, 16);
  const raw = Buffer.from(JSON.stringify(payload));
  const signature = cryptoSign(null, raw, privateKey);
  const code = `UWL.${keyId}.${publicDer.toString('base64url')}.${raw.toString('base64url')}.${signature.toString('base64url')}`;

  const response = await fetch(`${baseUrl}/api/userlist/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });
  const body = await response.json();

  assert.equal(response.status, 200);
  assert.equal(body.format, 'UWL');
  assert.equal(body.keyId, keyId);
  assert.deepEqual(body.payload, payload);

  const tamperedRaw = Buffer.from(JSON.stringify({ ...payload, created: '2026-08-18T00:00:00.000Z' }));
  const tamperedCode = `UWL.${keyId}.${publicDer.toString('base64url')}.${tamperedRaw.toString('base64url')}.${signature.toString('base64url')}`;
  const tamperedResponse = await fetch(`${baseUrl}/api/userlist/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: tamperedCode }),
  });
  const tamperedBody = await tamperedResponse.json();

  assert.equal(tamperedResponse.status, 400);
  assert.equal(tamperedBody.error, 'signature-failed');
});

test('UserLists remain valid without optional custom metadata', async () => {
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
  assert.ok(body.code.startsWith('UWL.'));
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
