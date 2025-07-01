
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
  reason?: string;
  recommendedReason?: string;
}

export interface DisputeAnalysis {
  negativeItems: Account[];
  recommendedDisputes: Account[];
  confidenceScore: number;
  summary: string;
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
          recommendedDisputes: mockNegativeItems.slice(0, 1), // Recommend first item
          confidenceScore: 0.92,
          summary: "Found 2 negative items, 1 recommended for dispute"
        });
      }, 3000);
    });
  }
}

export const aiService = new AIService();
