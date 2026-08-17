export const RATING_FORMATS = ['tier', 'ten'];

const QUALITY_VALUES = {
  B: 5,
  'B+': 6,
  A: 7,
  'A+': 8,
  S: 9,
  'S+': 10,
};

const PERSONAL_TIERS = [
  { tier: 'S+', minimum: 9.5, value: 10 },
  { tier: 'S', minimum: 9, value: 9 },
  { tier: 'A+', minimum: 8, value: 8 },
  { tier: 'A', minimum: 7, value: 7 },
  { tier: 'B+', minimum: 6, value: 6 },
  { tier: 'B', minimum: Number.EPSILON, value: 5 },
];

export function normalizeRatingFormat(value) {
  return RATING_FORMATS.includes(value) ? value : 'tier';
}

export function qualityRatingLabel(tier, format = 'tier', { suffix = false } = {}) {
  const normalizedTier = String(tier || 'CUSTOM').toUpperCase();
  if (normalizeRatingFormat(format) === 'tier' || !(normalizedTier in QUALITY_VALUES)) return normalizedTier;
  const value = QUALITY_VALUES[normalizedTier];
  return suffix ? `${value}/10` : String(value);
}

export function personalRatingTier(value) {
  const rating = Number(value) || 0;
  return PERSONAL_TIERS.find((entry) => rating >= entry.minimum)?.tier || '';
}

export function personalTierValue(tier) {
  return PERSONAL_TIERS.find((entry) => entry.tier === tier)?.value || 0;
}

export function personalTierOptions() {
  return [...PERSONAL_TIERS].reverse().map(({ tier, value }) => ({ tier, value }));
}
