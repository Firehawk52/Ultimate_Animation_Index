import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';

const appSource = await readFile(new URL('../public/app.js', import.meta.url), 'utf8');
const html = await readFile(new URL('../public/index.html', import.meta.url), 'utf8');

function tagsWithoutAttribute(tagName, attribute) {
  return [...appSource.matchAll(new RegExp(`<${tagName}\\b[^>]*>`, 'gi'))]
    .map(([tag]) => tag)
    .filter((tag) => !new RegExp(`\\b${attribute}\\s*=`, 'i').test(tag));
}

test('dynamic controls use explicit HTML types', () => {
  assert.deepEqual(tagsWithoutAttribute('button', 'type'), []);
  assert.deepEqual(tagsWithoutAttribute('input', 'type'), []);
});

test('every catalog search uses the shared labeled search component', () => {
  const searchIds = ['searchInput', 'collectionSearch', 'franchiseSearch', 'favoriteSearch'];

  for (const id of searchIds) {
    assert.match(
      html,
      new RegExp(
        `<div class="search-block">\\s*<label class="search-prompt" for="${id}">SEARCH //<\\/label>\\s*<input\\s+id="${id}"\\s+type="search"`,
      ),
    );
  }
  assert.equal((html.match(/class="search-block"/g) || []).length, searchIds.length);
});
