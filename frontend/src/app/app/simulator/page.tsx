"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, ArrowRight } from "lucide-react";
import StepCompany from "@/components/simulator/StepCompany";
import StepAsk from "@/components/simulator/StepAsk";
import StepTraction from "@/components/simulator/StepTraction";
import StepVerdict from "@/components/simulator/StepVerdict";
import { predictDeal, type PredictResponse } from "@/lib/api";

const STEPS = ["Your Company", "The Ask", "Your Traction", "The Verdict"];

export default function SimulatorPage() {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictResponse | null>(null);

  const [company, setCompany] = useState({ companyName: "", industry: "Food & Beverage", founderCount: 1 });
  const [ask, setAsk] = useState({ askAmount: 200000, equityPct: 10 });
  const [traction, setTraction] = useState({ revenue: 500000, confidence: 0.5, showAdvanced: false, objections: 0, negotiations: 0 });

  const canProceed = step === 0 ? company.companyName.length > 0 : true;

  async function handleSubmit() {
    setStep(3);
    setLoading(true);
    try {
      const res = await predictDeal({
        ask_amount: ask.askAmount,
        equity_offered_pct: ask.equityPct,
        revenue_trailing_12m: traction.revenue,
        industry: company.industry,
        founder_count: company.founderCount,
        pitch_sentiment_score: traction.confidence,
        objection_count: traction.objections,
        negotiation_rounds: traction.negotiations,
      });
      setResult(res);
    } catch (err) {
      console.error("Prediction failed:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-20">
      <div className="w-full max-w-2xl">
        {/* Progress Bar */}
        <div className="flex gap-2 mb-8">
          {STEPS.map((label, i) => (
            <div key={label} className="flex-1">
              <div className={`h-1 rounded-full transition-colors ${i <= step ? "bg-blue-500" : "bg-white/10"}`} />
              <span className={`text-xs mt-1 block ${i <= step ? "text-blue-400" : "text-slate-600"}`}>{label}</span>
            </div>
          ))}
        </div>

        {/* Step Title */}
        <h1 className="text-3xl font-bold mb-8">{STEPS[step]}</h1>

        {/* Step Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {step === 0 && <StepCompany data={company} onChange={(d) => setCompany({ ...company, ...d })} />}
            {step === 1 && <StepAsk data={ask} onChange={(d) => setAsk({ ...ask, ...d })} />}
            {step === 2 && <StepTraction data={traction} onChange={(d) => setTraction({ ...traction, ...d })} />}
            {step === 3 && <StepVerdict result={result} companyName={company.companyName} industry={company.industry} loading={loading} />}
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        {step < 3 && (
          <div className="flex justify-between mt-10">
            <button
              onClick={() => setStep(Math.max(0, step - 1))}
              disabled={step === 0}
              className="flex items-center gap-2 text-slate-400 hover:text-white disabled:opacity-30 transition-colors"
            >
              <ArrowLeft size={16} /> Back
            </button>

            {step < 2 ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={!canProceed}
                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-30 text-white px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2"
              >
                Next <ArrowRight size={16} />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3 rounded-xl font-semibold transition-all glow-blue flex items-center gap-2"
              >
                Get My Score <ArrowRight size={16} />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
