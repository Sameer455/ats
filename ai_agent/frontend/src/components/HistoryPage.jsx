import { useState, useEffect } from "react";
import { getHistory, getHistoryDetail } from "../api";
import ScoreCards from "./ScoreCards";
import ScoreBreakdown from "./ScoreBreakdown";
import SkillAnalysis from "./SkillAnalysis";
import ExtractedProfile from "./ExtractedProfile";
import RawJson from "./RawJson";

export default function HistoryPage({ onBack }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Load history on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoading(true);
        const data = await getHistory();
        setHistory(data || []);
      } catch (err) {
        setError(`Failed to load history: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
  }, []);

  // Load detail when selecting an entry
  const handleSelectHistory = async (historyId) => {
    try {
      setDetailLoading(true);
      const detail = await getHistoryDetail(historyId);
      setSelectedId(historyId);
      setSelectedDetail(detail);
    } catch (err) {
      setError(`Failed to load details: ${err.message}`);
    } finally {
      setDetailLoading(false);
    }
  };

  if (selectedDetail) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => {
            setSelectedId(null);
            setSelectedDetail(null);
          }}
          className="text-indigo-400 hover:text-indigo-300 text-sm font-medium"
        >
          ← Back to History
        </button>

        <div className="flex items-center gap-3 mb-2">
          <div className="h-px flex-1 bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />
          <h2 className="text-xl font-bold text-white tracking-tight">
            📊 Analysis Details
          </h2>
          <div className="h-px flex-1 bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />
        </div>

        {detailLoading ? (
          <div className="text-center py-8 text-slate-400">Loading details...</div>
        ) : (
          <div className="space-y-6">
            <ScoreCards result={selectedDetail} />
            <ScoreBreakdown result={selectedDetail} />
            <SkillAnalysis result={selectedDetail} />
            <ExtractedProfile result={selectedDetail} />
            <RawJson result={selectedDetail} />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-white">📋 Analysis History</h2>
        <button
          onClick={onBack}
          className="text-indigo-400 hover:text-indigo-300 text-sm font-medium"
        >
          Back to Analyzer
        </button>
      </div>

      {error && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/30 px-5 py-3.5 text-sm text-red-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-slate-400">Loading history...</div>
      ) : history.length === 0 ? (
        <div className="rounded-xl border border-slate-700/50 p-8 text-center">
          <div className="text-4xl mb-2">📭</div>
          <p className="text-slate-400">No analysis history yet. Start by analyzing a resume!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <button
              key={item.id}
              onClick={() => handleSelectHistory(item.id)}
              className="w-full text-left glass rounded-xl p-4 border border-slate-700/50 hover:border-indigo-500/50 transition-all duration-200 hover:bg-slate-800/30"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-white">{item.filename}</h3>
                  <p className="text-xs text-slate-400 mt-1">
                    {item.jd_snippet}
                  </p>
                  <p className="text-xs text-slate-500 mt-2">
                    {new Date(item.created_at).toLocaleDateString()} at{" "}
                    {new Date(item.created_at).toLocaleTimeString()}
                  </p>
                </div>
                <div className="text-right ml-4">
                  <div
                    className={`text-2xl font-bold ${
                      item.final_score >= 75
                        ? "text-green-400"
                        : item.final_score >= 50
                        ? "text-yellow-400"
                        : "text-red-400"
                    }`}
                  >
                    {item.final_score.toFixed(1)}%
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{item.fit_category}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
