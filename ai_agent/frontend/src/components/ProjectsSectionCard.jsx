import ScoreBadge from "./ScoreBadge";

// Parse projects section into structured entries
function parseProjects(text) {
  if (!text || !text.trim()) return [];

  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  const projects = [];
  let current = null;

  for (const line of lines) {
    // Project header: starts with bullet or has a year in parentheses or colon-delimited name
    const isHeader = (line.startsWith("•") || line.startsWith("-") || line.startsWith("*")) &&
      (line.includes("(201") || line.includes("(202") || line.includes(":"));

    if (isHeader) {
      if (current) projects.push(current);
      const bulletText = line.replace(/^[•\-*]\s*/, "");
      // Extract project name (before colon or before parenthesis)
      const nameMatch = bulletText.match(/^([^:(]+)/);
      const yearMatch = bulletText.match(/\((\d{4})\)/);
      const descMatch = bulletText.match(/\):\s*(.+)/);
      current = {
        name: nameMatch ? nameMatch[1].trim() : bulletText,
        year: yearMatch ? yearMatch[1] : null,
        description: descMatch ? descMatch[1].trim() : "",
        tech: [],
        details: [],
      };
    } else if (current) {
      // Last line of description usually has tech (comma-separated short words)
      const wordCount = line.split(/\s+/).length;
      const commaCount = (line.match(/,/g) || []).length;
      if (commaCount >= 1 && wordCount <= 12 && !/\b(developed|built|applied|implemented|used|using)\b/i.test(line)) {
        // Detect tech stack (e.g., "Python, BeautifulSoup" or "C++, OpenGL")
        current.tech = line.split(",").map((t) => t.trim()).filter(Boolean);
      } else if (!current.description) {
        current.description = line;
      } else {
        current.details.push(line);
      }
    }
  }
  if (current) projects.push(current);
  return projects;
}

export default function ProjectsSectionCard({ result }) {
  const score = result?.section_scores?.projects ?? result?.section_scores?.["project work"] ?? result?.section_scores?.["project"];
  const rawText =
    result?.sections?.projects ||
    result?.sections?.["project work"] ||
    result?.sections?.["projects"] ||
    "";

  const projects = parseProjects(rawText);

  if (!rawText.trim()) return null;

  return (
    <div className="glass rounded-2xl p-6 border border-slate-700/50 shadow-xl animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20 text-base">
            🚀
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Projects</h3>
            <p className="text-[11px] text-slate-500">Technical projects and implementations</p>
          </div>
        </div>
        <ScoreBadge score={score} />
      </div>

      {projects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {projects.map((proj, i) => (
            <div key={i} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-purple-500/30 transition-colors space-y-2">
              {/* Project title + year */}
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-bold text-white leading-tight">{proj.name}</p>
                {proj.year && (
                  <span className="shrink-0 text-[11px] px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/20">
                    {proj.year}
                  </span>
                )}
              </div>
              {/* Description */}
              {proj.description && (
                <p className="text-xs text-slate-400 leading-snug">{proj.description}</p>
              )}
              {proj.details.map((d, j) => (
                <p key={j} className="text-xs text-slate-500 leading-snug">{d}</p>
              ))}
              {/* Tech badges */}
              {proj.tech.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {proj.tech.map((t, j) => (
                    <span key={j} className="text-[11px] px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/20 font-mono">
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <p className="text-sm text-slate-300 whitespace-pre-wrap">{rawText}</p>
        </div>
      )}
    </div>
  );
}
