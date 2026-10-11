// API shapes follow contracts/openapi.yaml and contracts/schemas/*.json.
export type RiskBand = 'low' | 'moderate' | 'high' | 'severe';
export type AssetType = 'open_manhole' | 'missing_drain_cover' | 'pothole';
export type HazardType = AssetType | 'waterlogging' | 'none' | 'unclear';
export type Owner = 'NHAI' | 'NDMC' | 'PWD' | 'DJB' | 'MCD' | 'ORPHAN';
export type Provenance = 'sourced' | 'illustrative' | 'simulated';
export interface MockIdentification { mock?: boolean; source?: string }
export interface GroundAsset {
  asset_id: string; type: AssetType; severity: number; lat: number; lng: number;
  road_id?: string | null; reference_photo_key?: string | null;
  provenance: Provenance; seeded: boolean;
}
export interface Road {
  road_id?: string; name?: string; road_class?: string; width_ft?: number | null;
  provenance?: string;
}
export interface Jurisdiction {
  owner: Owner; confidence: number; reasons: string[]; start_rung: number;
  officer_role: string; provenance_note: string;
}
export interface Warranty {
  status: 'in_warranty' | 'expired' | 'unknown'; contractor_label: string;
  completion_date: string | null; end_date: string | null; days_remaining: number;
  work_type: string; clause_text: string | null; tender_doc_key: string | null;
  provenance: string;
}
export interface Hotspot {
  hotspot_id: string; name: string; lat: number; lng: number; coord_verified: boolean;
  provenance: Provenance; road_id?: string;
  features: {
    elev_m?: number | null; depression_m?: number | null; rel_elev_m?: number | null;
    underpass?: boolean; news_events_count?: number | null;
  };
  road: Road | null; jurisdiction: Jurisdiction; warranty: Warranty; assets: GroundAsset[];
}
export interface RiskScore {
  hotspot_id: string; susceptibility: number; probability: number; band: RiskBand;
  drivers: { name: string; contribution: number; missing: boolean }[];
  hazard_under_water?: { score: number; weight: number; asset_ids: string[] };
}
export interface RiskResponse extends MockIdentification {
  mode: 'whatif' | 'live'; generated_at: string;
  inputs: { rain_3h_mm: number; rain_prev24h_mm: number; traffic_slowdown: number; source: string };
  model: { version: string; fitted: boolean }; scores: RiskScore[];
}
export interface HazardAnalysis extends MockIdentification {
  hazard_type: HazardType; severity: number; submerged: boolean; confidence: number;
  description: string; visible_evidence: string;
}
export interface Case {
  case_id: string; hotspot_id?: string | null; asset_id?: string | null;
  lat: number; lng: number;
  status: 'OPEN' | 'AWAITING_FIX' | 'FIX_CLAIMED' | 'CLOSED_VERIFIED' | 'ESCALATED_DM' | 'UNRESOLVED_FINAL';
  rung: number; owner: Owner; jurisdiction: Jurisdiction; warranty: Warranty;
  analysis?: HazardAnalysis | null; photo_key?: string | null; execution_arn?: string | null;
  timer_profile?: 'demo' | 'real'; dry_run: boolean; seeded?: boolean; demo_run?: boolean;
  created_at: string; updated_at: string;
}
export interface CaseEvent {
  case_id: string; ts_seq: string;
  type: 'CASE_OPENED' | 'JURISDICTION_RESOLVED' | 'NOTICE_SENT' | 'REMINDER_SENT' | 'ESCALATED' | 'FIX_CLAIMED' | 'CLOSURE_VERIFIED' | 'CLOSURE_REJECTED' | 'UNRESOLVED_FINAL';
  message: string; rung: number; meta: Record<string, unknown>;
}
export interface CreateCaseRequest {
  hotspot_id?: string; lat?: number; lng?: number; asset_type?: AssetType;
  analysis?: HazardAnalysis | null; photo_key?: string; timer_profile: 'demo' | 'real';
}
export interface PresignResponse { upload_url: string; s3_key: string; expires_in: number }
export interface ResolveResponse { road: Road | null; jurisdiction: Jurisdiction; warranty: Warranty }
export interface ClauseResponse extends MockIdentification {
  found: boolean; quote: string; page_hint: string; verified_in_text: boolean | null;
}
export interface Verification extends MockIdentification {
  hazard_still_present?: boolean; same_location_plausible?: boolean | null;
  confidence?: number; explanation?: string;
}
export interface ClaimFixResponse {
  accepted: boolean; reason: string; distance_m: number; verification: Verification | null;
  explanation?: string;
}
export interface CaseDetails { case: Case; events: CaseEvent[]; photo_url?: string | null }
export interface RddResults {
  dataset: string; model_id: string; run_at: string; level: string;
  precision: number; recall: number; f1: number; n_pos: number; n_neg: number;
  tp: number; fp: number; fn: number; tn: number;
}
export interface BacktestEvent {
  event_id?: string; date?: string; description?: string; name?: string; label?: string; held_out?: boolean;
  rain_3h_mm?: number; rain_prev24h_mm?: number; traffic_slowdown?: number;
  precision_at_20?: number; recall?: number | null; random_baseline_precision?: number;
  top_20?: { hotspot_id: string; name: string; probability: number; reported_hit: boolean }[];
  top20_predicted?: string[]; reported_other_count?: number;
}
export interface EvalResultsResponse {
  rdd2022: RddResults | null; backtest: { events?: BacktestEvent[] } | null;
}
