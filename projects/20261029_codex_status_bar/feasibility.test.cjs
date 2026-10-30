'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { AppServerClient } = require('./codex-data.cjs');
const { validateEndpoint } = require('./agent.cjs');

const peer = `
const {createInterface}=require('node:readline');
const lines=createInterface({input:process.stdin});
const send=value=>process.stdout.write(JSON.stringify(value)+'\\n');
lines.on('line',line=>{
  const m=JSON.parse(line);
  if(m.method==='initialize') send({id:m.id,result:{}});
  else if(m.method==='account/rateLimits/read') send({id:m.id,result:{rateLimits:{limitId:'codex',primary:{usedPercent:25,windowDurationMins:300},secondary:null}}});
  else if(m.method==='slow') setTimeout(()=>send({id:m.id,result:'slow'}),40);
  else if(m.method==='fast') send({id:m.id,result:'fast'});
  else if(m.method==='reject') send({id:m.id,error:{message:'private-server-detail',code:-1}});
  else if(m.method==='notify') {send({method:'account/rateLimits/updated',params:{rateLimits:{primary:{usedPercent:26}}}});send({id:m.id,result:{}});}
});
`;

function client(timeoutMs = 1000) {
  return new AppServerClient(process.execPath, { args: ['-e', peer], timeoutMs });
}

test('initialization, allowance reading, and EOF shutdown leave no owned server', async () => {
  const rpc = client();
  try {
    await rpc.start();
    const child = rpc.child;
    const result = await rpc.readAllowance();
    assert.equal(result.rateLimits.primary.usedPercent, 25);
    await rpc.stop();
    assert.equal(child.exitCode, 0);
    assert.equal(rpc.pending.size, 0);
    assert.equal(rpc.child, null);
  } finally { await rpc.stop(); }
});

test('out-of-order replies resolve the matching request', async () => {
  const rpc = client();
  try {
    await rpc.start();
    const slow = rpc.request('slow');
    const fast = rpc.request('fast');
    assert.equal(await fast, 'fast');
    assert.equal(await slow, 'slow');
  } finally { await rpc.stop(); }
});

test('request errors expose a category without forwarding server details', async () => {
  const rpc = client();
  try {
    await rpc.start();
    await assert.rejects(rpc.request('reject'), { message: 'APP_SERVER_REQUEST_REJECTED' });
    assert.equal(rpc.pending.size, 0);
  } finally { await rpc.stop(); }
});

test('timeouts remove pending requests and permit clean shutdown', async () => {
  const rpc = client();
  try {
    await rpc.start();
    rpc.timeoutMs = 40;
    await assert.rejects(rpc.request('silent'), { message: 'APP_SERVER_REQUEST_TIMEOUT' });
    assert.equal(rpc.pending.size, 0);
    const child = rpc.child;
    await rpc.stop();
    assert.equal(child.exitCode, 0);
  } finally { await rpc.stop(); }
});

test('allowance notifications are delivered independently of request replies', async () => {
  const rpc = client();
  try {
    await rpc.start();
    const notification = new Promise(resolve => rpc.once('rate-limits', resolve));
    await rpc.request('notify');
    assert.equal((await notification).rateLimits.primary.usedPercent, 26);
  } finally { await rpc.stop(); }
});

test('CDP permits only credential-free loopback WebSockets on the fixed port', () => {
  for (const host of ['127.0.0.1', 'localhost', '[::1]']) {
    assert.equal(validateEndpoint(`ws://${host}:39222/devtools/page/fixture`).port, '39222');
  }
  for (const address of [
    'ws://example.com:39222/devtools/page/fixture',
    'ws://127.0.0.1:9222/devtools/page/fixture',
    'wss://127.0.0.1:39222/devtools/page/fixture',
    'http://127.0.0.1:39222/devtools/page/fixture',
    'ws://user:secret@127.0.0.1:39222/devtools/page/fixture',
  ]) assert.throws(() => validateEndpoint(address), { message: 'UNEXPECTED_DEBUGGING_ENDPOINT' });
});
