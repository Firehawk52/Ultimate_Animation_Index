import assert from 'node:assert/strict';
import test from 'node:test';

import {
  normalizeRatingFormat,
  personalRatingTier,
  personalTierOptions,
  personalTierValue,
  qualityRatingLabel,
} from '../public/rating-format.js';

test('quality tiers can be displayed as letter or 10-point ratings', () => {
  assert.equal(qualityRatingLabel('S+', 'tier'), 'S');
  assert.equal(qualityRatingLabel('B', 'tier'), 'D');
  assert.equal(qualityRatingLabel('S+', 'ten'), '10');
  assert.equal(qualityRatingLabel('A+', 'ten', { suffix: true }), '8/10');
  assert.equal(qualityRatingLabel('CUSTOM', 'ten'), 'CUSTOM');
});

test('personal numeric ratings map predictably to display tiers', () => {
  assert.equal(personalRatingTier(0), '');
  assert.equal(personalRatingTier(5.9), 'D');
  assert.equal(personalRatingTier(6), 'C');
  assert.equal(personalRatingTier(8.5), 'A');
  assert.equal(personalRatingTier(9), 'A+');
  assert.equal(personalRatingTier(10), 'S');
});

test('tier choices retain numeric values for storage and sorting', () => {
  assert.deepEqual(personalTierOptions(), [
    { tier: 'D', value: 5 },
    { tier: 'C', value: 6 },
    { tier: 'B', value: 7 },
    { tier: 'A', value: 8 },
    { tier: 'A+', value: 9 },
    { tier: 'S', value: 10 },
  ]);
  assert.equal(personalTierValue('A+'), 9);
  assert.equal(normalizeRatingFormat('unknown'), 'tier');
});
