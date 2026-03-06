"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Bot, ClipboardCheck, Globe2, TrendingUp, X } from "lucide-react";

const STORAGE_KEY = "dealscope_onboarded";

const steps = [
  {
    icon: TrendingUp,
    title: "Industry Intelligence Engine",
    href: "/app/market",
    description:
      "Pick an industry and risk profile. The engine maps sector-level success patterns — deal rates, objection pressure, founder confidence signals — from the full pitch corpus.",
    action: "Start with industry",
  },
  {
    icon: ClipboardCheck,
    title: "Startup Readiness Engine",
    href: "/app/simulator",
    description:
      "Enter your company's financials and profile. The engine benchmarks your readiness against top-performing peers and gives you a ranked US market recommendation.",
    action: "Benchmark your startup",
  },
  {
    icon: Globe2,
    title: "Market Fit Recommender",
    href: "/app/deals",
    description:
      "Describe your model and metrics. The engine ranks adjacent sectors, growth avenues, and US cities by fit confidence — with rationale drawn from the corpus.",
    action: "Find your market fit",
  },
  {
    icon: Bot,
    title: "Research Copilot",
    href: "/app/agent",
    description:
      "Ask anything in plain English. The copilot runs multiple research tools in sequence — corpus search, market stats, pattern analysis — and synthesises a strategy brief.",
    action: "Talk to the copilot",
  },
];

export default function OnboardingModal() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    const seen = localStorage.getItem(STORAGE_KEY);
    if (!seen) setOpen(true);
  }, []);

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, "1");
    setOpen(false);
  }

  const current = steps[step];
  const Icon = current.icon;
  const isLast = step === steps.length - 1;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center px-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={dismiss} />

          {/* Modal */}
          <motion.div
            className="relative z-10 w-full max-w-md rounded-2xl border border-white/15 bg-[#0f1015] shadow-2xl p-7"
            initial={{ scale: 0.94, opacity: 0, y: 16 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.94, opacity: 0, y: 16 }}
            transition={{ type: "spring", stiffness: 280, damping: 28 }}
          >
            <button
              onClick={dismiss}
              className="absolute top-4 right-4 text-white/30 hover:text-white/70 transition-colors"
            >
              <X size={18} />
            </button>

            {/* Step indicator */}
            <div className="flex gap-1.5 mb-6">
              {steps.map((_, i) => (
                <div
                  key={i}
                  className={`h-1 rounded-full transition-all duration-300 ${
                    i === step ? "bg-blue-500 w-6" : i < step ? "bg-white/30 w-4" : "bg-white/12 w-4"
                  }`}
                />
              ))}
            </div>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl border border-white/15 bg-white/5 flex items-center justify-center flex-shrink-0">
                <Icon size={20} className="text-[var(--accent-blue)]" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-muted)] mb-0.5">
                  Engine {step + 1} of {steps.length}
                </p>
                <h2 className="text-lg font-semibold leading-tight">{current.title}</h2>
              </div>
            </div>

            <p className="text-sm text-[var(--text-muted)] leading-relaxed">{current.description}</p>

            <div className="mt-6 flex items-center gap-3">
              <Link
                href={current.href}
                onClick={dismiss}
                className="flex items-center gap-2 rounded-xl bg-white text-black px-4 py-2.5 text-sm font-semibold hover:bg-white/90 transition-colors"
              >
                {current.action} <ArrowRight size={14} />
              </Link>

              {!isLast ? (
                <button
                  onClick={() => setStep((s) => s + 1)}
                  className="rounded-xl border border-white/20 px-4 py-2.5 text-sm hover:bg-white/5 transition-colors"
                >
                  Next
                </button>
              ) : (
                <button
                  onClick={dismiss}
                  className="rounded-xl border border-white/20 px-4 py-2.5 text-sm hover:bg-white/5 transition-colors"
                >
                  Get started
                </button>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
