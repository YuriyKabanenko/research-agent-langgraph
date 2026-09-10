import type { ResearchResponse } from "../api/types";

function slugify(topic: string): string {
  return topic.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

export function downloadResearchMarkdown(run: ResearchResponse) {
  const lines = [
    `# ${run.topic}`,
    "",
    `- **Agent:** ${run.agent_name}`,
    `- **Rate:** ${run.research_rate != null ? `${run.research_rate}/10` : "n/a"}`,
    `- **Tools used:** ${run.tools_used && run.tools_used.length > 0 ? run.tools_used.join(", ") : "none"}`,
    `- **Created:** ${new Date(run.created_at).toLocaleString()}`,
    "",
    "---",
    "",
    run.research ?? "",
  ];

  const blob = new Blob([lines.join("\n")], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const slug = slugify(run.topic) || "research";
  const link = document.createElement("a");
  link.href = url;
  link.download = `${slug}-${run.id.slice(0, 8)}.md`;
  link.click();
  URL.revokeObjectURL(url);
}
