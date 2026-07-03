import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { analyzeResume, analyzeBatch, getJDLibrary, getJDCategories } from "./api";
import { isLoggedIn, logout, getUserEmail, isManager, isRecruiter } from "./auth";

// Pages & components
import LoginPage from "./components/LoginPage";
import ManagerLoginPage from "./components/ManagerLoginPage";
import ManagerDashboard from "./components/ManagerDashboard";
import Header from "./components/Header";
import UploadArea from "./components/UploadArea";
import JDLibraryManager from "./components/JDLibraryManager";
import ScoreCards from "./components/ScoreCards";
import ScoreBreakdown from "./components/ScoreBreakdown";
import ResumeInsights from "./components/ResumeInsights";
import RawJson from "./components/RawJson";
import HistoryPage from "./components/HistoryPage";
import BatchUploadArea from "./components/BatchUploadArea";
import BatchResults from "./components/BatchResults";
import CandidateReport from "./components/CandidateReport";

// ─── Route Guards ─────────────────────────────────────────────────────────────

/**
 * Protects a route — redirects to login if not authenticated.
 * If `requiredRole` is "manager", only allows managers; redirects recruiter to /.
 * If `requiredRole` is "recruiter", only allows recruiters; redirects manager to /manager/dashboard.
 */
function ProtectedRoute({ children, requiredRole }) {
  if (!isLoggedIn()) {
    return <Navigate to={requiredRole === "manager" ? "/manager" : "/"} replace />;
  }
  if (requiredRole === "manager" && !isManager()) {
    return <Navigate to="/" replace />;
  }
  if (requiredRole === "recruiter" && !isRecruiter()) {
    return <Navigate to="/manager/dashboard" replace />;
  }
  return children;
}

// ─── Recruiter App (the existing full ATS page) ────────────────────────────────

