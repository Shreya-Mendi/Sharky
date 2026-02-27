"use client";

import { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

interface AnalyticsTabProps {
  pitches: Array<Record<string, any>>;
  stats: Record<string, any> | null;
}

export default function AnalyticsTab({ pitches, stats }: AnalyticsTabProps) {
  const seasonData = useMemo(() => {
    return stats?.seasons?.map((s: any) => ({
      name: s.season,
      pitches: s.pitch_count,
      episodes: s.episode_count,
    })) || [];
  }, [stats]);

  const signalDistribution = useMemo(() => {
    const buckets: Record<string, { total: number; count: number }> = {};
    for (const p of pitches) {
      const objections = p.signals?.objection_count ?? 0;
      const bucket = objections <= 1 ? "0-1" : objections <= 3 ? "2-3" : objections <= 5 ? "4-5" : "6+";
      if (!buckets[bucket]) buckets[bucket] = { total: 0, count: 0 };
      buckets[bucket].count++;
    }
    return ["0-1", "2-3", "4-5", "6+"].map((b) => ({ name: `${b} objections`, count: buckets[b]?.count || 0 }));
  }, [pitches]);

  return (
    <div className="space-y-8">
      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Pitches", value: stats?.total_pitches?.toLocaleString() ?? "—" },
          { label: "Total Episodes", value: stats?.total_episodes?.toLocaleString() ?? "—" },
          { label: "Avg Revenue Cited", value: stats ? `$${(stats.avg_revenue_mentioned / 1000).toFixed(0)}K` : "—" },
          { label: "Avg Confidence", value: stats ? `${(stats.avg_founder_confidence * 100).toFixed(1)}%` : "—" },
        ].map(({ label, value }) => (
          <div key={label} className="glass p-6 text-center">
            <div className="text-2xl font-bold text-white">{value}</div>
            <div className="text-xs text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="glass p-6">
          <h3 className="text-sm font-semibold text-slate-400 mb-4">Pitches by Season</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={seasonData}>
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} />
              <Bar dataKey="pitches" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass p-6">
          <h3 className="text-sm font-semibold text-slate-400 mb-4">Objection Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={signalDistribution}>
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} />
              <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
