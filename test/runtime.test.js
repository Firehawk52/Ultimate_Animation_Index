import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { test } from 'node:test';
import { assertSupportedNode, parsePort, readLocalHealth } from '../scripts/runtime.js';

function listen(server) {
  return new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
}

function close(server) {
  return new Promise((resolve, reject) => server.close((error) => (error ? reject(error) : resolve())));
}

test('runtime accepts supported Node versions and valid ports', () => {
  assert.doesNotThrow(() => assertSupportedNode('20.19.0'));
  assert.doesNotThrow(() => assertSupportedNode('22.16.0'));
  assert.doesNotThrow(() => assertSupportedNode('24.0.0'));
  assert.equal(parsePort(undefined), 8787);
  assert.equal(parsePort('49152'), 49152);
  assert.equal(parsePort('0', { allowZero: true }), 0);
});

test('runtime rejects unsupported Node versions and invalid ports', () => {
  assert.throws(() => assertSupportedNode('18.20.0'), /Node\.js 20\.19\+/);
  assert.throws(() => assertSupportedNode('20.18.3'), /Node\.js 20\.19\+/);
  assert.throws(() => assertSupportedNode('22.15.1'), /Node\.js 20\.19\+/);
  assert.throws(() => assertSupportedNode('23.11.1'), /Node\.js 20\.19\+/);
  assert.throws(() => parsePort('0'), /PORT must be a whole number/);
  assert.throws(() => parsePort('70000'), /PORT must be a whole number/);
  assert.throws(() => parsePort('not-a-port'), /PORT must be a whole number/);
});

test('readLocalHealth accepts UAI health and rejects lookalike services', async () => {
  let payload = { ok: true };
  const service = createServer((_request, response) => {
    response.writeHead(200, { 'Content-Type': 'application/json' });
    response.end(JSON.stringify(payload));
  });
  await listen(service);

  try {
    const address = service.address();
    assert.equal(typeof address, 'object');
    assert.equal(await readLocalHealth(address.port), null);

    payload = { ok: true, format: 'UWL', version: '2.1.0', userListSchema: 3 };
    assert.deepEqual(await readLocalHealth(address.port), payload);
  } finally {
    await close(service);
  }
});