function RecruiterApp() {
  const [view, setView] = useState("analyzer");
  const [requiredExperience, setRequiredExperience] = useState(0.0);
  const [llmProvider, setLlmProvider] = useState("groq");
  const [resumeFile, setResumeFile] = useState(null);
  const [jdText, setJdText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [jdMode, setJdMode] = useState("paste");
  const [selectedJdId, setSelectedJdId] = useState(null);
  const navigate = useNavigate();

  // Batch mode state
  const [analysisMode, setAnalysisMode] = useState("single");
  const [batchResumeFiles, setBatchResumeFiles] = useState([]);
  const [batchJdText, setBatchJdText] = useState("");
  const [batchJdMode, setBatchJdMode] = useState("paste");
  const [batchSelectedJdId, setBatchSelectedJdId] = useState(null);
  const [batchResult, setBatchResult] = useState(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);

  const handleLogout = () => {
    logout();
    navigate("/", { replace: true });
  };

  const handleAnalyze = async () => {
    setError("");
    if (!resumeFile) { setError("Please upload a resume (PDF) to continue."); return; }
    if (jdMode === "library" && !selectedJdId) {
      setError("Please select a JD from the library to continue.");
      return;
    }
    if (jdMode === "paste" && !jdText.trim()) {
      setError("Please paste a job description to continue.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeResume({
        resumeFile,
        jdText: jdMode === "paste" ? jdText : null,
        jdId: jdMode === "library" ? selectedJdId : null,
        requiredExperience,
        llmProvider,
      });
      setResult(data);
    } catch (err) {
      setError(`❌ Pipeline error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleBatchAnalyze = async () => {
    setError("");
    if (batchResumeFiles.length < 2) {
      setError("Upload at least 2 resumes for batch analysis.");
      return;
    }
    if (batchResumeFiles.length > 20) {
      setError("Maximum 20 resumes per batch.");
      return;
    }
    if (batchJdMode === "library" && !batchSelectedJdId) {
      setError("Please select a JD from the library.");
      return;
    }
    if (batchJdMode === "paste" && !batchJdText.trim()) {
      setError("Please paste a job description.");
      return;
    }
    setBatchLoading(true);
    setBatchResult(null);
    setSelectedCandidate(null);
    try {
      const data = await analyzeBatch({
        resumeFiles: batchResumeFiles,
        jdText: batchJdMode === "paste" ? batchJdText : null,
        jdId: batchJdMode === "library" ? batchSelectedJdId : null,
        requiredExperience,
        llmProvider,
        enableLlm: true,
      });
      setBatchResult(data);
    } catch (err) {
      setError(`❌ Batch analysis failed: ${err.message}`);
    } finally {
      setBatchLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Ambient background glow */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-indigo-600/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-purple-600/5 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Top navigation bar */}
        <div className="flex justify-between items-center mb-2 gap-3">
          <div className="flex gap-2">
            <button
              id="nav-analyzer"
              onClick={() => setView("analyzer")}
              className={`text-sm font-medium px-3 py-1.5 rounded-lg border transition-all ${
                view === "analyzer"
                  ? "bg-indigo-600 text-white border-indigo-600"
                  : "text-slate-400 border-slate-700 hover:border-indigo-500/50"
              }`}
            >
              🚀 Analyzer
            </button>
            <button
              id="nav-history"
              onClick={() => setView("history")}
              className={`text-sm font-medium px-3 py-1.5 rounded-lg border transition-all ${
                view === "history"
                  ? "bg-indigo-600 text-white border-indigo-600"
                  : "text-slate-400 border-slate-700 hover:border-indigo-500/50"
              }`}
            >
              📋 History
            </button>
            <button
              id="nav-jd-library"
              onClick={() => setView("jd-library")}
              className={`text-sm font-medium px-3 py-1.5 rounded-lg border transition-all ${
                view === "jd-library"
                  ? "bg-indigo-600 text-white border-indigo-600"
                  : "text-slate-400 border-slate-700 hover:border-indigo-500/50"
              }`}
            >
              📚 JD Library
            </button>
          </div>
          <div className="flex items-center gap-3">
            {/* Role badge */}
            <span className="hidden sm:inline-flex items-center gap-1.5 text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 px-2.5 py-1 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
              Recruiter
            </span>
            <span className="text-slate-500 text-sm">👤 {getUserEmail()}</span>
            <button
              id="logout-btn"
              onClick={handleLogout}
              className="text-xs text-slate-400 hover:text-red-400 border border-slate-700 hover:border-red-500/50 rounded-lg px-3 py-1.5 transition-all"
            >
              Logout
            </button>
          </div>
        </div>

        <Header />

        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
          {/* Sidebar */}
          <div className="order-2 lg:order-1">
            <div className="lg:sticky lg:top-6">
              <div className="glass rounded-xl p-6 space-y-4 border border-slate-700/50">
                <h3 className="text-sm font-semibold text-slate-300">⚙️ Configuration</h3>
                <div className="space-y-2">
                  <label className="text-xs text-slate-400">Required Experience (years)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.5"
                    value={requiredExperience}
                    onChange={(e) => setRequiredExperience(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-slate-400">LLM Model</label>
                  <select
                    value={llmProvider}
                    onChange={(e) => setLlmProvider(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                  >
                    <option value="groq">Groq (Llama 3.1)</option>
                    <option value="openai">OpenAI (GPT-4o mini)</option>
                    <option value="ollama">Ollama (Local)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <main className="order-1 lg:order-2 space-y-6">
            {view === "analyzer" ? (
              <>
                {/* Candidate detail view (batch) */}
                {selectedCandidate ? (
                  <CandidateReport
                    candidate={selectedCandidate}
                    onBack={() => setSelectedCandidate(null)}
                  />
                ) : (
                  <>
                    {/* Single / Batch mode toggle */}
                    <div className="flex mb-1 rounded-xl overflow-hidden border border-slate-700 w-fit">
                      <button
                        id="mode-single"
                        onClick={() => { setAnalysisMode("single"); setError(""); }}
                        className={`py-2 px-5 text-sm font-medium transition-all duration-300 ${
                          analysisMode === "single"
                            ? "bg-indigo-600 text-white"
                            : "bg-slate-800 text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        📄 Single Resume
                      </button>
                      <button
                        id="mode-batch"
                        onClick={() => { setAnalysisMode("batch"); setError(""); }}
                        className={`py-2 px-5 text-sm font-medium transition-all duration-300 ${
                          analysisMode === "batch"
                            ? "bg-indigo-600 text-white"
                            : "bg-slate-800 text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        📚 Batch Resumes
                      </button>
                    </div>

                    {/* ── SINGLE MODE ── */}
                    {analysisMode === "single" && (
                      <>
                        <UploadArea
                          resumeFile={resumeFile}
                          setResumeFile={setResumeFile}
                          jdText={jdText}
                          setJdText={setJdText}
                          jdMode={jdMode}
                          setJdMode={setJdMode}
                          selectedJdId={selectedJdId}
                          setSelectedJdId={setSelectedJdId}
                        />

                        {error && (
                          <div className="rounded-xl bg-red-500/10 border border-red-500/30 px-5 py-3.5 text-sm text-red-300">
                            {error}
                          </div>
                        )}

                        <button
                          id="analyze-btn"
                          onClick={handleAnalyze}
                          disabled={loading}
                          className={`w-full py-4 rounded-xl font-semibold text-base transition-all duration-300 cursor-pointer ${
                            loading
                              ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                              : "bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-indigo-600/25 animate-pulse-glow hover:shadow-indigo-500/40"
                          }`}
                        >
                          {loading ? (
                            <span className="flex items-center justify-center gap-3">
                              <svg className="animate-spin-slow h-5 w-5" viewBox="0 0 24 24" fill="none">
                                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
                              </svg>
                              Analyzing — extracting, embedding, and reasoning...
                            </span>
                          ) : (
                            "🚀 Analyze Resume"
                          )}
                        </button>

                        {result && (
                          <div className="space-y-6 pt-2">
                            <div className="flex items-center gap-3 mb-2">
                              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />
                              <h2 className="text-xl font-bold text-white tracking-tight">📊 Analysis Results</h2>
                              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />
                            </div>

                            <ScoreCards result={result} />
                            <ScoreBreakdown result={result} />
                            <ResumeInsights result={result} />
                            <RawJson result={result} />

                            <div className="pt-8 pb-4 flex justify-center">
                              <button
                                onClick={() => { setResult(null); setResumeFile(null); setJdText(""); }}
                                className="flex items-center gap-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl border border-slate-700 shadow-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                              >
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                <span className="font-medium">Analyze Another Resume</span>
                              </button>
                            </div>
                          </div>
                        )}
                      </>
                    )}

                    {/* ── BATCH MODE ── */}
                    {analysisMode === "batch" && (
                      <>
                        <BatchUploadArea
                          resumeFiles={batchResumeFiles}
                          setResumeFiles={setBatchResumeFiles}
                          jdText={batchJdText}
                          setJdText={setBatchJdText}
                          jdMode={batchJdMode}
                          setJdMode={setBatchJdMode}
                          selectedJdId={batchSelectedJdId}
                          setSelectedJdId={setBatchSelectedJdId}
                        />

                        {error && (
                          <div className="rounded-xl bg-red-500/10 border border-red-500/30 px-5 py-3.5 text-sm text-red-300">
                            {error}
                          </div>
                        )}

                        <button
                          id="batch-analyze-btn"
                          onClick={handleBatchAnalyze}
                          disabled={batchLoading}
                          className={`w-full py-4 rounded-xl font-semibold text-base transition-all duration-300 cursor-pointer ${
                            batchLoading
                              ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                              : "bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-indigo-600/25 animate-pulse-glow hover:shadow-indigo-500/40"
                          }`}
                        >
                          {batchLoading ? (
                            <span className="flex items-center justify-center gap-3">
                              <svg className="animate-spin-slow h-5 w-5" viewBox="0 0 24 24" fill="none">
                                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
                              </svg>
                              Analyzing {batchResumeFiles.length} resumes — this may take a few minutes...
                            </span>
                          ) : (
                            `🚀 Analyze ${batchResumeFiles.length} Resume${batchResumeFiles.length !== 1 ? "s" : ""}`
                          )}
                        </button>

                        {batchResult && (
                          <BatchResults
                            batchResult={batchResult}
                            onViewCandidate={(c) => setSelectedCandidate(c)}
                          />
                        )}
                      </>
                    )}
                  </>
                )}
              </>
            ) : view === "history" ? (
              <HistoryPage onBack={() => setView("analyzer")} />
            ) : (
              <JDLibraryManager />
            )}
          </main>
        </div>

        <footer className="mt-12 pb-6 text-center">
          <p className="text-xs text-slate-600">
            AI ATS Analyzer · Built with FastAPI + React + LangChain
          </p>
        </footer>
      </div>
    </div>
  );
}

// ─── Recruiter Login Wrapper ───────────────────────────────────────────────────

function RecruiterLoginRoute() {
  const navigate = useNavigate();
  // If already logged in as manager, go to manager dashboard
  if (isLoggedIn() && isManager()) return <Navigate to="/manager/dashboard" replace />;
  // If already logged in as recruiter, go to recruiter dashboard
  if (isLoggedIn() && isRecruiter()) return <Navigate to="/dashboard" replace />;

  return <LoginPage onLogin={() => navigate("/dashboard", { replace: true })} />;
}

// ─── Manager Login Wrapper ─────────────────────────────────────────────────────

function ManagerLoginRoute() {
  const navigate = useNavigate();
  if (isLoggedIn() && isManager()) return <Navigate to="/manager/dashboard" replace />;
  if (isLoggedIn() && isRecruiter()) return <Navigate to="/dashboard" replace />;

  return <ManagerLoginPage onLogin={() => navigate("/manager/dashboard", { replace: true })} />;
}

// ─── Manager Dashboard Wrapper ─────────────────────────────────────────────────

function ManagerDashboardRoute() {
  const navigate = useNavigate();
  return (
    <ProtectedRoute requiredRole="manager">
      <ManagerDashboard onLogout={() => navigate("/manager", { replace: true })} />
    </ProtectedRoute>
  );
}

// ─── Root App ─────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Recruiter routes */}
        <Route path="/" element={<RecruiterLoginRoute />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute requiredRole="recruiter">
              <RecruiterApp />
            </ProtectedRoute>
          }
        />

        {/* Manager routes */}
        <Route path="/manager" element={<ManagerLoginRoute />} />
        <Route path="/manager/dashboard" element={<ManagerDashboardRoute />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
