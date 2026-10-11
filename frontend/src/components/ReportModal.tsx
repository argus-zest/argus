import React, { useState, useEffect } from 'react';
import { Hotspot, HazardAnalysis, Road, Jurisdiction, Warranty, Case, CreateCaseRequest, AssetType } from '../lib/types';
import { presignUpload, analyzeHazard, resolveLocation, createCase, uploadPhoto } from '../lib/api';
import {
  X,
  Upload,
  Camera,
  MapPin,
  AlertTriangle,
  ShieldCheck,
  Clock,
  Sparkles,
  RefreshCw,
  Navigation,
} from 'lucide-react';

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  presetHotspot: Hotspot | null;
  hotspots: Hotspot[];
  onStartPickLocation: () => void;
  pickedLocation: { lat: number; lng: number } | null;
  onCaseCreated: (c: Case) => void;
}

export const ReportModal: React.FC<ReportModalProps> = ({
  isOpen,
  onClose,
  presetHotspot,
  hotspots,
  onStartPickLocation,
  pickedLocation,
  onCaseCreated,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [photoKey, setPhotoKey] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<HazardAnalysis | null>(null);

  // Location selection: 'hotspot' | 'geolocation' | 'picked'
  const [locationType, setLocationType] = useState<'hotspot' | 'geolocation' | 'picked'>('hotspot');
  const [selectedHotspotId, setSelectedHotspotId] = useState<string>(
    presetHotspot?.hotspot_id || hotspots[0]?.hotspot_id || ''
  );
  const [customLat, setCustomLat] = useState<number>(28.633);
  const [customLng, setCustomLng] = useState<number>(77.22);

  // Resolution result (road, jurisdiction, warranty)
  const [isResolving, setIsResolving] = useState(false);
  const [resolvedChain, setResolvedChain] = useState<{
    road: Road | null;
    jurisdiction: Jurisdiction;
    warranty: Warranty;
  } | null>(null);

  // Timer profile: 'demo' | 'real'
  const [timerProfile, setTimerProfile] = useState<'demo' | 'real'>('demo');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Reset or preset when opened
  useEffect(() => {
    if (presetHotspot) {
      setSelectedHotspotId(presetHotspot.hotspot_id);
      setLocationType('hotspot');
      if (presetHotspot.road && presetHotspot.jurisdiction && presetHotspot.warranty) {
        setResolvedChain({
          road: presetHotspot.road,
          jurisdiction: presetHotspot.jurisdiction,
          warranty: presetHotspot.warranty,
        });
      }
    }
  }, [presetHotspot, isOpen]);

  // If user picked a location on map
  useEffect(() => {
    if (pickedLocation) {
      setLocationType('picked');
      setCustomLat(pickedLocation.lat);
      setCustomLng(pickedLocation.lng);
      handleResolve(pickedLocation.lat, pickedLocation.lng, analysis?.hazard_type || null);
    }
  }, [pickedLocation]);

  if (!isOpen) return null;

  // Handle client-side resize and upload
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    const localUrl = URL.createObjectURL(file);
    setPreviewUrl(localUrl);

    try {
      setIsUploading(true);
      const resizedBlob = await resizeImage(file, 1280, 0.85);

      const presign = await presignUpload('report', 'image/jpeg');
      await uploadPhoto(presign.upload_url, resizedBlob, 'image/jpeg');

      setPhotoKey(presign.s3_key);
      setIsUploading(false);

      setIsAnalyzing(true);
      const anaResult = await analyzeHazard(presign.s3_key);
      setAnalysis(anaResult.analysis);

      let currentLat = customLat;
      let currentLng = customLng;
      if (locationType === 'hotspot') {
        const hs = hotspots.find((h) => h.hotspot_id === selectedHotspotId);
        if (hs) {
          currentLat = hs.lat;
          currentLng = hs.lng;
        }
      }
      handleResolve(currentLat, currentLng, anaResult.analysis.hazard_type);
    } catch (err: any) {
      console.error('Upload / analyze error:', err);
      setSubmitError(err.message || 'Error uploading or analyzing photo');
    } finally {
      setIsUploading(false);
      setIsAnalyzing(false);
    }
  };

  const resizeImage = (file: File, maxDim: number, quality: number): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        let width = img.width;
        let height = img.height;
        if (width > maxDim || height > maxDim) {
          if (width > height) {
            height = Math.round((height * maxDim) / width);
            width = maxDim;
          } else {
            width = Math.round((width * maxDim) / height);
            height = maxDim;
          }
        }
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (!ctx) return reject(new Error('Canvas context failed'));
        ctx.drawImage(img, 0, 0, width, height);
        canvas.toBlob(
          (blob) => {
            if (blob) resolve(blob);
            else reject(new Error('Canvas toBlob failed'));
          },
          'image/jpeg',
          quality
        );
      };
      img.onerror = reject;
      img.src = URL.createObjectURL(file);
    });
  };

  const handleResolve = async (lat: number, lng: number, hazardType: string | null) => {
    try {
      setIsResolving(true);
      const res = await resolveLocation(lat, lng, hazardType);
      setResolvedChain({
        road: res.road,
        jurisdiction: res.jurisdiction,
        warranty: res.warranty,
      });
    } catch (err) {
      console.error('Resolve error:', err);
    } finally {
      setIsResolving(false);
    }
  };

  const handleUseGeolocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation not supported by your browser');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocationType('geolocation');
        setCustomLat(pos.coords.latitude);
        setCustomLng(pos.coords.longitude);
        handleResolve(pos.coords.latitude, pos.coords.longitude, analysis?.hazard_type || null);
      },
      () => {
        alert('Could not retrieve browser location. Please choose a hotspot or pick on the map.');
      }
    );
  };

  const handleSubmit = async (_forceAnyway = false) => {
    setSubmitError(null);
    setIsSubmitting(true);

    try {
      let lat = customLat;
      let lng = customLng;
      let hotspotId: string | undefined = undefined;

      if (locationType === 'hotspot') {
        const hs = hotspots.find((h) => h.hotspot_id === selectedHotspotId);
        if (hs) {
          lat = hs.lat;
          lng = hs.lng;
          hotspotId = hs.hotspot_id;
        }
      }

      const payload: CreateCaseRequest = {
        hotspot_id: hotspotId,
        lat,
        lng,
        asset_type: ['pothole', 'open_manhole', 'missing_drain_cover'].includes(analysis?.hazard_type || '')
          ? analysis?.hazard_type as AssetType : undefined,
        analysis: analysis || {
          hazard_type: 'unclear',
          severity: 3,
          submerged: false,
          confidence: 0.5,
          description: 'Citizen reported hazard (photo omitted or manual override)',
          visible_evidence: 'Manual citizen report',
        },
        photo_key: photoKey || undefined,
        timer_profile: timerProfile,
      };

      const created = await createCase(payload);
      onCaseCreated(created);
    } catch (err: any) {
      console.error('Submit case error:', err);
      setSubmitError(err.message || 'Failed to create case');
    } finally {
      setIsSubmitting(false);
    }
  };

  const isHazardUnconfirmed = analysis && (analysis.hazard_type === 'none' || analysis.hazard_type === 'unclear');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm select-none">
      <div className="relative w-full max-w-2xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-100 shadow-2xs">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Report Road Hazard</h2>
              <p className="text-xs text-slate-500">
                Photo triage &bull; Amazon Nova Lite verification &bull; Escalation initiation
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

        {/* Scrollable Form Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6 bg-white text-slate-800">
          {/* Step 1: Photo Upload */}
          <div className="space-y-3">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600 block">
              1. Street Hazard Photo (Optional for Hotspots)
            </label>

            <div className="flex items-center space-x-4">
              <label className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-200 hover:border-sky-500 rounded-2xl p-5 cursor-pointer bg-slate-50/60 hover:bg-sky-50/20 transition">
                <Upload className="w-6 h-6 text-sky-600 mb-1.5" />
                <span className="text-xs font-bold text-slate-800">
                  {selectedFile ? selectedFile.name : 'Select or capture photo (JPEG / PNG)'}
                </span>
                <span className="text-[11px] text-slate-400 mt-0.5">Auto-resized to max 1280px</span>
                <input
                  type="file"
                  accept="image/jpeg,image/png"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>

              {previewUrl && (
                <div className="w-24 h-24 rounded-2xl border border-slate-200 overflow-hidden bg-slate-100 flex-shrink-0 shadow-2xs">
                  <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
                </div>
              )}
            </div>

            {isUploading && (
              <div className="flex items-center space-x-2 text-xs font-medium text-sky-600">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Uploading resized image to S3 bucket...</span>
              </div>
            )}
            {isAnalyzing && (
              <div className="flex items-center space-x-2 text-xs font-medium text-amber-600">
                <Sparkles className="w-3.5 h-3.5 animate-pulse" />
                <span>Analyzing visual features with Amazon Nova Lite...</span>
              </div>
            )}

            {/* Analysis Card */}
            {analysis && (
              <div className="p-4 rounded-2xl bg-sky-50/40 border border-sky-200/80 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-sky-900 flex items-center space-x-1">
                    <Sparkles className="w-3.5 h-3.5 text-sky-600" />
                    <span>Nova Lite Hazard Assessment</span>
                  </span>
                  <span className="text-xs font-mono font-bold text-sky-700 bg-sky-100/70 px-2 py-0.5 rounded-full">
                    {Math.round(analysis.confidence * 100)}% confidence
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-slate-500">Hazard Type:</span>
                    <span className="ml-2 font-bold text-slate-900 capitalize">
                      {analysis.hazard_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Submerged:</span>
                    <span
                      className={`ml-2 px-2 py-0.5 rounded text-[10px] font-bold ${
                        analysis.submerged
                          ? 'bg-rose-100 text-rose-800 border border-rose-200'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {analysis.submerged ? 'YES (Waterlogged)' : 'NO'}
                    </span>
                  </div>
                </div>

                {/* Severity Dots */}
                <div className="flex items-center space-x-2 text-xs">
                  <span className="text-slate-500">Severity:</span>
                  <div className="flex items-center space-x-1.5">
                    {[1, 2, 3, 4, 5].map((dot) => (
                      <span
                        key={dot}
                        className={`w-3 h-3 rounded-full ${
                          dot <= analysis.severity ? 'bg-rose-500' : 'bg-slate-200'
                        }`}
                      />
                    ))}
                    <span className="ml-1 font-mono font-bold text-slate-700">{analysis.severity}/5</span>
                  </div>
                </div>

                <div className="text-xs text-slate-700 leading-relaxed">
                  <span className="text-slate-500 font-medium">Description: </span>
                  {analysis.description}
                </div>
                <div className="text-xs text-slate-500 leading-relaxed italic">
                  <span className="text-slate-600 font-medium">Visual Evidence: </span>
                  {analysis.visible_evidence}
                </div>

                {isHazardUnconfirmed && (
                  <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 text-amber-600" />
                    <span>
                      Nova could not verify a hazard in the frame. You may still open a case if you believe one exists.
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Step 2: Location Picker */}
          <div className="space-y-3">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600 block">
              2. Hazard Location
            </label>

            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => {
                  setLocationType('hotspot');
                  const hs = hotspots.find((h) => h.hotspot_id === selectedHotspotId);
                  if (hs) handleResolve(hs.lat, hs.lng, analysis?.hazard_type || null);
                }}
                className={`py-2 px-3 rounded-xl text-xs font-semibold border transition ${
                  locationType === 'hotspot'
                    ? 'bg-sky-50 border-sky-400 text-sky-950 font-bold shadow-2xs'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                Selected Hotspot
              </button>

              <button
                type="button"
                onClick={handleUseGeolocation}
                className={`py-2 px-3 rounded-xl text-xs font-semibold border transition flex items-center justify-center space-x-1 ${
                  locationType === 'geolocation'
                    ? 'bg-sky-50 border-sky-400 text-sky-950 font-bold shadow-2xs'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                <Navigation className="w-3.5 h-3.5 text-sky-600" />
                <span>My Location</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  onClose();
                  onStartPickLocation();
                }}
                className={`py-2 px-3 rounded-xl text-xs font-semibold border transition flex items-center justify-center space-x-1 ${
                  locationType === 'picked'
                    ? 'bg-sky-50 border-sky-400 text-sky-950 font-bold shadow-2xs'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                <MapPin className="w-3.5 h-3.5 text-sky-600" />
                <span>Click on Map</span>
              </button>
            </div>

            {locationType === 'hotspot' && (
              <div className="space-y-1">
                <select
                  value={selectedHotspotId}
                  onChange={(e) => {
                    setSelectedHotspotId(e.target.value);
                    const hs = hotspots.find((h) => h.hotspot_id === e.target.value);
                    if (hs) handleResolve(hs.lat, hs.lng, analysis?.hazard_type || null);
                  }}
                  className="w-full py-2.5 px-3.5 rounded-xl bg-white border border-slate-300 text-xs text-slate-800 focus:outline-none focus:border-sky-500 shadow-2xs"
                >
                  {hotspots.map((hs) => (
                    <option key={hs.hotspot_id} value={hs.hotspot_id}>
                      {hs.name} ({hs.road?.name || 'Road unknown'})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {(locationType === 'geolocation' || locationType === 'picked') && (
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 flex items-center justify-between">
                <span>Attested GPS Coordinates:</span>
                <span className="font-mono font-bold text-sky-700">
                  {customLat.toFixed(5)}, {customLng.toFixed(5)}
                </span>
              </div>
            )}
          </div>

          {/* Step 3: Resolved Blame Chain Preview */}
          {resolvedChain && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-600 block">
                  3. Accountability &amp; Blame Chain Preview
                </label>
                {isResolving && <span className="text-[11px] text-sky-600 font-medium">Resolving...</span>}
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Agency &amp; Officer:</span>
                  <span className="font-bold text-slate-900">
                    {resolvedChain.jurisdiction.owner} &bull; {resolvedChain.jurisdiction.officer_role}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Contractor:</span>
                  <span className="text-slate-800 font-medium">
                    {resolvedChain.warranty.contractor_label || 'Unassigned'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Warranty Liability:</span>
                  <span className="font-bold text-emerald-700 capitalize bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    {resolvedChain.warranty.status.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Escalation Timer Profile */}
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-600 block">
              4. Escalation Timer Profile
            </label>
            <div className="flex items-center space-x-3 bg-slate-50 p-3 rounded-2xl border border-slate-200">
              <Clock className="w-5 h-5 text-sky-600 flex-shrink-0" />
              <div className="flex-1 text-xs">
                <span className="font-bold text-slate-900 block">
                  {timerProfile === 'demo' ? 'Demo Timers (20s per rung)' : 'Real Timers (2-3 days per rung)'}
                </span>
                <span className="text-[11px] text-slate-500">
                  Controls Step Functions progression speed before auto-escalating to higher officials
                </span>
              </div>
              <button
                type="button"
                onClick={() => setTimerProfile(timerProfile === 'demo' ? 'real' : 'demo')}
                className="py-1.5 px-3.5 rounded-lg text-xs font-bold bg-white hover:bg-slate-100 text-slate-800 border border-slate-300 shadow-2xs transition"
              >
                Switch to {timerProfile === 'demo' ? 'Real' : 'Demo'}
              </button>
            </div>
          </div>

          {submitError && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
              {submitError}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50/70 flex items-center justify-between">
          <button
            onClick={onClose}
            className="py-2 px-4 rounded-xl text-xs font-bold text-slate-500 hover:text-slate-800 transition"
          >
            Cancel
          </button>

          {isHazardUnconfirmed ? (
            <button
              onClick={() => handleSubmit(true)}
              disabled={isSubmitting}
              className="py-2.5 px-5 rounded-xl text-xs font-bold bg-amber-500 hover:bg-amber-600 text-white transition flex items-center space-x-1.5 shadow-xs"
            >
              <AlertTriangle className="w-4 h-4" />
              <span>{isSubmitting ? 'Opening Case...' : 'Open Case Anyway'}</span>
            </button>
          ) : (
            <button
              onClick={() => handleSubmit(false)}
              disabled={isSubmitting}
              className="py-2.5 px-6 rounded-xl text-xs font-bold bg-[#0c192c] hover:bg-[#162740] text-white transition flex items-center space-x-1.5 shadow-xs"
            >
              <ShieldCheck className="w-4 h-4 text-sky-400" />
              <span>{isSubmitting ? 'Opening Case...' : 'Submit & Open Escalation'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
