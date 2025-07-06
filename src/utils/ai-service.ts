
// Mock AI service for development
export interface ExtractedText {
  fullText: string;
  confidence: number;
  extractedAt: Date;
}

export interface Account {
  id: string;
  creditorName: string;
  accountNumber: string;
  accountType: string;
  balance: number;
  status: string;
  bureaus: string[];
  isNegative: boolean;
  amount: string;
  dateReported: string;
  reason: string;
  recommendedReason?: string;
}

export interface DisputeAnalysis {
  negativeItems: Account[];
  recommendedDisputes: Account[];
  confidenceScore: number;
  summary: string;
}

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

class AIService {
  async extractTextFromDocument(fileUrl: string, fileType: string): Promise<ExtractedText> {
    // Mock implementation - replace with actual AI service
    console.log(`Extracting text from ${fileUrl} of type ${fileType}`);
    
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          fullText: "Mock extracted text from credit report...",
          confidence: 0.95,
          extractedAt: new Date()
        });
      }, 2000);
    });
  }

  async analyzeReport(extractedText: ExtractedText): Promise<DisputeAnalysis> {
    // Mock implementation - replace with actual AI analysis
    console.log("Analyzing credit report text:", extractedText.fullText.substring(0, 100));
    
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockNegativeItems: Account[] = [
          {
            id: "1",
            creditorName: "Capital One",
            accountNumber: "****1234",
            accountType: "credit_card",
            balance: 1500,
            status: "charged_off",
            bureaus: ["Experian", "Equifax"],
            isNegative: true,
            amount: "$1,500",
            dateReported: "2023-01-15",
            reason: "Charged Off",
            recommendedReason: "Account shows as charged off but payment was made"
          },
          {
            id: "2",
            creditorName: "Chase Bank",
            accountNumber: "****5678",
            accountType: "credit_card",
            balance: 750,
            status: "collection",
            bureaus: ["TransUnion"],
            isNegative: true,
            amount: "$750",
            dateReported: "2023-02-20",
            reason: "Collection Account",
            recommendedReason: "Collection account may be past statute of limitations"
          }
        ];

        resolve({
          negativeItems: mockNegativeItems,
          recommendedDisputes: mockNegativeItems.slice(0, 1),
          confidenceScore: 0.92,
          summary: "Found 2 negative items, 1 recommended for dispute"
        });
      }, 3000);
    });
  }

  async chatCompletion(messages: ChatMessage[], model: string = 'gpt-4', _maxTokens: number = 256): Promise<string> {
    // Mock implementation for chat completion
    console.log(`Chat completion with ${messages.length} messages using ${model}`);
    
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockResponses = [
          "I understand you're asking about credit reports. Let me help you with that.",
          "Credit disputes are an important part of maintaining good credit health.",
          "I'd be happy to help you understand your credit report better.",
          "That's a great question about credit repair processes."
        ];
        
        const randomResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];
        resolve(randomResponse);
      }, 1000);
    });
  }
}

export const aiService = new AIService();
