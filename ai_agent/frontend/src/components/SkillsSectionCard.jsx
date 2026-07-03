import ScoreBadge from "./ScoreBadge";

function DetailedPill({ skill, detail, variant }) {
  const styles = {
    matched: "bg-green-500/10 border-green-500/30",
    missing: "bg-red-500/10 border-red-500/30",
    extra: "bg-cyan-500/10 border-cyan-500/30",
  };
  
  const textStyles = {
    matched: "text-green-300",
    missing: "text-red-300",
    extra: "text-cyan-300",
  };

  const isExact = detail?.method === "exact" || detail?.method === "fuzzy_fastpath" || detail?.method === "fuzzy_match";

  return (
    <div className={`rounded-lg border px-3 py-2.5 text-xs ${styles[variant]} flex flex-col hover:bg-opacity-20 transition-all`}>
      <span className={`font-bold ${textStyles[variant]}`}>{skill}</span>
      {detail && detail.matched_to && (
        <div className="mt-1 flex items-center justify-between text-[10px] opacity-80">
          <span className="truncate mr-2">
            {isExact ? "Exact Match" : `↳ "${detail.matched_to}"`}
          </span>
          {detail.confidence && (
            <span className="shrink-0 bg-black/20 px-1.5 py-0.5 rounded">
              {detail.confidence}%
            </span>
          )}
        </div>
      )}
      {detail && !detail.matched_to && (
        <span className="mt-1 text-[10px] opacity-70">
          Not found in resume
        </span>
      )}
    </div>
  );
}

function DetailedPillGroup({ title, icon, skills, variant, emptyText, matchDetails }) {
  return (
    <div className="space-y-3">
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
        <span>{icon}</span>{title}
        <span className="text-slate-600 font-normal normal-case tracking-normal">({skills?.length ?? 0})</span>
      </p>
      <div className="flex flex-col gap-2 min-h-[28px]">
        {skills && skills.length > 0
          ? skills.map((s, i) => {
              const detail = matchDetails?.find(d => d.jd_skill.toLowerCase() === s.toLowerCase());
              return <DetailedPill key={i} skill={s} detail={detail} variant={variant} />
            })
          : <div className="rounded-lg border border-slate-700/50 bg-slate-800/30 px-3 py-2.5 text-xs text-slate-500 italic">
              {emptyText}
            </div>
        }
      </div>
    </div>
  );
}

export default function SkillsSectionCard({ result }) {
  const score = result?.section_scores?.skills;
  const details = result?.match_details || [];

  return (
    <div className="glass rounded-2xl p-6 border border-slate-700/50 shadow-xl animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-base">
            🛠
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Skills Analysis</h3>
            <p className="text-[11px] text-slate-500">Deep AI mapping of resume vs JD</p>
          </div>
        </div>
        <ScoreBadge score={score} />
      </div>

      {/* Skill coverage progress bar */}
      <div className="mb-6 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex justify-between text-xs text-slate-400 mb-2">
          <span>Skill Coverage</span>
          <span className="font-bold text-slate-300">{result.skill_coverage_pct}%</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-1000 ${
              result.skill_coverage_pct >= 70 ? "bg-green-500" :
              result.skill_coverage_pct >= 50 ? "bg-yellow-500" : "bg-red-500"
            }`}
            style={{ width: `${Math.min(result.skill_coverage_pct, 100)}%` }}
          />
        </div>
        
        {/* Optional method summary stats if available */}
        {result.match_method_summary && result.match_method_summary.total_jd_skills > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-800 flex justify-between text-[10px] text-slate-500">
            <span>Fast Match: {result.match_method_summary.fuzzy_fastpath_count}</span>
            <span>Semantic: {result.match_method_summary.hybrid_count + result.match_method_summary.embedding_primary_count}</span>
            <span>Unmatched: {result.match_method_summary.unmatched_count}</span>
          </div>
        )}
      </div>

      {/* Skill groups */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <DetailedPillGroup
          title="Matched"
          icon="✅"
          skills={result.matched_skills}
          matchDetails={details}
          variant="matched"
          emptyText="No matches found"
        />
        <DetailedPillGroup
          title="Missing from JD"
          icon="❌"
          skills={result.missing_skills}
          matchDetails={details}
          variant="missing"
          emptyText="All skills matched!"
        />
        <DetailedPillGroup
          title="Additional Skills"
          icon="➕"
          skills={result.extra_skills}
          matchDetails={[]}
          variant="extra"
          emptyText="No extras"
        />
      </div>
    </div>
  );
}
