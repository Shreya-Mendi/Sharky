"use client";

import { useEffect, useState } from "react";
import { fetchIndustries, fetchDeals } from "@/lib/api";
import type { Industry, Deal } from "@/lib/api";
import IndustrySelector from "@/components/market/IndustrySelector";
import IndustryMetrics from "@/components/market/IndustryMetrics";
import IndustryCharts from "@/components/market/IndustryCharts";
import IndustryBrief from "@/components/market/IndustryBrief";

export default function MarketPage() {
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [selected, setSelected] = useState("All Industries");
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchIndustries().then(setIndustries).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const industry = selected === "All Industries" ? undefined : selected;
    fetchDeals({ limit: 1000, industry }).then((r) => setDeals(r.deals));
  }, [selected]);

  if (loading) return <div className="animate-pulse text-white/30 py-20 text-center">Loading market data...</div>;

  const currentIndustry = selected === "All Industries"
    ? { industry: "All Industries", deal_count: industries.reduce((s, i) => s + i.deal_count, 0), success_rate: 0, avg_ask: 0, avg_revenue: 0, pitch_count: industries.reduce((s, i) => s + i.pitch_count, 0) }
    : industries.find(i => i.industry === selected) || industries[0];

  return (
    <div className="space-y-6">
      <IndustrySelector industries={industries} selected={selected} onSelect={setSelected} />
      <IndustryMetrics industry={currentIndustry} />
      <IndustryCharts deals={deals} />
      <IndustryBrief industry={currentIndustry} allIndustries={industries} />
    </div>
  );
}
