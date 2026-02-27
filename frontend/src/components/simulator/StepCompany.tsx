"use client";

interface StepCompanyProps {
  data: { companyName: string; industry: string; founderCount: number };
  onChange: (data: Partial<StepCompanyProps["data"]>) => void;
}

const industries = [
  "Food & Beverage", "Technology", "Health & Wellness", "Fashion & Beauty",
  "Home & Garden", "Children & Education", "Fitness & Sports", "Entertainment",
  "Automotive", "Pet Products", "Other",
];

export default function StepCompany({ data, onChange }: StepCompanyProps) {
  return (
    <div className="space-y-8">
      <div>
        <label className="block text-sm text-slate-400 mb-2">Company Name</label>
        <input
          type="text"
          value={data.companyName}
          onChange={(e) => onChange({ companyName: e.target.value })}
          placeholder="Enter your company name"
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
        />
      </div>

      <div>
        <label className="block text-sm text-slate-400 mb-2">Industry</label>
        <select
          value={data.industry}
          onChange={(e) => onChange({ industry: e.target.value })}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-colors"
        >
          {industries.map((ind) => (
            <option key={ind} value={ind} className="bg-slate-900">{ind}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm text-slate-400 mb-2">Number of Founders</label>
        <div className="flex gap-3">
          {[1, 2, 3, 4].map((n) => (
            <button
              key={n}
              onClick={() => onChange({ founderCount: n })}
              className={`w-14 h-14 rounded-xl font-bold text-lg transition-all ${
                data.founderCount === n
                  ? "bg-blue-600 text-white glow-blue"
                  : "bg-white/5 text-slate-400 hover:bg-white/10"
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
