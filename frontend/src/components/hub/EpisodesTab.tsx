"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, User } from "lucide-react";

interface EpisodesTabProps {
  episodes: Array<Record<string, any>>;
}

const segmentColors: Record<string, string> = {
  founder_pitch: "bg-blue-500",
  product_demo: "bg-purple-500",
  shark_questions: "bg-cyan-500",
  objections: "bg-rose-500",
  negotiation: "bg-amber-500",
  closing_reason: "bg-slate-500",
};

export default function EpisodesTab({ episodes }: EpisodesTabProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="space-y-3">
      {episodes.map((ep) => (
        <div key={ep.episode} className="glass overflow-hidden">
          <button
            onClick={() => setExpanded(expanded === ep.episode ? null : ep.episode)}
            className="w-full flex items-center justify-between px-6 py-4 hover:bg-white/5 transition-colors"
          >
            <div className="flex items-center gap-4">
              <span className="text-blue-400 font-mono font-bold">{ep.episode}</span>
              <span className="text-sm text-slate-400">{ep.pitch_count} pitches</span>
            </div>
            {expanded === ep.episode ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          <AnimatePresence>
            {expanded === ep.episode && (
              <motion.div
                initial={{ height: 0 }}
                animate={{ height: "auto" }}
                exit={{ height: 0 }}
                className="overflow-hidden"
              >
                <div className="px-6 pb-6 space-y-4 border-t border-white/5 pt-4">
                  {ep.pitches?.map((pitch: any, i: number) => (
                    <div key={i} className="bg-white/5 rounded-xl p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <User size={14} className="text-blue-400" />
                          <span className="font-medium">{pitch.entrepreneur_name}</span>
                        </div>
                        <div className="flex gap-2 text-xs">
                          <span className="bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full">
                            Revenue: ${(pitch.signals?.revenue_mentioned / 1000 || 0).toFixed(0)}K
                          </span>
                          <span className="bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded-full">
                            {pitch.signals?.objection_count || 0} objections
                          </span>
                        </div>
                      </div>

                      {/* Segment bar */}
                      <div className="flex gap-0.5 h-2 rounded-full overflow-hidden">
                        {Object.entries(segmentColors).map(([seg, color]) => {
                          const texts = pitch.segments?.[seg] || [];
                          if (texts.length === 0) return null;
                          return (
                            <div
                              key={seg}
                              className={`${color} flex-grow`}
                              style={{ flexGrow: texts.length }}
                              title={`${seg}: ${texts.length} blocks`}
                            />
                          );
                        })}
                      </div>
                      <div className="flex gap-3 mt-2 flex-wrap">
                        {Object.entries(segmentColors).map(([seg, color]) => {
                          const texts = pitch.segments?.[seg] || [];
                          if (texts.length === 0) return null;
                          return (
                            <span key={seg} className="text-xs text-slate-500 flex items-center gap-1">
                              <span className={`w-2 h-2 rounded-full ${color}`} />
                              {seg.replace("_", " ")}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  );
}
