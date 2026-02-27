"use client";

import { useState, useEffect } from "react";
import { BarChart3, Tv, Search } from "lucide-react";
import AnalyticsTab from "@/components/hub/AnalyticsTab";
import EpisodesTab from "@/components/hub/EpisodesTab";
import ComparablesTab from "@/components/hub/ComparablesTab";
import { fetchEpisodes, fetchStats, fetchPitches } from "@/lib/api";

const tabs = [
  { key: "analytics", label: "Analytics", icon: BarChart3 },
  { key: "episodes", label: "Episodes", icon: Tv },
  { key: "comps", label: "Comparables", icon: Search },
];

export default function HubPage() {
  const [activeTab, setActiveTab] = useState("analytics");
  const [episodes, setEpisodes] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [pitches, setPitches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [episodeData, statsData, pitchData] = await Promise.all([
          fetchEpisodes(),
          fetchStats(),
          fetchPitches(9999, 0),
        ]);
        setEpisodes(episodeData);
        setStats(statsData);
        setPitches(pitchData.pitches || []);
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-slate-400 animate-pulse text-lg">Loading intelligence data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-6 py-20">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Intelligence Hub</h1>
        <p className="text-slate-400 mb-8">Explore patterns and facts across {stats?.total_episodes || 0} episodes</p>

        {/* Tabs */}
        <div className="flex gap-1 mb-8 bg-white/5 rounded-xl p-1 w-fit">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === key ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              <Icon size={16} /> {label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "analytics" && <AnalyticsTab pitches={pitches} stats={stats} />}
        {activeTab === "episodes" && <EpisodesTab episodes={episodes} />}
        {activeTab === "comps" && <ComparablesTab />}
      </div>
    </div>
  );
}
