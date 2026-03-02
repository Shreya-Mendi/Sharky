"use client";

import { useEffect, useState } from "react";
import { Database, TrendingUp, Target, Award } from "lucide-react";
import { fetchStats, fetchIndustries, fetchDeals } from "@/lib/api";
import type { Industry, Deal } from "@/lib/api";
import KPICard from "@/components/dashboard/KPICard";
import DealFlowChart from "@/components/dashboard/DealFlowChart";
import IndustryHeatmap from "@/components/dashboard/IndustryHeatmap";
import MarketPulse from "@/components/dashboard/MarketPulse";
import QuickActions from "@/components/dashboard/QuickActions";
import RecentDeals from "@/components/dashboard/RecentDeals";

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [recentDeals, setRecentDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchStats(),
      fetchIndustries(),
      fetchDeals({ limit: 5 }),
    ]).then(([s, ind, deals]) => {
      setStats(s);
      setIndustries(ind);
      setRecentDeals(deals.deals);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-pulse text-white/30 py-20 text-center">Loading dashboard...</div>;

  const totalDeals = stats?.total_pitches || 0;
  const avgRevenue = stats?.avg_revenue_mentioned || 0;
  const topIndustry = industries.length > 0
    ? industries.reduce((a, b) => a.deal_count > b.deal_count ? a : b).industry
    : "N/A";
  const successCount = industries.reduce((sum, i) => sum + Math.round(i.deal_count * i.success_rate), 0);
  const successRate = totalDeals > 0 ? ((successCount / totalDeals) * 100).toFixed(1) : "0";

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Total Deals" value={totalDeals.toLocaleString()} icon={Database} color="bg-blue-500/20 text-blue-400" />
        <KPICard label="Avg Revenue" value={`$${(avgRevenue / 1000).toFixed(0)}K`} icon={TrendingUp} color="bg-emerald-500/20 text-emerald-400" />
        <KPICard label="Success Rate" value={`${successRate}%`} icon={Target} color="bg-amber-500/20 text-amber-400" />
        <KPICard label="Top Industry" value={topIndustry} icon={Award} color="bg-purple-500/20 text-purple-400" />
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 space-y-6">
          <DealFlowChart seasons={stats?.seasons || []} />
          <IndustryHeatmap industries={industries} />
        </div>
        <div className="lg:col-span-2 space-y-6">
          <MarketPulse stats={stats} industries={industries} />
          <QuickActions />
          <RecentDeals deals={recentDeals} />
        </div>
      </div>
    </div>
  );
}
