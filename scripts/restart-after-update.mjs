// Compatibility bridge for one-click updates started by version 2.1.0.
// Active application modules use .js; the released server still invokes this exact path.
import { spawn } from 'node:child_process';
import { createConnection } from 'node:net';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const port = Number(process.env.PORT || 8787);

function portIsOpen() {
  return new Promise((resolve) => {
    const socket = createConnection({ host: '127.0.0.1', port });
    socket.setTimeout(300);
    socket.once('connect', () => {
      socket.destroy();
      resolve(true);
    });
    socket.once('timeout', () => {
      socket.destroy();
      resolve(false);
    });
    socket.once('error', () => resolve(false));
  });
}

const deadline = Date.now() + 15_000;
while ((await portIsOpen()) && Date.now() < deadline) {
  await new Promise((resolve) => setTimeout(resolve, 100));
}

const child = spawn(process.execPath, [join(root, 'scripts', 'start.js')], {
  cwd: root,
  detached: true,
  env: process.env,
  stdio: 'ignore',
  windowsHide: true,
});
child.unref();
