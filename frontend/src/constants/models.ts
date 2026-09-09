// Mirrors research_assistant/llm/model.py's supported providers - keep in sync by
// hand, same as api/types.ts.
import type { ModelFamily } from "../api/types";

export const MODEL_FAMILY_LABELS: Record<ModelFamily, string> = {
  anthropic: "Anthropic (Claude)",
  openai: "OpenAI (GPT)",
  google: "Google (Gemini)",
};

export const MODEL_FAMILIES = Object.keys(MODEL_FAMILY_LABELS) as ModelFamily[];

// A curated list of currently-popular models per family, not an exhaustive catalog.
export const MODELS_BY_FAMILY: Record<ModelFamily, string[]> = {
  anthropic: ["claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5-20251001"],
  openai: ["gpt-5", "gpt-5-mini", "gpt-4o"],
  google: ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
};

// Matches DEFAULT_MODEL_FAMILY/DEFAULT_MODEL_NAME in research_assistant/llm/model.py.
export const DEFAULT_MODEL_FAMILY: ModelFamily = "anthropic";
export const DEFAULT_MODEL_NAME = "claude-haiku-4-5-20251001";
