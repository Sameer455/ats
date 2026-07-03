// Shared score badge for all section cards
export default function ScoreBadge({ score }) {
  if (score === undefined || score === null) return null;

  const getStyle = (s) => {
    if (s >= 75) return { bg: "bg-green-500/15 border-green-500/30 text-green-300", label: "Strong Match" };
    if (s >= 50) return { bg: "bg-yellow-500/15 border-yellow-500/30 text-yellow-300", label: "Partial Match" };
    return { bg: "bg-red-500/15 border-red-500/30 text-red-300", label: "Weak Match" };
  };

  const { bg, label } = getStyle(score);

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold ${bg}`}>
      <span>{score}%</span>
      <span className="opacity-70">·</span>
      <span>{label}</span>
    </div>
  );
}
