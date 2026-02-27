"use client";

interface StepTractionProps {
  data: { revenue: number; confidence: number; showAdvanced: boolean; objections: number; negotiations: number };
  onChange: (data: Partial<StepTractionProps["data"]>) => void;
}

function formatCurrency(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  return `$${(n / 1000).toFixed(0)}K`;
}

export default function StepTraction({ data, onChange }: StepTractionProps) {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex justify-between mb-2">
          <label className="text-sm text-slate-400">Trailing 12-Month Revenue</label>
          <span className="text-lg font-bold text-white">{formatCurrency(data.revenue)}</span>
        </div>
        <input
          type="range"
          min={0} max={10000000} step={50000}
          value={data.revenue}
          onChange={(e) => onChange({ revenue: Number(e.target.value) })}
          className="w-full accent-blue-500"
        />
      </div>

      <div>
        <div className="flex justify-between mb-2">
          <label className="text-sm text-slate-400">Founder Confidence</label>
          <span className="text-lg font-bold text-white">{((data.confidence + 1) / 2 * 100).toFixed(0)}%</span>
        </div>
        <input
          type="range"
          min={-100} max={100} step={1}
          value={data.confidence * 100}
          onChange={(e) => onChange({ confidence: Number(e.target.value) / 100 })}
          className="w-full accent-blue-500"
        />
      </div>

      <button
        onClick={() => onChange({ showAdvanced: !data.showAdvanced })}
        className="text-blue-400 text-sm hover:text-blue-300"
      >
        {data.showAdvanced ? "Hide" : "Show"} advanced options
      </button>

      {data.showAdvanced && (
        <div className="space-y-6 pt-4 border-t border-white/10">
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm text-slate-400">Expected Objections</label>
              <span className="font-bold">{data.objections}</span>
            </div>
            <input
              type="range" min={0} max={10} step={1}
              value={data.objections}
              onChange={(e) => onChange({ objections: Number(e.target.value) })}
              className="w-full accent-amber-500"
            />
          </div>
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm text-slate-400">Negotiation Rounds</label>
              <span className="font-bold">{data.negotiations}</span>
            </div>
            <input
              type="range" min={0} max={8} step={1}
              value={data.negotiations}
              onChange={(e) => onChange({ negotiations: Number(e.target.value) })}
              className="w-full accent-amber-500"
            />
          </div>
        </div>
      )}
    </div>
  );
}
