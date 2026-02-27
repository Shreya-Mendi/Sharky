"use client";

import { useState } from "react";
import { Search } from "lucide-react";

export default function ComparablesTab() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleSearch() {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/comps`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: 10 }),
      });
      const data = await res.json();
      setResults(data.matches || []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Describe your pitch or company..."
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2"
        >
          <Search size={16} /> {loading ? "Searching..." : "Find Comps"}
        </button>
      </div>

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((r, i) => (
            <div key={i} className="glass p-5">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-blue-400 font-mono text-sm">{r.episode}</span>
                  <span className="mx-2 text-slate-600">·</span>
                  <span className="font-medium">{r.company_name || "Unknown"}</span>
                </div>
                {r.score && (
                  <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full">
                    {(r.score * 100).toFixed(0)}% match
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-400 mt-2 line-clamp-2">{r.text}</p>
              <span className="text-xs text-slate-500 mt-1 block">{r.segment_type}</span>
            </div>
          ))}
        </div>
      )}

      {results.length === 0 && !loading && (
        <p className="text-center text-slate-500 py-12">
          Search for comparable pitches using natural language. Requires API keys for vector search.
        </p>
      )}
    </div>
  );
}
