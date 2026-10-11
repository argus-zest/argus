import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { Hotspot, GroundAsset, RiskScore } from '../lib/types';
import { getBandColor, getHazardColor } from '../lib/api';
import { Eye, EyeOff, MapPin } from 'lucide-react';

interface MapViewProps {
  hotspots: Hotspot[];
  riskScores: RiskScore[];
  assets: GroundAsset[];
  selectedHotspotId: string | null;
  onSelectHotspot: (id: string) => void;
  rain3h: number;
  isPickingLocation?: boolean;
  onPickLocation?: (lat: number, lng: number) => void;
  isDemoMode?: boolean;
}

export const MapView: React.FC<MapViewProps> = ({
  hotspots,
  riskScores,
  assets,
  selectedHotspotId,
  onSelectHotspot,
  rain3h,
  isPickingLocation = false,
  onPickLocation,
  isDemoMode = false,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  const [isFallbackStyle, setIsFallbackStyle] = useState(false);
  const [showAssets, setShowAssets] = useState(true);
  const animFrameIdRef = useRef<number | null>(null);
  const pulseRadiusRef = useRef<number>(14);
  const pulseGrowingRef = useRef<boolean>(true);

  const region = import.meta.env.VITE_AWS_REGION || 'us-east-1';
  const apiKey = import.meta.env.VITE_LOCATION_API_KEY;

  // Helper to build Hotspot GeoJSON features
  const buildHotspotFeatures = (hsList: Hotspot[], sList: RiskScore[]): GeoJSON.Feature[] => {
    const sMap = new Map<string, RiskScore>();
    sList.forEach((s) => sMap.set(s.hotspot_id, s));

    return hsList.map((hs) => {
      const s = sMap.get(hs.hotspot_id);
      const band = s?.band || 'low';
      const color = getBandColor(band);

      return {
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [hs.lng, hs.lat],
        },
        properties: {
          hotspot_id: hs.hotspot_id,
          name: hs.name,
          band: band,
          color: color,
          probability: s?.probability ?? 0,
        },
      };
    });
  };

  // Helper to build Asset GeoJSON features
  const buildAssetFeatures = (astList: GroundAsset[]): GeoJSON.Feature[] => {
    return astList.map((a) => ({
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [a.lng, a.lat],
      },
      properties: {
        asset_id: a.asset_id,
        type: a.type,
        label: a.type.replace(/_/g, ' '),
        color: getHazardColor(a.type),
        severity: a.severity,
      },
    }));
  };

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Clean, watermark-free OpenStreetMap basemap styled to match light grey-blue aesthetic
    const defaultLightStyle: any = {
      version: 8,
      glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
      sources: {
        'osm-tiles': {
          type: 'raster',
          tiles: [
            'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
            'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
            'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
          ],
          tileSize: 256,
          attribution: '&copy; OpenStreetMap contributors',
        },
      },
      layers: [
        {
          id: 'osm-tiles-layer',
          type: 'raster',
          source: 'osm-tiles',
          minzoom: 0,
          maxzoom: 19,
          paint: {
            'raster-saturation': -0.55,
            'raster-contrast': -0.05,
            'raster-brightness-min': 0.08,
            'raster-brightness-max': 0.98,
          },
        },
      ],
    };

    let styleConfig: any = defaultLightStyle;
    let fallback = true;

    if (apiKey) {
      styleConfig = `https://maps.geo.${region}.amazonaws.com/v2/styles/Standard/descriptor?key=${apiKey}&color-scheme=Light`;
      fallback = false;
    }

    setIsFallbackStyle(fallback);

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: styleConfig,
      center: [77.2090, 28.6139],
      zoom: isDemoMode ? 11.2 : 10.8,
      pitch: 0,
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

    map.on('error', (e) => {
      if (!fallback && e.error && (e.error as any).status === 403) {
        setIsFallbackStyle(true);
        map.setStyle(defaultLightStyle);
      }
    });

    map.on('load', () => {
      // Add Hotspots Source with immediate data
      const initialHsFeatures = buildHotspotFeatures(hotspots, riskScores);
      map.addSource('hotspots-src', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: initialHsFeatures },
      });

      // Add Pulsing layer for severe hotspots
      map.addLayer({
        id: 'hotspots-pulse',
        type: 'circle',
        source: 'hotspots-src',
        filter: ['==', ['get', 'band'], 'severe'],
        paint: {
          'circle-radius': 16,
          'circle-color': '#ef4444',
          'circle-opacity': 0.35,
          'circle-stroke-width': 0,
        },
      });

      // Add Main Hotspot Circles
      map.addLayer({
        id: 'hotspots-circle',
        type: 'circle',
        source: 'hotspots-src',
        paint: {
          'circle-radius': [
            'case',
            ['==', ['get', 'hotspot_id'], selectedHotspotId || ''],
            15,
            11,
          ],
          'circle-color': ['get', 'color'],
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 2.5,
        },
      });

      // Add Hotspot Text Labels
      map.addLayer({
        id: 'hotspots-label',
        type: 'symbol',
        source: 'hotspots-src',
        layout: {
          'text-field': ['get', 'name'],
          'text-size': 12,
          'text-offset': [0, 1.2],
          'text-anchor': 'top',
        },
        paint: {
          'text-color': '#0f172a',
          'text-halo-color': '#ffffff',
          'text-halo-width': 2.5,
        },
      });

      // Add Assets Source with immediate data
      const initialAstFeatures = buildAssetFeatures(assets);
      map.addSource('assets-src', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: initialAstFeatures },
      });

      // Assets Layer
      map.addLayer({
        id: 'assets-circle',
        type: 'circle',
        source: 'assets-src',
        minzoom: 11.5,
        layout: {
          visibility: showAssets ? 'visible' : 'none',
        },
        paint: {
          'circle-radius': 6.5,
          'circle-color': ['get', 'color'],
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 2,
        },
      });

      // Assets Label
      map.addLayer({
        id: 'assets-label',
        type: 'symbol',
        source: 'assets-src',
        minzoom: 12.5,
        layout: {
          visibility: showAssets ? 'visible' : 'none',
          'text-field': ['get', 'label'],
          'text-size': 10,
          'text-offset': [0, 1],
          'text-anchor': 'top',
        },
        paint: {
          'text-color': '#475569',
          'text-halo-color': '#ffffff',
          'text-halo-width': 2,
        },
      });

      // Cursor & Click Handlers
      map.on('mouseenter', 'hotspots-circle', () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', 'hotspots-circle', () => {
        map.getCanvas().style.cursor = '';
      });

      map.on('click', 'hotspots-circle', (e) => {
        if (!e.features || e.features.length === 0) return;
        const clickedId = e.features[0].properties?.hotspot_id;
        if (clickedId) {
          onSelectHotspot(clickedId);
        }
      });

      // Map Click for Location Picker
      map.on('click', (e) => {
        if (isPickingLocation && onPickLocation) {
          onPickLocation(e.lngLat.lat, e.lngLat.lng);
        }
      });
    });

    mapRef.current = map;

    return () => {
      if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current);
      map.remove();
    };
  }, []);

  // Update Assets Visibility
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('assets-circle')) {
      map.setLayoutProperty('assets-circle', 'visibility', showAssets ? 'visible' : 'none');
    }
    if (map.getLayer('assets-label')) {
      map.setLayoutProperty('assets-label', 'visibility', showAssets ? 'visible' : 'none');
    }
  }, [showAssets]);

  // Update Hotspot GeoJSON Data when state changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const features = buildHotspotFeatures(hotspots, riskScores);
    const src = map.getSource('hotspots-src') as maplibregl.GeoJSONSource | undefined;
    if (src) {
      src.setData({
        type: 'FeatureCollection',
        features: features,
      });
    }
  }, [hotspots, riskScores, selectedHotspotId]);

  // Update Assets GeoJSON Data when state changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const features = buildAssetFeatures(assets);
    const src = map.getSource('assets-src') as maplibregl.GeoJSONSource | undefined;
    if (src) {
      src.setData({
        type: 'FeatureCollection',
        features: features,
      });
    }
  }, [assets]);

  // Update Selection Highlight and Fly-To
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('hotspots-circle')) {
      map.setPaintProperty('hotspots-circle', 'circle-radius', [
        'case',
        ['==', ['get', 'hotspot_id'], selectedHotspotId || ''],
        15,
        11,
      ]);
    }

    if (selectedHotspotId) {
      const selectedHs = hotspots.find((h) => h.hotspot_id === selectedHotspotId);
      if (selectedHs) {
        map.flyTo({
          center: [selectedHs.lng, selectedHs.lat],
          zoom: Math.max(map.getZoom(), 12.2),
          essential: true,
          duration: 900,
        });
      }
    }
  }, [selectedHotspotId, hotspots]);

  // Pulse Animation for Severe Hotspots
  useEffect(() => {
    const animatePulse = () => {
      const map = mapRef.current;
      if (map && map.isStyleLoaded() && map.getLayer('hotspots-pulse')) {
        if (pulseGrowingRef.current) {
          pulseRadiusRef.current += 0.25;
          if (pulseRadiusRef.current >= 26) pulseGrowingRef.current = false;
        } else {
          pulseRadiusRef.current -= 0.25;
          if (pulseRadiusRef.current <= 14) pulseGrowingRef.current = true;
        }

        const opacity = Math.max(0.1, 0.45 - (pulseRadiusRef.current - 14) / 30);

        map.setPaintProperty('hotspots-pulse', 'circle-radius', pulseRadiusRef.current);
        map.setPaintProperty('hotspots-pulse', 'circle-opacity', opacity);
      }

      animFrameIdRef.current = requestAnimationFrame(animatePulse);
    };

    animFrameIdRef.current = requestAnimationFrame(animatePulse);

    return () => {
      if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current);
    };
  }, []);

  // Rain Streak Canvas Overlay Animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = canvas.offsetWidth);
    let height = (canvas.height = canvas.offsetHeight);

    const onResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.offsetWidth;
      height = canvas.height = canvas.offsetHeight;
    };
    window.addEventListener('resize', onResize);

    const streakCount = Math.floor((rain3h / 100) * 140);
    const drops: Array<{ x: number; y: number; l: number; v: number }> = [];

    for (let i = 0; i < streakCount; i++) {
      drops.push({
        x: Math.random() * width,
        y: Math.random() * height,
        l: Math.random() * 16 + 10,
        v: Math.random() * 12 + 16,
      });
    }

    const drawRain = () => {
      ctx.clearRect(0, 0, width, height);

      if (streakCount > 0) {
        ctx.strokeStyle = 'rgba(29, 78, 216, 0.70)'; // subtle azure rain streaks
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        for (let i = 0; i < drops.length; i++) {
          const d = drops[i];
          ctx.moveTo(d.x, d.y);
          ctx.lineTo(d.x - d.l * 0.35, d.y + d.l);

          d.y += d.v;
          d.x -= d.v * 0.35;

          if (d.y > height) {
            d.y = -10;
            d.x = Math.random() * (width + 100);
          }
        }
        ctx.stroke();
      }

      animId = requestAnimationFrame(drawRain);
    };

    if (streakCount > 0) {
      animId = requestAnimationFrame(drawRain);
    } else {
      ctx.clearRect(0, 0, width, height);
    }

    return () => {
      window.removeEventListener('resize', onResize);
      if (animId) cancelAnimationFrame(animId);
    };
  }, [rain3h]);

  return (
    <div className="relative flex-1 h-full w-full overflow-hidden bg-[#eef2f6]">
      {/* Map Container */}
      <div ref={mapContainerRef} className="absolute inset-0 w-full h-full" />

      {/* Rain Canvas Overlay */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none z-10"
      />

      {/* Controls Overlay: Glass Floating Bar */}
      <div className="absolute top-4 left-4 z-20 flex flex-col space-y-2">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAssets(!showAssets)}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl text-xs font-semibold backdrop-blur-md border transition shadow-xs ${
              showAssets
                ? 'bg-white/95 text-slate-800 border-slate-300'
                : 'bg-white/75 text-slate-500 border-slate-200 hover:text-slate-800'
            }`}
          >
            {showAssets ? <Eye className="w-3.5 h-3.5 text-sky-600" /> : <EyeOff className="w-3.5 h-3.5" />}
            <span>{showAssets ? 'Ground Hazards Visible' : 'Ground Hazards Hidden'}</span>
          </button>

          {isFallbackStyle && (
            <div className="hidden sm:inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-xl text-[11px] font-medium bg-white/90 border border-slate-200 text-slate-600 backdrop-blur-md shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 mr-1" />
              <span>OpenStreetMap Silver Base</span>
            </div>
          )}
        </div>

        {isPickingLocation && (
          <div className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-[#0c192c] text-white shadow-lg animate-pulse border border-sky-400/50">
            <MapPin className="w-4 h-4 text-sky-400" />
            <span>Click on the map to pinpoint hazard coordinates</span>
          </div>
        )}
      </div>
    </div>
  );
};
