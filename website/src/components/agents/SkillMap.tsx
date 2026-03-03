import { fetchSkillMap } from "@/lib/agents-github";

const SKILL_ICONS: Record<string, string> = {
  docx: "📄",
  pdf: "📑",
  pptx: "📊",
  xlsx: "📈",
  "frontend-design": "🎨",
  "github-automation": "⚙️",
};

export async function SkillMap() {
  const skills = await fetchSkillMap();

  return (
    <div className="skill-grid">
      {skills.map((skill) => (
        <div key={skill.name} className="skill-card">
          <div className="skill-icon">{SKILL_ICONS[skill.name] ?? "◈"}</div>
          <h3 className="skill-name">{skill.name}</h3>
          <p className="skill-desc">{skill.description}</p>
          {skill.triggerKeywords.length > 0 && (
            <div className="skill-tags">
              {skill.triggerKeywords.slice(0, 4).map((kw) => (
                <span key={kw} className="skill-tag">{kw}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
