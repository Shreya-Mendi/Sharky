"use client";

import { usePathname } from "next/navigation";
import { Bell, Search } from "lucide-react";
import ThemeToggle from "@/components/theme/ThemeToggle";

const PAGE_TITLES: Record<string, string> = {
  "/app": "Engine Hub",
  "/app/market": "Industry Intelligence Engine",
  "/app/simulator": "Startup Readiness Engine",
  "/app/agent": "Research Copilot",
  "/app/deals": "Market Fit Recommender",
  "/app/settings": "Settings & Integrations",
};

export default function AppTopBar() {
  const pathname = usePathname();
  const title = PAGE_TITLES[pathname] || "DealScope";

  return (
    <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-[var(--bg-primary)]/70 backdrop-blur-xl sticky top-0 z-30">
      <h1 className="text-lg font-semibold">{title}</h1>
      <div className="flex items-center gap-4">
        <div className="relative hidden md:block">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
          <input
            type="text"
            placeholder="Search sectors, signals..."
            className="bg-black/20 border border-white/12 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-blue-400/50 w-72"
          />
        </div>
        <button className="w-9 h-9 rounded-lg bg-black/25 border border-white/10 flex items-center justify-center text-white/40 hover:text-white/70 transition-colors">
          <Bell size={18} />
        </button>
        <ThemeToggle />
      </div>
    </header>
  );
}
