"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, CheckCircle, AlertTriangle } from "lucide-react";
import DealScoreGauge from "@/components/ui/DealScoreGauge";
import type { PredictResponse } from "@/lib/api";

interface StepVerdictProps {
  result: PredictResponse | null;
  companyName: string;
  industry: string;
  loading: boolean;
}

export default function StepVerdict({ result, companyName, industry, loading }: StepVerdictProps) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <motion.div
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="text-2xl font-bold text-slate-400"
        >
          Analyzing your pitch...
        </motion.div>
      </div>
    );
  }

  if (!result) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3 }}
      className="space-y-8"
    >
      <div className="flex flex-col items-center py-8">
        <DealScoreGauge score={result.deal_score} size={160} />
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.5 }}
          className="text-center mt-4"
        >
          <span className="text-4xl font-bold">{(result.deal_probability * 100).toFixed(1)}%</span>
          <span className="text-slate-400 block text-sm mt-1">Deal Probability</span>
        </motion.div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {result.strengths.length > 0 && (
          <div className="glass p-6">
            <h3 className="text-emerald-400 font-semibold mb-3 flex items-center gap-2">
              <CheckCircle size={18} /> Strengths
            </h3>
            <ul className="space-y-2">
              {result.strengths.map((s, i) => (
                <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">•</span> {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {result.risks.length > 0 && (
          <div className="glass p-6">
            <h3 className="text-amber-400 font-semibold mb-3 flex items-center gap-2">
              <AlertTriangle size={18} /> Risks
            </h3>
            <ul className="space-y-2">
              {result.risks.map((r, i) => (
                <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                  <span className="text-amber-400 mt-0.5">•</span> {r}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="flex gap-4 justify-center pt-4">
        <Link
          href={`/chat?context=${encodeURIComponent(`I just simulated a pitch for ${companyName} in ${industry}. Deal score was ${result.deal_score}/10. What should I know?`)}`}
          className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-medium transition-all glow-blue flex items-center gap-2"
        >
          Ask SharkBot for Advice <ArrowRight size={16} />
        </Link>
        <Link
          href="/hub"
          className="border border-white/20 hover:border-white/40 text-white px-6 py-3 rounded-xl font-medium transition-all"
        >
          See Comparable Deals
        </Link>
      </div>
    </motion.div>
  );
}
