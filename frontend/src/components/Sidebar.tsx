import React, { useState } from 'react';
import { Hotspot, RiskScore, RiskBand } from '../lib/types';
import { getBandColor } from '../lib/api';
import {
  CloudRain,
  Activity,
  Layers,
  AlertCircle,
  RefreshCw,
  Sun,
  CloudDrizzle,
  CloudLightning,
  ChevronDown,
  ChevronUp,
  Sliders,
  AlertTriangle,
} from 'lucide-react';

interface SidebarProps {
  mode: 'whatif' | 'live';
  onModeChange: (m: 'whatif' | 'live') => void;
  rain3h: number;
  rain24h: number;
  traffic: number;
  onRain3hChange: (v: number) => void;
  onRain24hChange: (v: number) => void;
  onTrafficChange: (v: number) => void;
  onPreset: (r3: number, r24: number, tr: number) => void;
  hazardUnderWaterMode: boolean;
  onToggleHazardUnderWater: () => void;
  hotspots: Hotspot[];
  riskScores: RiskScore[];
  selectedHotspotId: string | null;
  onSelectHotspot: (id: string) => void;
  isLoadingRisk: boolean;
  liveError: string | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  mode,
  onModeChange,
  rain3h,
  rain24h,
  traffic,
  onRain3hChange,
  onRain24hChange,
  onTrafficChange,
  onPreset,
  hazardUnderWaterMode,
  onToggleHazardUnderWater,
  hotspots,
  riskScores,
  selectedHotspotId,
  onSelectHotspot,
  isLoadingRisk,
  liveError,
}) => {
  const [showAdvancedSliders, setShowAdvancedSliders] = useState(false);

  // Map risk score by hotspot id
  const scoreMap = new Map<string, RiskScore>();
  riskScores.forEach((s) => scoreMap.set(s.hotspot_id, s));

  // Count points > 50%
  const above50Count = riskScores.filter((s) => {
    const val = hazardUnderWaterMode ? (s.hazard_under_water?.score ?? s.probability) : s.probability;
    return val > 0.5;
  }).length;
  const totalCount = hotspots.length;

  // Sorted rankings list (top 10)
  const rankedHotspots = [...hotspots]
    .map((hs) => {
      const score = scoreMap.get(hs.hotspot_id);
      const prob = score?.probability ?? 0;
      const huw = score?.hazard_under_water?.score ?? 0;
      const rankVal = hazardUnderWaterMode ? huw : prob;
      const band: RiskBand = score?.band ?? 'low';
      return { hotspot: hs, score, rankVal, band, prob, huw };
    })
    .sort((a, b) => b.rankVal - a.rankVal)
    .slice(0, 10);

  // Determine which preset is currently active
  const isClearPreset = rain3h === 0 && rain24h === 0;
  const isLightPreset = rain3h === 10 && rain24h === 10;
  const isHeavyPreset = rain3h === 40 && rain24h === 30;
  const isExtremePreset = rain3h === 80 && rain24h === 60;

  return (
    <aside className="w-[380px] h-full bg-white border-r border-slate-200/90 flex flex-col text-slate-800 overflow-hidden select-none z-20 shadow-xs">
      {/* Top Header: Scenario Selector */}
      <div className="p-4 border-b border-slate-200/80 bg-slate-50/60 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Control Center
          </span>
          {isLoadingRisk && (
            <span className="flex items-center space-x-1 text-sky-600 text-xs font-medium">
              <RefreshCw className="w-3 h-3 animate-spin" />
              <span>Simulating...</span>
            </span>
          )}
        </div>

        {/* Mode Selector Toggle */}
        <div className="flex bg-slate-200/70 p-1 rounded-xl border border-slate-300/40">
          <button
            onClick={() => onModeChange('whatif')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition ${
              mode === 'whatif'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            🌧️ Rain Simulation
          </button>
          <button
            onClick={() => onModeChange('live')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition flex items-center justify-center space-x-1.5 ${
              mode === 'live'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-emerald-600" />
            <span>Live Forecast</span>
          </button>
        </div>

        {liveError && (
          <div className="flex items-start space-x-2 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-600" />
            <div>
              <p className="font-semibold">Live stream unavailable</p>
              <p className="text-[11px] text-amber-700/80">{liveError}</p>
            </div>
          </div>
        )}

        {/* Intuitive Rain Presets */}
        {mode === 'whatif' && (
          <div className="space-y-1.5 pt-1">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Rain Scenarios
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => onPreset(0, 0, 0)}
                className={`p-2.5 rounded-xl border text-left transition flex items-center space-x-2.5 ${
                  isClearPreset
                    ? 'bg-sky-50/80 border-sky-400 text-sky-950 font-semibold shadow-xs ring-1 ring-sky-300'
                    : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
                }`}
              >
                <div className="w-7 h-7 rounded-lg bg-amber-100/70 text-amber-600 flex items-center justify-center flex-shrink-0">
                  <Sun className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold leading-tight">Clear / Dry</div>
                  <div className="text-[10px] text-slate-500">0 mm rain</div>
                </div>
              </button>

              <button
                onClick={() => onPreset(10, 10, 10)}
                className={`p-2.5 rounded-xl border text-left transition flex items-center space-x-2.5 ${
                  isLightPreset
                    ? 'bg-sky-50/80 border-sky-400 text-sky-950 font-semibold shadow-xs ring-1 ring-sky-300'
                    : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
                }`}
              >
                <div className="w-7 h-7 rounded-lg bg-sky-100 text-sky-600 flex items-center justify-center flex-shrink-0">
                  <CloudDrizzle className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold leading-tight">Light Shower</div>
                  <div className="text-[10px] text-slate-500">10 mm rain</div>
                </div>
              </button>

              <button
                onClick={() => onPreset(40, 30, 30)}
                className={`p-2.5 rounded-xl border text-left transition flex items-center space-x-2.5 ${
                  isHeavyPreset
                    ? 'bg-sky-50/80 border-sky-400 text-sky-950 font-semibold shadow-xs ring-1 ring-sky-300'
                    : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
                }`}
              >
                <div className="w-7 h-7 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0">
                  <CloudRain className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold leading-tight">Heavy Monsoon</div>
                  <div className="text-[10px] text-slate-500">40 mm rain</div>
                </div>
              </button>

              <button
                onClick={() => onPreset(80, 60, 60)}
                className={`p-2.5 rounded-xl border text-left transition flex items-center space-x-2.5 ${
                  isExtremePreset
                    ? 'bg-rose-50/80 border-rose-400 text-rose-950 font-semibold shadow-xs ring-1 ring-rose-300'
                    : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
                }`}
              >
                <div className="w-7 h-7 rounded-lg bg-rose-100 text-rose-600 flex items-center justify-center flex-shrink-0">
                  <CloudLightning className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold leading-tight">Cloudburst</div>
                  <div className="text-[10px] text-slate-500">80 mm rain</div>
                </div>
              </button>
            </div>

            {/* Expandable Fine-Tuning Sliders Accordion */}
            <div className="pt-1">
              <button
                onClick={() => setShowAdvancedSliders(!showAdvancedSliders)}
                className="w-full flex items-center justify-between text-[11px] font-medium text-slate-500 hover:text-slate-800 py-1 transition"
              >
                <span className="flex items-center space-x-1">
                  <Sliders className="w-3 h-3" />
                  <span>Fine-tune parameters ({rain3h}mm / {rain24h}mm / {traffic}%)</span>
                </span>
                {showAdvancedSliders ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>

              {showAdvancedSliders && (
                <div className="mt-2 p-3 rounded-xl bg-white border border-slate-200 space-y-3 shadow-2xs">
                  {/* Slider 1 */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-600">Rain next 3 h:</span>
                      <span className="font-mono font-bold text-sky-700">{rain3h} mm</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      value={rain3h}
                      onChange={(e) => onRain3hChange(Number(e.target.value))}
                      className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-sky-600"
                    />
                  </div>

                  {/* Slider 2 */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-600">Rain past 24 h:</span>
                      <span className="font-mono font-bold text-sky-700">{rain24h} mm</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      value={rain24h}
                      onChange={(e) => onRain24hChange(Number(e.target.value))}
                      className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-sky-600"
                    />
                  </div>

                  {/* Slider 3 */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-600">Traffic slowdown:</span>
                      <span className="font-mono font-bold text-sky-700">{traffic} %</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      value={traffic}
                      onChange={(e) => onTrafficChange(Number(e.target.value))}
                      className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-sky-600"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Hazard Under Water Toggle Card */}
        <div className="p-2.5 rounded-xl bg-white border border-slate-200/90 flex items-center justify-between shadow-2xs">
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-800">Argus Hazard-Vision</div>
              <div className="text-[10px] text-slate-500">Detect underwater manholes &amp; grates</div>
            </div>
          </div>
          <button
            onClick={onToggleHazardUnderWater}
            className={`relative inline-flex h-5 w-10 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              hazardUnderWaterMode ? 'bg-[#0c192c]' : 'bg-slate-300'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-xs ring-0 transition duration-200 ease-in-out ${
                hazardUnderWaterMode ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Corridor Health / Alert Summary */}
      <div className="px-4 py-3 border-b border-slate-200/80 bg-slate-50/40 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <AlertTriangle className={`w-4 h-4 ${above50Count > 0 ? 'text-rose-500' : 'text-emerald-500'}`} />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            {hazardUnderWaterMode ? 'Submerged Hazard Hotspots' : 'Vulnerable Corridors'}
          </span>
        </div>
        <span
          className={`text-xs font-mono font-bold px-2 py-0.5 rounded-full ${
            above50Count > 0
              ? 'bg-rose-100 text-rose-800 border border-rose-200'
              : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
          }`}
        >
          {above50Count} of {totalCount} &gt; 50%
        </span>
      </div>

      {/* Rankings List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
        {rankedHotspots.map(({ hotspot, rankVal, band }, index) => {
          const isSelected = hotspot.hotspot_id === selectedHotspotId;
          const pct = Math.round(rankVal * 100);
          const color = getBandColor(band);

          return (
            <button
              key={hotspot.hotspot_id}
              onClick={() => onSelectHotspot(hotspot.hotspot_id)}
              className={`w-full text-left px-4 py-3 flex items-center justify-between transition ${
                isSelected
                  ? 'bg-sky-50/70 border-l-4 border-sky-600'
                  : 'hover:bg-slate-50/90'
              }`}
            >
              <div className="flex items-center space-x-3 min-w-0 pr-2">
                <span className="text-xs font-mono font-semibold text-slate-400 w-4">{index + 1}</span>
                <div className="truncate">
                  <p
                    className={`text-sm truncate ${
                      isSelected ? 'font-bold text-sky-950' : 'font-semibold text-slate-800'
                    }`}
                  >
                    {hotspot.name}
                  </p>
                  <p className="text-xs text-slate-500 truncate">
                    {hotspot.road?.name || 'Road unknown'}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2 flex-shrink-0">
                <span
                  className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                  style={{
                    backgroundColor: `${color}15`,
                    color: color,
                    border: `1px solid ${color}40`,
                  }}
                >
                  {band}
                </span>
                <span className="font-mono text-sm font-bold w-10 text-right" style={{ color }}>
                  {pct}%
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Footer: Risk Legend & Verbatim Disclaimer */}
      <div className="p-4 border-t border-slate-200/80 bg-slate-50/80 space-y-2.5">
        <div>
          <div className="text-[11px] font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">
            Risk Severity Scale
          </div>
          <div className="grid grid-cols-4 gap-1.5 text-[11px] text-center font-bold">
            <div className="py-1 rounded-md bg-emerald-100/70 text-emerald-800 border border-emerald-200">
              Low
            </div>
            <div className="py-1 rounded-md bg-amber-100/70 text-amber-800 border border-amber-200">
              Mod
            </div>
            <div className="py-1 rounded-md bg-orange-100/70 text-orange-800 border border-orange-200">
              High
            </div>
            <div className="py-1 rounded-md bg-rose-100/70 text-rose-800 border border-rose-200">
              Severe
            </div>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-white border border-slate-200 text-[11px] text-slate-500 leading-relaxed shadow-2xs">
          <strong className="text-slate-700">Note:</strong> Risk is a relative ranking from an
          expert-prior model, not a flood-depth forecast. Data tagged &apos;illustrative&apos; is
          placeholder and must be verified.
        </div>
      </div>
    </aside>
  );
};
