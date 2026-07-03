import { useState, useMemo } from "react";

function FitBadge({ category }) {
  const styles = {
    "Strong Fit": "bg-green-500/15 text-green-300 border-green-500/30",
    "Partial Fit": "bg-yellow-500/15 text-yellow-300 border-yellow-500/30",
    "Not a Fit": "bg-red-500/15 text-red-300 border-red-500/30",
    Error: "bg-slate-500/15 text-slate-400 border-slate-500/30",
  };
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium border ${
        styles[category] || styles["Error"]
      }`}
    >
      {category}
    </span>
  );
}

function ScoreBar({ value, small = false }) {
  const color =
    value >= 80
      ? "bg-green-500"
      : value >= 60
      ? "bg-yellow-500"
      : "bg-red-500";
  const textColor =
    value >= 80
      ? "text-green-400"
      : value >= 60
      ? "text-yellow-400"
      : "text-red-400";

  return (
    <div className="flex items-center gap-2">
      <span className={`text-sm font-bold ${textColor} ${small ? "w-8" : "w-10"}`}>
        {Math.round(value)}
      </span>
      <div className={`flex-1 ${small ? "h-1.5" : "h-2"} bg-slate-800 rounded-full overflow-hidden`}>
        <div
          className={`h-full rounded-full ${color} transition-all duration-500`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  );
}

function SkillPills({ skills, variant, max = 3 }) {
  const style =
    variant === "matched"
      ? "bg-green-500/15 text-green-300 border-green-500/30"
      : "bg-red-500/15 text-red-300 border-red-500/30";

  if (!skills || skills.length === 0) {
    return <span className="text-xs text-slate-600 italic">—</span>;
  }

  const shown = skills.slice(0, max);
  const remaining = skills.length - max;

  return (
    <div className="flex flex-wrap gap-1">
      {shown.map((s, i) => (
        <span
          key={i}
          className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium border ${style}`}
        >
          {s}
        </span>
      ))}
      {remaining > 0 && (
        <span className="text-[10px] text-slate-500">+{remaining}</span>
      )}
    </div>
  );
}

function SortHeader({ label, sortKey, currentSort, currentDir, onSort }) {
  const active = currentSort === sortKey;
  const arrow = active ? (currentDir === "asc" ? " ↑" : " ↓") : "";
  return (
    <th
      onClick={() => onSort(sortKey)}
      className="px-3 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-indigo-300 transition-colors select-none whitespace-nowrap"
    >
      {label}{arrow}
    </th>
  );
}

