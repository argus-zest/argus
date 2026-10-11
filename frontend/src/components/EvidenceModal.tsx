import React, { useState, useEffect } from 'react';
import { EvalResultsResponse } from '../lib/types';
import { fetchEvalResults } from '../lib/api';
import { X, Activity, CheckCircle2, AlertCircle } from 'lucide-react';

interface EvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  modelVersion?: string;
  modelFitted?: boolean;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({
  isOpen,
  onClose,
  modelVersion = '1.0.0',
  modelFitted = false,
}) => {
  const [activeTab, setActiveTab] = useState<'model' | 'rdd2022' | 'backtest'>('model');
  const [evalData, setEvalData] = useState<EvalResultsResponse>({ rdd2022: null, backtest: null });
  const [selectedEventIndex, setSelectedEventIndex] = useState<number>(0);

  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    fetchEvalResults()
      .then((data) => {
        if (active) setEvalData(data);
      })
      .catch((err) => console.error('Failed to load eval results:', err));

    return () => {
      active = false;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const rdd = evalData.rdd2022;
  const backtest = evalData.backtest;
  const events = backtest?.events || [];
  const currentEvent = events[selectedEventIndex] || null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm select-none">
      <div className="relative w-full max-w-4xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[85vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-100 shadow-2xs">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Model Specification &amp; Evidence</h2>
              <p className="text-xs text-slate-500">
                Honest empirical metrics &bull; Mathematical formulation &bull; Backtest replay benchmarks
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-800 p-1.5 rounded-lg hover:bg-slate-200/60 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 border-b border-slate-200 bg-slate-50/40 flex space-x-6">
          <button
            onClick={() => setActiveTab('model')}
            className={`py-3.5 text-xs font-bold uppercase tracking-wider border-b-2 transition ${
              activeTab === 'model'
                ? 'border-sky-600 text-sky-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            1. Susceptibility Model
          </button>
          <button
            onClick={() => setActiveTab('rdd2022')}
            className={`py-3.5 text-xs font-bold uppercase tracking-wider border-b-2 transition ${
              activeTab === 'rdd2022'
                ? 'border-sky-600 text-sky-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            2. Hazard Vision Accuracy (RDD2022)
          </button>
          <button
            onClick={() => setActiveTab('backtest')}
            className={`py-3.5 text-xs font-bold uppercase tracking-wider border-b-2 transition ${
              activeTab === 'backtest'
                ? 'border-sky-600 text-sky-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            3. Backtest Replay
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6 overflow-y-auto flex-1 bg-white text-slate-800 text-xs leading-relaxed space-y-6">
          {activeTab === 'model' && (
            <div className="space-y-6">
              {/* Version & Fitting Status */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                <div>
                  <span className="text-slate-500 text-xs">Model Version:</span>
                  <span className="ml-2 font-mono font-bold text-slate-900">{modelVersion}</span>
                </div>
                <div>
                  <span className="text-slate-500 text-xs">Fitted State:</span>
                  <span
                    className={`ml-2 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                      modelFitted
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                        : 'bg-amber-50 text-amber-800 border border-amber-200'
                    }`}
                  >
                    {modelFitted ? 'EMPIRICALLY FITTED' : 'EXPERT PRIORS'}
                  </span>
                </div>
              </div>

              {!modelFitted && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800">
                  Coefficients are expert priors and have not been fitted.
                </div>
              )}

              {/* Exact Formulas */}
              <div className="space-y-2.5">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                  Mathematical Formulation
                </h3>

                <pre className="p-4 rounded-2xl bg-slate-900 text-slate-200 font-mono text-xs overflow-x-auto leading-relaxed border border-slate-800">
{`z_dep  = clip((depression_m - mean_dep) / std_dep, -3, 3)         # null -> 0
z_low  = clip(-(rel_elev_m - mean_rel) / std_rel, -3, 3)           # null -> 0 ; lower ground => higher
S      = σ(bias + w_depression*z_dep + w_low_rel_elev*z_low + w_underpass*(1 if underpass else 0) + w_news*ln(1+news_events_count_or_0))

logit  = event.bias + a*S + b*ln(1+rain_3h_mm) + c*ln(1+rain_prev24h_mm) + d*traffic_slowdown
P      = σ(logit)

where σ(x) = 1 / (1 + e^-x)`}
                </pre>
              </div>

              <div className="space-y-2 text-slate-600 text-xs">
                <p>
                  <strong className="text-slate-800">Depression calculation:</strong> Uses elevation ring averages at 200m from Open-Meteo elevation contour API.
                </p>
                <p>
                  <strong className="text-slate-800">Relative elevation:</strong> Compares point elevation to average elevation across a 1500m regional radius.
                </p>
                <p>
                  <strong className="text-slate-800">Hazard under water interaction:</strong> Multiplies waterlogging probability by localized open manhole, missing drain cover, and pothole presence within 50m.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'rdd2022' && (
            <div className="space-y-6">
              {rdd ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-slate-500">Dataset:</span>
                      <span className="ml-2 font-bold text-slate-900">{rdd.dataset}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Model Evaluated:</span>
                      <span className="ml-2 font-mono text-sky-700 font-bold">{rdd.model_id}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Run Timestamp:</span>
                      <span className="ml-2 font-mono text-slate-700">{rdd.run_at}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Evaluation Scope:</span>
                      <span className="ml-2 font-bold text-slate-700">{rdd.level}-level</span>
                    </div>
                  </div>

                  {/* Confusion Matrix & Metrics */}
                  <div className="grid grid-cols-4 gap-3">
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-center shadow-2xs">
                      <div className="text-slate-500 text-[11px] uppercase font-bold">Precision</div>
                      <div className="text-xl font-bold font-mono text-sky-700 mt-0.5">
                        {(rdd.precision * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-center shadow-2xs">
                      <div className="text-slate-500 text-[11px] uppercase font-bold">Recall</div>
                      <div className="text-xl font-bold font-mono text-emerald-700 mt-0.5">
                        {(rdd.recall * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-center shadow-2xs">
                      <div className="text-slate-500 text-[11px] uppercase font-bold">F1 Score</div>
                      <div className="text-xl font-bold font-mono text-purple-700 mt-0.5">
                        {rdd.f1.toFixed(3)}
                      </div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-center shadow-2xs">
                      <div className="text-slate-500 text-[11px] uppercase font-bold">Sample Size</div>
                      <div className="text-xl font-bold font-mono text-amber-700 mt-0.5">
                        {rdd.n_pos + rdd.n_neg}
                      </div>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                    <div className="text-xs font-bold text-slate-600 mb-2 uppercase tracking-wide">
                      Confusion Matrix (Image-Level)
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono">
                      <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 font-bold">
                        TP: {rdd.tp}
                      </div>
                      <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 font-bold">
                        FP: {rdd.fp}
                      </div>
                      <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 font-bold">
                        FN: {rdd.fn}
                      </div>
                      <div className="p-2.5 bg-slate-100 rounded-xl text-slate-700 font-bold">
                        TN: {rdd.tn}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-10 rounded-2xl bg-slate-50 border border-dashed border-slate-300 text-center space-y-2">
                  <AlertCircle className="w-8 h-8 text-amber-500 mx-auto" />
                  <p className="text-base font-bold text-slate-900">Not yet measured.</p>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    Place ~50 RDD2022 India images + VOC XML in <code>eval/data/rdd2022_india/</code> and run{' '}
                    <code>python eval/rdd2022_eval.py</code> to generate empirical evaluation metrics.
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'backtest' && (
            <div className="space-y-6">
              {events.length > 0 ? (
                <div className="space-y-4">
                  {/* Event Selector Dropdown */}
                  <div className="space-y-1">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                      Select Historical News Event
                    </label>
                    <select
                      value={selectedEventIndex}
                      onChange={(e) => setSelectedEventIndex(Number(e.target.value))}
                      className="w-full py-2.5 px-3.5 rounded-xl bg-white border border-slate-300 text-xs text-slate-800 focus:outline-none focus:border-sky-500 shadow-2xs"
                    >
                      {events.map((ev, idx) => (
                        <option key={ev.event_id || idx} value={idx}>
                          {ev.date} &mdash; {ev.description || ev.event_id}
                        </option>
                      ))}
                    </select>
                  </div>

                  {currentEvent && (
                    <div className="space-y-4">
                      {/* Metric summary */}
                      <div className="grid grid-cols-3 gap-3">
                        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-center shadow-2xs">
                          <div className="text-slate-500 text-[11px] uppercase font-bold">Precision @ 20</div>
                          <div className="text-xl font-bold font-mono text-sky-700 mt-0.5">
                            {currentEvent.precision_at_20 !== undefined
                              ? `${(currentEvent.precision_at_20 * 100).toFixed(1)}%`
                              : 'N/A'}
                          </div>
                        </div>

                        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-center shadow-2xs">
                          <div className="text-slate-500 text-[11px] uppercase font-bold">Recall</div>
                          <div className="text-xl font-bold font-mono text-emerald-700 mt-0.5">
                            {currentEvent.recall != null
                              ? `${(currentEvent.recall * 100).toFixed(1)}%`
                              : 'N/A'}
                          </div>
                        </div>

                        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-center shadow-2xs">
                          <div className="text-slate-500 text-[11px] uppercase font-bold">Baseline Random</div>
                          <div className="text-xl font-bold font-mono text-slate-600 mt-0.5">
                            {currentEvent.random_baseline_precision !== undefined
                              ? `${(currentEvent.random_baseline_precision * 100).toFixed(1)}%`
                              : 'N/A'}
                          </div>
                        </div>
                      </div>

                      {/* Top 20 Hotspots Table */}
                      <div className="space-y-2">
                        <div className="text-xs font-bold uppercase tracking-wider text-slate-600">
                          Top 20 Predicted Hotspots
                        </div>
                        <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden max-h-60 overflow-y-auto divide-y divide-slate-100 shadow-2xs">
                          {currentEvent.top_20 && currentEvent.top_20.length > 0 ? (
                            currentEvent.top_20.map(
                              (
                                row: { hotspot_id: string; name: string; probability: number; reported_hit: boolean },
                                idx: number
                              ) => (
                                <div key={row.hotspot_id} className="px-3.5 py-2.5 flex items-center justify-between text-xs">
                                  <div className="flex items-center space-x-2">
                                    <span className="font-mono text-slate-400 w-4">{idx + 1}</span>
                                    <span className="text-slate-900 font-semibold">{row.name}</span>
                                  </div>
                                  <div className="flex items-center space-x-3">
                                    <span className="font-mono font-bold text-sky-700">
                                      {(row.probability * 100).toFixed(1)}%
                                    </span>
                                    {row.reported_hit && (
                                      <span className="flex items-center space-x-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 font-bold text-[11px]">
                                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                        <span>Verified Hit</span>
                                      </span>
                                    )}
                                  </div>
                                </div>
                              )
                            )
                          ) : (
                            <div className="p-3 text-slate-400 text-center italic text-xs">
                              {currentEvent.top20_predicted?.join(', ') || 'No predicted list recorded'}
                            </div>
                          )}
                        </div>
                      </div>

                      {currentEvent.reported_other_count !== undefined && (
                        <div className="text-xs text-slate-500">
                          Reported waterlogging incidents outside known hotspot set: {currentEvent.reported_other_count}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-10 rounded-2xl bg-slate-50 border border-dashed border-slate-300 text-center space-y-2">
                  <AlertCircle className="w-8 h-8 text-amber-500 mx-auto" />
                  <p className="text-base font-bold text-slate-900">No backtest events loaded.</p>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    Replace placeholders in <code>backtest/events.json</code> with real news events and run{' '}
                    <code>python backtest/run_backtest.py</code> to execute the historical backtest replay.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
