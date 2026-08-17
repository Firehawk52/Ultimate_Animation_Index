# Changelog

All notable changes to Ultimate Animation Index are documented here.

## [2.0.12] - 2026-08-18

### Safer season completion

- Applied the same two-second confirmation flow to **Mark season watched**.
- Added a distinct green confirmation state while sharing cancellation, accessibility and loading behavior with reset.
- Replaced CSP-blocked inline progress styles with SVG meters so overall and per-season status bars fill correctly.

## [2.0.11] - 2026-08-18

### Safer episode reset

- Added a two-second armed state before a season reset can be confirmed.
- Cancelled pending resets when the user clicks anywhere else or closes the active dialog.
- Added accessible loading, confirmation and reduced-motion states matching the episode tracker design.

## [2.0.10] - 2026-08-18

### Sorting and ratings

- Split main-list and collection sorting into separate **Sort by** and ascending/descending controls.
- Saved both sort directions across refreshes and private backup/import.
- Changed the letter scale to `S`, `A+`, `A`, `B`, `C` and `D`, with `S` as the highest rating.
- Removed the obsolete Python reference from the README.

## [2.0.9] - 2026-08-17

### One-command updates

- Added `npm run update` to safely fast-forward clean installations from `origin/main`.
- Added one-click update launchers for Windows and macOS plus a Linux update script.
- Refused automatic updates while the server is running, outside `main` or when local source changes could be overwritten.
- Synchronized packages and regenerated the local catalog after a successful update.
- Added a protected **Update now** action that installs updates in the background, restarts the server and refreshes the page.
- Added the update command to the in-app release notification and documented the workflow.

## [2.0.8] - 2026-08-17

### Compact top navigation

- Reduced the sticky topbar height and internal spacing while preserving its angled branding and navigation hierarchy.
- Scaled the brand mark, supporting type and add-title action proportionally across desktop and mobile layouts.
- Kept the update notification offset aligned with the slimmer topbar.

### Collection navigation and sorting

- Kept the selected studio or creator title list open when viewing a title, so Escape returns one level at a time.
- Added persistent collection-title sorting by rating, newest release or name.
- Included the collection sort preference in private UI backups.

## [2.0.7] - 2026-08-17

### Content-guide color mapping

- Matched every content-guide legend marker to its corresponding severity-bar color.
- Centralized the six severity colors so the legend and title details cannot drift apart.
- Increased compact severity-label text for clearer catalog-card scanning.
- Synchronized favorite-heart color and state immediately across Adult, Master and Favorites.

## [2.0.6] - 2026-08-17

### Unified UserList format

- Renamed the portable signed sharing envelope to the single `UWL` format.
- Removed the unused legacy compatibility path because no older codes were publicly issued.
- Updated interface guidance, security documentation and validation tests to use `UWL` consistently.

## [2.0.5] - 2026-08-17

### Node-only catalog generation

- Removed Python from local startup, Docker and continuous integration requirements.
- Replaced the Python catalog builder with a Node.js generator and structural validator.
- Added a readable, version-controlled catalog source while keeping the generated browser database outside Git.
- Regenerated the local browser database automatically when it is missing or its source has changed.
- Kept explicit `npm run build:catalog` rebuilding for development workflows.

## [2.0.4] - 2026-08-17

### Automatic update notifications

- Added a cached server-side check for the latest published GitHub release.
- Added an in-app update notice with the installed version, latest version and direct release link.
- Allowed each release notice to be dismissed locally without hiding notifications for future versions.
- Kept update-check failures silent so the self-hosted catalog remains fully usable offline.

## [2.0.3] - 2026-08-17

### Portable UserList verification

- Added the portable UWL envelope so signed UserLists can be verified and imported on another installation.
- Embedded only the sender's public Ed25519 key; private signing keys remain local and excluded from Git.
- Rejected malformed, modified and schema-invalid codes before importing any data.
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

[2.0.0]: https://github.com/Firehawk52/ultimate-animation-index/releases/tag/v2.0.0