function exportCSV(candidates, jdTitle) {
  const headers = [
    "Rank",
    "Filename",
    "Composite Score",
    "Skill Coverage",
    "Fit Category",
    "Experience Years",
    "Matched Count",
    "Missing Count",
    "Red Flags",
  ];
  const rows = candidates.map((c) => [
    c.rank,
    `"${c.resume_filename}"`,
    c.composite_score,
    c.skill_coverage_pct,
    `"${c.fit_category}"`,
    c.experience_years,
    c.matched_skills?.length || 0,
    c.missing_skills?.length || 0,
    c.red_flags?.length || 0,
  ]);

  const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `batch_results_${jdTitle.replace(/\s+/g, "_")}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function BatchResults({ batchResult, onViewCandidate }) {
  const [sortKey, setSortKey] = useState("rank");
  const [sortDir, setSortDir] = useState("asc");

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "composite_score" || key === "skill_coverage_pct" ? "desc" : "asc");
    }
  };

  const sorted = useMemo(() => {
    if (!batchResult?.candidates) return [];
    const list = [...batchResult.candidates];
    list.sort((a, b) => {
      let va = a[sortKey];
      let vb = b[sortKey];
      if (typeof va === "string") va = va.toLowerCase();
      if (typeof vb === "string") vb = vb.toLowerCase();
      if (Array.isArray(va)) va = va.length;
      if (Array.isArray(vb)) vb = vb.length;
      if (va < vb) return sortDir === "asc" ? -1 : 1;
      if (va > vb) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return list;
  }, [batchResult, sortKey, sortDir]);

  if (!batchResult || !batchResult.candidates) return null;

  const { total, jd_title, processed_at, candidates } = batchResult;
  const strongFits = candidates.filter((c) => c.fit_category === "Strong Fit").length;
  const partialFits = candidates.filter((c) => c.fit_category === "Partial Fit").length;
  const notFit = candidates.filter(
    (c) => c.fit_category !== "Strong Fit" && c.fit_category !== "Partial Fit"
  ).length;

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />
        <h2 className="text-xl font-bold text-white tracking-tight">
          📊 Batch Analysis Results
        </h2>
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-slate-400">
          <span className="text-white font-semibold">{total}</span> candidates
          analyzed against{" "}
          <span className="text-indigo-300 font-medium">"{jd_title}"</span>
        </p>
        <p className="text-xs text-slate-500">
          {new Date(processed_at).toLocaleString()}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="glass rounded-xl p-5 text-center border border-green-500/20">
          <div className="text-3xl font-bold text-green-400">{strongFits}</div>
          <div className="text-xs uppercase tracking-wide text-slate-400 mt-1">
            Strong Fits
          </div>
        </div>
        <div className="glass rounded-xl p-5 text-center border border-yellow-500/20">
          <div className="text-3xl font-bold text-yellow-400">{partialFits}</div>
          <div className="text-xs uppercase tracking-wide text-slate-400 mt-1">
            Partial Fits
          </div>
        </div>
        <div className="glass rounded-xl p-5 text-center border border-red-500/20">
          <div className="text-3xl font-bold text-red-400">{notFit}</div>
          <div className="text-xs uppercase tracking-wide text-slate-400 mt-1">
            Not a Fit
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="glass rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-700/50">
          <h3 className="text-sm font-semibold text-slate-300">
            Ranked Candidates
          </h3>
          <button
            id="batch-export-csv"
            onClick={() => exportCSV(candidates, jd_title)}
            className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 border border-indigo-500/30 hover:border-indigo-400/50 rounded-lg px-3 py-1.5 transition-all"
          >
            📥 Export CSV
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700/50">
                <SortHeader label="#" sortKey="rank" currentSort={sortKey} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Resume" sortKey="resume_filename" currentSort={sortKey} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Score" sortKey="composite_score" currentSort={sortKey} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Skill %" sortKey="skill_coverage_pct" currentSort={sortKey} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Fit" sortKey="fit_category" currentSort={sortKey} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Exp" sortKey="experience_years" currentSort={sortKey} currentDir={sortDir} onSort={handleSort} />
                <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Matched</th>
                <th className="px-3 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Missing</th>
                <SortHeader label="Flags" sortKey="red_flags" currentSort={sortKey} currentDir={sortDir} onSort={handleSort} />
                <th className="px-3 py-3 text-center text-xs font-semibold text-slate-400 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((c) => (
                <tr
                  key={c.analysis_id || c.resume_filename}
                  className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
                >
                  {/* Rank */}
                  <td className="px-3 py-3">
                    <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold ${
                      c.rank === 1
                        ? "bg-yellow-500/20 text-yellow-300 border border-yellow-500/30"
                        : c.rank === 2
                        ? "bg-slate-400/15 text-slate-300 border border-slate-500/30"
                        : c.rank === 3
                        ? "bg-amber-700/20 text-amber-400 border border-amber-600/30"
                        : "bg-slate-800 text-slate-500 border border-slate-700"
                    }`}>
                      {c.rank}
                    </span>
                  </td>

                  {/* Filename */}
                  <td className="px-3 py-3">
                    <span className="text-slate-300 font-medium text-xs">
                      {c.resume_filename}
                    </span>
                  </td>

                  {/* Composite Score */}
                  <td className="px-3 py-3 min-w-[120px]">
                    <ScoreBar value={c.composite_score} />
                  </td>

                  {/* Skill Coverage */}
                  <td className="px-3 py-3 min-w-[100px]">
                    <ScoreBar value={c.skill_coverage_pct} small />
                  </td>

                  {/* Fit Category */}
                  <td className="px-3 py-3">
                    <FitBadge category={c.fit_category} />
                  </td>

                  {/* Experience */}
                  <td className="px-3 py-3 text-slate-300 text-xs whitespace-nowrap">
                    {c.experience_years}y
                  </td>

                  {/* Matched Skills */}
                  <td className="px-3 py-3">
                    <SkillPills skills={c.matched_skills} variant="matched" />
                  </td>

                  {/* Missing Skills */}
                  <td className="px-3 py-3">
                    <SkillPills skills={c.missing_skills} variant="missing" />
                  </td>

                  {/* Red Flags */}
                  <td className="px-3 py-3 text-center">
                    {c.red_flags && c.red_flags.length > 0 ? (
                      <span className="inline-flex items-center justify-center min-w-[20px] h-5 rounded-full bg-red-500/15 text-red-300 border border-red-500/30 text-[10px] font-bold px-1.5">
                        {c.red_flags.length}
                      </span>
                    ) : (
                      <span className="text-xs text-slate-600">—</span>
                    )}
                  </td>

                  {/* Action */}
                  <td className="px-3 py-3 text-center">
                    <button
                      onClick={() => onViewCandidate(c)}
                      className="text-xs text-indigo-400 hover:text-indigo-300 border border-indigo-500/30 hover:border-indigo-400/50 rounded-lg px-3 py-1.5 transition-all whitespace-nowrap"
                    >
                      View Report →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
