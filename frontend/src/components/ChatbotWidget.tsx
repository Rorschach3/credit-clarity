<<<<<<< Updated upstream:src/components/ChatbotWidget.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardHeader, CardContent, CardFooter, CardTitle } from './ui/card';
import { Textarea } from './ui/textarea';
import { aiService } from '@/utils/ai-service';

interface ChatMessage {
  text: string;
  sender: 'user' | 'bot';
}

const ChatbotWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { text: "Hello! How can I help you today?", sender: "bot" }
  ]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const chatContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContentRef.current) {
      chatContentRef.current.scrollTop = chatContentRef.current.scrollHeight;
    }
  }, [messages, isOpen]);

  const sendMessage = async () => {
    if (!newMessage.trim() || loading) return;

    const userMessage: ChatMessage = { text: newMessage, sender: "user" };
    setMessages((prev) => [...prev, userMessage]);
    setNewMessage("");
    setLoading(true);

    try {
      // Prepare chat history for context (role: user/assistant)
      const chatHistory = [
        { role: "system" as const, content: "You are a helpful assistant for Credit Clarity users. Answer questions about credit, reports, disputes, and the platform." },
        ...messages.map((msg) => ({
          role: msg.sender === "user" ? "user" as const : "assistant" as const,
          content: msg.text
        })),
        { role: "user" as const, content: newMessage }
      ];

      const response = await aiService.chatCompletion(chatHistory, "gpt-4", 256);
      setMessages((prev) => [...prev, { text: response, sender: "bot" }]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { text: "Sorry, I couldn't process your request. Please try again.", sender: "bot" }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setNewMessage(e.target.value);
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {!isOpen ? (
        <Button
          className="rounded-full w-16 h-16 flex items-center justify-center shadow-lg"
          onClick={toggleChat}
        >
          Chat
        </Button>
      ) : (
        <Card className="w-80 h-[400px] flex flex-col shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-lg font-semibold">Chat with us!</CardTitle>
            <Button variant="ghost" size="sm" onClick={toggleChat}>
              X
            </Button>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto p-4 border-t border-b" ref={chatContentRef}>
            <div className="space-y-2">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`p-2 rounded-lg max-w-[80%] ${
                    message.sender === "bot"
                      ? "bg-gray-100 self-start"
                      : "bg-blue-100 self-end text-right ml-auto"
                  }`}
                >
                  {message.text}
                </div>
              ))}
              {loading && (
                <div className="p-2 rounded-lg bg-gray-100 max-w-[80%] self-start animate-pulse">
                  Typing...
                </div>
              )}
            </div>
          </CardContent>
          <CardFooter className="p-4 flex items-center space-x-2">
            <Textarea
              placeholder="Type your message..."
              className="flex-1 resize-none"
              rows={1}
              value={newMessage}
              onChange={handleInputChange}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              disabled={loading}
            />
            <Button onClick={sendMessage} disabled={loading || !newMessage.trim()}>
              Send
            </Button>
          </CardFooter>
        </Card>
      )}
    </div>
  );
};

=======
import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardHeader, CardContent, CardFooter, CardTitle } from './ui/card';
import { Textarea } from './ui/textarea';
import { useAuth } from '@/hooks/use-auth';
import { toast } from 'sonner';
import { MessageCircle, X, Loader2 } from 'lucide-react';

interface ChatMessage {
  text: string;
  sender: 'user' | 'bot';
  timestamp?: string;
}

interface CreditSuggestion {
  type: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  action: string;
}

