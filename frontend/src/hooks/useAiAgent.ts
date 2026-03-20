import { useState, useCallback } from "react";
import { supabase } from "@/integrations/supabase/client";

const API_BASE = import.meta.env.VITE_API_URL || "";

interface AiAgentState {
  loading: boolean;
  response: string | null;
  error: string | null;
}

export const useAiAgent = () => {
  const [state, setState] = useState<AiAgentState>({
    loading: false,
    response: null,
    error: null,
  });

  const analyzeProject = useCallback(
    async (context?: string, maxTokens?: number) => {
      setState({ loading: true, response: null, error: null });

      try {
        const { data: session } = await supabase.auth.getSession();
        const token = session.session?.access_token;
        if (!token) throw new Error("Not authenticated");

        const res = await fetch(`${API_BASE}/api/v1/ai/analyze-project`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            context: context || "",
            max_tokens: maxTokens || 2500,
          }),
        });

        if (!res.ok) {
          const errBody = await res.json().catch(() => null);
          throw new Error(
            errBody?.error?.message || errBody?.detail || `Request failed (${res.status})`
          );
        }

        const data = await res.json();
        const markdown = data?.data?.markdown ?? null;

        setState({ loading: false, response: markdown, error: null });
        return markdown;
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Unknown error";
        setState({ loading: false, response: null, error: msg });
        return null;
      }
    },
    []
  );

  return {
    loading: state.loading,
    response: state.response,
    error: state.error,
    analyzeProject,
  };
};
