import React, { useState } from 'react';
import { Hotspot, RiskScore, GroundAsset } from '../lib/types';
import { extractTenderClause } from '../lib/api';
import {
  X,
  MapPin,
  TrendingUp,
  AlertTriangle,
  Building,
  UserCheck,
  Briefcase,
  FileCheck2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  ShieldAlert,
  ArrowRight,
  Info,
} from 'lucide-react';

interface RightPanelProps {
  hotspot: Hotspot | null;
  score: RiskScore | null;
  nearbyAssets: GroundAsset[];
  onClose: () => void;
  onOpenCase: (hotspot: Hotspot) => void;
}

export const ProvenanceBadge: React.FC<{ type: string }> = ({ type }) => {
  let bg = 'bg-slate-100 text-slate-700 border-slate-200';
  if (type === 'sourced') {
    bg = 'bg-emerald-50 text-emerald-800 border-emerald-200';
  } else if (type === 'illustrative') {
    bg = 'bg-amber-50 text-amber-800 border-amber-200';
  } else if (type === 'simulated') {
    bg = 'bg-purple-50 text-purple-800 border-purple-200';
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${bg}`}
    >
      {type}
    </span>
  );
};

export const RightPanel: React.FC<RightPanelProps> = ({
  hotspot,
  score,
  nearbyAssets,
  onClose,
  onOpenCase,
}) => {
  const [whyOpen, setWhyOpen] = useState(false);
  const [extractingClause, setExtractingClause] = useState(false);
  const [extractedClause, setExtractedClause] = useState<{
    found: boolean;
    quote: string;
    page_hint: string;
    verified_in_text: boolean | null;
  } | null>(null);

  if (!hotspot) {
    return (
      <aside className="w-[420px] h-full bg-white border-l border-slate-200 flex flex-col text-slate-800 overflow-hidden select-none z-20 shadow-xs p-6 justify-center items-center text-center">
        <div className="w-16 h-16 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center mb-4 border border-sky-100 shadow-2xs">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 mb-2">Corridor Accountability</h3>
        <p className="text-xs text-slate-500 leading-relaxed max-w-xs mb-6">
          Select any critical road or underpass from the map or left panel to inspect real-time flood
          probability, municipal jurisdiction, contractor defect liability, and civic escalation history.
        </p>
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-200">
          <Info className="w-3.5 h-3.5" />
          <span>10 Delhi Arteries Monitored</span>
        </div>
      </aside>
    );
  }

  const probabilityPct = score ? Math.round(score.probability * 100) : 0;
  const huwScore = score?.hazard_under_water?.score ?? 0;
  const huwPct = Math.round(huwScore * 100);

  const road = hotspot.road;
  const jur = hotspot.jurisdiction;
  const war = hotspot.warranty;

  const handleExtractClause = async () => {
    if (!war?.tender_doc_key) return;
    try {
      setExtractingClause(true);
      const res = await extractTenderClause(war.tender_doc_key);
      setExtractedClause(res);
    } catch (err) {
      console.error('Failed to extract clause:', err);
    } finally {
      setExtractingClause(false);
    }
  };

  return (
    <aside className="w-[420px] h-full bg-white border-l border-slate-200 flex flex-col text-slate-800 overflow-hidden select-none z-20 shadow-lg">
      {/* Header */}
      <div className="p-5 border-b border-slate-200 bg-slate-50/50 relative">
        <button
          onClick={onClose}
          type="button"
          aria-label="Close hotspot details panel"
          title="Close details panel"
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-800 p-1.5 rounded-lg hover:bg-slate-200/60 transition"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center space-x-2 mb-1 pr-6">
          <MapPin className="w-5 h-5 text-sky-600 flex-shrink-0" />
          <h2 className="text-lg font-bold text-slate-900 truncate">{hotspot.name}</h2>
        </div>

        <p className="text-xs text-slate-500 mb-2">
          {road?.name || 'Road segment'} &bull; {road?.road_class || 'Arterial'} &bull; {road?.width_ft || 60} ft width
        </p>

        <div className="flex items-center flex-wrap gap-1.5">
          <ProvenanceBadge type={hotspot.provenance} />
          {hotspot.coord_verified ? (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
              Verified Coords
            </span>
          ) : (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
              Location Unverified
            </span>
          )}
          {hotspot.features.underpass && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-800 border border-purple-200">
              Underpass
            </span>
          )}
        </div>

        {/* Large Probability Display Cards */}
        <div className="mt-3.5 grid grid-cols-2 gap-2">
          <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs">
            <div className="text-[11px] text-slate-500 uppercase tracking-wider font-bold">
              Flood Probability
            </div>
            <div className="text-2xl font-black text-sky-700 font-mono mt-0.5">{probabilityPct}%</div>
            <div className="text-[10px] text-slate-400 mt-0.5">Calibrated Logistic Prior</div>
          </div>
          <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs">
            <div className="text-[11px] text-slate-500 uppercase tracking-wider font-bold">
              Submerged Hazard
            </div>
            <div className="text-2xl font-black text-rose-600 font-mono mt-0.5">{huwPct}%</div>
            <div className="text-[10px] text-slate-400 mt-0.5">Hidden Road Traps</div>
          </div>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {/* Section 1: Blame Chain Card (Hero Element) */}
        <div className="space-y-2.5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center space-x-1.5">
            <ShieldAlert className="w-4 h-4 text-sky-600" />
            <span>Civic Ownership &amp; Liability</span>
          </h3>

          <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden divide-y divide-slate-100 shadow-2xs">
            {/* Step 1: Owner Agency */}
            <div className="p-3.5 flex items-start space-x-3">
              <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0 mt-0.5 border border-amber-100">
                <Building className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  Jurisdictional Owner
                </div>
                <div className="flex items-center space-x-2 mt-0.5">
                  <span className="text-sm font-bold text-slate-900">{jur?.owner || 'ORPHAN'}</span>
                  <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                    {Math.round((jur?.confidence || 0) * 100)}% confidence
                  </span>
                </div>

                {/* Collapsible Why */}
                <div className="mt-1">
                  <button
                    onClick={() => setWhyOpen(!whyOpen)}
                    className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center space-x-1"
                  >
                    <span>Attribution logic</span>
                    {whyOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>
                  {whyOpen && jur?.reasons && (
                    <ul className="mt-1.5 pl-3 list-disc text-xs text-slate-600 space-y-1">
                      {jur.reasons.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>

            {/* Step 2: Officer Role */}
            <div className="p-3.5 flex items-start space-x-3">
              <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5 border border-purple-100">
                <UserCheck className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  Accountable Official
                </div>
                <div className="text-sm font-bold text-slate-900 mt-0.5">{jur?.officer_role}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">{jur?.provenance_note}</div>
              </div>
            </div>

            {/* Step 3: Contractor */}
            <div className="p-3.5 flex items-start space-x-3">
              <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0 mt-0.5 border border-indigo-100">
                <Briefcase className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  Maintenance Contractor
                </div>
                <div className="text-sm font-bold text-slate-900 mt-0.5">
                  {war?.contractor_label || 'Unassigned / Not Determined'}
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  Work Type: <span className="text-slate-700 font-medium">{war?.work_type || 'N/A'}</span>
                </div>
              </div>
            </div>

            {/* Step 4: Warranty */}
            <div className="p-3.5 flex items-start space-x-3">
              <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0 mt-0.5 border border-emerald-100">
                <FileCheck2 className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0 space-y-1.5">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  Defect Liability Warranty
                </div>

                {war?.status === 'in_warranty' && (
                  <div className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                    In warranty — {war.days_remaining} days left
                  </div>
                )}
                {war?.status === 'expired' && (
                  <div className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-rose-50 text-rose-800 border border-rose-200">
                    Warranty expired ({Math.abs(war.days_remaining)} days ago)
                  </div>
                )}
                {(!war || war.status === 'unknown') && (
                  <div className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-600 border border-slate-200">
                    Warranty status unknown
                  </div>
                )}

                {war && war.status !== 'unknown' && (
                  <div className="text-xs text-slate-500">
                    Completed: <span className="font-medium text-slate-700">{war.completion_date}</span> &bull; End:{' '}
                    <span className="font-medium text-slate-700">{war.end_date}</span>
                  </div>
                )}

                {/* Tender clause quote */}
                {war?.clause_text && (
                  <div className="mt-2 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700">
                    <p className="italic font-serif leading-relaxed text-slate-800">&ldquo;{war.clause_text}&rdquo;</p>
                    <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-400">
                      <span>Quoted from Public Tender</span>
                      <ProvenanceBadge type={war.provenance || 'illustrative'} />
                    </div>
                  </div>
                )}

                {war?.tender_doc_key && (
                  <div className="mt-2 space-y-2">
                    <button
                      onClick={handleExtractClause}
                      disabled={extractingClause}
                      className="w-full py-2 px-3 rounded-xl text-xs font-semibold bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-200 flex items-center justify-center space-x-1.5 transition"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-sky-600" />
                      <span>{extractingClause ? 'Extracting with Nova Lite...' : 'Verify Clause with Amazon Nova'}</span>
                    </button>

                    {extractedClause && (
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-semibold text-slate-700">{extractedClause.page_hint}</span>
                          {extractedClause.verified_in_text ? (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                              verified in PDF
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                              not found verbatim
                            </span>
                          )}
                        </div>
                        <p className="italic text-slate-700">&ldquo;{extractedClause.quote}&rdquo;</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Hidden Hazards Nearby */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center space-x-1.5">
              <AlertTriangle className="w-4 h-4 text-rose-500" />
              <span>Ground Hazards Nearby (&lt; 50m)</span>
            </h3>
            <span className="text-xs font-mono font-bold text-rose-700">
              Weight: {((score?.hazard_under_water?.weight ?? 0) * 100).toFixed(0)}%
            </span>
          </div>

          {nearbyAssets.length > 0 ? (
            <div className="space-y-1.5">
              {nearbyAssets.map((asset) => (
                <div
                  key={asset.asset_id}
                  className="p-3 rounded-xl bg-white border border-slate-200 flex items-center justify-between text-xs shadow-2xs"
                >
                  <div className="space-y-0.5">
                    <div className="font-bold text-slate-800 capitalize">
                      {asset.type.replace(/_/g, ' ')}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Severity: <span className="font-mono font-bold text-amber-600">{asset.severity}/5</span>
                    </div>
                  </div>
                  <ProvenanceBadge type={asset.provenance} />
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-xs text-slate-500 text-center">
              No known ground hazards mapped within 50 meters.
            </div>
          )}
        </div>

        {/* Section 3: Risk Drivers */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center space-x-1.5">
              <TrendingUp className="w-4 h-4 text-sky-600" />
              <span>Hydrological Drivers</span>
            </h3>
            <span className="text-[11px] text-slate-400">Logit contribution</span>
          </div>

          <div className="space-y-2 p-3 rounded-xl bg-white border border-slate-200 shadow-2xs">
            {score?.drivers && score.drivers.length > 0 ? (
              score.drivers.map((driver) => {
                const isPositive = driver.contribution >= 0;
                const absVal = Math.min(Math.abs(driver.contribution), 3.0);
                const barWidth = Math.round((absVal / 3.0) * 100);

                return (
                  <div key={driver.name} className="space-y-0.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-700 capitalize flex items-center space-x-1">
                        <span>{driver.name.replace(/_/g, ' ')}</span>
                        {driver.missing && (
                          <span className="px-1 py-0.2 rounded text-[9px] bg-slate-100 text-slate-400">
                            missing
                          </span>
                        )}
                      </span>
                      <span className="font-mono text-xs text-slate-600">
                        {driver.contribution > 0 ? '+' : ''}
                        {driver.contribution.toFixed(2)}
                      </span>
                    </div>

                    <div className="h-1.5 bg-slate-100 rounded-full flex overflow-hidden">
                      <div className="w-1/2 flex justify-end">
                        {!isPositive && (
                          <div
                            className="h-full bg-slate-400 rounded-l-full"
                            style={{ width: `${barWidth}%` }}
                          />
                        )}
                      </div>
                      <div className="w-1/2 flex justify-start">
                        {isPositive && (
                          <div
                            className="h-full bg-sky-600 rounded-r-full"
                            style={{ width: `${barWidth}%` }}
                          />
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-xs text-slate-400 italic">No drivers recorded.</p>
            )}
          </div>
        </div>
      </div>

      {/* Footer Action */}
      <div className="p-4 border-t border-slate-200 bg-slate-50/70">
        <button
          onClick={() => onOpenCase(hotspot)}
          className="w-full py-3 px-4 rounded-xl text-sm font-bold bg-[#0c192c] hover:bg-[#162740] text-white transition flex items-center justify-center space-x-2 shadow-xs active:scale-98"
        >
          <span>Initiate Civic Escalation Notice</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
};
