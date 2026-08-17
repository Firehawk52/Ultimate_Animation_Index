# Changelog

All notable changes to Ultimate Animation Index are documented here.

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
