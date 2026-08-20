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
  const searchIds = ['searchInput', 'collectionSearch', 'franchiseSearch', 'adultSearch', 'favoriteSearch'];

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

test('Adult titles have independent Master-style search, filters and sorting controls', () => {
  const adultSort = html.match(/<select id="adultSort"[\s\S]*?<\/select>/)?.[0] || '';
  for (const id of ['adultTierFilter', 'adultTypeFilter', 'adultGenreFilter', 'adultStatusFilter']) {
    assert.match(html, new RegExp(`<select id="${id}"`));
  }
  assert.match(html, /<select id="adultSort" aria-label="Sort Adult titles by">/);
  for (const value of ['rank', 'overall', 'production', 'story', 'emotional', 'year', 'title', 'myrating']) {
    assert.match(adultSort, new RegExp(`<option value="${value}">`));
  }
  assert.match(html, /<button\s+id="adultSortOrder"\s+class="master-sort-order"/);
  assert.match(appSource, /function filteredAdult\(\)/);
  assert.match(appSource, /function populateAdultFilters\(\)/);
  assert.match(appSource, /sortTitleItems\(narrowed, sort, state\.adultSortOrder\)/);
});

test('rating format is a global My Library preference with one required onboarding choice', () => {
  const masterPanel =
    html.match(/<section id="masterTab" class="panel active">[\s\S]*?<\/section>/)?.[0] || '';
  assert.match(html, /<span>MY LIBRARY<\/span>/);
  assert.match(html, /<h2>MY LIBRARY<\/h2>/);
  assert.match(html, /<section class="library-preferences" aria-labelledby="ratingDisplayTitle">/);
  assert.match(html, /<select id="ratingFormatSelect" aria-label="Global rating format">/);
  assert.doesNotMatch(masterPanel, /ratingFormatSelect/);
  assert.match(html, /<dialog\s+id="ratingFormatDialog"/);
  assert.match(html, /data-onboarding-rating-format="tier"/);
  assert.match(html, /data-onboarding-rating-format="ten"/);
  assert.match(html, /data-onboarding-rating-format="stars"/);
  assert.match(appSource, /ratingFormatOnboardingSeen/);
  assert.match(appSource, /showRatingFormatOnboarding/);
  assert.match(appSource, /function chooseRatingFormat\(format\)/);
  assert.match(appSource, /function applyRatingFormat\(format\)/);
  assert.match(html, /F · E · D · C · C\+ · B · B\+ · A · A\+ · S/);
  assert.match(appSource, /ratingFormatDialog'\)\.addEventListener\('cancel'/);
  assert.doesNotMatch(appSource, /data-rating-format=/);
});

test('content guides use severity cards in both detail and Adult views', () => {
  assert.match(appSource, /content-severity-card severity-\$\{v\}/);
  assert.match(appSource, /contentGuide\(x, true\)/);
  assert.doesNotMatch(appSource, /content-row severity-/);
});

test('tooltips use the global modern layer instead of native title attributes', () => {
  assert.match(appSource, /new MutationObserver/);
  assert.match(appSource, /target\.removeAttribute\('title'\)/);
  assert.match(appSource, /event\.target\.closest\('\[data-tooltip\]'\)/);
  assert.match(appSource, /globalTooltip\.setAttribute\('popover', 'manual'\)/);
  assert.match(appSource, /globalTooltip\.showPopover\(\)/);
  assert.doesNotMatch(html, /\stitle="/);
});
