import type {
  Case, CaseDetails, ClaimFixResponse, ClauseResponse, CreateCaseRequest,
  EvalResultsResponse, GroundAsset, HazardAnalysis, Hotspot, PresignResponse,
  ResolveResponse, RiskResponse,
} from './types.ts';
import { responseSchemas } from './response-schemas.ts';
import { MOCK_ASSETS, MOCK_HOTSPOTS, getMockRisk } from '../mocks/index.ts';

export class ApiError extends Error {
  code: string;
  statusCode: number;
  constructor(code: string, message: string, statusCode: number) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.statusCode = statusCode;
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function parseApiError(payload: unknown, statusCode: number): ApiError {
  const error = isObject(payload) && isObject(payload.error) ? payload.error : null;
  return new ApiError(
    typeof error?.code === 'string' ? error.code : 'INTERNAL',
    typeof error?.message === 'string' ? error.message : 'Unexpected server response',
    statusCode,
  );
}

// Validate contract fields before the single typed JSON boundary below.
function validate(value: unknown, schema: unknown, path = 'response'): void {
  if (!isObject(schema)) throw new ApiError('INVALID_RESPONSE', 'Missing response schema', 502);
  if (value === null && schema.nullable === true) return;
  const fail = () => { throw new ApiError('INVALID_RESPONSE', `Invalid API field: ${path}`, 502); };
  switch (schema.type) {
    case 'object':
      if (!isObject(value)) return fail();
      if (Array.isArray(schema.required)) {
        for (const key of schema.required) {
          if (typeof key === 'string' && !(key in value)) return fail();
        }
      }
      if (isObject(schema.properties)) {
        for (const [key, child] of Object.entries(schema.properties)) {
          if (key in value) validate(value[key], child, `${path}.${key}`);
        }
      }
      break;
    case 'array':
      if (!Array.isArray(value)) return fail();
      value.forEach((item, index) => validate(item, schema.items, `${path}[${index}]`));
      break;
    case 'string': if (typeof value !== 'string') return fail(); break;
    case 'boolean': if (typeof value !== 'boolean') return fail(); break;
    case 'integer': if (typeof value !== 'number' || !Number.isInteger(value)) return fail(); break;
    case 'number': if (typeof value !== 'number' || !Number.isFinite(value)) return fail(); break;
  }
  if (Array.isArray(schema.enum) && !schema.enum.includes(value)) return fail();
  if (typeof value === 'number') {
    if (typeof schema.minimum === 'number' && value < schema.minimum) return fail();
    if (typeof schema.maximum === 'number' && value > schema.maximum) return fail();
  }
  if (typeof value === 'string') {
    if (typeof schema.maxLength === 'number' && value.length > schema.maxLength) return fail();
    if (typeof schema.pattern === 'string' && !new RegExp(schema.pattern).test(value)) return fail();
  }
}

function decode<T>(operation: string, payload: unknown): T {
  validate(payload, responseSchemas[operation]);
  return payload as T;
}

export interface ApiClientOptions {
  baseUrl?: string;
  useMocks?: boolean;
  development?: boolean;
  fetch?: typeof globalThis.fetch;
}

export function createApiClient(options: ApiClientOptions = {}) {
  const base = (options.baseUrl || '/v1').replace(/\/+$/, '');
  const mock = options.useMocks === true;
  const ensureMode = () => {
    if (mock && !options.development) {
      throw new ApiError('MOCK_CONFIGURATION', 'Mock mode is permitted only in local development', 400);
    }
  };
  const request = async <T>(operation: string, path: string, body?: unknown): Promise<T> => {
    ensureMode();
    if (mock) {
      throw new ApiError('MOCK_READ_ONLY', 'Local mock mode is read-only; uploads, analysis and case workflows require a backend', 400);
    }
    let response: Response;
    try {
      response = await (options.fetch || globalThis.fetch)(`${base}${path}`, {
        method: body === undefined ? 'GET' : 'POST',
        headers: body === undefined ? { Accept: 'application/json' } : {
          Accept: 'application/json', 'Content-Type': 'application/json',
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
    } catch {
      throw new ApiError('NETWORK_ERROR', 'Could not connect to the backend', 0);
    }
    let payload: unknown;
    try { payload = await response.json(); }
    catch {
      if (!response.ok) throw parseApiError(null, response.status);
      throw new ApiError('INVALID_RESPONSE', 'Backend returned invalid JSON', response.status);
    }
    if (!response.ok) throw parseApiError(payload, response.status);
    return decode<T>(operation, payload);
  };
  return {
    fetchHealth: () => request<{ status: string; time: string }>('getHealth', '/health'),
    fetchHotspots: async (): Promise<{ hotspots: Hotspot[]; mock?: boolean }> => {
      ensureMode();
      return mock ? { hotspots: structuredClone(MOCK_HOTSPOTS), mock: true }
        : request<{ hotspots: Hotspot[]; mock?: boolean }>('getHotspots', '/hotspots');
    },
    fetchAssets: async (): Promise<{ assets: GroundAsset[]; mock?: boolean }> => {
      ensureMode();
      return mock ? { assets: structuredClone(MOCK_ASSETS), mock: true }
        : request<{ assets: GroundAsset[]; mock?: boolean }>('getAssets', '/assets');
    },
    // The UI slider expresses slowdown as percent; the contract requires a 0..1 fraction.
    fetchRisk: async (mode: 'whatif' | 'live', rain3h: number, rain24h: number, trafficPercent: number): Promise<RiskResponse> => {
      ensureMode();
      if (![rain3h, rain24h, trafficPercent].every(Number.isFinite)
          || rain3h < 0 || rain3h > 200 || rain24h < 0 || rain24h > 300
          || trafficPercent < 0 || trafficPercent > 100) {
        throw new ApiError('BAD_REQUEST', 'Risk inputs are outside the supported range', 400);
      }
      if (mock) {
        if (mode === 'live') throw new ApiError('MOCK_READ_ONLY', 'Live weather is unavailable in local mock mode', 400);
        return getMockRisk(rain3h, rain24h, trafficPercent / 100);
      }
      const params = new URLSearchParams({ mode, rain_3h_mm: String(rain3h),
        rain_prev24h_mm: String(rain24h), traffic_slowdown: String(trafficPercent / 100) });
      return request<RiskResponse>('getRisk', `/risk?${params}`);
    },
    presignUpload: (purpose: 'report' | 'fix', contentType: 'image/jpeg' | 'image/png') =>
      request<PresignResponse>('presignUpload', '/uploads/presign', { purpose, content_type: contentType }),
    analyzeHazard: (s3Key: string) => request<{ analysis: HazardAnalysis }>('analyzeHazard', '/analyze', { s3_key: s3Key }),
    resolveLocation: (lat: number, lng: number, assetType: string | null = null) => {
      const knownAsset = ['pothole', 'open_manhole', 'missing_drain_cover'].includes(assetType || '');
      return request<ResolveResponse>('resolveLocation', '/resolve', {
        lat, lng, ...(knownAsset ? { asset_type: assetType } : {}),
      });
    },
    createCase: (body: CreateCaseRequest) => request<Case>('createCase', '/cases', body),
    fetchCases: () => request<{ cases: Case[] }>('listCases', '/cases'),
    fetchCaseDetails: (caseId: string) => request<CaseDetails>('getCase', `/cases/${encodeURIComponent(caseId)}`),
    claimFix: async (caseId: string, s3Key: string, lat: number, lng: number): Promise<ClaimFixResponse> => {
      const result = await request<ClaimFixResponse>('claimFix', `/cases/${encodeURIComponent(caseId)}/claim-fix`, { s3_key: s3Key, lat, lng });
      return { ...result, explanation: result.verification?.explanation };
    },
    extractTenderClause: (docKey: string) => request<ClauseResponse>('extractTenderClause', '/tender/clause', { doc_key: docKey }),
    fetchEvalResults: async (): Promise<EvalResultsResponse> => {
      ensureMode();
      if (mock) return { rdd2022: null, backtest: null };
      return request<EvalResultsResponse>('getEvalResults', '/eval/results');
    },
  };
}

const env = import.meta.env || {};
export const MOCK_MODE = env.DEV === true && env.VITE_USE_MOCKS === 'true';
const client = createApiClient({ baseUrl: env.VITE_API_BASE,
  useMocks: env.VITE_USE_MOCKS === 'true', development: env.DEV === true });
export const { fetchHealth, fetchHotspots, fetchAssets, fetchRisk, presignUpload, analyzeHazard,
  resolveLocation, createCase, fetchCases, fetchCaseDetails, claimFix,
  extractTenderClause, fetchEvalResults } = client;

export function getBandColor(band: string): string {
  return ({ severe: '#ef4444', high: '#f97316', moderate: '#eab308', low: '#22c55e' } as Record<string, string>)[band] || '#22c55e';
}
export function getHazardColor(type: string): string {
  return ({ open_manhole: '#f43f5e', missing_drain_cover: '#a855f7', pothole: '#facc15' } as Record<string, string>)[type] || '#facc15';
}
export function debounce<Args extends unknown[]>(fn: (...args: Args) => void, delay: number) {
  let timer: ReturnType<typeof setTimeout> | undefined;
  return (...args: Args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

// Check the storage PUT before starting analysis or submitting a repair claim.
export async function uploadPhoto(uploadUrl: string, photo: Blob, contentType: 'image/jpeg' | 'image/png'): Promise<void> {
  let response: Response;
  try {
    response = await globalThis.fetch(uploadUrl, {
      method: 'PUT', headers: { 'Content-Type': contentType }, body: photo,
    });
  } catch {
    throw new ApiError('NETWORK_ERROR', 'Could not upload the photo', 0);
  }
  if (!response.ok) throw new ApiError('UPLOAD_FAILED', 'Photo upload failed', response.status);
}
