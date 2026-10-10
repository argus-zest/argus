import React from 'react';
import { X, Layers } from 'lucide-react';

interface ArchitectureModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ArchitectureModal: React.FC<ArchitectureModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm select-none">
      <div className="relative w-full max-w-5xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-100 shadow-2xs">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Argus System Architecture</h2>
              <p className="text-xs text-slate-500">AWS SAM Serverless &bull; Predict &amp; Enforce Dual Pipelines</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-800 p-1.5 rounded-lg hover:bg-slate-200/60 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content with Light-styled SVG Diagram */}
        <div className="p-6 overflow-y-auto flex-1 bg-slate-50/30">
          <div className="w-full bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs">
            <svg
              viewBox="0 0 960 520"
              className="w-full h-auto text-slate-800 font-sans"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              {/* Halves Dividers */}
              <rect x="20" y="30" width="445" height="460" rx="16" fill="#f8fafc" stroke="#0284c7" strokeWidth="1.5" strokeDasharray="4 4" />
              <rect x="495" y="30" width="445" height="460" rx="16" fill="#f8fafc" stroke="#e11d48" strokeWidth="1.5" strokeDasharray="4 4" />

              {/* Halves Badges */}
              <text x="40" y="60" fill="#0369a1" fontSize="15" fontWeight="bold">PREDICT PIPELINE (Risk &amp; Basemap)</text>
              <text x="515" y="60" fill="#be123c" fontSize="15" fontWeight="bold">ENFORCE PIPELINE (Hazard &amp; Escalation)</text>

              {/* Client Box */}
              <rect x="360" y="90" width="240" height="52" rx="10" fill="#ffffff" stroke="#0284c7" strokeWidth="2" />
              <text x="480" y="115" fill="#0f172a" fontSize="14" fontWeight="bold" textAnchor="middle">Browser / AWS Amplify</text>
              <text x="480" y="132" fill="#475569" fontSize="11" textAnchor="middle">React 18 + Vite + MapLibre GL</text>

              {/* Amazon Location */}
              <rect x="60" y="90" width="200" height="52" rx="10" fill="#ffffff" stroke="#0284c7" strokeWidth="1.5" />
              <text x="160" y="115" fill="#0f172a" fontSize="13" fontWeight="bold" textAnchor="middle">Amazon Location Service</text>
              <text x="160" y="132" fill="#64748b" fontSize="11" textAnchor="middle">Standard Dark / Light Vector Tiles</text>

              {/* Arrow Client <-> Location */}
              <path d="M 360 115 L 260 115" stroke="#0284c7" strokeWidth="2" strokeDasharray="3 3" markerEnd="url(#arrow)" />

              {/* API Gateway */}
              <rect x="370" y="180" width="220" height="48" rx="10" fill="#0284c7" stroke="#0369a1" strokeWidth="1.5" />
              <text x="480" y="203" fill="#ffffff" fontSize="14" fontWeight="bold" textAnchor="middle">Amazon API Gateway</text>
              <text x="480" y="219" fill="#e0f2fe" fontSize="11" textAnchor="middle">HTTP API v2 (/v1/*)</text>

              {/* Arrow Client -> API Gateway */}
              <path d="M 480 142 L 480 180" stroke="#0284c7" strokeWidth="2" markerEnd="url(#arrow)" />

              {/* PREDICT SIDE */}
              {/* EventBridge */}
              <rect x="50" y="180" width="160" height="48" rx="10" fill="#ffffff" stroke="#64748b" strokeWidth="1.5" />
              <text x="130" y="203" fill="#0f172a" fontSize="12" fontWeight="bold" textAnchor="middle">Amazon EventBridge</text>
              <text x="130" y="219" fill="#64748b" fontSize="10" textAnchor="middle">Hourly Schedule Rule</text>

              {/* Scheduled Scoring Lambda */}
              <rect x="50" y="260" width="160" height="52" rx="10" fill="#ffffff" stroke="#ca8a04" strokeWidth="1.5" />
              <text x="130" y="283" fill="#0f172a" fontSize="12" fontWeight="bold" textAnchor="middle">scheduled_score Lambda</text>
              <text x="130" y="300" fill="#a16207" fontSize="10" textAnchor="middle">Open-Meteo &rarr; S3 Export</text>

              <path d="M 130 228 L 130 260" stroke="#94a3b8" strokeWidth="1.5" markerEnd="url(#arrow)" />

              {/* Risk / Hotspots Lambdas */}
              <rect x="250" y="260" width="180" height="52" rx="10" fill="#ffffff" stroke="#0284c7" strokeWidth="1.5" />
              <text x="340" y="283" fill="#0f172a" fontSize="12" fontWeight="bold" textAnchor="middle">Hotspots &amp; Risk Lambdas</text>
              <text x="340" y="300" fill="#64748b" fontSize="10" textAnchor="middle">Heuristic Susceptibility Core</text>

              <path d="M 430 228 L 360 260" stroke="#0284c7" strokeWidth="1.5" markerEnd="url(#arrow)" />

              {/* S3 Storage */}
              <rect x="140" y="370" width="180" height="62" rx="10" fill="#ffffff" stroke="#16a34a" strokeWidth="1.5" />
              <text x="230" y="395" fill="#0f172a" fontSize="13" fontWeight="bold" textAnchor="middle">Amazon S3 Bucket</text>
              <text x="230" y="412" fill="#15803d" fontSize="10" textAnchor="middle">uploads/ &bull; exports/ &bull; eval/</text>

              <path d="M 130 312 L 190 370" stroke="#94a3b8" strokeWidth="1.5" markerEnd="url(#arrow)" />
              <path d="M 330 312 L 260 370" stroke="#94a3b8" strokeWidth="1.5" markerEnd="url(#arrow)" />

              {/* ENFORCE SIDE */}
              {/* Vision / Analysis Lambdas */}
              <rect x="520" y="260" width="180" height="52" rx="10" fill="#ffffff" stroke="#e11d48" strokeWidth="1.5" />
              <text x="610" y="283" fill="#0f172a" fontSize="12" fontWeight="bold" textAnchor="middle">analyze &amp; presign Lambdas</text>
              <text x="610" y="300" fill="#be123c" fontSize="10" textAnchor="middle">Uploads &amp; Hazard Inspection</text>

              <path d="M 510 228 L 580 260" stroke="#0284c7" strokeWidth="1.5" markerEnd="url(#arrow)" />

              {/* Amazon Bedrock */}
              <rect x="730" y="260" width="190" height="52" rx="10" fill="#fff1f2" stroke="#e11d48" strokeWidth="2" />
              <text x="825" y="283" fill="#881337" fontSize="13" fontWeight="bold" textAnchor="middle">Amazon Bedrock</text>
              <text x="825" y="300" fill="#be123c" fontSize="10" textAnchor="middle">Amazon Nova 2 Lite (Converse)</text>

              <path d="M 700 286 L 730 286" stroke="#e11d48" strokeWidth="1.5" markerEnd="url(#arrow)" />

              {/* Cases & DynamoDB */}
              <rect x="510" y="340" width="190" height="62" rx="10" fill="#ffffff" stroke="#9333ea" strokeWidth="1.5" />
              <text x="605" y="365" fill="#0f172a" fontSize="13" fontWeight="bold" textAnchor="middle">Amazon DynamoDB</text>
              <text x="605" y="382" fill="#7e22ce" fontSize="10" textAnchor="middle">Cases &bull; CaseEvents &bull; Assets</text>

              {/* Step Functions State Machine */}
              <rect x="730" y="340" width="190" height="62" rx="10" fill="#ffffff" stroke="#d97706" strokeWidth="1.5" />
              <text x="825" y="365" fill="#0f172a" fontSize="13" fontWeight="bold" textAnchor="middle">AWS Step Functions</text>
              <text x="825" y="382" fill="#b45309" fontSize="10" textAnchor="middle">4-Rung Escalation Flow</text>

              <path d="M 610 312 L 610 340" stroke="#94a3b8" strokeWidth="1.5" markerEnd="url(#arrow)" />
              <path d="M 700 371 L 730 371" stroke="#d97706" strokeWidth="1.5" markerEnd="url(#arrow)" />

              {/* Strands Notice Agent & SES */}
              <rect x="620" y="425" width="280" height="52" rx="10" fill="#ffffff" stroke="#64748b" strokeWidth="1.5" />
              <text x="760" y="448" fill="#0f172a" fontSize="12" fontWeight="bold" textAnchor="middle">Strands Notice Agent &rarr; Amazon SES</text>
              <text x="760" y="464" fill="#64748b" fontSize="10" textAnchor="middle">[DRY-RUN] Complaint Dispatch to Sandbox</text>

              <path d="M 825 402 L 825 425" stroke="#d97706" strokeWidth="1.5" markerEnd="url(#arrow)" />

              {/* Arrow Definitions */}
              <defs>
                <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 10 5 L 0 9 z" fill="#0284c7" />
                </marker>
              </defs>
            </svg>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-4 text-xs text-slate-700">
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-2xs">
              <span className="font-bold text-sky-700 text-sm block mb-1">Predict Pipeline</span>
              Open-Meteo elevation contours, 90m surface depression calculations, and live rainfall forecasts feed the calibrated logistic susceptibility model. Scores are cached to Amazon S3 and delivered via HTTP API to MapLibre GL.
            </div>
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-2xs">
              <span className="font-bold text-rose-700 text-sm block mb-1">Enforce Pipeline</span>
              Citizen reports are vision-inspected by Amazon Nova 2 Lite, resolved against official road records, and tracked through a 4-rung Step Functions workflow with automated SES dry-run notices.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
