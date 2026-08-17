import { spawn } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
await delay(900);

const child = spawn(process.execPath, [join(root, 'scripts', 'start.mjs')], {
  cwd: root,
  detached: true,
  env: process.env,
  stdio: 'ignore',
  windowsHide: true,
});
child.unref();
