const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { createApp } = require('../src/app');
const { listGear } = require('../src/gear');

let server;
let baseUrl;

before(async () => {
  // Port 0 means the OS picks a free port
  server = createApp().listen(0);
  await new Promise((resolve) => server.once('listening', resolve));
  baseUrl = `http://127.0.0.1:${server.address().port}`;
});

after(() => {
  server.close();
});

test('GET / returns app name, version and commit', async () => {
  const res = await fetch(`${baseUrl}/`);
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(body.app, 's16-gear-api');
  assert.match(body.version, /^\d+\.\d+\.\d+$/);
  assert.ok(body.commit);
});

test('GET /health returns ok', async () => {
  const res = await fetch(`${baseUrl}/health`);
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), { status: 'ok' });
});

test('GET /api/gear returns the full list', async () => {
  const res = await fetch(`${baseUrl}/api/gear`);
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(body.count, 4);
  assert.equal(body.items.length, body.count);
});

test('GET /api/gear?available=true returns only available items', async () => {
  const res = await fetch(`${baseUrl}/api/gear?available=true`);
  const body = await res.json();
  assert.ok(body.count > 0);
  assert.ok(body.items.every((g) => g.available === true));
});

test('unknown route returns 404 JSON', async () => {
  const res = await fetch(`${baseUrl}/does-not-exist`);
  assert.equal(res.status, 404);
  assert.deepEqual(await res.json(), { error: 'not found' });
});

test('listGear items have id, name, category and available', () => {
  for (const item of listGear()) {
    assert.equal(typeof item.id, 'number');
    assert.equal(typeof item.name, 'string');
    assert.equal(typeof item.category, 'string');
    assert.equal(typeof item.available, 'boolean');
  }
});
