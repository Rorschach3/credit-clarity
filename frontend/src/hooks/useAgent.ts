import { useState, useCallback, useRef, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";

const API_BASE = import.meta.env.VITE_API_URL || "";

// Build WebSocket URL from the API base or current host
function getWsBase(): string {
  if (API_BASE) {
    return API_BASE.replace(/^http/, "ws");
  }
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}`;
}

export interface AgentMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

interface UseAgentOptions {
  /** Extra context sent with every message (page name, user data, etc.) */
  context?: string;
  /** Use WebSocket streaming instead of REST (default: true) */
  stream?: boolean;
  /** Conversation ID to resume (defaults to "default") */
  conversationId?: string;
  /** Max tokens per response */
  maxTokens?: number;
}

export const useAgent = (options: UseAgentOptions = {}) => {
  const {
    context,
    stream = true,
    conversationId,
    maxTokens = 2048,
  } = options;

  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const streamBufferRef = useRef("");

  // Get the current Supabase session token
  const getToken = useCallback(async (): Promise<string | null> => {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  }, []);

  // ---------------------------------------------------------------
  // REST: POST /api/v1/ai/query
  // ---------------------------------------------------------------
  const sendRest = useCallback(
    async (message: string) => {
      setLoading(true);
      setError(null);

      const userMsg: AgentMessage = {
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);

      try {
        const token = await getToken();
        if (!token) throw new Error("Not authenticated");

        const res = await fetch(`${API_BASE}/api/v1/ai/query`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            message,
            context: context ?? undefined,
            conversation_id: conversationId,
            max_tokens: maxTokens,
          }),
        });

        if (!res.ok) {
          const errBody = await res.json().catch(() => null);
          throw new Error(
            errBody?.error?.message || errBody?.detail || `Request failed (${res.status})`
          );
        }

        const data = await res.json();
        const reply = data?.data?.message ?? "";

        const assistantMsg: AgentMessage = {
          role: "assistant",
          content: reply,
          timestamp: data?.data?.timestamp,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        return reply;
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Unknown error";
        setError(msg);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [context, conversationId, maxTokens, getToken]
  );

  // ---------------------------------------------------------------
  // WebSocket: /api/v1/ai/stream/{token}
  // ---------------------------------------------------------------
  const connectWs = useCallback(async (): Promise<WebSocket | null> => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return wsRef.current;

    const token = await getToken();
    if (!token) {
      setError("Not authenticated");
      return null;
    }

    const ws = new WebSocket(`${getWsBase()}/api/v1/ai/stream/${token}`);
    wsRef.current = ws;

    return new Promise((resolve) => {
      ws.onopen = () => resolve(ws);
      ws.onerror = () => {
        setError("WebSocket connection failed");
        resolve(null);
      };
      ws.onclose = () => {
        wsRef.current = null;
      };
    });
  }, [getToken]);

  const sendStream = useCallback(
    async (message: string) => {
      setError(null);
      setStreaming(true);
      streamBufferRef.current = "";

      const userMsg: AgentMessage = {
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);

      // Add a placeholder assistant message that we'll update as tokens arrive
      const placeholderIdx = { current: -1 };
      setMessages((prev) => {
        placeholderIdx.current = prev.length;
        return [...prev, { role: "assistant", content: "" }];
      });

      const ws = await connectWs();
      if (!ws) {
        setStreaming(false);
        return null;
      }

      return new Promise<string | null>((resolve) => {
        const onMessage = (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === "token") {
              streamBufferRef.current += data.content;
              const current = streamBufferRef.current;
              setMessages((prev) => {
                const updated = [...prev];
                if (placeholderIdx.current >= 0 && placeholderIdx.current < updated.length) {
                  updated[placeholderIdx.current] = {
                    role: "assistant",
                    content: current,
                  };
                }
                return updated;
              });
            }

            if (data.type === "done") {
              setMessages((prev) => {
                const updated = [...prev];
                if (placeholderIdx.current >= 0 && placeholderIdx.current < updated.length) {
                  updated[placeholderIdx.current] = {
                    role: "assistant",
                    content: data.content,
                    timestamp: data.timestamp,
                  };
                }
                return updated;
              });
              setStreaming(false);
              ws.removeEventListener("message", onMessage);
              resolve(data.content);
            }

            if (data.type === "error") {
              setError(data.content);
              setStreaming(false);
              ws.removeEventListener("message", onMessage);
              resolve(null);
            }
          } catch {
            // non-JSON frame, ignore
          }
        };

        ws.addEventListener("message", onMessage);

        ws.send(
          JSON.stringify({
            message,
            context: context ?? undefined,
            conversation_id: conversationId,
            max_tokens: maxTokens,
          })
        );
      });
    },
    [context, conversationId, maxTokens, connectWs]
  );

  // Unified send — picks REST or WS based on `stream` option
  const send = useCallback(
    (message: string) => (stream ? sendStream(message) : sendRest(message)),
    [stream, sendRest, sendStream]
  );

  // Clear conversation
  const clearConversation = useCallback(async () => {
    setMessages([]);
    setError(null);

    // Tell backend to clear cache
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "clear", conversation_id: conversationId }));
    }
  }, [conversationId]);

  // Cleanup WS on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return {
    messages,
    send,
    loading: loading || streaming,
    streaming,
    error,
    clearConversation,
  };
};
