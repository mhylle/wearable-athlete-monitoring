import { useState } from "react";
import { useParams } from "react-router-dom";
import { useAthletes } from "@/api/hooks/useAthletes";
import { useLLMAnalysis } from "@/api/hooks/useLLMAnalysis";
import { LLMInsightCard } from "@/components/cards/LLMInsightCard";
import { apiClient } from "@/api/client";

const ANALYSIS_ORDER = [
  "recovery_analysis",
  "training_load",
  "sleep_analysis",
  "wellness_trends",
  "fitness_progression",
  "combined_summary",
];

export function AIInsightsPage() {
  const { athleteId: routeAthleteId } = useParams<{ athleteId: string }>();
  const { data: athletes } = useAthletes();
  const [selectedAthleteId, setSelectedAthleteId] = useState(routeAthleteId ?? "");

  const activeAthleteId = routeAthleteId ?? selectedAthleteId;
  const { analyses, isStreaming, error, startAnalysis, resetAnalysis } =
    useLLMAnalysis(activeAthleteId);

  const handleRegenerate = async () => {
    if (!activeAthleteId) return;
    // Invalidate cache then restart
    try {
      await apiClient.delete(`/api/v1/llm/athlete/${activeAthleteId}/cache`);
    } catch {
      // Cache invalidation is best-effort
    }
    resetAnalysis();
    // Small delay to allow state reset
    setTimeout(() => startAnalysis(), 100);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Insights</h1>
          <p className="mt-1 text-sm text-gray-500">
            LLM-powered analysis of athlete performance data
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Athlete selector (only if no route param) */}
          {!routeAthleteId && athletes && athletes.length > 0 && (
            <select
              value={selectedAthleteId}
              onChange={(e) => {
                setSelectedAthleteId(e.target.value);
                resetAnalysis();
              }}
              className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm"
              aria-label="Select athlete"
            >
              <option value="">Select Athlete...</option>
              {athletes
                .filter((a) => a.is_active)
                .map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.full_name}
                  </option>
                ))}
            </select>
          )}

          <button
            onClick={startAnalysis}
            disabled={!activeAthleteId || isStreaming}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isStreaming ? "Analyzing..." : "Generate Insights"}
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* No athlete selected */}
      {!activeAthleteId && (
        <div className="rounded-xl border border-gray-200 bg-white p-12 text-center">
          <p className="text-sm text-gray-400">
            Select an athlete and click "Generate Insights" to begin.
          </p>
        </div>
      )}

      {/* Analysis cards grid */}
      {activeAthleteId && (
        <div className="grid gap-4 lg:grid-cols-2">
          {ANALYSIS_ORDER.map((type) => (
            <LLMInsightCard
              key={type}
              type={type}
              state={analyses[type] ?? { status: "pending", text: "" }}
              onRegenerate={handleRegenerate}
            />
          ))}
        </div>
      )}
    </div>
  );
}
