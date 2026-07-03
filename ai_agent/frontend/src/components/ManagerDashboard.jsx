import { useState, useEffect } from "react";
import { getManagerCandidates, approveCandidate, rejectCandidate } from "../api";
import { getUserEmail, logout } from "../auth";
import StatusBadge from "./StatusBadge";
import CandidateDetailModal from "./CandidateDetailModal";

const DEPARTMENTS = ["All", "Engineering", "Product", "Data Science", "Design", "Marketing", "Sales", "HR"];
const STATUS_FILTERS = ["All", "Uploaded", "AI Screened", "Under Review", "Interview Scheduled", "Rejected", "Selected"];

function ScoreRing({ score, color = "#10b981", size = 64 }) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  return (
    <svg width={size} height={size} className="rotate-[-90deg]">
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
      <circle
        cx={size / 2} cy={size / 2} r={radius} fill="none"
        stroke={color} strokeWidth="4"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: "stroke-dashoffset 1s ease-out" }}
      />
    </svg>
  );
}

function MiniScoreRing({ score, label, color }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative">
        <ScoreRing score={score} color={color} size={52} />
        <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white">{score}</span>
      </div>
      <span className="text-[10px] text-slate-500 text-center leading-tight">{label}</span>
    </div>
  );
}

function CandidateCard({ candidate, onSelect, onApprove, onReject }) {
  const [actionLoading, setActionLoading] = useState(null);

  const handleApprove = async (e) => {
    e.stopPropagation();
    setActionLoading("approve");
    await onApprove(candidate.id);
    setActionLoading(null);
  };

  const handleReject = async (e) => {
    e.stopPropagation();
    setActionLoading("reject");
    await onReject(candidate.id);
    setActionLoading(null);
  };

  const initials = candidate.name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  const avatarColors = ["from-purple-500 to-indigo-600", "from-emerald-500 to-teal-600", "from-orange-500 to-amber-600", "from-pink-500 to-rose-600", "from-blue-500 to-cyan-600"];
  const avatarColor = avatarColors[parseInt(candidate.id) % avatarColors.length];

  return (
    <div
      id={`candidate-card-${candidate.id}`}
      onClick={() => onSelect(candidate)}
      className="group bg-white/[0.03] hover:bg-white/[0.06] border border-white/8 hover:border-emerald-500/30 rounded-2xl p-5 cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-emerald-500/5"
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${avatarColor} flex items-center justify-center text-white font-bold text-sm flex-shrink-0`}>
          {initials}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 flex-wrap">
            <div>
              <h3 className="text-white font-semibold text-sm leading-tight truncate">{candidate.name}</h3>
              <p className="text-slate-400 text-xs mt-0.5 truncate">{candidate.role}</p>
            </div>
            <StatusBadge status={candidate.status} />
          </div>

          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className="text-xs text-slate-500 bg-slate-800/80 rounded-md px-2 py-0.5">{candidate.department}</span>
            <span className="text-slate-600 text-xs">·</span>
            <span className="text-xs text-slate-500">{new Date(candidate.uploadedAt).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</span>
          </div>
        </div>
      </div>

      {/* Scores */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/6">
        <div className="flex gap-4">
          <MiniScoreRing score={candidate.jdScore} label="JD Match" color="#10b981" />
          <MiniScoreRing score={candidate.semanticScore} label="Semantic" color="#6366f1" />
          <MiniScoreRing score={candidate.skillCoverage} label="Skills" color="#f59e0b" />
        </div>

        {/* Action buttons */}
        {(candidate.status === "Under Review" || candidate.status === "AI Screened") && (
          <div className="flex gap-2" onClick={e => e.stopPropagation()}>
            <button
              id={`approve-btn-${candidate.id}`}
              onClick={handleApprove}
              disabled={actionLoading !== null}
              className="text-xs px-3 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30 transition-all disabled:opacity-50"
            >
              {actionLoading === "approve" ? "..." : "✓ Approve"}
            </button>
            <button
              id={`reject-btn-${candidate.id}`}
              onClick={handleReject}
              disabled={actionLoading !== null}
              className="text-xs px-3 py-1.5 rounded-lg bg-red-500/15 hover:bg-red-500/25 text-red-400 border border-red-500/30 transition-all disabled:opacity-50"
            >
              {actionLoading === "reject" ? "..." : "✕ Reject"}
            </button>
          </div>
        )}
      </div>

      {/* Skills preview */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {candidate.matchedSkills.slice(0, 4).map(skill => (
          <span key={skill} className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{skill}</span>
        ))}
        {candidate.missingSkills.slice(0, 2).map(skill => (
          <span key={skill} className="text-[10px] px-2 py-0.5 rounded-md bg-red-500/10 text-red-400 border border-red-500/20">{skill}</span>
        ))}
        {candidate.matchedSkills.length > 4 && (
          <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-700/60 text-slate-400">+{candidate.matchedSkills.length - 4} more</span>
        )}
      </div>
    </div>
  );
}

function StatsBar({ candidates }) {
  const total = candidates.length;
  const selected = candidates.filter(c => c.status === "Selected").length;
  const interviews = candidates.filter(c => c.status === "Interview Scheduled").length;
  const reviewing = candidates.filter(c => c.status === "Under Review").length;
  const rejected = candidates.filter(c => c.status === "Rejected").length;

  const stats = [
    { label: "Total", value: total, color: "text-white", bg: "bg-slate-700/50" },
    { label: "Under Review", value: reviewing, color: "text-amber-400", bg: "bg-amber-500/10" },
    { label: "Interviews", value: interviews, color: "text-purple-400", bg: "bg-purple-500/10" },
    { label: "Selected", value: selected, color: "text-emerald-400", bg: "bg-emerald-500/10" },
    { label: "Rejected", value: rejected, color: "text-red-400", bg: "bg-red-500/10" },
  ];

  return (
    <div className="grid grid-cols-5 gap-3 mb-6">
      {stats.map(s => (
        <div key={s.label} className={`${s.bg} rounded-xl p-3 text-center border border-white/6`}>
          <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
          <div className="text-xs text-slate-500 mt-0.5">{s.label}</div>
        </div>
      ))}
    </div>
  );
}

export default function ManagerDashboard({ onLogout }) {
  const [candidates, setCandidates] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deptFilter, setDeptFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [search, setSearch] = useState("");
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const email = getUserEmail();
  const managerName = localStorage.getItem("managerName") || email.split("@")[0];

  useEffect(() => {
    loadCandidates();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [candidates, deptFilter, statusFilter, search]);

  const loadCandidates = async () => {
    setLoading(true);
    try {
      const data = await getManagerCandidates();
      setCandidates(data);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let result = [...candidates];
    if (deptFilter !== "All") result = result.filter(c => c.department === deptFilter);
    if (statusFilter !== "All") result = result.filter(c => c.status === statusFilter);
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(c =>
        c.name.toLowerCase().includes(q) ||
        c.role.toLowerCase().includes(q) ||
        c.email.toLowerCase().includes(q)
      );
    }
    setFiltered(result);
  };

  const handleApprove = async (id) => {
    await approveCandidate(id);
    setCandidates(prev => prev.map(c => c.id === id ? { ...c, status: "Selected" } : c));
  };

  const handleReject = async (id) => {
    await rejectCandidate(id);
    setCandidates(prev => prev.map(c => c.id === id ? { ...c, status: "Rejected" } : c));
  };

  const handleLogout = () => {
    logout();
    onLogout();
  };

  return (
    <div className="min-h-screen bg-slate-950 font-sans">
      {/* Background glows */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-emerald-600/4 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-teal-600/4 rounded-full blur-[120px]" />
      </div>

      {/* Top navigation */}
      <nav className="relative z-10 border-b border-white/6 bg-slate-950/80 backdrop-blur-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <span className="text-white font-semibold text-sm">ATS</span>
              <span className="text-slate-500 text-sm"> · Manager Dashboard</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-xs text-white font-medium">{managerName}</p>
              <p className="text-xs text-slate-500">{email}</p>
            </div>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white text-xs font-bold">
              {managerName[0]?.toUpperCase()}
            </div>
            <button
              id="manager-logout-btn"
              onClick={handleLogout}
              className="text-xs text-slate-400 hover:text-red-400 border border-slate-700 hover:border-red-500/40 rounded-lg px-3 py-1.5 transition-all"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Candidate Pipeline</h1>
          <p className="text-slate-400 text-sm mt-1">Review, approve, and manage candidates across your department</p>
        </div>

        {/* Stats */}
        {!loading && <StatsBar candidates={candidates} />}

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          {/* Search */}
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              id="candidate-search"
              type="text"
              placeholder="Search candidates..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-white/[0.04] border border-white/8 focus:border-emerald-500/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-all"
            />
          </div>

          {/* Dept filter */}
          <select
            id="dept-filter"
            value={deptFilter}
            onChange={e => setDeptFilter(e.target.value)}
            className="bg-white/[0.04] border border-white/8 focus:border-emerald-500/50 rounded-xl px-4 py-2.5 text-sm text-slate-300 focus:outline-none transition-all cursor-pointer"
            style={{ backgroundImage: "none" }}
          >
            {DEPARTMENTS.map(d => <option key={d} value={d} className="bg-slate-900">{d}</option>)}
          </select>

          {/* Status filter */}
          <select
            id="status-filter"
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="bg-white/[0.04] border border-white/8 focus:border-emerald-500/50 rounded-xl px-4 py-2.5 text-sm text-slate-300 focus:outline-none transition-all cursor-pointer"
            style={{ backgroundImage: "none" }}
          >
            {STATUS_FILTERS.map(s => <option key={s} value={s} className="bg-slate-900">{s}</option>)}
          </select>
        </div>

        {/* Candidate grid */}
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <div className="text-center">
              <svg className="animate-spin h-8 w-8 text-emerald-500 mx-auto mb-4" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
              </svg>
              <p className="text-slate-400 text-sm">Loading candidates...</p>
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <p className="text-slate-400 font-medium">No candidates found</p>
            <p className="text-slate-600 text-sm mt-1">Try adjusting your filters</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {filtered.map(candidate => (
              <CandidateCard
                key={candidate.id}
                candidate={candidate}
                onSelect={setSelectedCandidate}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            ))}
          </div>
        )}
      </div>

      {/* Candidate Detail Modal */}
      {selectedCandidate && (
        <CandidateDetailModal
          candidateId={selectedCandidate.id}
          onClose={() => setSelectedCandidate(null)}
          onStatusChange={(id, newStatus) => {
            setCandidates(prev => prev.map(c => c.id === id ? { ...c, status: newStatus } : c));
            setSelectedCandidate(prev => prev ? { ...prev, status: newStatus } : null);
          }}
        />
      )}
    </div>
  );
}
