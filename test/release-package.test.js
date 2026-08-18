import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { cp, mkdir, mkdtemp, rm } from 'node:fs/promises';
import { createServer } from 'node:http';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';

const root = dirname(dirname(fileURLToPath(import.meta.url)));

async function availablePort() {
  const probe = createServer();
  await new Promise((resolve, reject) => {
    probe.listen(0, '127.0.0.1', resolve);
    probe.once('error', reject);
  });
  const address = probe.address();
  assert.equal(typeof address, 'object');
  await new Promise((resolve, reject) => probe.close((error) => (error ? reject(error) : resolve())));
  return address.port;
}

test('release-style installs run without Git and hide source updating', async () => {
  const installation = await mkdtemp(join(tmpdir(), 'uai-release-'));
  const port = await availablePort();
  let child;
  let output = '';

  try {
    for (const path of ['package.json', 'scripts', 'src', 'public']) {
      await cp(join(root, path), join(installation, path), { recursive: true });
    }
    await mkdir(join(installation, 'data'));
    await cp(join(root, 'data', 'catalog-source.json'), join(installation, 'data', 'catalog-source.json'));

    child = spawn(process.execPath, ['scripts/start.js'], {
      cwd: installation,
      env: { ...process.env, PORT: String(port), UAI_SKIP_WARM: '1' },
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });
    child.stdout.on('data', (chunk) => (output += chunk));
    child.stderr.on('data', (chunk) => (output += chunk));

    let health = null;
    for (let attempt = 0; attempt < 50 && !health; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, 100));
      try {
        const response = await fetch(`http://127.0.0.1:${port}/api/health`);
        if (response.ok) health = await response.json();
      } catch {}
    }

    assert.ok(health, `Release-style server did not start.\n${output}`);
    assert.equal(health.updateToken, '');
    assert.equal(health.catalogWriteEnabled, true);
    const home = await fetch(`http://127.0.0.1:${port}/`);
    assert.equal(home.status, 200);
  } finally {
    if (child && child.exitCode === null) {
      child.kill();
      await Promise.race([once(child, 'exit'), new Promise((resolve) => setTimeout(resolve, 3000))]);
    }
    await rm(installation, { recursive: true, force: true });
  }
});
