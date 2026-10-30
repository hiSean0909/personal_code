'use strict';

const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { execFileSync, spawn } = require('node:child_process');
const { AppServerClient } = require('./codex-data.cjs');
const { CDP_PORT, listTargets, CdpSession } = require('./agent.cjs');

function powershell(code) {
  return execFileSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', code], {
    encoding: 'utf8', windowsHide: true, stdio: ['ignore', 'pipe', 'ignore'], timeout: 15000,
  }).trim();
}

function desktopState() {
  const script = "@{running=@(Get-Process ChatGPT -ErrorAction SilentlyContinue | Where-Object {$_.Path -like '*OpenAI.Codex_*'} | Select-Object -ExpandProperty Path -Unique);installed=@(Get-AppxPackage -Name OpenAI.Codex -ErrorAction SilentlyContinue | Select-Object -ExpandProperty InstallLocation)} | ConvertTo-Json -Compress";
  const state = JSON.parse(powershell(script));
  const running = Array.isArray(state.running) ? state.running : [];
  const candidates = [...running, ...(state.installed || []).map(root => path.join(root, 'app', 'ChatGPT.exe'))];
  return { running: running.length > 0, app: candidates.find(file => fs.existsSync(file)) || null };
}

function discoverCli() {
  const root = path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local'), 'OpenAI', 'Codex', 'bin');
  const candidates = [path.join(root, 'codex.exe')];
  try {
    candidates.push(...fs.readdirSync(root, { withFileTypes: true })
      .filter(entry => entry.isDirectory())
      .map(entry => path.join(root, entry.name, 'codex.exe'))
      .filter(file => fs.existsSync(file))
      .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs));
  } catch {}
  for (const command of candidates) {
    if (!fs.existsSync(command)) continue;
    try {
      const version = execFileSync(command, ['--version'], {
        encoding: 'utf8', windowsHide: true, stdio: ['ignore', 'pipe', 'ignore'], timeout: 5000,
      }).trim();
      if (/^codex-cli\s+\S+$/.test(version)) return { command, version };
    } catch {}
  }
  throw new Error('EXECUTABLE_CODEX_CLI_NOT_FOUND');
}

function codexEnvironment() {
  const profile = process.env.USERPROFILE || os.homedir();
  return { ...process.env, HOME: process.env.HOME || profile,
    CODEX_HOME: process.env.CODEX_HOME || path.join(profile, '.codex') };
}

function requireRuntime() {
  if (Number(process.versions.node.split('.')[0]) < 24) throw new Error('NODE_24_REQUIRED');
  if (typeof WebSocket !== 'function' || typeof fetch !== 'function' ||
      typeof require('node:sqlite').DatabaseSync !== 'function') throw new Error('NODE_CAPABILITY_MISSING');
}

async function quota() {
  const cli = discoverCli();
  const client = new AppServerClient(cli.command, { env: codexEnvironment() });
  let result;
  try {
    await client.start();
    const response = await client.readAllowance();
    const bucket = Object.hasOwn(response.rateLimitsByLimitId || {}, 'codex')
      ? response.rateLimitsByLimitId.codex : response.rateLimits;
    const validBucket = bucket && (bucket.limitId == null || bucket.limitId === 'codex');
    const windows = validBucket ? [bucket.primary, bucket.secondary].filter(Boolean) : [];
    result = { available: true, windows: windows.map(window => ({
      durationMinutes: window.windowDurationMins,
      usedPercent: window.usedPercent,
    })) };
  } finally {
    await client.stop();
  }
  return { ...result, ownedServerStopped: true };
}

async function inspect() {
  const targets = await listTargets();
  const reports = [];
  for (const target of targets) {
    const session = new CdpSession(target.webSocketDebuggerUrl);
    try {
      await session.connect();
      const report = await session.evaluate(`(() => {
        const visible = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
        const bars = [...document.querySelectorAll('[data-window-titlebar], [data-app-shell-titlebar-content]')].filter(visible);
        const pages = [...document.querySelectorAll('[data-app-shell-active-page]')].filter(visible);
        const match = (location.pathname + location.hash).match(/\\/local\\/([a-zA-Z0-9-]+)/);
        return {isCodexPage: typeof window.electronBridge === 'object' && typeof window.codexWindowType === 'string',
          windowType: window.codexWindowType ?? null, viewport: {width: innerWidth, height: innerHeight},
          visibleTitlebars: bars.map(el => {const r=el.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};}),
          visibleActivePageCount: pages.length, locationHasConversationId: !!match};
      })()`);
      reports.push(report);
    } finally {
      session.close();
    }
  }
  return { debuggingAvailable: true, pages: reports };
}

async function start() {
  try {
    const targets = await listTargets();
    if (targets.length && (await inspect()).pages.some(page => page.isCodexPage)) {
      return { debuggingAvailable: true, message: 'Codex is ready for integration inspection. Ring monitoring is not implemented yet.' };
    }
    throw new Error('DEBUGGING_PORT_IN_USE');
  } catch (error) {
    if (error.message === 'DEBUGGING_PORT_IN_USE') throw error;
    if (error.message !== 'fetch failed' && error.code !== 'ECONNREFUSED') throw error;
    if (error.cause?.code !== 'ECONNREFUSED' && error.code !== 'ECONNREFUSED') throw new Error('DEBUGGING_PORT_STATE_UNCONFIRMED');
  }
  const desktop = desktopState();
  if (desktop.running) throw new Error('SAVE_WORK_AND_FULLY_QUIT_CODEX_BEFORE_START');
  if (!desktop.app) throw new Error('INSTALLED_CODEX_APP_NOT_FOUND');
  const child = spawn(desktop.app, ['--remote-debugging-address=127.0.0.1', `--remote-debugging-port=${CDP_PORT}`], {
    detached: true, stdio: 'ignore', windowsHide: false,
  });
  await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', () => reject(new Error('CODEX_LAUNCH_FAILED'))); });
  child.unref();
  return { launched: true, message: 'Codex opened for integration inspection. Ring monitoring is not implemented yet. Return to this chat after reopening.' };
}

async function main() {
  requireRuntime();
  const action = process.argv[2] || 'doctor';
  let result;
  if (action === 'doctor') {
    const cli = discoverCli(), desktop = desktopState();
    let debuggingAvailable = false;
    try { debuggingAvailable = (await listTargets()).length > 0; } catch {}
    result = { node: process.version, cli: cli.version, appFound: !!desktop.app, appRunning: desktop.running, debuggingAvailable };
  } else if (action === 'quota') result = await quota();
  else if (action === 'inspect') result = await inspect();
  else if (action === 'start') result = await start();
  else throw new Error('USE_DOCTOR_QUOTA_START_OR_INSPECT');
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
}

module.exports = { discoverCli, desktopState, codexEnvironment, requireRuntime, quota, inspect, start };
if (require.main === module) main().catch(error => {
  const category = /^[A-Z][A-Z0-9_]+$/.test(error.message) ? error.message : 'OPERATION_FAILED';
  process.stderr.write(category + '\n');
  process.exitCode = 1;
});
