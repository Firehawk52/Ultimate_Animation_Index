import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';

process.env.UAI_SKIP_WARM = '1';

const { server, startServer } = await import('../server.mjs');
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
