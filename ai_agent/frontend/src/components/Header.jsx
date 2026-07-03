export default function Header() {
  return (
    <header className="gradient-bg rounded-2xl p-8 text-center mb-8 shadow-2xl shadow-indigo-950/50 relative overflow-hidden">
      {/* Decorative blurred circles */}
      <div className="absolute -top-10 -left-10 w-40 h-40 bg-indigo-500/20 rounded-full blur-3xl" />
      <div className="absolute -bottom-10 -right-10 w-56 h-56 bg-purple-500/15 rounded-full blur-3xl" />

      {/* Top right logo */}
      <img src="/logo1.png" alt="Logo" className="absolute top-4 right-6 h-10 w-auto z-20 object-contain" />

      <div className="relative z-10">
        <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight">
          <span className="inline-block mr-3"></span>
          AI ATS Analyzer
        </h1>
        <p className="mt-3 text-base md:text-lg text-indigo-200/70 font-light tracking-wide">
          Semantic Resume-to-Job Matching · Skill Gap Analysis · LLM-Powered Insights
        </p>
      </div>
    </header>
  );
}
