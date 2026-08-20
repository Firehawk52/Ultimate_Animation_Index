import assert from 'node:assert/strict';
import test from 'node:test';

import {
  normalizeRatingFormat,
  personalRatingTier,
  personalStarOptions,
  personalTierOptions,
  personalTierValue,
  qualityRatingLabel,
  starRatingLabel,
} from '../public/rating-format.js';

test('quality tiers can be displayed as letter, 10-point, or star ratings', () => {
  assert.equal(qualityRatingLabel('S+', 'tier'), 'S');
  assert.equal(qualityRatingLabel('B', 'tier'), 'D');
  assert.equal(qualityRatingLabel('S+', 'ten'), '10');
  assert.equal(qualityRatingLabel('A+', 'ten', { suffix: true }), '8/10');
  assert.equal(qualityRatingLabel('S+', 'stars'), '★★★★★');
  assert.equal(qualityRatingLabel('A', 'stars'), '★★★½');
  assert.equal(qualityRatingLabel('CUSTOM', 'ten'), 'CUSTOM');
});

test('personal numeric ratings map predictably to display tiers', () => {
  assert.equal(personalRatingTier(0), '');
  assert.equal(personalRatingTier(1), 'F');
  assert.equal(personalRatingTier(2), 'E');
  assert.equal(personalRatingTier(3), 'D');
  assert.equal(personalRatingTier(4), 'C');
  assert.equal(personalRatingTier(5), 'C+');
  assert.equal(personalRatingTier(6), 'B');
  assert.equal(personalRatingTier(7), 'B+');
  assert.equal(personalRatingTier(8.5), 'A');
  assert.equal(personalRatingTier(9), 'A+');
  assert.equal(personalRatingTier(10), 'S');
});

test('tier choices retain numeric values for storage and sorting', () => {
  assert.deepEqual(personalTierOptions(), [
    { tier: 'F', value: 1 },
    { tier: 'E', value: 2 },
    { tier: 'D', value: 3 },
    { tier: 'C', value: 4 },
    { tier: 'C+', value: 5 },
    { tier: 'B', value: 6 },
    { tier: 'B+', value: 7 },
    { tier: 'A', value: 8 },
    { tier: 'A+', value: 9 },
    { tier: 'S', value: 10 },
  ]);
  assert.equal(personalTierValue('F'), 1);
  assert.equal(personalTierValue('E'), 2);
  assert.equal(personalTierValue('A+'), 9);
  assert.equal(normalizeRatingFormat('unknown'), 'tier');
});

test('star ratings have ten half-star steps while retaining 1–10 storage values', () => {
  assert.equal(starRatingLabel(0.5), '½');
  assert.equal(starRatingLabel(2.5), '★★½');
  assert.deepEqual(personalStarOptions()[0], { value: 1, stars: 0.5, label: '½' });
  assert.deepEqual(personalStarOptions().at(-1), { value: 10, stars: 5, label: '★★★★★' });
});
