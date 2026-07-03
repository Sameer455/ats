import SkillsSectionCard from "./SkillsSectionCard";
import ExperienceSectionCard from "./ExperienceSectionCard";
import EducationSectionCard from "./EducationSectionCard";
import ProjectsSectionCard from "./ProjectsSectionCard";
import AwardsSectionCard from "./AwardsSectionCard";

/**
 * ResumeInsights — master container that renders all per-section analysis cards.
 * Replaces SkillAnalysis, ExtractedProfile, and ResumeSections.
 *
 * Section order:
 *   1. Skills      (always shown — most critical for ATS)
 *   2. Experience  (always shown)
 *   3. Education   (always shown)
 *   4. Projects    (shown only if section exists)
 *   5. Awards      (shown only if section exists)
 */
export default function ResumeInsights({ result }) {
  if (!result) return null;

  return (
    <div className="space-y-6">
      {/* Divider with title */}
      <div className="flex items-center gap-4 pt-2">
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-700 to-transparent" />
        <span className="text-xs font-semibold uppercase tracking-widest text-slate-500">
          Resume Sections Analysis
        </span>
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-700 to-transparent" />
      </div>

      <SkillsSectionCard result={result} />
      <ExperienceSectionCard result={result} />
      <EducationSectionCard result={result} />
      <ProjectsSectionCard result={result} />
      <AwardsSectionCard result={result} />
    </div>
  );
}
