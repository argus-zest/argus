import React, { useState, useEffect, useRef } from 'react';
import { Hotspot, GroundAsset, RiskResponse, Case } from './lib/types';
import { fetchHotspots, fetchAssets, fetchRisk, debounce, MOCK_MODE } from './lib/api';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { MapView } from './components/MapView';
import { RightPanel } from './components/RightPanel';
import { ArchitectureModal } from './components/ArchitectureModal';
import { ReportModal } from './components/ReportModal';
import { CasesModal } from './components/CasesModal';
import { EvidenceModal } from './components/EvidenceModal';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const isDemoMode = new URLSearchParams(window.location.search).get('demo') === '1';

  // Core Data State
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [assets, setAssets] = useState<GroundAsset[]>([]);
  const [riskData, setRiskData] = useState<RiskResponse | null>(null);
  const [coreError, setCoreError] = useState<string | null>(null);

  // Risk Controls State
  const [mode, setMode] = useState<'whatif' | 'live'>('whatif');
  const [rain3h, setRain3h] = useState<number>(0);
  const [rain24h, setRain24h] = useState<number>(0);
  const [traffic, setTraffic] = useState<number>(0);
  const [hazardUnderWaterMode, setHazardUnderWaterMode] = useState<boolean>(false);
  const [isLoadingRisk, setIsLoadingRisk] = useState<boolean>(false);
  const [liveError, setLiveError] = useState<string | null>(null);

  // Selection & UI State
  const [selectedHotspotId, setSelectedHotspotId] = useState<string | null>(null);
  const [isRightPanelOpen, setIsRightPanelOpen] = useState<boolean>(true);
  const [isPickingLocation, setIsPickingLocation] = useState<boolean>(false);
  const [pickedLocation, setPickedLocation] = useState<{ lat: number; lng: number } | null>(null);

  // Modals
  const [isReportOpen, setIsReportOpen] = useState<boolean>(false);
  const [isCasesOpen, setIsCasesOpen] = useState<boolean>(false);
  const [isEvidenceOpen, setIsEvidenceOpen] = useState<boolean>(false);
  const [isArchitectureOpen, setIsArchitectureOpen] = useState<boolean>(false);
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);

  // Initial Data Load
  const loadInitialData = async () => {
    try {
      setCoreError(null);

      const [hsRes, astRes] = await Promise.all([fetchHotspots(), fetchAssets()]);
      setHotspots(hsRes.hotspots);
      setAssets(astRes.assets);

      if (isDemoMode) {
        setSelectedHotspotId('minto_bridge');
        setIsRightPanelOpen(true);
      } else if (hsRes.hotspots.length > 0) {
        setSelectedHotspotId(hsRes.hotspots[0].hotspot_id);
        setIsRightPanelOpen(true);
      }
    } catch (err: any) {
      console.error('Failed to load initial data:', err);
      setCoreError(err.message || 'Failed to connect to backend service.');
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // Debounced Risk Fetch
  const executeFetchRisk = async (
    targetMode: 'whatif' | 'live',
    r3: number,
    r24: number,
    tr: number
  ) => {
    try {
      setIsLoadingRisk(true);
      setLiveError(null);
      const res = await fetchRisk(targetMode, r3, r24, tr);
      setRiskData(res);
    } catch (err: any) {
      console.error('Fetch risk error:', err);
      if (targetMode === 'live') {
        setLiveError(err.message || 'Live scores not available yet');
        setMode('whatif');
      }
    } finally {
      setIsLoadingRisk(false);
    }
  };

  const debouncedFetchRiskRef = useRef(
    debounce((m: 'whatif' | 'live', r3: number, r24: number, tr: number) => {
      executeFetchRisk(m, r3, r24, tr);
    }, 200)
  );

  // Trigger risk recalculation whenever parameters change
  useEffect(() => {
    debouncedFetchRiskRef.current(mode, rain3h, rain24h, traffic);
  }, [mode, rain3h, rain24h, traffic]);

  // Preset Handler
  const handlePreset = (r3: number, r24: number, tr: number) => {
    setRain3h(r3);
    setRain24h(r24);
    setTraffic(tr);
  };

  // Keyboard Shortcuts in Demo Mode
  useEffect(() => {
    if (!isDemoMode) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if typing in an input
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }

      switch (e.key) {
        case '1':
          handlePreset(10, 10, 10);
          break;
        case '2':
          handlePreset(40, 30, 30);
          break;
        case '3':
          handlePreset(80, 60, 60);
          break;
        case '0':
          handlePreset(0, 0, 0);
          break;
        case 'h':
        case 'H':
          setHazardUnderWaterMode((prev) => !prev);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isDemoMode]);

  // Handle location picking from map
  const handlePickLocation = (lat: number, lng: number) => {
    setPickedLocation({ lat, lng });
    setIsPickingLocation(false);
    setIsReportOpen(true);
  };

  const handleSelectHotspot = (id: string) => {
    setSelectedHotspotId(id);
    setIsRightPanelOpen(true);
  };

  const selectedHotspot = hotspots.find((h) => h.hotspot_id === selectedHotspotId) || null;
  const selectedScore =
    riskData?.scores.find((s) => s.hotspot_id === selectedHotspotId) || null;

  // Nearby assets within 50m of selected hotspot
  const nearbyAssets = selectedHotspot?.assets || [];

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#f0f4f8] text-[#0f172a]">
      {/* Top Navigation */}
      <Navbar
        isDemoMode={isDemoMode}
        onOpenReport={() => {
          setIsReportOpen(true);
        }}
        onOpenCases={() => setIsCasesOpen(true)}
        onOpenEvidence={() => setIsEvidenceOpen(true)}
        onOpenArchitecture={() => setIsArchitectureOpen(true)}
      />

      {MOCK_MODE && (
        <div role="status" className="px-4 py-2 bg-amber-50 text-amber-900 text-sm">
          Local mock data — simulated risk, no live inference. Uploads and case workflows require a backend.
        </div>
      )}

      {/* Main Workspace Layout */}
      {coreError ? (
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-rose-500" />
          <h2 className="text-xl font-bold text-slate-900">Backend Connection Required</h2>
          <p className="text-sm text-slate-500 max-w-md">{coreError}</p>
          <button
            onClick={loadInitialData}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-[#0c192c] hover:bg-[#162740] text-white font-bold transition shadow-xs"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry Connection</span>
          </button>
        </div>
      ) : (
        <div className="flex-1 flex relative min-h-0 bg-[#f0f4f8]">
          {/* Left Sidebar Controls */}
          <Sidebar
            mode={mode}
            onModeChange={setMode}
            rain3h={rain3h}
            rain24h={rain24h}
            traffic={traffic}
            onRain3hChange={setRain3h}
            onRain24hChange={setRain24h}
            onTrafficChange={setTraffic}
            onPreset={handlePreset}
            hazardUnderWaterMode={hazardUnderWaterMode}
            onToggleHazardUnderWater={() => setHazardUnderWaterMode((v) => !v)}
            hotspots={hotspots}
            riskScores={riskData?.scores || []}
            selectedHotspotId={selectedHotspotId}
            onSelectHotspot={handleSelectHotspot}
            isLoadingRisk={isLoadingRisk}
            liveError={liveError}
          />

          {/* Central Full-Screen Map */}
          <MapView
            hotspots={hotspots}
            assets={assets}
            riskScores={riskData?.scores || []}
            selectedHotspotId={selectedHotspotId}
            onSelectHotspot={handleSelectHotspot}
            rain3h={rain3h}
            isPickingLocation={isPickingLocation}
            onPickLocation={handlePickLocation}
            isDemoMode={isDemoMode}
          />

          {/* Right Selected Hotspot Panel */}
          {isRightPanelOpen && (
            <RightPanel
              hotspot={selectedHotspot}
              score={selectedScore}
              nearbyAssets={nearbyAssets}
              onClose={() => setIsRightPanelOpen(false)}
              onOpenCase={(hs) => {
                setSelectedHotspotId(hs.hotspot_id);
                setIsReportOpen(true);
              }}
            />
          )}
        </div>
      )}

      {/* Modals */}
      <ReportModal
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
        presetHotspot={selectedHotspot}
        hotspots={hotspots}
        onStartPickLocation={() => {
          setIsPickingLocation(true);
        }}
        pickedLocation={pickedLocation}
        onCaseCreated={(newCase: Case) => {
          setIsReportOpen(false);
          setActiveCaseId(newCase.case_id);
          setIsCasesOpen(true);
        }}
      />

      <CasesModal
        isOpen={isCasesOpen}
        onClose={() => setIsCasesOpen(false)}
        activeCaseId={activeCaseId}
        onSelectCase={setActiveCaseId}
      />

      <EvidenceModal
        isOpen={isEvidenceOpen}
        onClose={() => setIsEvidenceOpen(false)}
        modelVersion={riskData?.model?.version || '1.0.0'}
        modelFitted={riskData?.model?.fitted || false}
      />

      <ArchitectureModal
        isOpen={isArchitectureOpen}
        onClose={() => setIsArchitectureOpen(false)}
      />
    </div>
  );
};
