import { buildCatalog, catalogNeedsBuild } from './build-catalog.mjs';

if (catalogNeedsBuild() || process.env.UAI_REBUILD_CATALOG === '1') {
  console.log('Generating public/catalog.json...');
  buildCatalog();
}

const { startServer } = await import('../server.mjs');
startServer();
