import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  applyCorrectionPackage,
  catalogSnapshot,
  parseCorrectionCode,
  validateCorrectionPackage,
} from '../scripts/catalog-corrections.js';

const source = JSON.parse(await readFile(new URL('../data/catalog-source.json', import.meta.url), 'utf8'));

function packageWith(entries) {
  return {
    format: 'ultimate-animation-index-corrections',
    schema: 1,
    createdAt: '2026-08-18T10:00:00.000Z',
    catalogVersion: source.version,
    entries,
  };
}

test('catalog corrections update only curated scores and content ratings', () => {
  const title = source.items[0];
  const base = catalogSnapshot(title);
  const values = structuredClone(base);
  values.content.nudity = values.content.nudity === 5 ? 4 : values.content.nudity + 1;
  const correction = packageWith([{ operation: 'update', id: title.id, title: title.title, base, values }]);
  const result = applyCorrectionPackage(source, correction, {
    generatedAt: new Date('2026-08-18T10:00:00.000Z'),
  });
  const updated = result.catalog.items.find((item) => item.id === title.id);
  assert.equal(updated.content.nudity, values.content.nudity);
  assert.equal(updated.title, title.title);
  assert.equal(result.catalog.generated, '2026-08-18');
});

test('stale correction packages are rejected before changing the catalog', () => {
  const title = source.items[0];
  const base = catalogSnapshot(title);
  base.scores.story = base.scores.story === 10 ? 9 : 10;
  assert.throws(
    () =>
      validateCorrectionPackage(
        packageWith([
          {
            operation: 'update',
            id: title.id,
            title: title.title,
            base,
            values: catalogSnapshot(title),
          },
        ]),
        source,
      ),
    /catalog-correction-conflict/,
  );
});

test('completed custom titles can be promoted to unranked catalog entries', () => {
  const entry = {
    operation: 'add',
    id: 'c:review-candidate:123abc',
    title: 'Review Candidate',
    base: null,
    values: {
      year: 2026,
      type: 'Series',
      origin: 'Denmark',
      api: 'none',
      lookupTitle: 'Review Candidate',
      externalId: '',
      genres: 'Drama, Animation',
      scores: { overall: 84, production: 8, story: 9, emotional: 7 },
      content: { sex: 0, nudity: 0, violence: 2, gore: 0, disturbing: 1, tags: [] },
    },
  };
  const result = applyCorrectionPackage(source, packageWith([entry]));
  const added = result.catalog.items.at(-1);
  assert.equal(added.id, entry.id);
  assert.equal(added.tier, 'A');
  assert.deepEqual(added.scores, entry.values.scores);
});

test('correction codes use a data-only UAIC envelope', () => {
  const payload = packageWith([]);
  const code = `UAIC.${Buffer.from(JSON.stringify(payload)).toString('base64url')}`;
  assert.deepEqual(parseCorrectionCode(code), payload);
  assert.throws(() => parseCorrectionCode('UWL.invalid'), /invalid-correction-code/);
});
