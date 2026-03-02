"use client";

import { Search } from "lucide-react";

interface Filters {
  industry: string;
  has_deal: boolean | undefined;
  search: string;
}

interface Props {
  filters: Filters;
  onChange: (filters: Filters) => void;
  industries: Array<{ industry: string }>;
}

export default function DealsFilters({ filters, onChange, industries }: Props) {
  return (
    <div className="glass p-4">
      <div className="flex flex-wrap items-center gap-4">
        {/* Industry dropdown */}
        <select
          value={filters.industry}
          onChange={(e) => onChange({ ...filters, industry: e.target.value })}
          className="bg-white/5 border border-white/10 text-white rounded-lg text-sm px-3 py-2 focus:outline-none focus:border-blue-500 transition-colors"
        >
          <option value="">All Industries</option>
          {industries.map((ind) => (
            <option key={ind.industry} value={ind.industry}>
              {ind.industry}
            </option>
          ))}
        </select>

        {/* Outcome toggle pills */}
        <div className="flex rounded-lg overflow-hidden border border-white/10">
          <button
            onClick={() => onChange({ ...filters, has_deal: undefined })}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              filters.has_deal === undefined
                ? "bg-blue-600 text-white"
                : "bg-white/5 text-white/60 hover:text-white/80"
            }`}
          >
            All
          </button>
          <button
            onClick={() => onChange({ ...filters, has_deal: true })}
            className={`px-4 py-2 text-sm font-medium transition-colors border-l border-white/10 ${
              filters.has_deal === true
                ? "bg-blue-600 text-white"
                : "bg-white/5 text-white/60 hover:text-white/80"
            }`}
          >
            Got Deal
          </button>
          <button
            onClick={() => onChange({ ...filters, has_deal: false })}
            className={`px-4 py-2 text-sm font-medium transition-colors border-l border-white/10 ${
              filters.has_deal === false
                ? "bg-blue-600 text-white"
                : "bg-white/5 text-white/60 hover:text-white/80"
            }`}
          >
            No Deal
          </button>
        </div>

        {/* Search input */}
        <div className="relative flex-1 min-w-[200px]">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30"
          />
          <input
            type="text"
            value={filters.search}
            onChange={(e) => onChange({ ...filters, search: e.target.value })}
            placeholder="Search companies..."
            className="w-full bg-white/5 border border-white/10 text-white rounded-lg text-sm pl-9 pr-3 py-2 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>
      </div>
    </div>
  );
}
