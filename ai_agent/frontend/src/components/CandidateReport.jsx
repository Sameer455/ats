import ScoreCards from "./ScoreCards";
import ScoreBreakdown from "./ScoreBreakdown";
import ResumeInsights from "./ResumeInsights";
import LLMAnalysis from "./LLMAnalysis";
import RawJson from "./RawJson";

export default function CandidateReport({ candidate, onBack }) {
  if (!candidate || !candidate.full_report) return null;

  const report = candidate.full_report;
  const scoreColor =
    candidate.composite_score >= 80
      ? "text-green-400"
      : candidate.composite_score >= 60
      ? "text-yellow-400"
      : "text-red-400";

  const fitStyles = {
    "Strong Fit": "bg-green-500/15 text-green-300 border-green-500/30",
    "Partial Fit": "bg-yellow-500/15 text-yellow-300 border-yellow-500/30",
    "Not a Fit": "bg-red-500/15 text-red-300 border-red-500/30",
  };

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Top bar: back button + candidate header */}
      <div className="glass rounded-xl p-5 border border-slate-700/50">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button
              id="candidate-back-btn"
              onClick={onBack}
              className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-indigo-300 border border-slate-700 hover:border-indigo-500/50 rounded-lg px-3 py-2 transition-all"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Results
            </button>

            <div>
              <div className="flex items-center gap-3">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-sm font-bold">
                  #{candidate.rank}
                </span>
                <h2 className="text-lg font-bold text-white">
                  {candidate.resume_filename}
                </h2>
              </div>
              <div className="flex items-center gap-3 mt-1.5 ml-11">
                <span className={`text-sm font-semibold ${scoreColor}`}>
                  Score: {Math.round(candidate.composite_score)}%
                </span>
                <span
                  className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium border ${
                    fitStyles[candidate.fit_category] || "bg-slate-500/15 text-slate-400 border-slate-500/30"
                  }`}
                >
                  {candidate.fit_category}
                </span>
                {candidate.risk_level && candidate.risk_level !== "Low" && (
                  <span className="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium border bg-orange-500/15 text-orange-300 border-orange-500/30">
                    Risk: {candidate.risk_level}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Quick stats */}
          <div className="flex gap-4 text-center">
            <div>
              <div className="text-lg font-bold text-green-400">
                {candidate.matched_skills?.length || 0}
              </div>
              <div className="text-[10px] uppercase tracking-wider text-slate-500">Matched</div>
            </div>
            <div>
              <div className="text-lg font-bold text-red-400">
                {candidate.missing_skills?.length || 0}
              </div>
              <div className="text-[10px] uppercase tracking-wider text-slate-500">Missing</div>
            </div>
            <div>
              <div className="text-lg font-bold text-indigo-400">
                {candidate.experience_years || 0}y
              </div>
              <div className="text-[10px] uppercase tracking-wider text-slate-500">Experience</div>
            </div>
          </div>
        </div>

        {/* Hiring recommendation */}
        {candidate.hiring_recommendation && (
          <div className="mt-4 pt-4 border-t border-slate-700/50">
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
              Hiring Recommendation
            </p>
            <p className="text-sm text-slate-300 leading-relaxed">
              {candidate.hiring_recommendation}
            </p>
          </div>
        )}
      </div>

      {/* Full analysis — reusing existing components */}
      <ScoreCards result={report} />
      <ScoreBreakdown result={report} />
      <ResumeInsights result={report} />
      <LLMAnalysis analysis={report.llm_analysis} />
      <RawJson result={report} />

      {/* Bottom back button */}
      <div className="pt-4 pb-4 flex justify-center">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl border border-slate-700 shadow-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <span className="font-medium">Back to Batch Results</span>
        </button>
      </div>
    </div>
  );
}
