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
  assert.equal(qualityRatingLabel('S+', 'tier'), 'S+');
  assert.equal(qualityRatingLabel('S+', 'ten'), '10');
  assert.equal(qualityRatingLabel('A+', 'ten', { suffix: true }), '8/10');
  assert.equal(qualityRatingLabel('CUSTOM', 'ten'), 'CUSTOM');
});

test('personal numeric ratings map predictably to display tiers', () => {
  assert.equal(personalRatingTier(0), '');
  assert.equal(personalRatingTier(5.9), 'B');
  assert.equal(personalRatingTier(6), 'B+');
  assert.equal(personalRatingTier(8.5), 'A+');
  assert.equal(personalRatingTier(9), 'S');
  assert.equal(personalRatingTier(9.5), 'S+');
});

test('tier choices retain numeric values for storage and sorting', () => {
  assert.deepEqual(personalTierOptions(), [
    { tier: 'B', value: 5 },
    { tier: 'B+', value: 6 },
    { tier: 'A', value: 7 },
    { tier: 'A+', value: 8 },
    { tier: 'S', value: 9 },
    { tier: 'S+', value: 10 },
  ]);
  assert.equal(personalTierValue('A+'), 8);
  assert.equal(normalizeRatingFormat('unknown'), 'tier');
});
