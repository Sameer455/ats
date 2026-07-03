import { useState, useEffect } from "react";
import { getCandidateDetail, scheduleInterview, addInterviewNotes, approveCandidate, rejectCandidate } from "../api";
import StatusBadge from "./StatusBadge";

function ScoreBar({ label, score, color = "bg-emerald-500" }) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center">
        <span className="text-xs text-slate-400">{label}</span>
        <span className="text-xs font-semibold text-white">{score}%</span>
      </div>
      <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-1000 ease-out`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

function SkillTag({ skill, matched }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border font-medium ${
      matched
        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25"
        : "bg-red-500/10 text-red-400 border-red-500/25"
    }`}>
      {matched ? "✓" : "✕"} {skill}
    </span>
  );
}

export default function CandidateDetailModal({ candidateId, onClose, onStatusChange }) {
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [notes, setNotes] = useState("");
  const [savedNotes, setSavedNotes] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);
  const [interviewDate, setInterviewDate] = useState("");
  const [interviewTime, setInterviewTime] = useState("");
  const [schedulingInterview, setSchedulingInterview] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    loadCandidate();
  }, [candidateId]);

  const loadCandidate = async () => {
    setLoading(true);
    try {
      const data = await getCandidateDetail(candidateId);
      setCandidate(data);
      setSavedNotes(data.notes || "");
      setNotes(data.notes || "");
      if (data.interviewDate) {
        const dt = new Date(data.interviewDate);
        setInterviewDate(dt.toISOString().split("T")[0]);
        setInterviewTime(dt.toTimeString().slice(0, 5));
      }
    } finally {
      setLoading(false);
    }
  };

  const showSuccess = (msg) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 3000);
  };

  const handleSaveNotes = async () => {
    setSavingNotes(true);
    await addInterviewNotes(candidateId, notes);
    setSavedNotes(notes);
    setSavingNotes(false);
    showSuccess("Notes saved successfully");
  };

  const handleScheduleInterview = async () => {
    if (!interviewDate || !interviewTime) return;
    setSchedulingInterview(true);
    await scheduleInterview(candidateId, { date: interviewDate, time: interviewTime });
    setSchedulingInterview(false);
    onStatusChange(candidateId, "Interview Scheduled");
    setCandidate(prev => ({ ...prev, status: "Interview Scheduled" }));
    showSuccess("Interview scheduled successfully!");
  };

  const handleApprove = async () => {
    setActionLoading("approve");
    await approveCandidate(candidateId);
    onStatusChange(candidateId, "Selected");
    setCandidate(prev => ({ ...prev, status: "Selected" }));
    setActionLoading(null);
    showSuccess("Candidate selected!");
  };

  const handleReject = async () => {
    setActionLoading("reject");
    await rejectCandidate(candidateId);
    onStatusChange(candidateId, "Rejected");
    setCandidate(prev => ({ ...prev, status: "Rejected" }));
    setActionLoading(null);
    showSuccess("Candidate rejected.");
  };

  const TABS = [
    { id: "overview", label: "Overview" },
    { id: "skills", label: "Skills" },
    { id: "interview", label: "Interview" },
    { id: "notes", label: "Notes" },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end" onClick={onClose}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Panel */}
      <div
        id="candidate-detail-panel"
        className="relative z-10 w-full max-w-2xl h-full bg-slate-900 border-l border-white/8 overflow-y-auto animate-fade-in-up"
        style={{ animation: "slideInRight 0.3s ease-out" }}
        onClick={e => e.stopPropagation()}
      >
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <svg className="animate-spin h-8 w-8 text-emerald-500" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
            </svg>
          </div>
        ) : candidate ? (
          <>
            {/* Header */}
            <div className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur-lg border-b border-white/6 px-6 py-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                    {candidate.name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2)}
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-white leading-tight">{candidate.name}</h2>
                    <p className="text-slate-400 text-sm">{candidate.role} · {candidate.department}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={candidate.status} size="lg" />
                  <button
                    id="close-detail-panel"
                    onClick={onClose}
                    className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-all"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex gap-1 mt-4">
                {TABS.map(tab => (
                  <button
                    key={tab.id}
                    id={`tab-${tab.id}`}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      activeTab === tab.id
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : "text-slate-400 hover:text-white hover:bg-white/5"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Success toast */}
            {successMsg && (
              <div className="mx-6 mt-4 px-4 py-3 bg-emerald-500/15 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm flex items-center gap-2">
                <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {successMsg}
              </div>
            )}

            <div className="px-6 py-5 space-y-5">
              {/* OVERVIEW TAB */}
              {activeTab === "overview" && (
                <>
                  {/* AI Recommendation */}
                  <div className="bg-indigo-500/8 border border-indigo-500/20 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">🤖</span>
                      <h3 className="text-sm font-semibold text-indigo-300">AI Recommendation</h3>
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed">{candidate.aiRecommendation}</p>
                  </div>

                  {/* Score breakdown */}
                  <div className="bg-white/[0.03] rounded-2xl p-4 border border-white/6 space-y-3">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">📊 Score Breakdown</h3>
                    <ScoreBar label="JD Match Score" score={candidate.jdScore} color="bg-emerald-500" />
                    <ScoreBar label="Semantic Score" score={candidate.semanticScore} color="bg-indigo-500" />
                    <ScoreBar label="Skill Coverage" score={candidate.skillCoverage} color="bg-amber-500" />
                  </div>

                  {/* Resume summary */}
                  <div className="bg-white/[0.03] rounded-2xl p-4 border border-white/6">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">📄 Resume Summary</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">{candidate.resumeSummary}</p>
                  </div>

                  {/* Education & Experience */}
                  {candidate.education && (
                    <div className="bg-white/[0.03] rounded-2xl p-4 border border-white/6">
                      <h3 className="text-sm font-semibold text-slate-300 mb-3">🎓 Education</h3>
                      <p className="text-sm text-slate-400">{candidate.education}</p>
                    </div>
                  )}

                  {candidate.experience && candidate.experience.length > 0 && (
                    <div className="bg-white/[0.03] rounded-2xl p-4 border border-white/6">
                      <h3 className="text-sm font-semibold text-slate-300 mb-3">💼 Experience</h3>
                      <div className="space-y-2">
                        {candidate.experience.map((exp, i) => (
                          <div key={i} className="flex items-start gap-3">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-2 flex-shrink-0" />
                            <div>
                              <p className="text-sm text-white font-medium">{exp.role}</p>
                              <p className="text-xs text-slate-400">{exp.company} · {exp.duration}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Resume PDF preview placeholder */}
                  <div className="bg-white/[0.02] border border-dashed border-white/10 rounded-2xl p-6 text-center">
                    <svg className="w-10 h-10 text-slate-600 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p className="text-slate-500 text-sm">Resume PDF Preview</p>
                    <p className="text-slate-600 text-xs mt-1">PDF viewer will render here when backend provides the resume URL</p>
                    <button className="mt-3 text-xs text-emerald-400 hover:text-emerald-300 border border-emerald-500/30 rounded-lg px-3 py-1.5 transition-colors">
                      📥 Download Resume
                    </button>
                  </div>
                </>
              )}

              {/* SKILLS TAB */}
              {activeTab === "skills" && (
                <>
                  <div className="bg-emerald-500/8 border border-emerald-500/20 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-base">✅</span>
                      <h3 className="text-sm font-semibold text-emerald-300">Matched Skills ({candidate.matchedSkills.length})</h3>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {candidate.matchedSkills.map(skill => (
                        <SkillTag key={skill} skill={skill} matched={true} />
                      ))}
                      {candidate.matchedSkills.length === 0 && (
                        <p className="text-sm text-slate-500">No matched skills found</p>
                      )}
                    </div>
                  </div>

                  <div className="bg-red-500/8 border border-red-500/20 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-base">⚠️</span>
                      <h3 className="text-sm font-semibold text-red-300">Missing Skills ({candidate.missingSkills.length})</h3>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {candidate.missingSkills.map(skill => (
                        <SkillTag key={skill} skill={skill} matched={false} />
                      ))}
                      {candidate.missingSkills.length === 0 && (
                        <p className="text-sm text-emerald-400 font-medium">🎉 All required skills matched!</p>
                      )}
                    </div>
                  </div>

                  {/* Skill coverage bar */}
                  <div className="bg-white/[0.03] rounded-2xl p-4 border border-white/6">
                    <ScoreBar label="Overall Skill Coverage" score={candidate.skillCoverage} color="bg-gradient-to-r from-emerald-500 to-teal-500" />
                  </div>

                  {/* Quick actions */}
                  <div className="flex gap-3 pt-2">
                    {candidate.status !== "Selected" && candidate.status !== "Rejected" && (
                      <>
                        <button
                          id="detail-approve-btn"
                          onClick={handleApprove}
                          disabled={actionLoading !== null}
                          className="flex-1 py-3 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30 font-medium text-sm transition-all disabled:opacity-50"
                        >
                          {actionLoading === "approve" ? "Processing..." : "✓ Approve Candidate"}
                        </button>
                        <button
                          id="detail-reject-btn"
                          onClick={handleReject}
                          disabled={actionLoading !== null}
                          className="flex-1 py-3 rounded-xl bg-red-500/15 hover:bg-red-500/25 text-red-400 border border-red-500/30 font-medium text-sm transition-all disabled:opacity-50"
                        >
                          {actionLoading === "reject" ? "Processing..." : "✕ Reject Candidate"}
                        </button>
                      </>
                    )}
                  </div>
                </>
              )}

              {/* INTERVIEW TAB */}
              {activeTab === "interview" && (
                <>
                  <div className="bg-purple-500/8 border border-purple-500/20 rounded-2xl p-5">
                    <h3 className="text-sm font-semibold text-purple-300 mb-4">📅 Schedule Interview</h3>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs text-slate-400 mb-1 block">Date</label>
                        <input
                          id="interview-date"
                          type="date"
                          value={interviewDate}
                          onChange={e => setInterviewDate(e.target.value)}
                          min={new Date().toISOString().split("T")[0]}
                          className="w-full bg-slate-800 border border-slate-700 focus:border-purple-500/60 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none transition-all"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-400 mb-1 block">Time</label>
                        <input
                          id="interview-time"
                          type="time"
                          value={interviewTime}
                          onChange={e => setInterviewTime(e.target.value)}
                          className="w-full bg-slate-800 border border-slate-700 focus:border-purple-500/60 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none transition-all"
                        />
                      </div>
                    </div>
                    <button
                      id="schedule-interview-btn"
                      onClick={handleScheduleInterview}
                      disabled={schedulingInterview || !interviewDate || !interviewTime}
                      className="w-full mt-4 py-3 rounded-xl bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/30 font-medium text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {schedulingInterview ? "Scheduling..." : "📅 Confirm Interview Schedule"}
                    </button>
                  </div>

                  {candidate.status === "Interview Scheduled" && interviewDate && (
                    <div className="bg-emerald-500/8 border border-emerald-500/20 rounded-2xl p-4 text-center">
                      <div className="text-2xl mb-1">✅</div>
                      <p className="text-emerald-400 font-semibold text-sm">Interview Scheduled</p>
                      <p className="text-slate-400 text-xs mt-1">
                        {new Date(`${interviewDate}T${interviewTime || "00:00"}`).toLocaleString("en-IN", {
                          weekday: "long", year: "numeric", month: "long", day: "numeric", hour: "2-digit", minute: "2-digit"
                        })}
                      </p>
                    </div>
                  )}
                </>
              )}

              {/* NOTES TAB */}
              {activeTab === "notes" && (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-slate-300 font-medium block mb-2">Interview Notes & Feedback</label>
                    <textarea
                      id="interview-notes"
                      value={notes}
                      onChange={e => setNotes(e.target.value)}
                      placeholder="Add interview notes, observations, feedback about the candidate..."
                      rows={8}
                      className="w-full bg-white/[0.04] border border-white/8 focus:border-emerald-500/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none resize-none transition-all"
                    />
                  </div>
                  <button
                    id="save-notes-btn"
                    onClick={handleSaveNotes}
                    disabled={savingNotes || notes === savedNotes}
                    className="w-full py-3 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30 font-medium text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {savingNotes ? "Saving..." : "💾 Save Notes"}
                  </button>
                  {savedNotes && (
                    <div className="bg-white/[0.03] rounded-xl p-4 border border-white/6">
                      <p className="text-xs text-slate-500 mb-2">Last saved:</p>
                      <p className="text-sm text-slate-400 whitespace-pre-wrap">{savedNotes}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        ) : null}
      </div>

      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
