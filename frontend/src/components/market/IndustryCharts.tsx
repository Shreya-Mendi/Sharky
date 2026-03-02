"use client";

import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { Deal } from "@/lib/api";

interface Props {
  deals: Deal[];
}

const COLORS_PIE = ["#10b981", "#f43f5e"];

function getRevenueBucket(revenue: number): string {
  if (revenue === 0) return "$0";
  if (revenue <= 100_000) return "$1-100K";
  if (revenue <= 500_000) return "$100K-500K";
  if (revenue <= 1_000_000) return "$500K-1M";
  return "$1M+";
}

const BUCKET_ORDER = ["$0", "$1-100K", "$100K-500K", "$500K-1M", "$1M+"];

export default function IndustryCharts({ deals }: Props) {
  // Deal outcome data
  const dealCount = deals.filter((d) => d.has_deal).length;
  const noDealCount = deals.filter((d) => !d.has_deal).length;
  const pieData = [
    { name: "Deal", value: dealCount },
    { name: "No Deal", value: noDealCount },
  ];

  // Revenue distribution data
  const buckets: Record<string, number> = {};
  BUCKET_ORDER.forEach((b) => (buckets[b] = 0));
  deals.forEach((d) => {
    const bucket = getRevenueBucket(d.revenue);
    buckets[bucket] = (buckets[bucket] || 0) + 1;
  });
  const barData = BUCKET_ORDER.map((bucket) => ({
    bucket,
    count: buckets[bucket],
  }));

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      {/* Deal Outcome Pie Chart */}
      <div className="glass p-6">
        <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wide mb-4">
          Deal Outcomes
        </h3>
        {deals.length === 0 ? (
          <div className="text-white/30 text-center py-12">No deal data available</div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                dataKey="value"
                stroke="none"
                paddingAngle={2}
              >
                {pieData.map((_, idx) => (
                  <Cell key={idx} fill={COLORS_PIE[idx]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "rgba(15, 15, 25, 0.95)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: "10px",
                  color: "#fff",
                  fontSize: "13px",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
        <div className="flex justify-center gap-6 mt-2">
          <div className="flex items-center gap-2 text-sm">
            <span className="w-3 h-3 rounded-full bg-emerald-500" />
            <span className="text-white/60">Deal ({dealCount})</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="w-3 h-3 rounded-full bg-rose-500" />
            <span className="text-white/60">No Deal ({noDealCount})</span>
          </div>
        </div>
      </div>

      {/* Revenue Distribution Bar Chart */}
      <div className="glass p-6">
        <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wide mb-4">
          Revenue Distribution
        </h3>
        {deals.length === 0 ? (
          <div className="text-white/30 text-center py-12">No deal data available</div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={barData}>
              <XAxis
                dataKey="bucket"
                tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: "rgba(15, 15, 25, 0.95)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: "10px",
                  color: "#fff",
                  fontSize: "13px",
                }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
