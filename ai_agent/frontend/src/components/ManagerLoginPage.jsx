import { useState } from "react";
import { managerLogin, managerSignup } from "../auth";

export default function ManagerLoginPage({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", name: "", department: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const departments = [
    "Engineering", "Product", "Data Science", "Design", "Marketing",
    "Sales", "Finance", "HR", "Operations", "Legal"
  ];

  const handle = async () => {
    setError("");
    if (!form.email.trim()) { setError("Email is required"); return; }
    if (!form.password.trim()) { setError("Password is required"); return; }
    if (mode === "register") {
      if (!form.name.trim()) { setError("Full name is required"); return; }
      if (!form.department) { setError("Department is required"); return; }
      const hasNumber = /[0-9]/.test(form.password);
      const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(form.password);
      if (form.password.length < 8 || !hasNumber || !hasSpecial) {
        setError("Password must be at least 8 characters, include a number and a special character.");
        return;
      }
    }

    setLoading(true);
    try {
      if (mode === "login") {
        await managerLogin(form.email, form.password);
      } else {
        await managerSignup(form.email, form.password, form.name, form.department);
        await managerLogin(form.email, form.password);
        localStorage.setItem("managerName", form.name);
        localStorage.setItem("managerDepartment", form.department);
      }
      onLogin();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4 font-sans relative overflow-hidden"
      style={{
        background: "linear-gradient(135deg, #0a0e1a 0%, #0d1b2a 40%, #1a0a2e 100%)",
      }}
    >
      {/* Animated ambient glows */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-[600px] h-[600px] bg-emerald-600/8 rounded-full blur-[140px] animate-pulse" />
        <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] bg-teal-600/8 rounded-full blur-[140px] animate-pulse" style={{ animationDelay: "1s" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-cyan-600/5 rounded-full blur-[100px]" />
      </div>

      {/* Grid overlay */}
      <div className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
          backgroundSize: "48px 48px"
        }}
      />

      <div className="relative z-10 w-full max-w-[460px]">
        {/* Header badge */}
        <div className="flex justify-center mb-6">
          <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full px-4 py-1.5">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-emerald-400 text-xs font-semibold tracking-wide uppercase">Hiring Manager Portal</span>
          </div>
        </div>

        {/* Card */}
        <div className="bg-white/[0.04] backdrop-blur-2xl rounded-3xl p-8 shadow-2xl border border-white/10">
          {/* Icon */}
          <div className="flex justify-center mb-5">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
              <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
          </div>

          <h1 className="text-3xl font-bold text-white text-center mb-1">
            {mode === "login" ? "Manager Sign In" : "Register as Manager"}
          </h1>
          <p className="text-slate-400 text-sm text-center mb-6">
            {mode === "login" ? "Don't have a manager account? " : "Already registered? "}
            <button
              onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
              className="text-emerald-400 hover:text-emerald-300 underline decoration-emerald-500/40 transition-colors"
            >
              {mode === "login" ? "Register here" : "Sign in"}
            </button>
          </p>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-sm text-red-300 mb-5 flex items-start gap-2">
              <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </div>
          )}

          <div className="space-y-4">
            {mode === "register" && (
              <>
                <input
                  id="manager-name"
                  type="text"
                  placeholder="Full name"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  className="w-full bg-white/[0.06] border border-white/10 focus:border-emerald-500/60 rounded-xl px-4 py-3.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-all"
                />
                <select
                  id="manager-department"
                  value={form.department}
                  onChange={e => setForm({ ...form, department: e.target.value })}
                  className="w-full bg-white/[0.06] border border-white/10 focus:border-emerald-500/60 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none transition-all appearance-none cursor-pointer"
                  style={{ backgroundImage: "none" }}
                >
                  <option value="" className="bg-slate-900">Select department</option>
                  {departments.map(d => (
                    <option key={d} value={d} className="bg-slate-900">{d}</option>
                  ))}
                </select>
              </>
            )}

            <input
              id="manager-email"
              type="email"
              placeholder="Work email"
              value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
              className="w-full bg-white/[0.06] border border-white/10 focus:border-emerald-500/60 rounded-xl px-4 py-3.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-all"
            />

            <div className="relative">
              <input
                id="manager-password"
                type={showPassword ? "text" : "password"}
                placeholder="Password"
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
                onKeyDown={e => e.key === "Enter" && handle()}
                className="w-full bg-white/[0.06] border border-white/10 focus:border-emerald-500/60 rounded-xl px-4 py-3.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-all pr-12"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors"
              >
                {showPassword ? (
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0Z" />
                  </svg>
                )}
              </button>
            </div>

            <button
              id="manager-auth-btn"
              onClick={handle}
              disabled={loading}
              className="w-full py-3.5 mt-2 rounded-xl text-white font-semibold text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: "linear-gradient(135deg, #10b981 0%, #0d9488 100%)",
                boxShadow: "0 4px 24px rgba(16, 185, 129, 0.25)",
              }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
                  </svg>
                  Please wait...
                </span>
              ) : (
                mode === "login" ? "Sign In to Dashboard" : "Create Manager Account"
              )}
            </button>
          </div>

          {/* Back to recruiter login */}
          <div className="mt-6 pt-5 border-t border-white/8 text-center">
            <a href="/" className="text-xs text-slate-500 hover:text-slate-400 transition-colors">
              ← Back to Recruiter Login
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
