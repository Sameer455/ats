// Candidate workflow status badge component
const STATUS_CONFIG = {
  "Uploaded": {
    bg: "bg-slate-700/60",
    border: "border-slate-600/50",
    text: "text-slate-300",
    dot: "bg-slate-400",
    icon: "📁",
  },
  "AI Screened": {
    bg: "bg-blue-500/15",
    border: "border-blue-500/30",
    text: "text-blue-300",
    dot: "bg-blue-400",
    icon: "🤖",
  },
  "Under Review": {
    bg: "bg-amber-500/15",
    border: "border-amber-500/30",
    text: "text-amber-300",
    dot: "bg-amber-400",
    icon: "👁️",
  },
  "Interview Scheduled": {
    bg: "bg-purple-500/15",
    border: "border-purple-500/30",
    text: "text-purple-300",
    dot: "bg-purple-400",
    icon: "📅",
  },
  "Rejected": {
    bg: "bg-red-500/15",
    border: "border-red-500/30",
    text: "text-red-300",
    dot: "bg-red-400",
    icon: "❌",
  },
  "Selected": {
    bg: "bg-emerald-500/15",
    border: "border-emerald-500/30",
    text: "text-emerald-300",
    dot: "bg-emerald-400",
    icon: "✅",
  },
};

export default function StatusBadge({ status, size = "sm" }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG["Uploaded"];
  const sizeClasses = size === "lg"
    ? "px-3 py-1.5 text-xs gap-1.5"
    : "px-2.5 py-1 text-xs gap-1";

  return (
    <span className={`inline-flex items-center rounded-full border font-medium ${cfg.bg} ${cfg.border} ${cfg.text} ${sizeClasses}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {status}
    </span>
  );
}

export { STATUS_CONFIG };
