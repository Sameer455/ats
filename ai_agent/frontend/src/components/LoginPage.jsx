import { useState } from "react";
import { login, signup } from "../auth";

export default function LoginPage({ onLogin }) {
  // Default mode aligns with the provided design (register view first)
  const [mode, setMode] = useState("register");
  const [form, setForm] = useState({ email: "", password: "", firstName: "", lastName: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handle = async () => {
    setError("");
    if (!form.email.trim()) { setError("Email is required"); return; }
    if (!form.password.trim()) { setError("Password is required"); return; }

    // Password validation rules for registration
    if (mode === "register") {
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
        await login(form.email, form.password);
      } else {
        await signup(form.email, form.password);
        await login(form.email, form.password);
      }
      onLogin();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    // Full‑page background image (background image file should be placed at public/bg.png)
    <div
      className="min-h-screen flex items-center justify-center p-4 font-sans relative"
      style={{ backgroundImage: "url('/bg.png')", backgroundSize: "cover", backgroundPosition: "center" }}
    >
      {/* Dark overlay for readability */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-[2px]" />


      {/* Floating & Transparent authentication card */}
      <div className="relative z-10 w-full max-w-[420px] bg-[#2A2634]/60 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-white/10">
        <h1 className="text-4xl font-semibold text-white mb-3">
          {mode === "login" ? "Welcome back" : "Create an account"}
        </h1>
        <p className="text-[#A19DAB] mb-8">
          {mode === "login" ? "Don't have an account? " : "Already have an account? "}
          <button
            onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
            className="text-[#9F8BE4] hover:text-white underline decoration-[#9F8BE4]/50 transition-colors"
          >
            {mode === "login" ? "Sign up" : "Log in"}
          </button>
        </p>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-300 mb-6">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {mode === "register" && (
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="First name"
                value={form.firstName}
                onChange={e => setForm({ ...form, firstName: e.target.value })}
                className="w-1/2 bg-[#383344]/80 border border-transparent focus:border-[#7052C4] rounded-lg px-4 py-3.5 text-sm text-white placeholder-[#7C7885] focus:outline-none transition-all"
              />
              <input
                type="text"
                placeholder="Last name"
                value={form.lastName}
                onChange={e => setForm({ ...form, lastName: e.target.value })}
                className="w-1/2 bg-[#383344]/80 border border-transparent focus:border-[#7052C4] rounded-lg px-4 py-3.5 text-sm text-white placeholder-[#7C7885] focus:outline-none transition-all"
              />
            </div>
          )}
          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={e => setForm({ ...form, email: e.target.value })}
            className="w-full bg-[#383344]/80 border border-transparent focus:border-[#7052C4] rounded-lg px-4 py-3.5 text-sm text-white placeholder-[#7C7885] focus:outline-none transition-all"
          />
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              placeholder={mode === "login" ? "Password" : "Enter your password"}
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              onKeyDown={e => e.key === "Enter" && handle()}
              className="w-full bg-[#383344]/80 border border-transparent focus:border-[#7052C4] rounded-lg px-4 py-3.5 text-sm text-white placeholder-[#7C7885] focus:outline-none transition-all pr-12 [&::-ms-reveal]:hidden [&::-webkit-contacts-auto-fill-button]:hidden"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-[#7C7885] hover:text-white transition-colors focus:outline-none"
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
          {mode === "register" && (
            <label className="flex items-center gap-3 mt-4 cursor-pointer group">
              <div className="relative flex items-center justify-center">
                <input type="checkbox" className="peer appearance-none w-5 h-5 border-2 border-[#7C7885] rounded bg-transparent checked:bg-[#7052C4] checked:border-[#7052C4] transition-colors cursor-pointer" defaultChecked />
                <svg className="absolute w-3 h-3 text-white pointer-events-none opacity-0 peer-checked:opacity-100 transition-opacity" viewBox="0 0 14 10" fill="none">
                  <path d="M1 5L4.5 8.5L13 1" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <span className="text-sm text-[#A19DAB]">
                I agree to the <a href="#" className="text-[#9F8BE4] hover:underline">Terms & Conditions</a>
              </span>
            </label>
          )}
          <button
            onClick={handle}
            disabled={loading}
            className="w-full py-3.5 mt-6 bg-[#7052C4] hover:bg-[#6042A4] rounded-lg text-white font-medium transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-[#7052C4]/20"
          >
            {loading ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}
          </button>
          <div className="flex items-center gap-4 my-8">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-xs text-[#7C7885]">Or register with</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>
          <div className="flex gap-4">
            <button className="flex-1 py-3 border border-white/10 bg-white/5 rounded-lg flex items-center justify-center gap-3 text-white hover:bg-white/10 transition-colors">
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Google
            </button>
          </div>
          <div className="mt-6 pt-5 border-t border-white/8 text-center">
            <p className="text-xs text-[#7C7885]">
              Are you a Hiring Manager?{" "}
              <a
                href="/manager"
                className="text-emerald-400 hover:text-emerald-300 underline decoration-emerald-500/40 transition-colors"
              >
                Sign in here
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

