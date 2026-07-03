function ProgressBar({ label, value, color = "bg-indigo-500" }) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <span className="text-slate-400 font-medium">{label}</span>
        <span className="text-slate-300 font-semibold">{value}%</span>
      </div>
      <div className="h-2.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full animate-progress ${color}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  );
}

export default function ScoreBreakdown({ result }) {
  const expPct = Math.min(
    Math.round(
      (result.experience_years / Math.max(result.required_experience, 1)) * 100
    ),
    100
  );

  return (
    <div className="animate-fade-in-up glass rounded-xl p-6" style={{ animationDelay: "0.1s" }}>
      <h3 className="text-base font-semibold text-indigo-300 mb-5 flex items-center gap-2">
        <span className="w-1 h-5 bg-indigo-500 rounded-full inline-block" />
        Score Breakdown
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <ProgressBar
            label="Skill Coverage"
            value={result.skill_coverage_pct}
            color={result.skill_coverage_pct >= 70 ? "bg-green-500" : result.skill_coverage_pct >= 50 ? "bg-yellow-500" : "bg-red-500"}
          />
        </div>

        <div className="space-y-4">
          <ProgressBar
            label="ATS Composite"
            value={result.composite_score}
            color="bg-gradient-to-r from-indigo-500 to-purple-500"
          />
          <ProgressBar
            label={`Experience Fulfillment`}
            value={expPct}
            color={expPct >= 100 ? "bg-green-500" : expPct >= 60 ? "bg-yellow-500" : "bg-red-500"}
          />
        </div>
      </div>
    </div>
  );
}
