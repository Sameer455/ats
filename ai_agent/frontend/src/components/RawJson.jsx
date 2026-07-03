import { useState } from "react";

export default function RawJson({ result }) {
  const [open, setOpen] = useState(false);

  // Exclude llm_analysis from raw view (it's shown separately)
  const filtered = Object.fromEntries(
    Object.entries(result).filter(([key]) => key !== "llm_analysis")
  );

  return (
    <div className="animate-fade-in-up" style={{ animationDelay: "0.5s" }}>
      <button
        id="raw-json-toggle"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-indigo-300 transition-colors font-medium"
      >
        <span
          className={`inline-block transition-transform duration-200 ${
            open ? "rotate-90" : ""
          }`}
        >
          ▶
        </span>
        🔧 Raw Analysis Data (JSON)
      </button>

      {open && (
        <pre className="mt-3 glass rounded-xl p-5 text-xs text-slate-300 overflow-x-auto leading-relaxed max-h-96 overflow-y-auto">
          {JSON.stringify(filtered, null, 2)}
        </pre>
      )}
    </div>
  );
}
