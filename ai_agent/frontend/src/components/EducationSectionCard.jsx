import ScoreBadge from "./ScoreBadge";

// Parse education section raw text into structured entries
function parseEducationEntries(text) {
  if (!text || !text.trim()) return [];

  const datePattern = /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{4})\s*[-–]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{4}|Present)/i;

  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  const entries = [];
  let current = null;

  for (const line of lines) {
    const hasDate = datePattern.test(line);
    // Institution lines: have a date, or contain "University", "Institute", "College", "School", "BITS", "IIT", "NIT" etc.
    const isInstitution = hasDate || /\b(university|institute|college|school|bits|iit|nit|academy|polytechnic)\b/i.test(line);

    if (isInstitution && line.length < 120) {
      if (current) entries.push(current);
      current = { institution: line, degree: "", cgpa: "", coursework: [], extras: [] };
    } else if (current) {
      // CGPA / GPA
      const cgpaMatch = line.match(/(?:cgpa|gpa|score)[\s:]*([0-9.]+(?:\s*\/\s*[0-9.]+)?)/i);
      if (cgpaMatch) {
        current.cgpa = cgpaMatch[1];
        // Degree line might contain cgpa too, extract degree separately
        const degreeText = line.replace(/(?:cgpa|gpa|score)[\s:]*[0-9./\s]+/i, "").trim();
        if (degreeText && !current.degree) current.degree = degreeText;
      } else if (!current.degree && /\b(b\.?e|b\.?tech|b\.?sc|m\.?tech|m\.?sc|m\.?e|phd|mba|bachelor|master|doctor)\b/i.test(line)) {
        current.degree = line;
      } else if (/\b(coursework|courses|relevant)\b/i.test(line)) {
        const courseText = line.replace(/.*coursework[:\s]*/i, "").trim();
        if (courseText) current.coursework = courseText.split(",").map(c => c.trim()).filter(Boolean);
      } else if (line.startsWith("•") || line.startsWith("-")) {
        current.extras.push(line.replace(/^[•\-]\s*/, ""));
      }
    }
  }
  if (current) entries.push(current);
  return entries;
}

export default function EducationSectionCard({ result }) {
  const score = result?.section_scores?.education;
  const rawText = result?.sections?.education || "";
  const entries = parseEducationEntries(rawText);
  const hasDegree = result?.education && result.education.length > 0;

  return (
    <div className="glass rounded-2xl p-6 border border-slate-700/50 shadow-xl animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-teal-500/10 flex items-center justify-center border border-teal-500/20 text-base">
            🎓
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Education</h3>
            <p className="text-[11px] text-slate-500">Academic background and qualifications</p>
          </div>
        </div>
        <ScoreBadge score={score} />
      </div>

      {/* Education status */}
      <div className="mb-4 flex items-center gap-2">
        <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${
          hasDegree
            ? "bg-green-500/15 border-green-500/30 text-green-300"
            : "bg-yellow-500/15 border-yellow-500/30 text-yellow-300"
        }`}>
          {hasDegree ? `✅ ${result.education.join(", ")}` : "⚠️ No degree detected"}
        </span>
      </div>

      {/* Parsed entries */}
      {entries.length > 0 ? (
        <div className="space-y-4">
          {entries.map((entry, i) => (
            <div key={i} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <p className="text-sm font-bold text-white">{entry.institution}</p>
              {entry.degree && <p className="text-xs text-teal-300 font-medium">{entry.degree}</p>}
              {entry.cgpa && (
                <p className="text-xs text-slate-400">
                  GPA / CGPA: <span className="text-white font-semibold">{entry.cgpa}</span>
                </p>
              )}
              {entry.coursework.length > 0 && (
                <div>
                  <p className="text-[11px] text-slate-500 uppercase tracking-wider mb-1.5">Relevant Coursework</p>
                  <div className="flex flex-wrap gap-1.5">
                    {entry.coursework.map((c, j) => (
                      <span key={j} className="text-[11px] px-2 py-0.5 rounded-md bg-teal-500/10 text-teal-300 border border-teal-500/20">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {entry.extras.map((e, j) => (
                <p key={j} className="text-xs text-slate-400">• {e}</p>
              ))}
            </div>
          ))}
        </div>
      ) : rawText.trim() ? (
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <p className="text-sm text-slate-300 whitespace-pre-wrap">{rawText}</p>
        </div>
      ) : (
        <div className="text-center py-6 text-slate-500 text-sm italic">
          No education section detected in resume.
        </div>
      )}
    </div>
  );
}
