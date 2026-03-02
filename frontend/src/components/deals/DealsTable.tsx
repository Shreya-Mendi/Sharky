"use client";

import { useState, useMemo } from "react";
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";
import type { Deal } from "@/lib/api";

const PAGE_SIZE = 25;

type SortKey = keyof Deal;
type SortDir = "asc" | "desc";

interface Props {
  deals: Deal[];
  total: number;
  page: number;
  onPageChange: (page: number) => void;
  loading?: boolean;
}

function formatRevenue(revenue: number): string {
  if (revenue >= 1_000_000) return `$${(revenue / 1_000_000).toFixed(1)}M`;
  if (revenue >= 1_000) return `$${(revenue / 1_000).toFixed(0)}K`;
  return `$${revenue.toLocaleString()}`;
}

const COLUMNS: { key: SortKey; label: string; className?: string }[] = [
  { key: "company_name", label: "Company" },
  { key: "industry", label: "Industry" },
  { key: "season", label: "Season" },
  { key: "revenue", label: "Revenue", className: "text-right" },
  { key: "objection_count", label: "Objections", className: "text-right" },
  { key: "founder_confidence", label: "Confidence", className: "text-right" },
  { key: "has_deal", label: "Outcome", className: "text-center" },
];

export default function DealsTable({ deals, total, page, onPageChange, loading }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("company_name");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  const sortedDeals = useMemo(() => {
    const sorted = [...deals].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDir === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      if (typeof aVal === "boolean" && typeof bVal === "boolean") {
        const aNum = aVal ? 1 : 0;
        const bNum = bVal ? 1 : 0;
        return sortDir === "asc" ? aNum - bNum : bNum - aNum;
      }

      const aNum = Number(aVal) || 0;
      const bNum = Number(bVal) || 0;
      return sortDir === "asc" ? aNum - bNum : bNum - aNum;
    });
    return sorted;
  }, [deals, sortKey, sortDir]);

  function SortIcon({ columnKey }: { columnKey: SortKey }) {
    if (sortKey !== columnKey) {
      return (
        <span className="inline-flex flex-col ml-1 opacity-30">
          <ChevronUp size={12} />
          <ChevronDown size={12} className="-mt-1" />
        </span>
      );
    }
    return sortDir === "asc" ? (
      <ChevronUp size={14} className="inline ml-1 text-blue-400" />
    ) : (
      <ChevronDown size={14} className="inline ml-1 text-blue-400" />
    );
  }

  return (
    <div className="glass p-0 overflow-hidden relative">
      {/* Loading overlay */}
      {loading && (
        <div className="absolute inset-0 bg-black/40 backdrop-blur-sm z-10 flex items-center justify-center">
          <span className="text-white/60 text-sm animate-pulse">Loading...</span>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-white/[0.02]">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={`px-4 py-3 text-left text-xs font-semibold text-white/50 uppercase tracking-wider cursor-pointer select-none hover:text-white/70 transition-colors ${
                    col.className || ""
                  }`}
                >
                  <span className="inline-flex items-center">
                    {col.label}
                    <SortIcon columnKey={col.key} />
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedDeals.length === 0 && !loading ? (
              <tr>
                <td
                  colSpan={COLUMNS.length}
                  className="px-4 py-12 text-center text-white/30"
                >
                  No deals found.
                </td>
              </tr>
            ) : (
              sortedDeals.map((deal, i) => (
                <tr
                  key={`${deal.episode}-${deal.company_name}-${i}`}
                  className="border-b border-white/[0.06] hover:bg-white/[0.04] transition-colors"
                >
                  <td className="px-4 py-3 font-medium text-white">
                    {deal.company_name}
                  </td>
                  <td className="px-4 py-3 text-white/60">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-white/10">
                      {deal.industry}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-white/60">{deal.season}</td>
                  <td className="px-4 py-3 text-white/60 text-right font-mono">
                    {formatRevenue(deal.revenue)}
                  </td>
                  <td className="px-4 py-3 text-white/60 text-right">
                    {deal.objection_count}
                  </td>
                  <td className="px-4 py-3 text-white/60 text-right">
                    {(deal.founder_confidence * 100).toFixed(0)}%
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                        deal.has_deal
                          ? "bg-emerald-500/20 text-emerald-400"
                          : "bg-white/10 text-white/40"
                      }`}
                    >
                      {deal.has_deal ? "Deal" : "No Deal"}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-white/[0.06]">
        <span className="text-sm text-white/40">
          {total > 0
            ? `Showing ${page * PAGE_SIZE + 1}–${Math.min((page + 1) * PAGE_SIZE, total)} of ${total}`
            : "No results"}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 0}
            className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg bg-white/5 text-white/60 hover:bg-white/10 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={14} />
            Previous
          </button>
          <span className="text-sm text-white/50 px-2">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages - 1}
            className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg bg-white/5 text-white/60 hover:bg-white/10 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Next
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
