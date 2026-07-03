import { useState, useEffect } from "react";
import {
  getJDCategories,
  getJDLibrary,
  getJDById,
  createJDCategory,
  createJD,
  deleteJD,
  updateJD,
} from "../api";
import { getUserEmail } from "../auth";

export default function JDLibraryManager() {
  // ── Data state ──────────────────────────────────────────────────────────────
  const [categories, setCategories] = useState([]);
  const [library, setLibrary] = useState([]);
  const [loading, setLoading] = useState(true);

  // ── Create Category form ────────────────────────────────────────────────────
  const [categoryName, setCategoryName] = useState("");
  const [categoryStatus, setCategoryStatus] = useState({ type: "", msg: "" });
  const [categorySubmitting, setCategorySubmitting] = useState(false);

  // ── Upload JD form ──────────────────────────────────────────────────────────
  const [jdCategoryId, setJdCategoryId] = useState("");
  const [jdTitle, setJdTitle] = useState("");
  const [jdTextVal, setJdTextVal] = useState("");
  const [jdStatus, setJdStatus] = useState({ type: "", msg: "" });
  const [jdSubmitting, setJdSubmitting] = useState(false);

  // ── Delete state ────────────────────────────────────────────────────────────
  const [deletingId, setDeletingId] = useState(null);

  // ── Edit state ──────────────────────────────────────────────────────────────
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [editCategoryId, setEditCategoryId] = useState("");
  const [editJdText, setEditJdText] = useState("");
  const [editLoading, setEditLoading] = useState(false);
  const [editSubmitting, setEditSubmitting] = useState(false);
  const [editStatus, setEditStatus] = useState({ type: "", msg: "" });

  // ── Expand / collapse categories ────────────────────────────────────────────
  const [expandedCats, setExpandedCats] = useState({});

  const currentEmail = getUserEmail();

  // ── Load data ───────────────────────────────────────────────────────────────
  async function loadAll() {
    setLoading(true);
    try {
      const [cats, lib] = await Promise.all([
        getJDCategories(),
        getJDLibrary(),
      ]);
      setCategories(cats);
      setLibrary(lib);
    } catch (err) {
      console.error("Failed to load library data:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  // ── Create Category ─────────────────────────────────────────────────────────
  const handleCreateCategory = async (e) => {
    e.preventDefault();
    if (!categoryName.trim()) return;
    setCategorySubmitting(true);
    setCategoryStatus({ type: "", msg: "" });
    try {
      await createJDCategory(categoryName.trim());
      setCategoryStatus({ type: "success", msg: `Category "${categoryName.trim()}" created!` });
      setCategoryName("");
      await loadAll();
    } catch (err) {
      setCategoryStatus({ type: "error", msg: err.message });
    } finally {
      setCategorySubmitting(false);
    }
  };

  // ── Upload JD ───────────────────────────────────────────────────────────────
  const handleCreateJD = async (e) => {
    e.preventDefault();
    if (!jdCategoryId || !jdTitle.trim() || !jdTextVal.trim()) return;
    setJdSubmitting(true);
    setJdStatus({ type: "", msg: "" });
    try {
      await createJD({
        category_id: parseInt(jdCategoryId),
        title: jdTitle.trim(),
        jd_text: jdTextVal.trim(),
      });
      setJdStatus({ type: "success", msg: `JD "${jdTitle.trim()}" saved to library!` });
      setJdTitle("");
      setJdTextVal("");
      setJdCategoryId("");
      await loadAll();
    } catch (err) {
      setJdStatus({ type: "error", msg: err.message });
    } finally {
      setJdSubmitting(false);
    }
  };

  // ── Delete JD ───────────────────────────────────────────────────────────────
  const handleDelete = async (jdId) => {
    if (!window.confirm("Are you sure you want to delete this JD?")) return;
    setDeletingId(jdId);
    try {
      await deleteJD(jdId);
      await loadAll();
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  // ── Edit JD ─────────────────────────────────────────────────────────────────
  const handleStartEdit = async (jdId) => {
    setEditingId(jdId);
    setEditLoading(true);
    setEditStatus({ type: "", msg: "" });
    try {
      const fullJd = await getJDById(jdId);
      setEditTitle(fullJd.title);
      setEditCategoryId(String(fullJd.category_id));
      setEditJdText(fullJd.jd_text);
    } catch (err) {
      setEditStatus({ type: "error", msg: `Failed to load JD: ${err.message}` });
    } finally {
      setEditLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditTitle("");
    setEditCategoryId("");
    setEditJdText("");
    setEditStatus({ type: "", msg: "" });
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editTitle.trim() || !editCategoryId || !editJdText.trim()) return;
    setEditSubmitting(true);
    setEditStatus({ type: "", msg: "" });
    try {
      await updateJD(editingId, {
        category_id: parseInt(editCategoryId),
        title: editTitle.trim(),
        jd_text: editJdText.trim(),
      });
      setEditStatus({ type: "success", msg: "JD updated!" });
      setEditingId(null);
      setEditTitle("");
      setEditCategoryId("");
      setEditJdText("");
      await loadAll();
    } catch (err) {
      setEditStatus({ type: "error", msg: err.message });
    } finally {
      setEditSubmitting(false);
    }
  };

  const toggleCategory = (catId) => {
    setExpandedCats((prev) => ({ ...prev, [catId]: !prev[catId] }));
  };

  // ── Loading skeleton ────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in-up">
        <div className="glass rounded-xl p-6 border border-slate-700/50">
          <div className="flex items-center justify-center py-12">
            <svg className="animate-spin-slow h-8 w-8 text-indigo-400" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
            </svg>
            <span className="ml-3 text-slate-400">Loading JD Library...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* ── Section 1: Create Category ──────────────────────────────────────── */}
      <div className="glass rounded-xl p-6 border border-slate-700/50">
        <h3 className="text-base font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <span>🏷️</span> Create Category
        </h3>
        <form onSubmit={handleCreateCategory} className="flex gap-3">
          <input
            id="new-category-name"
            type="text"
            value={categoryName}
            onChange={(e) => setCategoryName(e.target.value)}
            placeholder="e.g. Backend Engineering"
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
          />
          <button
            id="create-category-btn"
            type="submit"
            disabled={categorySubmitting || !categoryName.trim()}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
              categorySubmitting || !categoryName.trim()
                ? "bg-slate-700 text-slate-500 cursor-not-allowed"
                : "bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-indigo-600/20"
            }`}
          >
            {categorySubmitting ? "Creating..." : "Add Category"}
          </button>
        </form>
        {categoryStatus.msg && (
          <p
            className={`text-xs mt-2 ${
              categoryStatus.type === "success"
                ? "text-emerald-400"
                : "text-red-400"
            }`}
          >
            {categoryStatus.type === "success" ? "✅" : "❌"}{" "}
            {categoryStatus.msg}
          </p>
        )}
      </div>

      {/* ── Section 2: Upload New JD ────────────────────────────────────────── */}
      <div className="glass rounded-xl p-6 border border-slate-700/50">
        <h3 className="text-base font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <span>📝</span> Upload New JD
        </h3>

        {categories.length === 0 ? (
          <p className="text-sm text-slate-500 py-4 text-center">
            Create a category first to upload JDs.
          </p>
        ) : (
          <form onSubmit={handleCreateJD} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs text-slate-400 font-medium">
                Category *
              </label>
              <select
                id="jd-upload-category"
                value={jdCategoryId}
                onChange={(e) => setJdCategoryId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
              >
                <option value="">— Select a category —</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-slate-400 font-medium">
                JD Title *
              </label>
              <input
                id="jd-upload-title"
                type="text"
                value={jdTitle}
                onChange={(e) => setJdTitle(e.target.value)}
                placeholder="e.g. Senior Backend Engineer — Remote"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-slate-400 font-medium">
                JD Text *
              </label>
              <textarea
                id="jd-upload-text"
                value={jdTextVal}
                onChange={(e) => setJdTextVal(e.target.value)}
                placeholder="Paste the full job description here..."
                rows={8}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none transition-all"
              />
            </div>

            <button
              id="save-jd-btn"
              type="submit"
              disabled={
                jdSubmitting ||
                !jdCategoryId ||
                !jdTitle.trim() ||
                !jdTextVal.trim()
              }
              className={`w-full py-3 rounded-xl text-sm font-semibold transition-all duration-300 ${
                jdSubmitting ||
                !jdCategoryId ||
                !jdTitle.trim() ||
                !jdTextVal.trim()
                  ? "bg-slate-700 text-slate-500 cursor-not-allowed"
                  : "bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-indigo-600/20"
              }`}
            >
              {jdSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin-slow h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
                  </svg>
                  Saving...
                </span>
              ) : (
                "💾 Save to Library"
              )}
            </button>

            {jdStatus.msg && (
              <p
                className={`text-xs ${
                  jdStatus.type === "success"
                    ? "text-emerald-400"
                    : "text-red-400"
                }`}
              >
                {jdStatus.type === "success" ? "✅" : "❌"} {jdStatus.msg}
              </p>
            )}
          </form>
        )}
      </div>

      {/* ── Section 3: Browse Library ───────────────────────────────────────── */}
      <div className="glass rounded-xl p-6 border border-slate-700/50">
        <h3 className="text-base font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <span>📚</span> Browse Library
        </h3>

        {library.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-slate-500 text-sm">No JDs in the library yet.</p>
            <p className="text-slate-600 text-xs mt-1">
              Upload your first JD using the form above.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {library.map((group) => {
              const isExpanded = expandedCats[group.category_id] !== false; // default open
              return (
                <div
                  key={group.category_id}
                  className="border border-slate-700/50 rounded-xl overflow-hidden"
                >
                  {/* Category Header */}
                  <button
                    onClick={() => toggleCategory(group.category_id)}
                    className="w-full flex items-center justify-between px-4 py-3 bg-slate-800/50 hover:bg-slate-800 transition-colors text-left"
                  >
                    <span className="text-sm font-medium text-slate-200">
                      {group.category_name}
                      <span className="ml-2 text-xs text-slate-500">
                        ({group.jds.length} JD{group.jds.length !== 1 ? "s" : ""})
                      </span>
                    </span>
                    <svg
                      className={`w-4 h-4 text-slate-500 transition-transform duration-200 ${
                        isExpanded ? "rotate-180" : ""
                      }`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </button>

                  {/* JD List */}
                  {isExpanded && (
                    <div className="divide-y divide-slate-700/30">
                      {group.jds.length === 0 ? (
                        <p className="px-4 py-3 text-xs text-slate-500">
                          No JDs in this category.
                        </p>
                      ) : (
                        group.jds.map((jd) => (
                          <div key={jd.id}>
                            {/* ── Inline Edit Form ──────────────────────── */}
                            {editingId === jd.id ? (
                              <div className="px-4 py-4 bg-slate-800/40 border-l-2 border-indigo-500">
                                {editLoading ? (
                                  <div className="flex items-center gap-2 py-4">
                                    <svg className="animate-spin-slow h-4 w-4 text-indigo-400" viewBox="0 0 24 24" fill="none">
                                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
                                    </svg>
                                    <span className="text-sm text-slate-400">Loading JD details...</span>
                                  </div>
                                ) : (
                                  <form onSubmit={handleSaveEdit} className="space-y-3">
                                    <div className="flex items-center gap-2 mb-2">
                                      <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wide">✏️ Editing JD</span>
                                    </div>

                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                      <div className="space-y-1">
                                        <label className="text-xs text-slate-400 font-medium">Title</label>
                                        <input
                                          id={`edit-title-${jd.id}`}
                                          type="text"
                                          value={editTitle}
                                          onChange={(e) => setEditTitle(e.target.value)}
                                          className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                                        />
                                      </div>
                                      <div className="space-y-1">
                                        <label className="text-xs text-slate-400 font-medium">Category</label>
                                        <select
                                          id={`edit-category-${jd.id}`}
                                          value={editCategoryId}
                                          onChange={(e) => setEditCategoryId(e.target.value)}
                                          className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                                        >
                                          {categories.map((cat) => (
                                            <option key={cat.id} value={cat.id}>
                                              {cat.name}
                                            </option>
                                          ))}
                                        </select>
                                      </div>
                                    </div>

                                    <div className="space-y-1">
                                      <label className="text-xs text-slate-400 font-medium">JD Text</label>
                                      <textarea
                                        id={`edit-jdtext-${jd.id}`}
                                        value={editJdText}
                                        onChange={(e) => setEditJdText(e.target.value)}
                                        rows={6}
                                        className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none transition-all"
                                      />
                                    </div>

                                    <div className="flex items-center gap-2">
                                      <button
                                        id={`save-edit-${jd.id}`}
                                        type="submit"
                                        disabled={editSubmitting || !editTitle.trim() || !editCategoryId || !editJdText.trim()}
                                        className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-all duration-300 ${
                                          editSubmitting || !editTitle.trim() || !editCategoryId || !editJdText.trim()
                                            ? "bg-slate-700 text-slate-500 cursor-not-allowed"
                                            : "bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-500 hover:to-teal-500 shadow-lg shadow-emerald-600/20"
                                        }`}
                                      >
                                        {editSubmitting ? "Saving..." : "💾 Save Changes"}
                                      </button>
                                      <button
                                        type="button"
                                        onClick={handleCancelEdit}
                                        disabled={editSubmitting}
                                        className="px-4 py-1.5 rounded-lg text-xs font-medium border border-slate-600 text-slate-400 hover:bg-slate-700 hover:text-slate-200 transition-all"
                                      >
                                        Cancel
                                      </button>
                                    </div>

                                    {editStatus.msg && (
                                      <p className={`text-xs ${editStatus.type === "success" ? "text-emerald-400" : "text-red-400"}`}>
                                        {editStatus.type === "success" ? "✅" : "❌"} {editStatus.msg}
                                      </p>
                                    )}
                                  </form>
                                )}
                              </div>
                            ) : (
                              /* ── Normal JD Row ────────────────────────── */
                              <div className="px-4 py-3 flex items-center justify-between gap-3 hover:bg-slate-800/30 transition-colors">
                                <div className="min-w-0 flex-1">
                                  <p className="text-sm font-medium text-slate-200 truncate">
                                    {jd.title}
                                  </p>
                                  <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                                    <span>👤 {jd.uploaded_by_name}</span>
                                    <span>🔄 Used {jd.usage_count}×</span>
                                    <span>
                                      📅{" "}
                                      {new Date(jd.created_at).toLocaleDateString()}
                                    </span>
                                  </div>
                                </div>

                                {/* Action buttons — only for own JDs */}
                                {jd.uploaded_by_name === currentEmail && (
                                  <div className="flex items-center gap-2">
                                    <button
                                      id={`edit-jd-${jd.id}`}
                                      onClick={() => handleStartEdit(jd.id)}
                                      disabled={editingId !== null}
                                      className={`text-xs px-2.5 py-1 rounded-lg border transition-all ${
                                        editingId !== null
                                          ? "border-slate-700 text-slate-600 cursor-not-allowed"
                                          : "border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/10 hover:border-indigo-500/50"
                                      }`}
                                    >
                                      ✏️ Edit
                                    </button>
                                    <button
                                      onClick={() => handleDelete(jd.id)}
                                      disabled={deletingId === jd.id}
                                      className={`text-xs px-2.5 py-1 rounded-lg border transition-all ${
                                        deletingId === jd.id
                                          ? "border-slate-700 text-slate-600 cursor-not-allowed"
                                          : "border-red-500/30 text-red-400 hover:bg-red-500/10 hover:border-red-500/50"
                                      }`}
                                    >
                                      {deletingId === jd.id ? "..." : "🗑️ Delete"}
                                    </button>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
