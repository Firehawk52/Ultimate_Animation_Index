import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';

async function text(path) {
  return readFile(new URL(path, import.meta.url), 'utf8');
}

test('release version stays consistent across distributable files', async () => {
  const packageJson = JSON.parse(await text('../package.json'));
  const packageLock = JSON.parse(await text('../package-lock.json'));
  const [app, backup, html, changelog, issueTemplate] = await Promise.all([
    text('../public/app.js'),
    text('../public/user-backup.js'),
    text('../public/index.html'),
    text('../CHANGELOG.md'),
    text('../.github/ISSUE_TEMPLATE/bug_report.yml'),
  ]);
  const version = packageJson.version;
  const escapedVersion = version.replaceAll('.', '\\.');

  assert.equal(packageLock.version, version);
  assert.equal(packageLock.packages[''].version, version);
  assert.match(app, new RegExp(`APP_VERSION = '${escapedVersion}'`));
  assert.match(backup, new RegExp(`appVersion = '${escapedVersion}'`));
  assert.match(html, new RegExp(`styles\\.css\\?v=${escapedVersion}`));
  assert.match(html, new RegExp(`app\\.js\\?v=${escapedVersion}`));
  assert.match(changelog, new RegExp(`## \\[${escapedVersion}\\]`));
  assert.match(issueTemplate, new RegExp(`placeholder: ${escapedVersion}`));
});
