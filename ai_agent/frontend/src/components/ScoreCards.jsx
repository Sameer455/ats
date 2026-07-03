function ScorePie({ score, size = 120 }) {
  const radius = size / 4;
  const strokeWidth = size / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const getColor = (s) => {
    if (s >= 70) return "#22c55e";
    if (s >= 50) return "#eab308";
    return "#ef4444";
  };

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90 rounded-full bg-slate-800/50 overflow-hidden shadow-inner">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor(score)}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="score-pie-circle"
          style={{ transition: "stroke-dashoffset 1.5s ease-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center drop-shadow-md">
        <span className="text-2xl font-extrabold text-white bg-slate-900/40 px-2 py-0.5 rounded backdrop-blur-sm">{score}%</span>
        <span className="text-[9px] uppercase tracking-widest text-white mt-1 bg-slate-900/40 px-1.5 py-0.5 rounded backdrop-blur-sm">ATS Score</span>
      </div>
    </div>
  );
}

function MetricCard({ value, label, suffix = "%", color }) {
  const colorClass = color || "text-indigo-300";
  return (
    <div className="glass rounded-xl p-5 text-center hover:scale-[1.03] transition-transform duration-300">
      <div className={`text-3xl font-bold ${colorClass}`}>
        {value}{suffix}
      </div>
      <div className="text-xs uppercase tracking-wide text-slate-400 mt-1.5">
        {label}
      </div>
    </div>
  );
}

function getScoreColor(score) {
  if (score >= 70) return "text-green-400";
  if (score >= 50) return "text-yellow-400";
  return "text-red-400";
}

export default function ScoreCards({ result }) {
  return (
    <div className="animate-fade-in-up">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 items-center">
        {/* Composite Score Pie Chart */}
        <div className="flex justify-center">
          <div className="glass rounded-2xl p-6 shadow-xl shadow-indigo-950/30">
            <ScorePie score={result.composite_score} />
          </div>
        </div>

        {/* Skill Coverage */}
        <MetricCard
          value={result.skill_coverage_pct}
          label="Skill Coverage"
          color={getScoreColor(result.skill_coverage_pct)}
        />

        {/* Experience - Clearly showing Required vs Actual */}
        <div className="glass rounded-xl p-5 text-center hover:scale-[1.03] transition-transform duration-300">
          <div className="flex items-center justify-center gap-3">
            <div className="text-right">
              <div className="text-xs text-slate-400 uppercase">Actual</div>
              <div className={`text-2xl font-bold ${result.experience_years >= result.required_experience ? "text-green-400" : "text-yellow-400"}`}>
                {result.experience_years}
              </div>
            </div>
            <div className="text-slate-600 text-2xl font-light">/</div>
            <div className="text-left">
              <div className="text-xs text-slate-400 uppercase">Required</div>
              <div className="text-2xl font-bold text-indigo-300">
                {result.required_experience || 0}
              </div>
            </div>
          </div>
          <div className="text-xs uppercase tracking-wide text-slate-400 mt-1.5">
            Years of Experience
          </div>
        </div>
      </div>
    </div>
  );
}
