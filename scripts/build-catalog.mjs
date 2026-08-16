import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const builder = join(root, 'build_catalog.py');
const candidates =
  process.platform === 'win32'
    ? [
        ['py', ['-3']],
        ['python', []],
        ['python3', []],
      ]
    : [
        ['python3', []],
        ['python', []],
      ];

export function buildCatalog() {
  for (const [command, prefix] of candidates) {
    const result = spawnSync(command, [...prefix, builder], {
      cwd: root,
      stdio: 'inherit',
    });

    if (result.error?.code === 'ENOENT') continue;
    if (result.error) throw result.error;
    if (result.status !== 0) throw new Error(`Catalog build failed with exit code ${result.status}`);
    return;
  }

  throw new Error('Python 3 is required to generate public/catalog.json.');
}

const isDirectRun = process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url));
if (isDirectRun) {
  try {
    buildCatalog();
  } catch (error) {
    console.error(error.message);
    console.error('Install Python 3, then run the command again.');
    process.exitCode = 1;
  }
}
