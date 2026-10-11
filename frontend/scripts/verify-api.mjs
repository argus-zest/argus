// Dependency-free runtime checks for Node 22+; these do not replace tsc/Vitest/browser checks.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  createApiClient, parseApiError, getBandColor, getHazardColor, debounce, uploadPhoto,
} from '../src/lib/api.ts';
import { MOCK_HOTSPOTS, getMockRisk } from '../src/mocks/index.ts';

const json = (payload, status = 200) => new Response(JSON.stringify(payload), { status });
const rejecting = (code) => (error) => error.code === code;

test('contract request paths, JSON body and encoded case IDs', async () => {
  const calls = [];
  const client = createApiClient({ baseUrl: 'https://api.test/v1/', fetch: async (url, options) => {
    calls.push({ url, options });
    return json({ upload_url: 'https://bucket.test/upload', s3_key: 'uploads/test.jpg', expires_in: 300 });
  } });
  const response = await client.presignUpload('report', 'image/jpeg');
  assert.equal(response.s3_key, 'uploads/test.jpg');
  assert.equal(calls[0].url, 'https://api.test/v1/uploads/presign');
  assert.deepEqual(JSON.parse(calls[0].options.body), { purpose: 'report', content_type: 'image/jpeg' });
  assert.equal(calls[0].options.method, 'POST');
  assert.equal(calls[0].options.headers['Content-Type'], 'application/json');
  await assert.rejects(client.fetchCaseDetails('CS/a?'), rejecting('INVALID_RESPONSE'));
  assert.equal(calls[1].url, 'https://api.test/v1/cases/CS%2Fa%3F');
});

test('risk slider percent becomes a bounded contract fraction', async () => {
  let url;
  const client = createApiClient({ fetch: async (target) => { url = target; return json(getMockRisk(40, 30, .3)); } });
  await client.fetchRisk('whatif', 40, 30, 30);
  assert.equal(new URL(url, 'http://local.test').searchParams.get('traffic_slowdown'), '0.3');
  await assert.rejects(client.fetchRisk('whatif', 40, 30, 101), rejecting('BAD_REQUEST'));
});

test('read responses validate nested contract fields and ranges', async () => {
  const valid = structuredClone(MOCK_HOTSPOTS);
  const client = createApiClient({ fetch: async () => json({ hotspots: valid }) });
  assert.equal((await client.fetchHotspots()).hotspots.length, 10);
  valid[0].jurisdiction.confidence = 2;
  await assert.rejects(client.fetchHotspots(), rejecting('INVALID_RESPONSE'));
});

test('malformed success payloads fail before consumers render them', async () => {
  const client = createApiClient({ fetch: async () => json({ assets: [{ asset_id: 'missing-fields' }] }) });
  await assert.rejects(client.fetchAssets(), rejecting('INVALID_RESPONSE'));
  const badJson = createApiClient({ fetch: async () => new Response('<html>proxy error</html>') });
  await assert.rejects(badJson.fetchAssets(), rejecting('INVALID_RESPONSE'));
});

test('evaluation objects cannot masquerade as renderable metric results', async () => {
  const client = createApiClient({ fetch: async () => json({ rdd2022: { precision: 'not-a-number' }, backtest: null }) });
  await assert.rejects(client.fetchEvalResults(), rejecting('INVALID_RESPONSE'));
});

test('backend errors retain code, message and HTTP status', async () => {
  const client = createApiClient({ fetch: async () => json({ error: { code: 'IMAGE_TOO_LARGE', message: 'Too large' } }, 413) });
  await assert.rejects(client.analyzeHazard('uploads/test.jpg'), (error) =>
    error.code === 'IMAGE_TOO_LARGE' && error.message === 'Too large' && error.statusCode === 413);
  assert.equal(parseApiError(null, 500).message, 'Unexpected server response');
});

test('connection failure never falls back to mock data', async () => {
  const client = createApiClient({ fetch: async () => { throw new Error('offline'); } });
  await assert.rejects(client.fetchHotspots(), rejecting('NETWORK_ERROR'));
});

test('local fixtures are read-only, visibly identified, and not live weather', async () => {
  const client = createApiClient({ useMocks: true, development: true, fetch: async () => { throw new Error('Unexpected network'); } });
  const first = await client.fetchHotspots();
  assert.equal(first.mock, true);
  first.hotspots[0].name = 'mutated';
  assert.notEqual((await client.fetchHotspots()).hotspots[0].name, 'mutated');
  assert.equal((await client.fetchRisk('whatif', 40, 30, 30)).mock, true);
  assert.deepEqual(await client.fetchEvalResults(), { rdd2022: null, backtest: null });
  await assert.rejects(client.fetchRisk('live', 0, 0, 0), rejecting('MOCK_READ_ONLY'));
  await assert.rejects(client.presignUpload('report', 'image/jpeg'), rejecting('MOCK_READ_ONLY'));
  await assert.rejects(client.createCase({ timer_profile: 'demo' }), rejecting('MOCK_READ_ONLY'));
});

test('production rejects any requested mock mode', async () => {
  const client = createApiClient({ useMocks: true, development: false });
  await assert.rejects(client.fetchHotspots(), rejecting('MOCK_CONFIGURATION'));
});

test('closure explanation comes from the nested backend verification', async () => {
  const client = createApiClient({ fetch: async () => json({ accepted: false, reason: 'LOW_CONFIDENCE', distance_m: 10, verification: { confidence: .1, explanation: 'Unclear image' } }) });
  assert.equal((await client.claimFix('CS-ABC123', 'uploads/fix.jpg', 28, 77)).explanation, 'Unclear image');
});

test('failed storage PUT does not count as a completed upload', async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async () => new Response('', { status: 403 });
    await assert.rejects(uploadPhoto('https://bucket.test/upload', new Blob(['image']), 'image/jpeg'), rejecting('UPLOAD_FAILED'));
  } finally { globalThis.fetch = original; }
});

test('color mappings and debounced calls preserve existing utility behavior', async () => {
  assert.equal(getBandColor('severe'), '#ef4444');
  assert.equal(getBandColor('unknown'), '#22c55e');
  assert.equal(getHazardColor('open_manhole'), '#f43f5e');
  const calls = [];
  const delayed = debounce((value) => calls.push(value), 10);
  delayed(1); delayed(2);
  assert.deepEqual(calls, []);
  await new Promise((resolve) => setTimeout(resolve, 25));
  assert.deepEqual(calls, [2]);
});
