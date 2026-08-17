import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(dirname(fileURLToPath(import.meta.url)));

function execute(command, args, { capture = false, allowFailure = false } = {}) {
  const result = spawnSync(command, args, {
    cwd: root,
    encoding: 'utf8',
    stdio: capture ? 'pipe' : 'inherit',
  });
  if (result.error?.code === 'ENOENT') throw new Error(`${command} is required but was not found.`);
  if (result.error) throw result.error;
  if (!allowFailure && result.status !== 0)
    throw new Error(`${command} ${args.join(' ')} failed with exit code ${result.status}.`);
  return { status: result.status, output: String(result.stdout || '').trim() };
}

function executeNpm(args) {
  if (process.env.npm_execpath) return execute(process.execPath, [process.env.npm_execpath, ...args]);
  const command = process.platform === 'win32' ? 'npm.cmd' : 'npm';
  return execute(command, args);
}

export function validateUpdateState({ insideWorkTree, branch, changes }) {
  if (insideWorkTree !== 'true')
    throw new Error('Automatic updates require a Git clone. Download the latest release manually instead.');
  if (branch !== 'main')
    throw new Error(`Automatic updates require the main branch. Current branch: ${branch || 'detached'}.`);
  if (changes.trim())
    throw new Error('Local source changes were found. Commit, stash, or remove them before updating.');
}

async function appIsRunning() {
  const port = process.env.PORT || '8787';
  try {
    const response = await fetch(`http://127.0.0.1:${port}/api/health`, {
      signal: AbortSignal.timeout(900),
    });
    return response.ok;
  } catch {
    return false;
  }
}

export async function updateInstallation({ checkRunningServer = true } = {}) {
  console.log('\nUltimate Animation Index updater\n');
  if (checkRunningServer && (await appIsRunning()))
    throw new Error('The app is still running. Close its server window, then run the updater again.');

  const insideWorkTree = execute('git', ['rev-parse', '--is-inside-work-tree'], { capture: true }).output;
  const branch = execute('git', ['branch', '--show-current'], { capture: true }).output;
  const changes = execute('git', ['status', '--porcelain'], { capture: true }).output;
  validateUpdateState({ insideWorkTree, branch, changes });

  console.log('Checking GitHub for updates...');
  execute('git', ['fetch', '--prune', 'origin', 'main']);
  const current = execute('git', ['rev-parse', 'HEAD'], { capture: true }).output;
  const latest = execute('git', ['rev-parse', 'origin/main'], { capture: true }).output;

  if (current === latest) {
    console.log('Already up to date.');
  } else {
    const canFastForward = execute('git', ['merge-base', '--is-ancestor', 'HEAD', 'origin/main'], {
      capture: true,
      allowFailure: true,
    });
    if (canFastForward.status !== 0)
      throw new Error(
        'The local branch has diverged from origin/main. Update manually to preserve its commits.',
      );

    console.log('Installing the latest source...');
    execute('git', ['merge', '--ff-only', 'origin/main']);
    console.log('Synchronizing packages...');
    executeNpm(['ci', '--ignore-scripts', '--no-audit', '--no-fund']);
  }

  console.log('Validating and regenerating the local catalog...');
  execute(process.execPath, ['scripts/build-catalog.mjs']);
  console.log('\nUpdate complete. Start the app again with npm start or its RUN launcher.\n');
}

const isDirectRun = process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url));
if (isDirectRun) {
  try {
    await updateInstallation();
  } catch (error) {
    console.error(`\nUpdate stopped: ${error.message}\n`);
    process.exitCode = 1;
  }
}
