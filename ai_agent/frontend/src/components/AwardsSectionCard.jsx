// Awards & Certifications section card
function AwardItem({ text }) {
  // Try to split "Source: Title" or "Title — Source" patterns
  const colonIdx = text.indexOf(":");
  const hasBulletPrefix = /^[•\-*]/.test(text);
  const cleanText = hasBulletPrefix ? text.replace(/^[•\-*]\s*/, "") : text;

  return (
    <div className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-amber-500/20 transition-colors group">
      <div className="w-7 h-7 rounded-lg bg-amber-500/10 flex items-center justify-center border border-amber-500/20 text-sm shrink-0 mt-0.5">
        🏆
      </div>
      <p className="text-sm text-slate-300 leading-snug group-hover:text-white transition-colors">{cleanText}</p>
    </div>
  );
}

export default function AwardsSectionCard({ result }) {
  // Try multiple possible section key names
  const rawText =
    result?.sections?.awards ||
    result?.sections?.certifications ||
    result?.sections?.["awards and certificates"] ||
    result?.sections?.["awards & certificates"] ||
    result?.sections?.["achievements"] ||
    result?.sections?.["certifications & awards"] ||
    "";

  if (!rawText.trim()) return null;

  const lines = rawText.split("\n").map((l) => l.trim()).filter(Boolean);

  return (
    <div className="glass rounded-2xl p-6 border border-slate-700/50 shadow-xl animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        <div className="w-9 h-9 rounded-xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20 text-base">
          🏆
        </div>
        <div>
          <h3 className="text-base font-bold text-white">Awards & Certifications</h3>
          <p className="text-[11px] text-slate-500">Recognitions, credentials, and achievements</p>
        </div>
      </div>

      <div className="space-y-2">
        {lines.map((line, i) => <AwardItem key={i} text={line} />)}
      </div>
    </div>
  );
}