const ChatbotWidget: React.FC = () => {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { text: "Hello! I'm Credit Clarity AI. I can help you with credit questions, dispute strategies, and understanding your credit report. How can I assist you today?", sender: "bot" }
  ]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<CreditSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const chatContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContentRef.current) {
      chatContentRef.current.scrollTop = chatContentRef.current.scrollHeight;
    }
  }, [messages, isOpen]);

  // Load conversation history when opened
  useEffect(() => {
    if (isOpen && user?.id && messages.length <= 1) {
      loadConversationHistory();
      loadCreditSuggestions();
    }
  }, [isOpen, user?.id]);

  const loadConversationHistory = async () => {
    if (!user?.id) return;
    
    try {
      const response = await fetch(`/api/chat/history/${user.id}?limit=10`);
      const data = await response.json();
      
      if (data.success && data.history.length > 0) {
        const formattedHistory = data.history.map((msg: any) => ({
          text: msg.content,
          sender: msg.role === 'user' ? 'user' : 'bot',
          timestamp: msg.timestamp
        }));
        setMessages(prev => [prev[0], ...formattedHistory]); // Keep welcome message first
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    }
  };

  const loadCreditSuggestions = async () => {
    if (!user?.id) return;
    
    try {
      const response = await fetch(`/api/chat/suggestions/${user.id}`);
      const data = await response.json();
      
      if (data.success && data.suggestions.length > 0) {
        setSuggestions(data.suggestions);
        setShowSuggestions(true);
      }
    } catch (error) {
      console.error('Failed to load credit suggestions:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || loading || !user?.id) return;

    const userMessage: ChatMessage = { text: newMessage, sender: "user", timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMessage]);
    const currentMessage = newMessage;
    setNewMessage("");
    setLoading(true);
    setShowSuggestions(false); // Hide suggestions when user starts chatting

    try {
      // Prepare conversation history for context
      const conversationHistory = messages.map((msg) => ({
        role: msg.sender === "user" ? "user" : "assistant",
        content: msg.text
      }));

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: user.id,
          message: currentMessage,
          conversationHistory: conversationHistory
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setMessages((prev) => [...prev, { 
          text: data.response, 
          sender: "bot",
          timestamp: data.timestamp
        }]);
      } else {
        throw new Error(data.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        { text: "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.", sender: "bot" }
      ]);
      toast.error('Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion: CreditSuggestion) => {
    setNewMessage(`Tell me more about: ${suggestion.title}`);
    setShowSuggestions(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setNewMessage(e.target.value);
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
    if (!isOpen && !user?.id) {
      toast.info('Please sign in to use the chat feature');
      return;
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {!isOpen ? (
        <Button
          className="rounded-full w-16 h-16 flex items-center justify-center shadow-lg bg-blue-600 hover:bg-blue-700"
          onClick={toggleChat}
          disabled={!user?.id}
        >
          <MessageCircle className="h-6 w-6" />
        </Button>
      ) : (
        <Card className="w-96 h-[500px] flex flex-col shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-lg font-semibold">Credit Clarity AI</CardTitle>
            <Button variant="ghost" size="sm" onClick={toggleChat}>
              <X className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto p-4 border-t border-b" ref={chatContentRef}>
            <div className="space-y-3">
              {/* Show credit suggestions if available */}
              {showSuggestions && suggestions.length > 0 && (
                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-600">💡 Quick Actions for You:</div>
                  {suggestions.slice(0, 3).map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className={`w-full text-left p-2 rounded-lg border text-sm hover:bg-gray-50 transition-colors ${
                        suggestion.priority === 'high' ? 'border-red-200 bg-red-50' : 
                        suggestion.priority === 'medium' ? 'border-yellow-200 bg-yellow-50' :
                        'border-blue-200 bg-blue-50'
                      }`}
                    >
                      <div className="font-medium">{suggestion.title}</div>
                      <div className="text-gray-600">{suggestion.description}</div>
                    </button>
                  ))}
                </div>
              )}
              
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${
                    message.sender === "bot" ? "justify-start" : "justify-end"
                  }`}
                >
                  <div
                    className={`p-3 rounded-lg max-w-[85%] ${
                      message.sender === "bot"
                        ? "bg-gray-100 text-gray-800"
                        : "bg-blue-600 text-white"
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.text}</div>
                    {message.timestamp && (
                      <div className={`text-xs mt-1 ${
                        message.sender === "bot" ? "text-gray-500" : "text-blue-200"
                      }`}>
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="flex justify-start">
                  <div className="p-3 rounded-lg bg-gray-100 text-gray-800 flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Credit Clarity AI is thinking...</span>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
          <CardFooter className="p-4 flex items-center space-x-2">
            <Textarea
              placeholder={user?.id ? "Ask about credit, disputes, or your report..." : "Please sign in to chat"}
              className="flex-1 resize-none"
              rows={2}
              value={newMessage}
              onChange={handleInputChange}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              disabled={loading || !user?.id}
            />
            <Button 
              onClick={sendMessage} 
              disabled={loading || !newMessage.trim() || !user?.id}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Send"}
            </Button>
          </CardFooter>
        </Card>
      )}
    </div>
  );
};

>>>>>>> Stashed changes:frontend/src/components/ChatbotWidget.tsx
export default ChatbotWidget;