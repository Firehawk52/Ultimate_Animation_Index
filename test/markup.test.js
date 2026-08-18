import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';

const appSource = await readFile(new URL('../public/app.js', import.meta.url), 'utf8');

function tagsWithoutAttribute(tagName, attribute) {
  return [...appSource.matchAll(new RegExp(`<${tagName}\\b[^>]*>`, 'gi'))]
    .map(([tag]) => tag)
    .filter((tag) => !new RegExp(`\\b${attribute}\\s*=`, 'i').test(tag));
}

test('dynamic controls use explicit HTML types', () => {
  assert.deepEqual(tagsWithoutAttribute('button', 'type'), []);
  assert.deepEqual(tagsWithoutAttribute('input', 'type'), []);
});
