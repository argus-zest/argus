import { describe, it, expect, vi } from 'vitest';
import { createApiClient, uploadPhoto } from '../lib/api';
import { MOCK_HOTSPOTS, getMockRisk } from '../mocks';

const json = (payload: unknown, status = 200) => new Response(JSON.stringify(payload), { status });

describe('restored API client', () => {
  it('converts UI traffic percent to the contract fraction', async () => {
    const fetch = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => json(getMockRisk(40, 30, .3)));
    const client = createApiClient({ baseUrl: '/v1/', fetch });
    await client.fetchRisk('whatif', 40, 30, 30);
    expect(fetch.mock.calls[0][0]).toContain('traffic_slowdown=0.3');
  });

  it('rejects malformed nested fields before rendering', async () => {
    const hotspots = structuredClone(MOCK_HOTSPOTS);
    hotspots[0].jurisdiction.confidence = 2;
    const client = createApiClient({ fetch: async () => json({ hotspots }) });
    await expect(client.fetchHotspots()).rejects.toMatchObject({ code: 'INVALID_RESPONSE' });
  });

  it('retains HTTP errors and never silently enables mocks', async () => {
    const client = createApiClient({ fetch: async () => json({ error: { code: 'MODEL_ERROR', message: 'Model unavailable' } }, 502) });
    await expect(client.analyzeHazard('uploads/test.jpg')).rejects.toMatchObject({ code: 'MODEL_ERROR', statusCode: 502 });
    const offline = createApiClient({ fetch: async () => { throw new Error('offline'); } });
    await expect(offline.fetchHotspots()).rejects.toMatchObject({ code: 'NETWORK_ERROR' });
  });

  it('permits explicitly marked local read fixtures and refuses writes', async () => {
    const client = createApiClient({ development: true, useMocks: true });
    expect((await client.fetchHotspots()).mock).toBe(true);
    await expect(client.presignUpload('report', 'image/jpeg')).rejects.toMatchObject({ code: 'MOCK_READ_ONLY' });
    await expect(client.fetchRisk('live', 0, 0, 0)).rejects.toMatchObject({ code: 'MOCK_READ_ONLY' });
  });

  it('rejects production mock configuration', async () => {
    const client = createApiClient({ development: false, useMocks: true });
    await expect(client.fetchHotspots()).rejects.toMatchObject({ code: 'MOCK_CONFIGURATION' });
  });

  it('refuses failed S3 uploads', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('', { status: 403 })));
    try {
      await expect(uploadPhoto('https://bucket.test/upload', new Blob(['test']), 'image/jpeg'))
        .rejects.toMatchObject({ code: 'UPLOAD_FAILED', statusCode: 403 });
    } finally { vi.unstubAllGlobals(); }
  });
});
