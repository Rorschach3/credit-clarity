import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/hooks/use-auth";
import { useAgent, AgentMessage } from "@/hooks/useAgent";
import { toast } from "sonner";
import { Bot, X, Loader2, Trash2, Send } from "lucide-react";

interface AIChatWidgetProps {
  /** Extra context sent with every message (page name, data summary, etc.) */
  context?: string;
  /** Use WebSocket streaming (default true) */
  stream?: boolean;
}

const AIChatWidget: React.FC<AIChatWidgetProps> = ({
  context,
  stream = true,
}) => {
  const { user } = useAuth();
  const { messages, send, loading, streaming, error, clearConversation } =
    useAgent({ context, stream });

  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const contentRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [messages, isOpen]);

  // Surface errors as toasts
  useEffect(() => {
    if (error) toast.error(error);
  }, [error]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    await send(text);
  };

  const toggleOpen = () => {
    if (!isOpen && !user?.id) {
      toast.info("Please sign in to use the AI assistant");
      return;
    }
    setIsOpen((v) => !v);
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {!isOpen ? (
        <Button
          className="rounded-full w-16 h-16 flex items-center justify-center shadow-lg bg-violet-600 hover:bg-violet-700"
          onClick={toggleOpen}
          disabled={!user?.id}
        >
          <Bot className="h-6 w-6" />
        </Button>
      ) : (
        <Card className="w-[400px] h-[540px] flex flex-col shadow-xl">
          {/* Header */}
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <Bot className="h-5 w-5 text-violet-600" />
              Credit Clarity AI
            </CardTitle>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={clearConversation}
                title="Clear conversation"
                disabled={messages.length === 0}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm" onClick={toggleOpen}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>

          {/* Messages */}
          <CardContent
            className="flex-1 overflow-y-auto p-4 border-t border-b"
            ref={contentRef}
          >
            <div className="space-y-3">
              {messages.length === 0 && (
                <div className="text-center text-sm text-gray-500 mt-8">
                  Ask me anything about credit repair, disputes, or your credit
                  report.
                </div>
              )}

              {messages.map((msg, i) => (
                <MessageBubble key={i} message={msg} />
              ))}

              {streaming && (
                <div className="flex justify-start">
                  <div className="p-2 rounded-lg bg-gray-100 text-gray-600 flex items-center gap-2 text-sm">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Streaming...
                  </div>
                </div>
              )}
            </div>
          </CardContent>

          {/* Input */}
          <CardFooter className="p-3 flex items-end gap-2">
            <Textarea
              placeholder={
                user?.id
                  ? "Ask about credit, disputes, or your report..."
                  : "Sign in to chat"
              }
              className="flex-1 resize-none text-sm"
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={loading || !user?.id}
            />
            <Button
              size="sm"
              onClick={handleSend}
              disabled={loading || !input.trim() || !user?.id}
              className="bg-violet-600 hover:bg-violet-700"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </CardFooter>
        </Card>
      )}
    </div>
  );
};

// ---------------------------------------------------------------
// Message bubble sub-component
// ---------------------------------------------------------------

const MessageBubble: React.FC<{ message: AgentMessage }> = ({ message }) => {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`p-3 rounded-lg max-w-[85%] text-sm ${
          isUser
            ? "bg-violet-600 text-white"
            : "bg-gray-100 text-gray-800"
        }`}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>
        {message.timestamp && (
          <div
            className={`text-xs mt-1 ${
              isUser ? "text-violet-200" : "text-gray-500"
            }`}
          >
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
};

export default AIChatWidget;
