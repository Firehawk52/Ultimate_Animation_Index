import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

import { validateUpdateState } from '../scripts/update.js';

const root = dirname(dirname(fileURLToPath(import.meta.url)));

test('updater accepts a clean main Git checkout', () => {
  assert.doesNotThrow(() => validateUpdateState({ insideWorkTree: 'true', branch: 'main', changes: '' }));
});

test('updater refuses unsafe installation states', () => {
  assert.throws(
    () => validateUpdateState({ insideWorkTree: 'false', branch: '', changes: '' }),
    /require a Git clone/,
  );
  assert.throws(
    () => validateUpdateState({ insideWorkTree: 'true', branch: 'feature', changes: '' }),
    /require the main branch/,
  );
  assert.throws(
    () => validateUpdateState({ insideWorkTree: 'true', branch: 'main', changes: ' M public/app.js' }),
    /Local source changes/,
  );
});

test('version 2.1 catalog-build entry point remains compatible', () => {
  const result = spawnSync(process.execPath, ['scripts/build-catalog.mjs'], {
    cwd: root,
    encoding: 'utf8',
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Generated public\/catalog\.json/);
});
