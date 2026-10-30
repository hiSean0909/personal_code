'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

for (const shell of ['powershell.exe', 'pwsh.exe']) {
  test(`${shell} file launcher selects Node.js 24 and preserves management failures`, {
    skip: process.platform !== 'win32',
  }, () => {
    const runtimeRoot = path.resolve(__dirname, '.runtime');
    fs.mkdirSync(runtimeRoot, { recursive: true });
    const fixture = fs.mkdtempSync(path.join(runtimeRoot, 'launcher-test-'));
    try {
      const script = path.join(fixture, 'manage.ps1');
      const entry = path.join(fixture, 'manage.cjs');
      fs.copyFileSync(path.join(__dirname, 'manage.ps1'), script);
      fs.writeFileSync(entry, 'console.log(JSON.stringify({node:process.versions.node}));\n');
      const run = () => spawnSync(shell, [
        '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', script, 'doctor',
      ], { encoding: 'utf8', windowsHide: true, timeout: 20000 });

      const success = run();
      assert.ifError(success.error);
      assert.equal(success.status, 0, success.stderr);
      assert.ok(Number(JSON.parse(success.stdout).node.split('.')[0]) >= 24);

      fs.writeFileSync(entry, "process.stderr.write('KNOWN_MANAGEMENT_FAILURE\\n');process.exitCode=7;\n");
      const failure = run();
      assert.ifError(failure.error);
      assert.equal(failure.status, 7, failure.stderr);
      assert.match(failure.stderr, /KNOWN_MANAGEMENT_FAILURE/);
      assert.doesNotMatch(failure.stderr, /selected Node.js runtime could not execute/);
    } finally {
      if (path.dirname(fixture) === runtimeRoot) fs.rmSync(fixture, { recursive: true, force: true });
    }
  });
}
