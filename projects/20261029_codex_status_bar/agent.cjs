'use strict';

const CDP_PORT = 39222;

function validateEndpoint(address) {
  const url = new URL(address);
  if (url.protocol !== 'ws:' || !['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname) ||
      url.port !== String(CDP_PORT) || url.username || url.password) {
    throw new Error('UNEXPECTED_DEBUGGING_ENDPOINT');
  }
  return url;
}

async function listTargets() {
  const response = await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`, {
    redirect: 'error', signal: AbortSignal.timeout(3000),
  });
  if (!response.ok) throw new Error('DEBUGGING_ENDPOINT_UNAVAILABLE');
  const targets = await response.json();
  if (!Array.isArray(targets)) throw new Error('INVALID_DEBUGGING_TARGETS');
  return targets.filter(target => target.type === 'page' && typeof target.webSocketDebuggerUrl === 'string');
}

class CdpSession {
  constructor(address) {
    this.address = validateEndpoint(address);
    this.socket = null;
    this.pending = new Map();
    this.nextId = 0;
  }

  async connect() {
    this.socket = new WebSocket(this.address);
    const socket = this.socket;
    socket.addEventListener('message', event => {
      let message;
      try { message = JSON.parse(event.data); } catch { return; }
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      clearTimeout(pending.timer);
      if (message.error || message.result?.exceptionDetails) pending.reject(new Error('DEBUGGING_EVALUATION_FAILED'));
      else pending.resolve(message.result?.result?.value);
    });
    const disconnected = () => {
      for (const pending of this.pending.values()) {
        clearTimeout(pending.timer);
        pending.reject(new Error('DEBUGGING_CONNECTION_CLOSED'));
      }
      this.pending.clear();
    };
    socket.addEventListener('close', disconnected);
    socket.addEventListener('error', disconnected);
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        socket.close();
        reject(new Error('DEBUGGING_CONNECTION_TIMEOUT'));
      }, 3000);
      socket.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
      socket.addEventListener('error', () => {
        clearTimeout(timer);
        reject(new Error('DEBUGGING_CONNECTION_FAILED'));
      }, { once: true });
    });
  }

  evaluate(expression) {
    if (this.socket?.readyState !== WebSocket.OPEN) return Promise.reject(new Error('DEBUGGING_CONNECTION_CLOSED'));
    const id = ++this.nextId;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error('DEBUGGING_EVALUATION_TIMEOUT'));
      }, 3000);
      this.pending.set(id, { resolve, reject, timer });
      this.socket.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: {
        expression, returnByValue: true, awaitPromise: true,
      } }));
    });
  }

  close() {
    this.socket?.close();
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timer);
      pending.reject(new Error('DEBUGGING_CONNECTION_CLOSED'));
    }
    this.pending.clear();
  }
}

module.exports = { CDP_PORT, validateEndpoint, listTargets, CdpSession };
