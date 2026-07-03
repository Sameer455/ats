import { useRef, useState, useEffect } from "react";
import { getJDCategories, getJDLibrary, getJDById } from "../api";

export default function BatchUploadArea({
  resumeFiles,
  setResumeFiles,
  jdText,
  setJdText,
  jdMode,
  setJdMode,
  selectedJdId,
  setSelectedJdId,
}) {
  const fileInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);

  // JD library state
  const [categories, setCategories] = useState([]);
  const [library, setLibrary] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [jdPreview, setJdPreview] = useState("");
  const [libraryLoading, setLibraryLoading] = useState(false);

  useEffect(() => {
    async function loadLibraryData() {
      setLibraryLoading(true);
      try {
        const [cats, lib] = await Promise.all([
          getJDCategories(),
          getJDLibrary(),
        ]);
        setCategories(cats);
        setLibrary(lib);
      } catch (err) {
        console.error("Failed to load JD library:", err);
      } finally {
        setLibraryLoading(false);
      }
    }
    loadLibraryData();
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const dropped = Array.from(e.dataTransfer.files).filter((f) =>
      f.name.match(/\.(pdf|docx)$/i)
    );
    if (dropped.length > 0) {
      setResumeFiles((prev) => [...prev, ...dropped]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => setDragActive(false);

  const handleFileSelect = (e) => {
    const selected = Array.from(e.target.files).filter((f) =>
      f.name.match(/\.(pdf|docx)$/i)
    );
    if (selected.length > 0) {
      setResumeFiles((prev) => [...prev, ...selected]);
    }
    e.target.value = "";
  };

  const removeFile = (index) => {
    setResumeFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const filteredJDs =
    selectedCategory !== null
      ? library.find((g) => g.category_id === selectedCategory)?.jds || []
      : [];

  const handleJDSelect = async (jdId) => {
    setSelectedJdId(jdId);
    try {
      const jd = await getJDById(jdId);
      setJdPreview(
        jd.jd_text.length > 300
          ? jd.jd_text.slice(0, 300) + "..."
          : jd.jd_text
      );
    } catch {
      setJdPreview("Failed to load preview.");
    }
  };

  const countColor =
    resumeFiles.length > 20
      ? "text-red-400"
      : resumeFiles.length >= 2
      ? "text-green-400"
      : "text-yellow-400";

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Resume Upload Zone */}
      <div>
        <h3 className="text-base font-semibold text-slate-300 mb-3 flex items-center gap-2">
          <span>📄</span> Upload Resumes
          <span className={`ml-auto text-xs font-normal ${countColor}`}>
            {resumeFiles.length} selected (min 2, max 20)
          </span>
        </h3>

        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`glass rounded-xl p-8 text-center cursor-pointer border-2 border-dashed transition-all duration-300 group ${
            dragActive
              ? "border-indigo-400 bg-indigo-500/10"
              : "border-slate-700 hover:border-indigo-500/50"
          }`}
        >
          <input
            ref={fileInputRef}
            id="batch-resume-upload"
            type="file"
            accept=".pdf,.docx"
            multiple
            className="hidden"
            onChange={handleFileSelect}
          />

          <div className="text-4xl mb-3 group-hover:scale-110 transition-transform duration-300">
            {resumeFiles.length > 0 ? "✅" : "📁"}
          </div>

          <p className="text-slate-400 font-medium">
            {resumeFiles.length > 0
              ? "Drop more files or click to add"
              : "Drop PDF / DOCX files here"}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            or click to browse · accepts PDF and DOCX
          </p>
        </div>

        {/* Validation banners */}
        {resumeFiles.length > 0 && resumeFiles.length < 2 && (
          <div className="mt-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30 px-4 py-2 text-xs text-yellow-300">
            ⚠️ Upload at least 2 resumes for batch analysis
          </div>
        )}
        {resumeFiles.length > 20 && (
          <div className="mt-3 rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2 text-xs text-red-300">
            ❌ Maximum 20 resumes per batch — remove {resumeFiles.length - 20} file(s)
          </div>
        )}

        {/* File list */}
        {resumeFiles.length > 0 && (
          <div className="mt-3 space-y-1.5 max-h-60 overflow-y-auto">
            {resumeFiles.map((file, idx) => (
              <div
                key={`${file.name}-${idx}`}
                className="flex items-center justify-between glass rounded-lg px-3 py-2 border border-slate-700/50"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-xs">
                    {file.name.endsWith(".pdf") ? "📕" : "📘"}
                  </span>
                  <span className="text-sm text-slate-300 truncate">
                    {file.name}
                  </span>
                  <span className="text-xs text-slate-500 shrink-0">
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(idx);
                  }}
                  className="text-slate-500 hover:text-red-400 transition-colors ml-2 text-lg leading-none"
                  title="Remove file"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Job Description Section */}
      <div>
        <h3 className="text-base font-semibold text-slate-300 mb-3 flex items-center gap-2">
          <span>📋</span> Job Description
        </h3>

        {/* Mode Toggle */}
        <div className="flex mb-3 rounded-xl overflow-hidden border border-slate-700">
          <button
            id="batch-jd-mode-paste"
            type="button"
            onClick={() => {
              setJdMode("paste");
              setSelectedJdId(null);
              setJdPreview("");
            }}
            className={`flex-1 py-2 px-4 text-sm font-medium transition-all duration-300 ${
              jdMode === "paste"
                ? "bg-indigo-600 text-white"
                : "bg-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            ✏️ Paste JD
          </button>
          <button
            id="batch-jd-mode-library"
            type="button"
            onClick={() => {
              setJdMode("library");
              setJdText("");
            }}
            className={`flex-1 py-2 px-4 text-sm font-medium transition-all duration-300 ${
              jdMode === "library"
                ? "bg-indigo-600 text-white"
                : "bg-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            📚 From Library
          </button>
        </div>

        {/* Paste mode */}
        {jdMode === "paste" && (
          <>
            <textarea
              id="batch-jd-text"
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the full job description here..."
              rows={7}
              className="w-full glass rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none transition-all"
            />
            {jdText && (
              <p className="text-xs text-slate-500 mt-1.5">
                📝 {jdText.split(/\s+/).filter(Boolean).length} words detected
              </p>
            )}
          </>
        )}

        {/* Library mode */}
        {jdMode === "library" && (
          <div className="glass rounded-xl p-4 border border-slate-700 space-y-4">
            {libraryLoading ? (
              <div className="flex items-center justify-center py-8">
                <svg className="animate-spin-slow h-6 w-6 text-indigo-400" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
                </svg>
                <span className="ml-2 text-sm text-slate-400">Loading library...</span>
              </div>
            ) : categories.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-slate-500 text-sm">No categories yet.</p>
                <p className="text-slate-600 text-xs mt-1">
                  Go to JD Library tab to add categories and JDs.
                </p>
              </div>
            ) : (
              <>
                {/* Category Dropdown */}
                <div className="space-y-1.5">
                  <label className="text-xs text-slate-400 font-medium">Category</label>
                  <select
                    id="batch-jd-library-category"
                    value={selectedCategory ?? ""}
                    onChange={(e) => {
                      const val = e.target.value ? parseInt(e.target.value) : null;
                      setSelectedCategory(val);
                      setSelectedJdId(null);
                      setJdPreview("");
                    }}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                  >
                    <option value="">— Select a category —</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name} ({cat.jd_count} JDs)
                      </option>
                    ))}
                  </select>
                </div>

                {/* JD Dropdown */}
                {selectedCategory !== null && (
                  <div className="space-y-1.5">
                    <label className="text-xs text-slate-400 font-medium">Job Description</label>
                    {filteredJDs.length === 0 ? (
                      <p className="text-xs text-slate-500 py-2">No JDs in this category.</p>
                    ) : (
                      <select
                        id="batch-jd-library-select"
                        value={selectedJdId ?? ""}
                        onChange={(e) => {
                          const val = e.target.value ? parseInt(e.target.value) : null;
                          if (val) handleJDSelect(val);
                          else {
                            setSelectedJdId(null);
                            setJdPreview("");
                          }
                        }}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                      >
                        <option value="">— Select a JD —</option>
                        {filteredJDs.map((jd) => (
                          <option key={jd.id} value={jd.id}>
                            {jd.title} (used {jd.usage_count}×)
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                )}

                {/* Preview */}
                {jdPreview && (
                  <div className="space-y-1.5">
                    <label className="text-xs text-slate-400 font-medium">Preview</label>
                    <div className="bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2.5 text-xs text-slate-300 leading-relaxed max-h-32 overflow-y-auto">
                      {jdPreview}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* JD validation */}
        {jdMode === "paste" && !jdText.trim() && resumeFiles.length >= 2 && (
          <div className="mt-3 rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2 text-xs text-red-300">
            ❌ Please paste a job description before analyzing
          </div>
        )}
        {jdMode === "library" && !selectedJdId && resumeFiles.length >= 2 && (
          <div className="mt-3 rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2 text-xs text-red-300">
            ❌ Please select a JD from the library before analyzing
          </div>
        )}
      </div>
    </div>
  );
}
