# Contributing

Thanks for helping improve the Ultimate Animation Index.

## Before making a change

1. Install Node.js 20 or newer and Python 3.10 or newer.
2. Run `npm install` once to install the formatter.
3. Keep the change focused. Avoid committing local covers, metadata caches or
   UserList signing keys.

## Catalog changes

The source of truth is `build_catalog.py`, with legacy input in
`data/original-v1.json`. Do not edit the generated `public/catalog.json` directly.

After changing catalog data or curation rules, run:

```bash
npm run build:catalog
```

Do not commit the generated catalog file; CI rebuilds it from the source. Stable title
IDs are derived from normalized titles, so renaming an existing canonical title can
affect saved browser data and imported UserLists. Add an alias when a rename is meant
to preserve identity.

## Application changes

Before opening a pull request, run:

```bash
npm run format
npm run check
npm test
```

`npm test` rebuilds the catalog before running the integration tests.

## Pull requests

Describe the user-visible outcome, note any data migrations or compatibility risks,
and include screenshots for visual changes. Never include `public/catalog.json` or
files from `.userlist-keys/`, `.cache/`, `covers/` or `node_modules/`.
