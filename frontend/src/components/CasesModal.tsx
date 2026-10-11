import React, { useState, useEffect } from 'react';
import { Case, CaseEvent } from '../lib/types';
import { fetchCases, fetchCaseDetails, claimFix, presignUpload, uploadPhoto } from '../lib/api';
import {
  X,
  FileText,
  ShieldCheck,
  CheckCircle,
  Clock,
  Mail,
  ChevronDown,
  ChevronUp,
  Award,
  MapPin,
} from 'lucide-react';

interface CasesModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeCaseId: string | null;
  onSelectCase: (caseId: string) => void;
}

export const CasesModal: React.FC<CasesModalProps> = ({
  isOpen,
  onClose,
  activeCaseId,
  onSelectCase,
}) => {
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [caseEvents, setCaseEvents] = useState<CaseEvent[]>([]);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);

  // Expanded event meta toggles
  const [expandedEventSeqs, setExpandedEventSeqs] = useState<Set<string>>(new Set());
  const [emailDrawerOpen, setEmailDrawerOpen] = useState(false);

  // Claim fix state
  const [claimFile, setClaimFile] = useState<File | null>(null);
  const [claimLat, setClaimLat] = useState<number>(0);
  const [claimLng, setClaimLng] = useState<number>(0);
  const [isClaiming, setIsClaiming] = useState(false);
  const [claimResult, setClaimResult] = useState<{
    accepted: boolean;
    reason: string;
    distance_m?: number;
    explanation?: string;
    unavailable?: boolean;
  } | null>(null);

  // Countdown timer state
  const [countdownSeconds, setCountdownSeconds] = useState<number | null>(null);

  // Poll cases list every 5s
  useEffect(() => {
    if (!isOpen) return;

    let active = true;
    const loadCases = async () => {
      try {
        const res = await fetchCases();
        if (active) {
          setCases(res.cases);
          if (!activeCaseId && res.cases.length > 0) {
            onSelectCase(res.cases[0].case_id);
          }
        }
      } catch (err) {
        console.error('Failed to load cases:', err);
      }
    };

    loadCases();
    const interval = setInterval(loadCases, 5000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [isOpen, activeCaseId]);

  // Poll case details every 2s
  useEffect(() => {
    if (!isOpen || !activeCaseId) return;

    let active = true;
    const loadDetails = async () => {
      try {
        const res = await fetchCaseDetails(activeCaseId);
        if (active) {
          setSelectedCase(res.case);
          setCaseEvents(res.events || []);
          if (res.photo_url) setPhotoUrl(res.photo_url);

          // Calculate countdown
          const timerDuration = res.case.timer_profile === 'demo' ? 20 : 259200;
          const lastEvent = (res.events && res.events.length > 0) ? res.events[res.events.length - 1] : null;
          if (lastEvent) {
            const eventTimeStr = lastEvent.ts_seq.split('#')[0];
            const eventTime = new Date(eventTimeStr).getTime();
            const elapsed = Math.floor((Date.now() - eventTime) / 1000);
            const remaining = Math.max(0, timerDuration - elapsed);
            setCountdownSeconds(remaining);
          }
        }
      } catch (err) {
        console.error('Failed to load case details:', err);
      }
    };

    loadDetails();
    const interval = setInterval(loadDetails, 2000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [isOpen, activeCaseId]);

  if (!isOpen) return null;

  const toggleEventExpand = (tsSeq: string) => {
    setExpandedEventSeqs((prev) => {
      const next = new Set(prev);
      if (next.has(tsSeq)) next.delete(tsSeq);
      else next.add(tsSeq);
      return next;
    });
  };

  const handleUseLocation = () => {
    if (selectedCase) {
      setClaimLat(selectedCase.lat);
      setClaimLng(selectedCase.lng);
    }
  };

  const handleSubmitClaim = async () => {
    if (!selectedCase) return;
    setIsClaiming(true);
    setClaimResult(null);

    try {
      let repairPhotoKey: string | undefined = undefined;
      if (!selectedCase.photo_key) {
        throw Object.assign(new Error('The original report photo is missing; both before and after photos are required to verify a repair.'), { code: 'MISSING_BEFORE_PHOTO' });
      }
      if (!claimFile) {
        throw Object.assign(new Error('Add an after-repair photo before submitting a claim.'), { code: 'MISSING_AFTER_PHOTO' });
      }
      if (claimFile) {
        if (!['image/jpeg', 'image/png'].includes(claimFile.type)) {
          throw new Error('Repair photos must be JPEG or PNG');
        }
        const contentType = claimFile.type as 'image/jpeg' | 'image/png';
        const presign = await presignUpload('fix', contentType);
        await uploadPhoto(presign.upload_url, claimFile, contentType);
        repairPhotoKey = presign.s3_key;
      }

      const res = await claimFix(
        selectedCase.case_id,
        repairPhotoKey || '',
        claimLat || selectedCase.lat,
        claimLng || selectedCase.lng
      );

      setClaimResult({
        accepted: res.accepted,
        reason: res.reason,
        distance_m: res.distance_m,
        explanation: res.explanation,
      });

      // Reload details immediately
      const refreshed = await fetchCaseDetails(selectedCase.case_id);
      setSelectedCase(refreshed.case);
      setCaseEvents(refreshed.events || []);
    } catch (err: any) {
      console.error('Claim fix error:', err);
      setClaimResult({
        accepted: false,
        reason: err.message || 'Error processing repair verification claim',
        // A transport or dependency error is not a verified rejection.
        unavailable: true,
      });
    } finally {
      setIsClaiming(false);
    }
  };

  const rungs = [
    { rung: 1, label: 'Executive Engineer', agency: selectedCase?.owner || 'PWD', role: 'Local Division Nodal' },
    { rung: 2, label: 'Flood Control Officer', agency: 'Delhi Flood Control', role: 'Designated Nodal Officer' },
    { rung: 3, label: 'Superintending Engineer', agency: selectedCase?.owner || 'PWD', role: 'Senior Agency Oversight' },
    { rung: 4, label: 'District Magistrate', agency: 'Revenue Dept / DM Taskforce', role: 'Inter-Agency Convening' },
  ];

  const currentRung = selectedCase?.rung || 1;
  const isClosed = selectedCase?.status === 'CLOSED_VERIFIED';
  const isFinalUnresolved = selectedCase?.status === 'UNRESOLVED_FINAL';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm select-none">
      <div className="relative w-full max-w-6xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-100 shadow-2xs">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Escalation &amp; Case Workflow</h2>
              <p className="text-xs text-slate-500">Step Functions 4-Rung Autonomous Civic Engine</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-800 p-1.5 rounded-lg hover:bg-slate-200/60 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body: Split 2-Column Layout */}
        <div className="flex-1 flex flex-col md:flex-row min-h-0 overflow-y-auto md:overflow-hidden bg-slate-50/40">
          {/* Left Column: Cases List */}
          <div className="w-full md:w-80 shrink-0 max-h-48 md:max-h-none border-b md:border-b-0 md:border-r border-slate-200 flex flex-col bg-white">
            <div className="p-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-600">Active Cases</span>
              <span className="text-xs font-mono font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                {cases.length} cases
              </span>
            </div>

            <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
              {cases.map((c) => {
                const isSelected = c.case_id === activeCaseId;
                return (
                  <button
                    key={c.case_id}
                    onClick={() => onSelectCase(c.case_id)}
                    className={`w-full text-left p-3.5 transition flex flex-col space-y-1.5 ${
                      isSelected
                        ? 'bg-sky-50/70 border-l-4 border-sky-600'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-sky-900">{c.case_id}</span>
                      <div className="flex items-center space-x-1.5">
                        {c.seeded && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                            SEEDED
                          </span>
                        )}
                        <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                          {c.status}
                        </span>
                      </div>
                    </div>

                    <div className="text-xs font-semibold text-slate-800 truncate">
                      {c.hotspot_id ? c.hotspot_id.replace(/_/g, ' ') : `Coord: ${c.lat.toFixed(3)}, ${c.lng.toFixed(3)}`}
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>Agency: {c.owner}</span>
                      <span className="font-medium text-slate-700">Rung {c.rung}/4</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Column: Case Details & Timeline */}
          {selectedCase ? (
            <div className="flex-1 shrink-0 md:shrink overflow-visible md:overflow-y-auto p-6 space-y-6 bg-white text-slate-800">
              {/* Top Case Summary Card */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-between shadow-2xs">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-lg font-bold text-slate-900">{selectedCase.case_id}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-amber-100 text-amber-800 border border-amber-200">
                      {selectedCase.status}
                    </span>
                    {selectedCase.timer_profile && (
                      <span className="text-[10px] font-mono uppercase bg-slate-200/80 px-2 py-0.5 rounded text-slate-600 font-bold">
                        {selectedCase.timer_profile} timers
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-500 mt-1 flex items-center space-x-2">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    <span>
                      {selectedCase.lat.toFixed(4)}, {selectedCase.lng.toFixed(4)} &bull; Owner Agency:{' '}
                      <strong className="text-slate-700">{selectedCase.owner}</strong>
                    </span>
                  </div>
                </div>

                {/* Countdown Timer Badge */}
                {!isClosed && !isFinalUnresolved && countdownSeconds !== null && (
                  <div className="flex items-center space-x-2 bg-white px-3.5 py-2 rounded-xl border border-slate-200 shadow-2xs">
                    <Clock className="w-4 h-4 text-sky-600 animate-spin" />
                    <div className="text-right">
                      <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Next Escalation</div>
                      <div className="font-mono text-sm font-bold text-sky-800">{countdownSeconds}s remaining</div>
                    </div>
                  </div>
                )}
              </div>

              {/* 4-Rung Escalation Ladder */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center space-x-1.5">
                    <Award className="w-4 h-4 text-sky-600" />
                    <span>4-Rung Escalation Ladder</span>
                  </h3>
                  <span className="text-xs text-slate-500">Autonomous progression across bureaucratic levels</span>
                </div>

                <details className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700">
                  <summary className="cursor-pointer font-semibold text-slate-800">How the four rungs work</summary>
                  <div className="mt-2 space-y-1.5 leading-relaxed">
                    <p>A rung is the current escalation level for an unresolved case. Rung 1 notifies the assigned agency officer, rung 2 the Flood Control Order nodal officer, rung 3 the owning agency's Superintending/Chief Engineer, and rung 4 the District Magistrate.</p>
                    <p>The workflow advances when its timer expires or a repair claim is actually rejected after verification. Demo timers are 20 seconds per rung. Real timers are 3 days, 2 days, 2 days, then 3 days.</p>
                    <p>A verified repair closes the case. If the final rung times out or a verified claim is rejected there, the case is marked unresolved after all four levels.</p>
                  </div>
                </details>

                <div className="grid grid-cols-4 gap-3">
                  {rungs.map((r) => {
                    const isPassed = currentRung > r.rung;
                    const isCurrent = currentRung === r.rung;

                    let borderClass = 'border-slate-200 bg-slate-50/50';
                    let textClass = 'text-slate-400';
                    let badgeClass = 'bg-slate-200 text-slate-600';

                    if (isCurrent && !isClosed) {
                      borderClass = 'border-sky-400 bg-sky-50/60 ring-2 ring-sky-200 shadow-xs';
                      textClass = 'text-sky-950 font-bold';
                      badgeClass = 'bg-[#0c192c] text-white';
                    } else if (isPassed || isClosed) {
                      borderClass = 'border-emerald-200 bg-emerald-50/40';
                      textClass = 'text-emerald-900 font-bold';
                      badgeClass = 'bg-emerald-600 text-white';
                    }

                    return (
                      <div
                        key={r.rung}
                        className={`p-3.5 rounded-2xl border transition relative flex flex-col justify-between ${borderClass}`}
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${badgeClass}`}>
                              RUNG {r.rung}
                            </span>
                            {isPassed && <CheckCircle className="w-4 h-4 text-emerald-600" />}
                            {isCurrent && !isClosed && (
                              <span className="w-2.5 h-2.5 rounded-full bg-sky-600 animate-ping" />
                            )}
                          </div>
                          <div className={`text-xs ${textClass}`}>{r.label}</div>
                          <div className="text-[11px] text-slate-500 mt-0.5">{r.agency}</div>
                        </div>
                        <div className="text-[10px] text-slate-400 mt-2 italic">{r.role}</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Photo Evidence & Details */}
              {photoUrl && (
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 flex items-center space-x-4 shadow-2xs">
                  <img
                    src={photoUrl}
                    alt="Citizen Report"
                    className="w-16 h-16 rounded-xl object-cover border border-slate-200 shadow-2xs"
                  />
                  <div>
                    <div className="text-xs font-bold text-slate-800">Original Citizen Photo Evidence</div>
                    <div className="text-xs text-slate-500">
                      {selectedCase.analysis && (
                        selectedCase.analysis.description === 'Citizen reported hazard (photo omitted or manual override)'
                        || selectedCase.analysis.visible_evidence === 'Manual citizen report'
                      )
                        ? 'AI analysis unavailable; the saved value is a legacy manual fallback, not a model result. No severity assessment is recorded.'
                        : selectedCase.analysis
                        ? `${selectedCase.analysis.source === 'bedrock' ? 'AI estimate' : selectedCase.analysis.source === 'local_mock' ? 'Local mock (not AI)' : 'Assessment source not recorded'}: ${selectedCase.analysis.hazard_type.replace(/_/g, ' ')} (recorded severity: ${selectedCase.analysis.severity}/5)`
                        : selectedCase.photo_key
                          ? 'AI analysis unavailable; severity was not assessed. Original photo is retained as evidence.'
                          : 'No photo assessment was submitted; severity was not assessed.'}
                    </div>
                  </div>
                </div>
              )}

              {/* Claim Fix Verification Section */}
              {!isClosed && (
                <div className="p-4 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-2xs">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      <span>Submit Verified Repair Claim</span>
                    </h3>
                    <span className="text-[11px] text-slate-400">Must be within 25m of hazard</span>
                  </div>
                  {(!selectedCase.photo_key || !claimFile) && (
                    <p className="text-[11px] text-slate-500">Repair verification requires the original report photo and a new after-repair photo.</p>
                  )}

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <label className="text-[11px] font-semibold text-slate-500 block mb-1">
                        Repair Geo-Coordinates:
                      </label>
                      <div className="flex space-x-2">
                        <input
                          type="number"
                          step="0.0001"
                          placeholder="Lat"
                          value={claimLat || ''}
                          onChange={(e) => setClaimLat(Number(e.target.value))}
                          className="w-1/2 p-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 focus:outline-none focus:border-sky-500"
                        />
                        <input
                          type="number"
                          step="0.0001"
                          placeholder="Lng"
                          value={claimLng || ''}
                          onChange={(e) => setClaimLng(Number(e.target.value))}
                          className="w-1/2 p-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 focus:outline-none focus:border-sky-500"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={handleUseLocation}
                        className="text-[11px] font-semibold text-sky-600 hover:text-sky-700 mt-1"
                      >
                        Use case coordinates
                      </button>
                    </div>

                    <div>
                      <label className="text-[11px] font-semibold text-slate-500 block mb-1">
                        Fixed Spot Photo:
                      </label>
                      <input
                        type="file"
                        accept="image/jpeg,image/png"
                        onChange={(e) => setClaimFile(e.target.files?.[0] || null)}
                        className="w-full text-xs text-slate-500 file:mr-2 file:py-1.5 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
                      />
                    </div>
                  </div>

                  <button
                    onClick={handleSubmitClaim}
                    disabled={isClaiming || !claimFile || !selectedCase.photo_key}
                    className="w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-[#0c192c] hover:bg-[#162740] text-white transition flex items-center justify-center space-x-2 shadow-xs"
                  >
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    <span>{isClaiming ? 'Verifying with Nova Lite...' : 'Verify Repair & Close Case'}</span>
                  </button>

                  {claimResult && (
                    <div
                      className={`p-3 rounded-xl border text-xs ${
                        claimResult.unavailable ? 'bg-amber-50 border-amber-200 text-amber-900' : claimResult.accepted
                          ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                          : 'bg-rose-50 border-rose-200 text-rose-800'
                      }`}
                    >
                      <div className="font-bold">
                        {claimResult.unavailable ? 'Verification unavailable — claim remains pending' : claimResult.accepted ? 'Fix Verified & Case Resolved!' : 'Claim Verification Rejected'}
                      </div>
                      <div className="mt-0.5">{claimResult.reason}</div>
                      {claimResult.distance_m !== undefined && (
                        <div className="text-[11px] mt-0.5">
                          Distance from recorded hazard: <strong>{claimResult.distance_m.toFixed(1)}m</strong> (Limit: 25m)
                        </div>
                      )}
                      {claimResult.explanation && <div className="mt-1">{claimResult.explanation}</div>}
                    </div>
                  )}
                </div>
              )}

              {/* Event History / Audit Timeline */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center space-x-1.5">
                    <Clock className="w-4 h-4 text-sky-600" />
                    <span>Audit Trail Timeline</span>
                  </h3>
                  <button
                    onClick={() => setEmailDrawerOpen(!emailDrawerOpen)}
                    className="text-xs font-bold text-sky-600 hover:text-sky-700 flex items-center space-x-1"
                  >
                    <Mail className="w-3.5 h-3.5" />
                    <span>{emailDrawerOpen ? 'Hide Notice Preview' : 'Preview Sent Notice'}</span>
                  </button>
                </div>

                {/* Email Drawer Preview */}
                {emailDrawerOpen && (
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-2 shadow-2xs font-mono">
                    <div className="text-[11px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 inline-block font-sans">
                      [DRY-RUN] Routed to Sandbox Inbox
                    </div>
                    <div className="text-slate-800">
                      <strong>Subject:</strong> [DRY-RUN] Notice to {selectedCase.owner}: Waterlogging hazard at {selectedCase.hotspot_id || 'Corridor'}
                    </div>
                    <div className="p-3 bg-white rounded-xl border border-slate-200 text-[11px] text-slate-700 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                      {`DRY-RUN: this notice was NOT sent to any official.\n\nCase ID: ${selectedCase.case_id}\n\nLocation: https://www.openstreetmap.org/?mlat=${selectedCase.lat}&mlon=${selectedCase.lng}#map=18/${selectedCase.lat}/${selectedCase.lng}\n\n${selectedCase.analysis ? `Recorded assessment: ${selectedCase.analysis.hazard_type} (AI-estimated severity: ${selectedCase.analysis.severity}/5)` : 'AI analysis unavailable; no severity assessment is recorded.'}\n\nDemand: Please inspect and repair, and reply with a geo-tagged photo of the repaired spot.\n\nGenerated by Argus (hackathon prototype)`}
                    </div>
                  </div>
                )}

                {/* Event Items */}
                <div className="space-y-2">
                  {caseEvents.map((ev) => {
                    const isExpanded = expandedEventSeqs.has(ev.ts_seq);
                    return (
                      <div
                        key={ev.ts_seq}
                        className="p-3.5 rounded-xl bg-white border border-slate-200 text-xs space-y-1 shadow-2xs"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-slate-900">{ev.type}</span>
                            <span className="text-[11px] text-slate-400 font-mono">
                              {new Date(ev.ts_seq.split('#')[0]).toLocaleTimeString()}
                            </span>
                          </div>
                          <button
                            onClick={() => toggleEventExpand(ev.ts_seq)}
                            className="text-slate-400 hover:text-slate-700 p-0.5"
                          >
                            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>
                        </div>

                        {ev.message && (
                          <div className="text-[11px] text-slate-600">
                            {ev.message}
                          </div>
                        )}

                        {isExpanded && ev.meta && (
                          <pre className="mt-2 p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-[10px] text-slate-600 font-mono overflow-x-auto">
                            {JSON.stringify(ev.meta, null, 2)}
                          </pre>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 p-8 flex items-center justify-center text-slate-400 text-xs">
              Select a case from the left list to view escalation ladder details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
