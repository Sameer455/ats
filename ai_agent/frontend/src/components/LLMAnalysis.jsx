/**
 * Renders LLM analysis markdown as HTML.
 * Simple markdown-to-HTML converter for the analysis output.
 */
function renderMarkdown(text) {
  if (!text) return "";

  return text
    // Headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Lists
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
    // Paragraphs (double newline)
    .replace(/\n\n/g, '</p><p>')
    // Single newlines within list context
    .replace(/\n/g, '<br/>')
    // Wrap
    .replace(/^/, '<p>')
    .replace(/$/, '</p>');
}

export default function LLMAnalysis({ analysis }) {
  if (!analysis) return null;

  return (
    <div className="animate-fade-in-up glass rounded-xl p-6" style={{ animationDelay: "0.4s" }}>
      <h3 className="text-base font-semibold text-indigo-300 mb-5 flex items-center gap-2">
        <span className="w-1 h-5 bg-indigo-500 rounded-full inline-block" />
        <span>🤖</span> AI-Powered Evaluation
      </h3>

      <div
        className="llm-content text-sm leading-relaxed"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(analysis) }}
      />
    </div>
  );
}
