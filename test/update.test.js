import assert from 'node:assert/strict';
import test from 'node:test';

import { validateUpdateState } from '../scripts/update.js';

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
