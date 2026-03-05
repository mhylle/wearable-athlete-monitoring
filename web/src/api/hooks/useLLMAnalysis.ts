import { useCallback, useRef, useState } from "react";
import { getAccessToken } from "@/api/client";
import type { LLMAnalysisState } from "@/types/api";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8001";

const ANALYSIS_TYPES = [
  "recovery_analysis",
  "training_load",
  "sleep_analysis",
  "wellness_trends",
  "fitness_progression",
  "combined_summary",
] as const;

interface UseLLMAnalysisReturn {
  analyses: Record<string, LLMAnalysisState>;
  isStreaming: boolean;
  error: string | null;
  startAnalysis: () => void;
  resetAnalysis: () => void;
}

function initialState(): Record<string, LLMAnalysisState> {
  const state: Record<string, LLMAnalysisState> = {};
  for (const type of ANALYSIS_TYPES) {
    state[type] = { status: "pending", text: "" };
  }
  return state;
}

export function useLLMAnalysis(athleteId: string): UseLLMAnalysisReturn {
  const [analyses, setAnalyses] = useState<Record<string, LLMAnalysisState>>(initialState);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const startAnalysis = useCallback(() => {
    if (!athleteId) return;

    // Abort any existing stream
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setAnalyses(initialState());
    setIsStreaming(true);
    setError(null);

    const token = getAccessToken();
    const url = `${API_BASE_URL}/api/v1/llm/athlete/${athleteId}/analyze-all`;

    fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          let currentEvent = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith("data: ") && currentEvent) {
              try {
                const data = JSON.parse(line.slice(6));
                handleSSEEvent(currentEvent, data, setAnalyses);
              } catch {
                // Skip malformed JSON
              }
              currentEvent = "";
            }
          }
        }

        setIsStreaming(false);
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          setError(err.message);
          setIsStreaming(false);
        }
      });
  }, [athleteId]);

  const resetAnalysis = useCallback(() => {
    abortRef.current?.abort();
    setAnalyses(initialState());
    setIsStreaming(false);
    setError(null);
  }, []);

  return { analyses, isStreaming, error, startAnalysis, resetAnalysis };
}

function handleSSEEvent(
  event: string,
  data: Record<string, unknown>,
  setAnalyses: React.Dispatch<React.SetStateAction<Record<string, LLMAnalysisState>>>,
) {
  const type = data.type as string;
  if (!type) return;

  switch (event) {
    case "analysis_start":
      setAnalyses((prev) => ({
        ...prev,
        [type]: { status: "streaming", text: "" },
      }));
      break;

    case "analysis_chunk":
      setAnalyses((prev) => ({
        ...prev,
        [type]: {
          ...prev[type],
          status: "streaming",
          text: (prev[type]?.text ?? "") + (data.chunk as string),
        },
      }));
      break;

    case "analysis_complete":
      setAnalyses((prev) => ({
        ...prev,
        [type]: {
          status: "complete",
          text: data.result as string,
          cached: data.cached as boolean | undefined,
        },
      }));
      break;

    case "all_complete":
      // All done — combined_summary should already be set via analysis_complete
      break;
  }
}
