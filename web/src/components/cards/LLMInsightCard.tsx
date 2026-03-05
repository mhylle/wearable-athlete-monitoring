import type { LLMAnalysisState } from "@/types/api";

const TYPE_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  recovery_analysis: { label: "Recovery Analysis", icon: "R", color: "bg-green-100 text-green-700" },
  training_load: { label: "Training Load", icon: "T", color: "bg-orange-100 text-orange-700" },
  sleep_analysis: { label: "Sleep Analysis", icon: "S", color: "bg-blue-100 text-blue-700" },
  wellness_trends: { label: "Wellness Trends", icon: "W", color: "bg-purple-100 text-purple-700" },
  fitness_progression: { label: "Fitness Progression", icon: "F", color: "bg-cyan-100 text-cyan-700" },
  combined_summary: { label: "Executive Summary", icon: "E", color: "bg-gray-100 text-gray-700" },
};

interface LLMInsightCardProps {
  type: string;
  state: LLMAnalysisState;
  onRegenerate?: () => void;
}

export function LLMInsightCard({ type, state, onRegenerate }: LLMInsightCardProps) {
  const cfg = TYPE_CONFIG[type] ?? { label: type, icon: "?", color: "bg-gray-100 text-gray-700" };

  return (
    <div className="flex flex-col rounded-xl border border-gray-200 bg-white">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
        <div className="flex items-center gap-2.5">
          <span className={`flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold ${cfg.color}`}>
            {cfg.icon}
          </span>
          <h3 className="text-sm font-semibold text-gray-900">{cfg.label}</h3>
        </div>
        <div className="flex items-center gap-2">
          {state.cached && (
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
              Cached
            </span>
          )}
          {state.status === "complete" && onRegenerate && (
            <button
              onClick={onRegenerate}
              className="rounded-lg px-2 py-1 text-xs text-gray-500 transition hover:bg-gray-100 hover:text-gray-700"
            >
              Regenerate
            </button>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 px-4 py-3">
        {state.status === "pending" && (
          <div className="flex items-center gap-2 py-6">
            <div className="h-2 w-2 animate-pulse rounded-full bg-gray-300" />
            <span className="text-sm text-gray-400">Waiting...</span>
          </div>
        )}

        {state.status === "streaming" && (
          <div>
            <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">
              {state.text}
              <span className="inline-block h-4 w-1 animate-pulse bg-blue-500" />
            </div>
          </div>
        )}

        {state.status === "complete" && (
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">
            {state.text || <span className="text-gray-400">No analysis generated.</span>}
          </div>
        )}

        {state.status === "error" && (
          <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
            Failed to generate analysis. Check that Ollama is running.
          </div>
        )}
      </div>
    </div>
  );
}
