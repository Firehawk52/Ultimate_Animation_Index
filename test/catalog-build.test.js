import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import { catalogNeedsBuild, validateCatalog } from '../scripts/build-catalog.js';

const sourceUrl = new URL('../data/catalog-source.json', import.meta.url);
const generatedUrl = new URL('../public/catalog.json', import.meta.url);

test('generated catalog exactly matches its version-controlled source', async () => {
  const [source, generated] = await Promise.all([
    readFile(sourceUrl, 'utf8'),
    readFile(generatedUrl, 'utf8'),
  ]);

  assert.equal(generated, source);
  assert.equal(catalogNeedsBuild(), false);
});

test('catalog validation rejects duplicate title IDs', async () => {
  const catalog = JSON.parse(await readFile(sourceUrl, 'utf8'));
  catalog.items[1].id = catalog.items[0].id;

  assert.throws(() => validateCatalog(catalog), /duplicates/);
});

test('catalog validation rejects unknown collection title IDs', async () => {
  const catalog = JSON.parse(await readFile(sourceUrl, 'utf8'));
  catalog.collections[0].items.push('m:missing-title:00000000');

  assert.throws(() => validateCatalog(catalog), /references unknown item/);
});
