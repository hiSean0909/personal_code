'use strict';

const { EventEmitter } = require('node:events');
const { spawn } = require('node:child_process');
const { createInterface } = require('node:readline');

class AppServerClient extends EventEmitter {
  constructor(command, { args = ['app-server', '--stdio'], env = process.env, timeoutMs = 10000 } = {}) {
    super();
    Object.assign(this, { command, args, env, timeoutMs });
    this.child = null;
    this.lines = null;
    this.pending = new Map();
    this.nextId = 0;
    this.stopping = false;
  }

  async start() {
    if (this.child) throw new Error('APP_SERVER_ALREADY_STARTED');
    this.stopping = false;
    const child = spawn(this.command, this.args, {
      env: this.env, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'],
    });
    this.child = child;
    child.stderr.resume();
    const failed = () => {
      this.rejectPending('APP_SERVER_EXITED');
      if (!this.stopping) this.emit('unavailable');
    };
    child.on('error', failed);
    child.on('exit', failed);
    child.stdin.on('error', failed);
    this.lines = createInterface({ input: child.stdout });
    this.lines.on('line', line => this.receive(line));
    try {
      await this.request('initialize', {
        clientInfo: { name: 'codex_status_bar', title: 'Codex Status Bar', version: '0.1.0' },
      });
      this.notify('initialized', {});
    } catch (error) {
      await this.stop();
      throw error;
    }
  }

  receive(line) {
    let message;
    try { message = JSON.parse(line); } catch { return; }
    if (!message || typeof message !== 'object') return;
    const pending = this.pending.get(message.id);
    if (pending && !message.method) {
      this.pending.delete(message.id);
      clearTimeout(pending.timer);
      if (message.error) pending.reject(new Error('APP_SERVER_REQUEST_REJECTED'));
      else pending.resolve(message.result);
      return;
    }
    if (message.method && message.id !== undefined) {
      this.write({ id: message.id, error: { code: -32601, message: 'Request not supported by the usage monitor' } });
    } else if (message.method === 'account/rateLimits/updated') {
      this.emit('rate-limits', message.params);
    } else if (message.method === 'account/updated') {
      this.emit('account-changed');
    }
  }

  write(message) {
    if (!this.child?.stdin.writable) throw new Error('APP_SERVER_UNAVAILABLE');
    this.child.stdin.write(JSON.stringify(message) + '\n', () => {});
  }

  notify(method, params) {
    this.write({ method, params });
  }

  request(method, params) {
    if (!this.child?.stdin.writable) return Promise.reject(new Error('APP_SERVER_UNAVAILABLE'));
    const id = ++this.nextId;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error('APP_SERVER_REQUEST_TIMEOUT'));
      }, this.timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      try {
        this.write({ id, method, ...(params === undefined ? {} : { params }) });
      } catch {
        this.pending.delete(id);
        clearTimeout(timer);
        reject(new Error('APP_SERVER_UNAVAILABLE'));
      }
    });
  }

  readAllowance() {
    return this.request('account/rateLimits/read');
  }

  rejectPending(category) {
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timer);
      pending.reject(new Error(category));
    }
    this.pending.clear();
  }

  async stop() {
    this.stopping = true;
    this.rejectPending('APP_SERVER_STOPPED');
    const child = this.child;
    this.child = null;
    this.lines?.close();
    this.lines = null;
    if (!child || child.exitCode !== null || child.signalCode !== null) return;
    await new Promise(resolve => {
      let forceTimer;
      const done = () => { clearTimeout(forceTimer); resolve(); };
      child.once('exit', done);
      child.once('error', done);
      forceTimer = setTimeout(() => {
        child.kill();
        // The exit event confirms cleanup; the caller does not just assume it.
      }, 2000);
      child.stdin.end();
    });
  }
}

module.exports = { AppServerClient };
