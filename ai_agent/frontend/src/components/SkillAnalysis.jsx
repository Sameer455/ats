function SkillPills({ skills, variant }) {
  const styles = {
    matched:
      "bg-green-500/15 text-green-300 border border-green-500/30",
    missing:
      "bg-red-500/15 text-red-300 border border-red-500/30",
    extra:
      "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30",
  };

  if (!skills || skills.length === 0) {
    return <span className="text-sm text-slate-500 italic">None detected</span>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {skills.map((skill, i) => (
        <span
          key={i}
          className={`inline-block rounded-full px-3 py-1 text-xs font-medium transition-transform hover:scale-105 ${styles[variant]}`}
        >
          {skill}
        </span>
      ))}
    </div>
  );
}

export default function SkillAnalysis({ result }) {
  return (
    <div className="animate-fade-in-up glass rounded-xl p-6" style={{ animationDelay: "0.2s" }}>
      <h3 className="text-base font-semibold text-indigo-300 mb-5 flex items-center gap-2">
        <span className="w-1 h-5 bg-indigo-500 rounded-full inline-block" />
        Skill Analysis
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Matched */}
        <div>
          <p className="text-sm font-medium text-green-400 mb-2.5 flex items-center gap-1.5">
            <span>✅</span> Matched Skills ({result.matched_skills.length})
          </p>
          <SkillPills skills={result.matched_skills} variant="matched" />
        </div>

        {/* Missing */}
        <div>
          <p className="text-sm font-medium text-red-400 mb-2.5 flex items-center gap-1.5">
            <span>❌</span> Missing Skills ({result.missing_skills.length})
          </p>
          <SkillPills skills={result.missing_skills} variant="missing" />
        </div>

        {/* Extra */}
        <div>
          <p className="text-sm font-medium text-cyan-400 mb-2.5 flex items-center gap-1.5">
            <span>➕</span> Additional Skills ({result.extra_skills.length})
          </p>
          <SkillPills skills={result.extra_skills} variant="extra" />
        </div>
      </div>
    </div>
  );
}
