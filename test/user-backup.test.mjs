import assert from 'node:assert/strict';
import test from 'node:test';

import {
  combineUserData,
  createUserBackup,
  summarizeUserData,
  validateUserBackup,
} from '../public/user-backup.js';

function userData() {
  return {
    progress: {
      'm:arcane:e7cbd6b1': { status: 'Watching', rating: 9.5, note: 'Continue with season two.' },
    },
    opinions: { 'm:arcane:e7cbd6b1': 'recommend' },
    customTitles: [
      {
        id: 't:999',
        title: 'Backup Example',
        year: 2026,
        type: 'Western series',
        origin: 'US',
        genres: 'Animation, Drama',
        api: 'tvmaze',
        lookupTitle: 'Backup Example',
        externalId: '999',
        custom: true,
        addedByMe: true,
        content: { sex: 0, nudity: 0, violence: 2, gore: 0, disturbing: 1, tags: ['Drama'] },
      },
    ],
    sources: {
      'src:sample': {
        label: 'Sample source',
        importedAt: '2026-08-17T10:00:00.000Z',
        opinions: { 'm:arcane:e7cbd6b1': 'recommend' },
        titleIds: ['t:999'],
      },
    },
    favorites: { 'm:arcane:e7cbd6b1': true },
    episodeProgress: { 'tvmaze:123:season:1': { 1: 'watched', 2: 'watching' } },
    ui: {
      searchInput: 'Arcane',
      statusFilter: 'Watching',
      ratingFormat: 'tier',
      collectionSort: 'release',
      collectionSortOrder: 'desc',
      masterSortOrder: 'asc',
      hideCompleted: false,
    },
    compact: true,
  };
}

test('private user backups preserve all supported local user data', () => {
  const backup = createUserBackup(userData(), {
    createdAt: '2026-08-17T12:00:00.000Z',
    appVersion: '2.0.11',
  });
  const restored = validateUserBackup(JSON.parse(JSON.stringify(backup)));
  const summary = summarizeUserData(restored.data);

  assert.equal(restored.format, 'uai-user-backup');
  assert.equal(restored.version, 1);
  assert.equal(restored.data.progress['m:arcane:e7cbd6b1'].note, 'Continue with season two.');
  assert.equal(restored.data.episodeProgress['tvmaze:123:season:1']['2'], 'watching');
  assert.equal(restored.data.ui.ratingFormat, 'tier');
  assert.equal(restored.data.ui.collectionSort, 'release');
  assert.equal(restored.data.ui.collectionSortOrder, 'desc');
  assert.equal(restored.data.ui.masterSortOrder, 'asc');
  assert.deepEqual(summary, {
    statuses: 1,
    ratings: 1,
    notes: 1,
    favorites: 1,
    episodes: 2,
    customTitles: 1,
    sources: 1,
  });
});

test('backup validation rejects invalid status and episode values', () => {
  const badStatus = createUserBackup(userData());
  badStatus.data.progress['m:arcane:e7cbd6b1'].status = 'Finished-ish';
  assert.throws(() => validateUserBackup(badStatus), /invalid-watch-status/);

  const badEpisode = createUserBackup(userData());
  badEpisode.data.episodeProgress['tvmaze:123:season:1']['2'] = 'complete';
  assert.throws(() => validateUserBackup(badEpisode), /invalid-episode-state/);

  const badCollectionSort = createUserBackup(userData());
  badCollectionSort.data.ui.collectionSort = 'random';
  assert.throws(() => validateUserBackup(badCollectionSort), /invalid-collection-sort/);

  const badCollectionSortOrder = createUserBackup(userData());
  badCollectionSortOrder.data.ui.collectionSortOrder = 'sideways';
  assert.throws(() => validateUserBackup(badCollectionSortOrder), /invalid-collection-sort-order/);

  const badMasterSortOrder = createUserBackup(userData());
  badMasterSortOrder.data.ui.masterSortOrder = 'mixed';
  assert.throws(() => validateUserBackup(badMasterSortOrder), /invalid-master-sort-order/);
});

test('merge import keeps current records while backup values win conflicts', () => {
  const current = userData();
  current.progress['m:arcane:e7cbd6b1'].rating = 7;
  current.favorites['m:other:123'] = true;
  current.episodeProgress['tvmaze:123:season:1'] = { 1: 'watching', 3: 'watched' };

  const incoming = userData();
  const merged = combineUserData(current, incoming, 'merge');

  assert.equal(merged.progress['m:arcane:e7cbd6b1'].rating, 9.5);
  assert.equal(merged.favorites['m:other:123'], true);
  assert.deepEqual(merged.episodeProgress['tvmaze:123:season:1'], {
    1: 'watched',
    2: 'watching',
    3: 'watched',
  });
});

test('replace import returns only validated backup data', () => {
  const current = userData();
  current.favorites['m:other:123'] = true;
  const replaced = combineUserData(current, userData(), 'replace');

  assert.equal(replaced.favorites['m:other:123'], undefined);
  assert.equal(replaced.favorites['m:arcane:e7cbd6b1'], true);
});
