import React, { useState } from "react";

export default function ResumeSections({ result }) {
  if (!result || !result.sections) return null;

  const sections = result.sections;
  const sectionKeys = Object.keys(sections).filter((key) => sections[key]?.trim());

  if (sectionKeys.length === 0) return null;

  const [expandedSection, setExpandedSection] = useState(sectionKeys.includes("experience") ? "experience" : sectionKeys[0]);

  // Format section names beautifully (e.g. "experience" -> "Experience")
  const formatSectionName = (key) => {
    return key.charAt(0).toUpperCase() + key.slice(1);
  };

  return (
    <div className="glass rounded-2xl p-6 border border-slate-700/50 shadow-xl overflow-hidden mt-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
          <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>
        <div>
          <h3 className="text-xl font-bold text-white tracking-tight">Extracted Sections</h3>
          <p className="text-xs text-slate-400 font-medium">Raw content grouped by category</p>
        </div>
      </div>

      <div className="space-y-4">
        {sectionKeys.map((key) => {
          const isExpanded = expandedSection === key;
          
          return (
            <div key={key} className={`border rounded-xl transition-colors duration-300 ${isExpanded ? 'bg-slate-800/80 border-purple-500/30' : 'bg-slate-900/50 border-slate-700/50 hover:border-slate-600'}`}>
              <button
                onClick={() => setExpandedSection(isExpanded ? null : key)}
                className="w-full px-5 py-4 flex items-center justify-between text-left focus:outline-none"
              >
                <div className="flex items-center gap-3">
                  <span className={`text-sm font-semibold tracking-wide ${isExpanded ? 'text-purple-300' : 'text-slate-300'}`}>
                    {formatSectionName(key)}
                  </span>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-500">
                    {sections[key].length} chars
                  </span>
                </div>
                <svg
                  className={`w-5 h-5 transition-transform duration-300 ${isExpanded ? 'rotate-180 text-purple-400' : 'text-slate-500'}`}
                  fill="none" viewBox="0 0 24 24" stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {isExpanded && (
                <div className="px-5 pb-5">
                  <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 text-sm whitespace-pre-wrap font-mono leading-relaxed max-h-[400px] overflow-y-auto custom-scrollbar">
                    {sections[key]}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
