export default function ConfigPanel({
  llmProvider,
  setLlmProvider,
  groqApiKey,
  setGroqApiKey,
  openaiApiKey,
  setOpenaiApiKey,
  enableLlm,
  setEnableLlm,
  requiredExperience,
  setRequiredExperience,
}) {
  return (
    <aside className="glass rounded-2xl p-6 space-y-6">
      <h2 className="text-lg font-semibold text-indigo-300 flex items-center gap-2">
        <span className="text-xl">⚙️</span> Configuration
      </h2>

      {/* LLM Provider */}
      <div>
        <label htmlFor="llm-provider" className="block text-sm font-medium text-slate-400 mb-1.5">
          LLM Provider
        </label>
        <select
          id="llm-provider"
          value={llmProvider}
          onChange={(e) => setLlmProvider(e.target.value)}
          className="w-full bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all cursor-pointer"
        >
          <option value="groq">Groq (Free — Fastest)</option>
          <option value="openai">OpenAI (Paid)</option>
          <option value="ollama">Ollama (Local)</option>
        </select>
      </div>

      {/* Groq API Key */}
      {llmProvider === "groq" && (
        <div>
          <label htmlFor="groq-key" className="block text-sm font-medium text-slate-400 mb-1.5">
            Groq API Key
          </label>
          <input
            id="groq-key"
            type="password"
            value={groqApiKey}
            onChange={(e) => setGroqApiKey(e.target.value)}
            placeholder="Overrides .env value"
            className="w-full bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
          />
        </div>
      )}

      {/* OpenAI API Key */}
      {llmProvider === "openai" && (
        <div>
          <label htmlFor="openai-key" className="block text-sm font-medium text-slate-400 mb-1.5">
            OpenAI API Key
          </label>
          <input
            id="openai-key"
            type="password"
            value={openaiApiKey}
            onChange={(e) => setOpenaiApiKey(e.target.value)}
            placeholder="sk-..."
            className="w-full bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
          />
        </div>
      )}

      {/* Enable LLM Toggle */}
      <div className="flex items-center justify-between">
        <label htmlFor="enable-llm" className="text-sm font-medium text-slate-400">
          AI Analysis (LLM)
        </label>
        <button
          id="enable-llm"
          role="switch"
          aria-checked={enableLlm}
          onClick={() => setEnableLlm(!enableLlm)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900 ${
            enableLlm ? "bg-indigo-500" : "bg-slate-600"
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-lg transition-transform duration-300 ${
              enableLlm ? "translate-x-6" : "translate-x-1"
            }`}
          />
        </button>
      </div>

      {/* Required Experience */}
      <div>
        <label htmlFor="required-exp" className="block text-sm font-medium text-slate-400 mb-1.5">
          Required Experience
        </label>
        <div className="flex items-center gap-3">
          <input
            id="required-exp"
            type="range"
            min="0"
            max="30"
            step="0.5"
            value={requiredExperience}
            onChange={(e) => setRequiredExperience(parseFloat(e.target.value))}
            className="flex-1 h-2 rounded-lg appearance-none cursor-pointer accent-indigo-500 bg-slate-700"
          />
          <span className="text-sm font-semibold text-indigo-300 w-14 text-right">
            {requiredExperience} yrs
          </span>
        </div>
      </div>

      {/* Divider + About */}
      <div className="border-t border-slate-700/60 pt-4">
        <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">About</p>
        <p className="text-xs text-slate-500 leading-relaxed">
          PDF Parser → NLP → Embeddings → Skill Gap → LangChain LLM → Insights
        </p>
      </div>
    </aside>
  );
}
