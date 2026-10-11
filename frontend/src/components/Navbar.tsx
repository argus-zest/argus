import React from 'react';
import { ShieldCheck, MapPin, Layers, FileText, Activity, Radio, PanelRightOpen } from 'lucide-react';

interface NavbarProps {
  isDemoMode: boolean;
  onOpenReport: () => void;
  onOpenCases: () => void;
  onOpenEvidence: () => void;
  onOpenArchitecture: () => void;
  isRightPanelOpen: boolean;
  onOpenRightPanel: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  isDemoMode,
  onOpenReport,
  onOpenCases,
  onOpenEvidence,
  onOpenArchitecture,
  isRightPanelOpen,
  onOpenRightPanel,
}) => {
  return (
    <header className="flex flex-col bg-white border-b border-slate-200/90 select-none z-30 shadow-xs">
      {isDemoMode && (
        <div className="bg-sky-50 border-b border-sky-100 text-sky-800 text-xs py-1 px-4 text-center font-medium tracking-wide flex items-center justify-center space-x-2">
          <span className="font-bold text-sky-900 bg-sky-200/70 px-1.5 py-0.5 rounded text-[10px] uppercase tracking-wider">
            Demo Sandbox
          </span>
          <span>
            Seeded records active. Shortcuts: <strong>[1]</strong> Light &bull; <strong>[2]</strong> Heavy &bull;{' '}
            <strong>[3]</strong> Cloudburst &bull; <strong>[0]</strong> Clear &bull; <strong>[h]</strong> Submerged Hazards
          </span>
        </div>
      )}

      <div className="min-h-16 px-4 py-3 flex flex-col gap-3 items-center justify-between xl:h-16 xl:flex-row xl:px-5 xl:py-0">
        {/* Brand / Logo */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
            <img
              src="/argus-logo.png"
              alt="ARGUS"
              className="h-9 w-auto object-contain drop-shadow-xs"
            />
            <div className="hidden sm:flex flex-col border-l border-slate-200 pl-3">
              <span className="text-xs font-semibold text-slate-800 leading-tight">
                Urban Hazard &amp; Flood Intelligence
              </span>
              <span className="text-[11px] text-slate-500 leading-tight">
                Delhi NCR Drainage &amp; Road Accountability
              </span>
            </div>
          </div>

          {/* Status Pills */}
          <div className="hidden xl:flex items-center space-x-2 pl-2">
            <div className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              <Radio className="w-3 h-3 mr-1 text-emerald-500 animate-pulse" />
              <span>Live Telemetry</span>
            </div>

            <div className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
              <ShieldCheck className="w-3 h-3 mr-1 text-amber-500" />
              <span>DRY-RUN (Safe Sandbox)</span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 w-full xl:flex xl:w-auto [&>button]:justify-center [&>button]:min-h-11">
          <button
            onClick={onOpenReport}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-lg text-sm font-semibold bg-[#0c192c] hover:bg-[#162740] text-white shadow-xs transition active:scale-95"
          >
            <MapPin className="w-4 h-4 text-sky-400" />
            <span>Report Hazard</span>
          </button>

          <button
            onClick={onOpenCases}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-2xs transition"
          >
            <FileText className="w-4 h-4 text-slate-500" />
            <span>Cases</span>
          </button>

          <button
            onClick={onOpenEvidence}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-2xs transition"
          >
            <Activity className="w-4 h-4 text-slate-500" />
            <span>Model &amp; Evidence</span>
          </button>

          <button
            onClick={onOpenArchitecture}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-2xs transition"
          >
            <Layers className="w-4 h-4 text-slate-500" />
            <span>Architecture</span>
          </button>
          {!isRightPanelOpen && (
            <button
              type="button"
              onClick={onOpenRightPanel}
              aria-label="Open hotspot details panel"
              title="Open hotspot details panel"
              className="flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-2xs transition"
            >
              <PanelRightOpen className="w-4 h-4 text-slate-500" aria-hidden="true" />
              <span>Details</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
