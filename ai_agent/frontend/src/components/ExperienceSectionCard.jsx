import ScoreBadge from "./ScoreBadge";

// Parses experience section raw text into structured role entries.
// Detects company lines (contain a date pattern) as entry boundaries.
function parseExperienceEntries(text) {
  if (!text || !text.trim()) return [];

  const datePattern = /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|(\d{4})\s*[-–]\s*(\d{4}|Present|present|current)/i;

  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  const entries = [];
  let current = null;

  for (const line of lines) {
    const isEntryHeader = datePattern.test(line) && line.length < 100;
    if (isEntryHeader) {
      if (current) entries.push(current);
      current = { header: line, title: "", bullets: [], tech: "" };
    } else if (current) {
      if (line.startsWith("•") || line.startsWith("-") || line.startsWith("*")) {
        // Heuristic: detect tech-stack-only lines (mostly comma-separated known tech terms, no verbs)
        const bulletText = line.replace(/^[•\-*]\s*/, "");
        const wordCount = bulletText.split(/\s+/).length;
        const commaCount = (bulletText.match(/,/g) || []).length;
        if (commaCount >= 2 && wordCount <= 20 && !/\b(developed|built|led|created|improved|reduced|worked|designed|implemented|migrated)\b/i.test(bulletText)) {
          current.tech = bulletText;
        } else {
          current.bullets.push(bulletText);
        }
      } else if (!current.title && line.length < 60 && line.length > 2) {
        current.title = line;
      }
    }
  }
  if (current) entries.push(current);
  return entries;
}

function ExpEntryCard({ entry, index }) {
  return (
    <div className="relative pl-5 border-l-2 border-indigo-500/30 space-y-2">
      {/* Timeline dot */}
      <div className="absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.6)]" />

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-sm font-bold text-white leading-tight">{entry.header}</p>
          {entry.title && (
            <p className="text-xs text-indigo-300 font-semibold mt-0.5">{entry.title}</p>
          )}
        </div>
      </div>

      {/* Bullet points */}
      {entry.bullets.length > 0 && (
        <ul className="space-y-1.5 mt-2">
          {entry.bullets.map((b, i) => (
            <li key={i} className="text-sm text-slate-300 flex gap-2 leading-snug">
              <span className="text-indigo-400 mt-0.5 shrink-0">›</span>
              <span>{b}</span>
            </li>
          ))}
        </ul>
      )}

      {/* Tech stack */}
      {entry.tech && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {entry.tech.split(",").map((t, i) => (
            <span key={i} className="text-[11px] px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 border border-slate-700 font-mono">
              {t.trim()}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ExperienceSectionCard({ result }) {
  const score = result?.section_scores?.experience;
  const rawText = result?.sections?.experience || "";
  const entries = parseExperienceEntries(rawText);
  const expYears = result?.experience_years ?? 0;
  const reqYears = result?.required_experience ?? 0;
  const expPct = reqYears > 0 ? Math.min(Math.round((expYears / reqYears) * 100), 100) : 100;
  const exceedsReq = expYears >= reqYears;

  return (
    <div className="glass rounded-2xl p-6 border border-slate-700/50 shadow-xl animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20 text-base">
            💼
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Work Experience</h3>
            <p className="text-[11px] text-slate-500">Extracted roles, companies and contributions</p>
          </div>
        </div>
        <ScoreBadge score={score} />
      </div>

      {/* Experience fulfillment bar */}
      <div className="mb-6 p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex-1 w-full">
          <div className="flex justify-between text-xs mb-1.5">
            <span className="text-slate-400">Experience Fulfillment</span>
            <span className={`font-bold ${exceedsReq ? "text-green-400" : "text-yellow-400"}`}>
              {expYears} yrs / {reqYears} required
            </span>
          </div>
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-1000 ${exceedsReq ? "bg-green-500" : "bg-yellow-500"}`}
              style={{ width: `${expPct}%` }}
            />
          </div>
        </div>
        <span className={`text-xs font-bold px-3 py-1.5 rounded-full border whitespace-nowrap ${
          exceedsReq
            ? "bg-green-500/15 border-green-500/30 text-green-300"
            : "bg-yellow-500/15 border-yellow-500/30 text-yellow-300"
        }`}>
          {result?.experience_gap}
        </span>
      </div>

      {/* Entries */}
      {entries.length > 0 ? (
        <div className="space-y-6">
          {entries.map((entry, i) => <ExpEntryCard key={i} entry={entry} index={i} />)}
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500 text-sm italic">
          No structured experience entries detected in resume.
        </div>
      )}
    </div>
  );
}
