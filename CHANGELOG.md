# Changelog

All notable changes to Ultimate Animation Index are documented here.

## [2.0.4] - 2026-08-17

### Automatic update notifications

- Added a cached server-side check for the latest published GitHub release.
- Added an in-app update notice with the installed version, latest version and direct release link.
- Allowed each release notice to be dismissed locally without hiding notifications for future versions.
- Kept update-check failures silent so the self-hosted catalog remains fully usable offline.

## [2.0.3] - 2026-08-17

### Portable UserList verification

- Added the UWL2 envelope so signed UserLists can be verified and imported on another installation.
- Embedded only the sender's public Ed25519 key; private signing keys remain local and excluded from Git.
- Kept same-installation UWL1 verification for existing codes and added a clear regeneration message for foreign legacy codes.
- Displayed the verified sender-key fingerprint after import so recipients can compare it with the sender.
- Added cross-installation verification coverage to the server test suite.

## [2.0.2] - 2026-08-17

### Selectable rating formats

- Added a global choice between the S+ letter scale and the 10-point scale.
- Applied the preference to catalog quality labels, filters, collections and personal rating controls.
- Preserved numeric personal ratings internally so format changes do not affect sorting, backup or import.
- Saved the selected format across refreshes and included it in private user backups.

## [2.0.1] - 2026-08-17

### Private backup and restore

- Added local JSON backups for watch statuses, ratings, private notes, favorites and episode progress.
- Included personal opinions, custom titles, imported sources and saved interface preferences.
- Added validated merge and replace import modes with rollback if a browser storage write fails.
- Kept backup creation and parsing entirely in the browser without sending private data to the server.

## [2.0.0] - 2026-08-17

### Episode and series tracking

- Added per-episode `Unwatched`, `Watching` and `Watched` states.
- Grouped AniList prequels, sequels, OVAs and concluding specials under one series tracker.
- Added TVMaze season and episode tracking for western shows such as Arcane.
- Synchronized episode progress between title details and franchise guides.
- Added season actions for advancing to the next episode, completing a season and resetting progress.
- Derived the title-level watch status from episode progress while preserving manual `On hold` and `Dropped` states.
- Cached finished series permanently and checked releasing, announced or paused series whenever their tracker is opened.

### Personal library

- Added distinct cover icons for every watch status.
- Persisted searches, filters, sorting, dropdowns and interface preferences across refreshes.
- Added editable custom titles with genres, tags and independent content-rating values.
- Included custom metadata in signed UserList imports and exports.
- Added metadata lookup and conservative content-rating estimates for custom titles.
- Added removal of custom titles and their associated local data.

### Interface and content guidance

- Redesigned content-severity bars with different lengths, colors, labels and numeric values.
- Added a responsive, keyboard-accessible season tracker that follows the existing visual system.
- Fixed toast notifications appearing behind dialogs.
- Improved the readability of the generated catalog JSON and contributor-facing source.

### Public repository

- Added English setup, architecture, contribution, security and copyright documentation.
- Added annotated screenshots for the catalog, content ratings, franchise guides and episode tracking.
- Kept generated catalogs, downloaded covers, caches, personal data and all video files out of Git.
- Added automated formatting, syntax, catalog and server tests through GitHub Actions.

[2.0.0]: https://github.com/Firehawk52/Ultimate_Animation_Index/releases/tag/v2.0.0
