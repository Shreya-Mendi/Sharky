"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface Season {
  season: string;
  pitch_count: number;
  episode_count: number;
}

interface Props {
  seasons: Season[];
}

export default function DealFlowChart({ seasons }: Props) {
  const data = seasons.map((s) => ({
    name: s.season,
    pitches: s.pitch_count,
    episodes: s.episode_count,
  }));

  return (
    <div className="glass p-5">
      <h3 className="text-sm font-semibold text-white/50 mb-4">Deal Flow by Season</h3>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorPitches" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey="name"
            tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 12 }}
            axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 12 }}
            axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "#1e293b",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 8,
              color: "#fff",
            }}
          />
          <Area
            type="monotone"
            dataKey="pitches"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#colorPitches)"
            name="Pitches"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
