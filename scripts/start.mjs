import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const catalogPath = join(root, 'public', 'catalog.json');

if (!existsSync(catalogPath) || process.env.UAI_REBUILD_CATALOG === '1') {
  console.log('Generating public/catalog.json...');
  const { buildCatalog } = await import('./build-catalog.mjs');
  buildCatalog();
}

const { startServer } = await import('../server.mjs');
startServer();
