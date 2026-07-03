export default function ExtractedProfile({ result }) {
  return (
    <div className="animate-fade-in-up glass rounded-xl p-6" style={{ animationDelay: "0.3s" }}>
      <h3 className="text-base font-semibold text-indigo-300 mb-5 flex items-center gap-2">
        <span className="w-1 h-5 bg-indigo-500 rounded-full inline-block" />
        Extracted Profile
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Column */}
        <div className="space-y-4">
          <div>
            <p className="text-sm font-medium text-slate-400 mb-1">Detected Roles</p>
            <p className="text-sm text-slate-200">
              {result.roles && result.roles.length > 0
                ? result.roles.join(", ")
                : <span className="italic text-slate-500">None detected</span>}
            </p>
          </div>

          <div>
            <p className="text-sm font-medium text-slate-400 mb-1">Education Qualifications</p>
            <p className="text-sm text-slate-200 uppercase tracking-wide">
              {result.education && result.education.length > 0
                ? result.education.join(", ")
                : <span className="italic text-slate-500 normal-case">None detected</span>}
            </p>
          </div>
        </div>

        {/* Right Column */}
        <div>
          <p className="text-sm font-medium text-slate-400 mb-2">JD Required Skills</p>
          <div className="flex flex-wrap gap-2">
            {result.jd_skills && result.jd_skills.length > 0 ? (
              result.jd_skills.map((skill, i) => (
                <span
                  key={i}
                  className="inline-block rounded-full px-3 py-1 text-xs font-medium bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 hover:scale-105 transition-transform"
                >
                  {skill}
                </span>
              ))
            ) : (
              <span className="text-sm italic text-slate-500">None detected</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
