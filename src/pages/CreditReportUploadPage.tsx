"use client";

import { useState, useEffect, useRef, useCallback, ChangeEvent } from "react";
import { createWorker, Worker } from "tesseract.js";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { toast } from "@/components/ui/use-toast";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { pdfToImages } from "@/utils/pdfToImage";
import { useAuth } from "@/hooks/use-auth";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  saveTradelinesToDatabase,
  parseTradelinesFromText,
  validateAccountType, 
  validateAccountStatus 
} from "@/utils/tradelineParser";
import { ManualTradelineModal } from "@/components/disputes/ManualTradelineModal";
import { Checkbox } from "@/components/ui/checkbox";
import { parseDocumentViaProxy, generateContent } from "@/services/llm-parser";
import { DocumentAIResponse, ParsedTradeline } from "@/types";
import { fileToBase64, sanitizeAIResponse } from "@/utils/helpers";
import { v4 as uuidv4 } from 'uuid';

// Define the AI analysis response interface
interface AIAnalysisResponse {
  tradelines?: Array<{
    creditor_name?: string;
    account_number?: string;
    account_balance?: string;
    account_status?: string;
    account_type?: string;
    credit_limit?: string;
    date_opened?: string;
    monthly_payment?: string;    
    credit_bureau?: string;
    is_negative?: boolean;
    dispute_count?: number;
    raw_text?: string; // Added to match ParsedTradeline
  }>;
  keywords?: string[];
  insights?: string;
  negativeItems?: Array<{
    type: string;
    description: string;
    impact: string;
  }>;
}
interface TradelineItem {
  id?: string;
  creditor_name?: string;
  account_number?: string;
  account_balance?: string;
  account_status?: string;
  account_type?: string;
  credit_limit?: string;
  date_opened?: string;
  monthly_payment?: string;
  is_negative?: boolean;
  dispute_count?: number;
  credit_bureau?: string;
  created_at?: string;
  raw_text?: string;
  user_id?: string;
}

function safeValue<T extends string | number | null | undefined>(v: T): string {
  if (typeof v === "number") return String(v);
  return v ?? "";
}

const CreditReportUploadPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const workerRef = useRef<Worker | null>(null);
  const [tradelines, setTradelines] = useState<ParsedTradeline[]>([]);
  const [selectedTradelineIds, setSelectedTradelineIds] = useState<Set<string>>(new Set());
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const [processingMethod, setProcessingMethod] = useState<'ocr' | 'ai'>('ai');
  const [extractedKeywords, setExtractedKeywords] = useState<string[]>([]);
  const [aiInsights, setAiInsights] = useState<string>('');
  const [showAiResults, setShowAiResults] = useState(false);
  const [extractedText, setExtractedText] = useState<string>('');

  useEffect(() => {
    console.log("Current tradelines:", tradelines);
  }, [tradelines]);

  const handleSelectTradeline = (id: string, isSelected: boolean) => {
    setSelectedTradelineIds(prev => {
      const newSet = new Set(prev);
      if (isSelected) {
        newSet.add(id);
      } else {
        newSet.delete(id);
      }
      return newSet;
    });
  };

  // Initialize OCR worker
  useEffect(() => {
    const initWorker = async () => {
      if (processingMethod === 'ocr' && !workerRef.current) {
        workerRef.current = await createWorker('eng');
      }
    };
    initWorker();

    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
        workerRef.current = null;
      }
    };
  }, [processingMethod]);

  const processWithOCR = async (file: File): Promise<string> => {
    if (!workerRef.current) {
      workerRef.current = await createWorker('eng');
    }

    const buffer = await file.arrayBuffer();
    const images = await pdfToImages(buffer);
    let textContent = "";
    
    for (let i = 0; i < images.length; i++) {
      const { data } = await workerRef.current.recognize(images[i]);
      textContent += data.text + "\n";
      setUploadProgress(((i + 1) / images.length) * 70); // 70% for OCR
    }
    
    return textContent;
  };

  const extractKeywordsFromText = (text: string): string[] => {
    const creditKeywords = [
      'credit', 'debt', 'payment', 'balance', 'collection', 'charge-off', 'charge off',
      'bankruptcy', 'foreclosure', 'late', 'delinquent', 'dispute', 'inquiry',
      'account', 'tradeline', 'bureau', 'experian', 'equifax', 'transunion',
      'score', 'report', 'limit', 'utilization', 'negative', 'positive'
    ];
    
    const foundKeywords = new Set<string>();
    const lowerText = text.toLowerCase();
    
    creditKeywords.forEach(keyword => {
      if (lowerText.includes(keyword)) {
        foundKeywords.add(keyword);
      }
    });
    
    return Array.from(foundKeywords);
  };

  const generateAIInsights = (text: string, keywords: string[]): string => {
    const insights = [];
    
    if (keywords.includes('collection') || keywords.includes('charge-off')) {
      insights.push("⚠️ Negative items detected that may be affecting your credit score.");
    }
    
    if (keywords.includes('late') || keywords.includes('delinquent')) {
      insights.push("📉 Payment history issues found - these can be disputed if inaccurate.");
    }
    
    if (keywords.includes('inquiry')) {
      insights.push("🔍 Credit inquiries found - too many can lower your score.");
    }
    
    if (keywords.includes('utilization')) {
      insights.push("💳 Credit utilization information detected - keeping it below 30% is recommended.");
    }
    
    if (insights.length === 0) {
      insights.push("✅ Initial analysis complete. Review the extracted tradelines below.");
    }
    
    return insights.join('\n\n');
  };

  const processAIResponse = async (aiResponse: string, extractedText: string): Promise<void> => {
    if (!aiResponse.trim()) {
      console.warn('AI returned empty response, using fallback analysis');
      
      // Fallback to basic keyword extraction and tradeline parsing
      const keywords = extractKeywordsFromText(extractedText);
      setExtractedKeywords(keywords);
      setAiInsights(generateAIInsights(extractedText, keywords));
      
      // Try to parse tradelines using existing parser
      try {
        const fallbackTradelines = await parseTradelinesFromText(extractedText, user?.id || "");
        if (fallbackTradelines.length > 0) {
          setTradelines(prev => [...prev, ...fallbackTradelines]);
          console.log(`Fallback: extracted ${fallbackTradelines.length} tradelines`);
        }
      } catch (parseError) {
        console.error('Fallback tradeline parsing failed:', parseError);
      }
      return;
    }

    try {
      let cleanedResponse = aiResponse.trim();
      if (cleanedResponse.startsWith('```json')) {
        cleanedResponse = cleanedResponse.replace(/```json\n?/, '').replace(/\n?```$/, '');
      } else if (cleanedResponse.startsWith('```')) {
        cleanedResponse = cleanedResponse.replace(/```\n?/, '').replace(/\n?```$/, '');
      }

      const sanitizedResponse = sanitizeAIResponse(cleanedResponse);
      const parsedAI: AIAnalysisResponse = JSON.parse(sanitizedResponse);
      
      setExtractedKeywords(parsedAI.keywords || extractKeywordsFromText(extractedText));
      setAiInsights(parsedAI.insights || generateAIInsights(extractedText, parsedAI.keywords || []));
      
      if (parsedAI.tradelines && parsedAI.tradelines.length > 0) {
        const convertedTradelines = parsedAI.tradelines.map((item) => ({
          id: uuidv4(),
          creditor_name: item.creditor_name || '',
          account_number: item.account_number || '',
          account_balance: item.account_balance || '$0',
          account_status: validateAccountStatus(item.account_status || "") || "",
          account_type: validateAccountType(item.account_type) || "credit_card",
          credit_limit: item.credit_limit || '$0',
          date_opened: item.date_opened || '',
          monthly_payment: item.monthly_payment || '$0',
          is_negative: Boolean(item.is_negative),
          dispute_count: Number(item.dispute_count) || 0,
          credit_bureau: validateCreditBureau(item.credit_bureau) || '',
          created_at: new Date().toISOString(),
          raw_text: extractedText,
          user_id: user?.id || ''
        }));

        setTradelines(prev => [...prev, ...convertedTradelines]);
        console.log(`Successfully extracted ${convertedTradelines.length} tradelines via AI`);
      }
    } catch (jsonError) {
      console.error('Failed to parse AI response as JSON:', jsonError);
      
      // Fallback to basic analysis
      const keywords = extractKeywordsFromText(extractedText);
      setExtractedKeywords(keywords);
      setAiInsights(generateAIInsights(extractedText, keywords));
      
      try {
        const fallbackTradelines = await parseTradelinesFromText(extractedText, user?.id || "");
        if (fallbackTradelines.length > 0) {
          setTradelines(prev => [...prev, ...fallbackTradelines]);
          console.log(`Fallback: extracted ${fallbackTradelines.length} tradelines`);
        }
      } catch (parseError) {
        console.error('Traditional parser also failed:', parseError);
      }
    }
  };

  const processWithAI = async (file: File): Promise<string> => {
    try {
      console.log("Starting AI processing...");
      setUploadProgress(10);

      let textContent = '';
      
      // First try OCR for text extraction
      try {
        textContent = await processWithOCR(file);
        setUploadProgress(50);
        console.log("OCR extraction completed, text length:", textContent.length);
      } catch (ocrError) {
        console.error('OCR failed, trying Document AI:', ocrError);
        
        // Fallback to Document AI
        const base64Content = await fileToBase64(file);
        const documentData = await parseDocumentViaProxy(base64Content) as DocumentAIResponse | undefined;
        
        if (documentData?.document?.text) {
          textContent = documentData.document.text;
          setUploadProgress(50);
        } else {
          throw new Error('Both OCR and Document AI failed to extract text');
        }
      }

      setExtractedText(textContent);

      // Now analyze with AI for insights and structured data
      if (textContent.trim()) {
        try {
          const prompt = `
            Analyze this credit report text and extract key information. Return a JSON object with this structure:
            {
              "keywords": ["array", "of", "credit", "related", "terms", "found"],
              "insights": "Brief analysis of the credit report findings and recommendations",
              "tradelines": [
                {
                  "creditor_name": "Company Name",
                  "account_number": "Account Number",
                  "account_balance": "$Amount",
                  "account_status": "open|closed|in_collection|charged_off|disputed",
                  "account_type": "credit_card|loan|mortgage|auto_loan|student_loan|collection",
                  "credit_limit": "$Amount",
                  "date_opened": "YYYY-MM-DD",
                  "monthly_payment": "$Amount",
                  "credit_bureau": "experian|equifax|transunion",
                  "is_negative": true/false
                }
              ]
            }

            Focus on finding negative items, payment history issues, and accounts that could be disputed.
          `;

          let aiResponse = '';
          
          await generateContent(
            [
              {
                role: "user",
                parts: [
                  {
                    text: `${prompt}\n\nCredit Report Content:\n${textContent.substring(0, 4000)}` // Limit text to prevent token issues
                  }
                ]
              }
            ],
            (chunk: string) => {
              aiResponse += chunk;
            }
          );

          setUploadProgress(80);
          console.log("AI analysis completed");
          
          await processAIResponse(aiResponse, textContent);
          
        } catch (aiError) {
          console.error('AI analysis failed, using basic analysis:', aiError);
          
          // Basic fallback analysis
          const keywords = extractKeywordsFromText(textContent);
          setExtractedKeywords(keywords);
          setAiInsights(generateAIInsights(textContent, keywords));
          
          // Try basic tradeline parsing
          try {
            const basicTradelines = await parseTradelinesFromText(textContent, user?.id || "");
            if (basicTradelines.length > 0) {
              setTradelines(prev => [...prev, ...basicTradelines]);
            }
          } catch (parseError) {
            console.error('Basic parsing also failed:', parseError);
          }
        }
      }
      
      setUploadProgress(100);
      return textContent;
      
    } catch (error) {
      console.error('AI processing error:', error);
      toast({ 
        title: "Processing Failed", 
        description: "Failed to process document. Please try OCR method.",
        variant: "destructive"
      });
      
      throw error;
    }
  };

  const saveTradelines = useCallback(async () => {
    if (user && tradelines.length > 0) {
      try {
        console.log('Parsed tradelines before saving:', tradelines);
        await saveTradelinesToDatabase(tradelines, user.id);
        console.log(`Saved ${tradelines.length} tradelines to database`);
      } catch (saveError) {
        console.error('Failed to save tradelines:', saveError);
        toast({
          title: "Save Warning",
          description: "Tradelines extracted but failed to save to database.",
          variant: "destructive"
        });
      }
    }
  }, [user, tradelines]);

  const handleFileUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    console.log("handleFileUpload triggered");
    try {
      const file = event.target.files?.[0];
      if (!file || file.type !== "application/pdf") {
        toast({ title: "Invalid file", description: "Please upload a PDF file." });
        return;
      }
      if (!user || !user.id) {
        toast({ title: "Error", description: "You must be logged in.", variant: "destructive" });
        return;
      }

      setIsUploading(true);
      setTradelines([]);
      setUploadProgress(0);
      setExtractedKeywords([]);
      setAiInsights('');
      setExtractedText('');
      setShowAiResults(true);

      let textContent = '';
      
      if (processingMethod === 'ai') {
        textContent = await processWithAI(file);
      } else {
        textContent = await processWithOCR(file);
        setUploadProgress(80);
        
        // Basic analysis for OCR
        const keywords = extractKeywordsFromText(textContent);
        setExtractedKeywords(keywords);
        setAiInsights(generateAIInsights(textContent, keywords));
        setExtractedText(textContent);
        
        try {
          const parsed = await parseTradelinesFromText(textContent, user.id);
          setTradelines(parsed);
          console.log("OCR: Parsed tradelines successfully", parsed);
        } catch (parseError) {
          console.error("OCR tradeline parsing failed:", parseError);
        }
        setUploadProgress(100);
      }
      
      toast({
        title: "Upload complete",
        description: `Document processed using ${processingMethod.toUpperCase()}.`
      });
    } catch (error) {
      console.error("PDF processing error:", error instanceof Error ? error.message : String(error));
      toast({
        title: "Error",
        description: "Failed to process PDF. Please try again or use a different processing method.",
        variant: "destructive"
      });
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  // Effect to save tradelines when they are updated
  useEffect(() => {
    if (tradelines.length > 0 && user?.id) {
      console.log("useEffect triggered to save tradelines:", tradelines); // Added for debugging
      const timeoutId = setTimeout(() => {
        saveTradelines();
      }, 1000);
      
      return () => clearTimeout(timeoutId);
    }
  }, [tradelines, user, saveTradelines]);

  const updateTradeline = (index: number, updated: Partial<ParsedTradeline>) => {
    setTradelines((prev) => {
      const newTradelines = [...prev];
      newTradelines[index] = { ...newTradelines[index], ...updated };
      console.log("Updated tradeline:", newTradelines[index]);
      return newTradelines;
    });
  };

  const deleteTradeline = (index: number) => {
    setTradelines((prev) => prev.filter((_, i) => i !== index));
  };

  const handleProceed = () => {
    navigate("/dispute-letter");
  };

  return (
    <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
      <Card className="max-w-6xl mx-auto space-y-6">
        <CardHeader>
          <CardTitle className="text-2xl">Step 1: Upload or Add Tradelines</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label htmlFor="processing-method" className="mb-2 block">Processing Method</Label>
            <div className="flex gap-4 mb-4">
              <Button
                variant={processingMethod === 'ocr' ? 'default' : 'outline'}
                onClick={() => setProcessingMethod('ocr')}
              >
                OCR (Fast)
              </Button>
              <Button
                variant={processingMethod === 'ai' ? 'default' : 'outline'}
                onClick={() => setProcessingMethod('ai')}
              >
                AI Analysis (Advanced)
              </Button>
            </div>
            
            <Label htmlFor="pdf-upload">Upload Credit Report (PDF)</Label>
            <Input
              id="pdf-upload"
              type="file"
              accept="application/pdf"
              onChange={handleFileUpload}
              disabled={isUploading}
            />
            {isUploading && (
              <div className="mt-2">
                <Progress value={uploadProgress} className="w-full" />
                <p className="text-sm text-muted-foreground mt-1">
                  Processing with {processingMethod.toUpperCase()}... {Math.round(uploadProgress)}%
                </p>
              </div>
            )}
          </div>

          {showAiResults && (extractedKeywords.length > 0 || aiInsights || extractedText) && (
            <Card>
              <CardContent className="pt-6">
                <Tabs defaultValue="keywords" className="w-full">
                  <TabsList>
                    <TabsTrigger value="keywords">Keywords</TabsTrigger>
                    <TabsTrigger value="insights">AI Insights</TabsTrigger>
                    <TabsTrigger value="text">Extracted Text</TabsTrigger>
                  </TabsList>
                  <TabsContent value="keywords" className="space-y-2">
                    <h4 className="font-semibold">Extracted Keywords</h4>
                    <div className="flex flex-wrap gap-2">
                      {extractedKeywords.map((keyword, i) => (
                        <Badge key={i} variant="secondary">{keyword}</Badge>
                      ))}
                      {extractedKeywords.length === 0 && (
                        <p className="text-muted-foreground text-sm">No keywords extracted yet.</p>
                      )}
                    </div>
                  </TabsContent>
                  <TabsContent value="insights" className="space-y-2">
                    <h4 className="font-semibold">AI Analysis</h4>
                    <div className="bg-muted p-4 rounded-md text-sm whitespace-pre-line">
                      {aiInsights || "No insights generated yet."}
                    </div>
                  </TabsContent>
                  <TabsContent value="text" className="space-y-2">
                    <h4 className="font-semibold">Raw Extracted Text</h4>
                    <div className="bg-muted p-4 rounded-md text-xs max-h-60 overflow-y-auto">
                      {extractedText ? extractedText.substring(0, 2000) + (extractedText.length > 2000 ? '...' : '') : "No text extracted yet."}
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}

          <div>
            <div className="flex items-center justify-between mb-2">
              <Label className="block">Tradelines</Label>
              <Button size="sm" variant="outline" onClick={() => setManualModalOpen(true)}>
                + Add Tradeline Manually
              </Button>
            </div>
            {tradelines.length === 0 ? (
              <p className="text-muted-foreground text-sm">No tradelines found.</p>
            ) : (
              tradelines.map((t, i) => (
                <div key={t.id || i} className="border p-4 rounded mb-3 space-y-2">
                  <div className="flex items-center mb-2">
                    <Checkbox
                      id={`select-tradeline-${t.id}`}
                      checked={selectedTradelineIds.has(t.id || '')}
                      onCheckedChange={(checked) => handleSelectTradeline(t.id || '', checked as boolean)}
                      className="mr-2"
                    />
                    <Label htmlFor={`select-tradeline-${t.id}`} className="font-semibold">
                      Select for Dispute
                    </Label>
                  </div>
                  <div>
                    <label className="block font-semibold mb-1">Creditor Name</label>
                    <Input
                      value={safeValue(t.creditor_name)}
                      onChange={(e) => updateTradeline(i, { creditor_name: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block font-semibold mb-1">Account Number</label>
                    <Input
                      value={safeValue(t.account_number)}
                      onChange={(e) => updateTradeline(i, { account_number: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block font-semibold mb-1">Status</label>
                    <Select
                      value={safeValue(t.account_status)}
                      onValueChange={(value) => updateTradeline(i, {
                        account_status: value as "" | "open" | "closed" | "in_collection" | "charged_off" | "disputed"
                      })}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="open">Open</SelectItem>
                        <SelectItem value="closed">Closed</SelectItem>
                        <SelectItem value="in_collection">In Collection</SelectItem>
                        <SelectItem value="charged_off">Charged Off</SelectItem>
                        <SelectItem value="disputed">Disputed</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="block font-semibold mb-1">Balance</label>
                    <Input
                      type="text"
                      value={safeValue(t.account_balance)}
                      onChange={(e) =>
                        updateTradeline(i, { account_balance: e.target.value })
                      }
                    />
                  </div>
                  <div>
                    <label className="block font-semibold mb-1">Credit Limit</label>
                    <Input
                      type="text"
                      value={safeValue(t.credit_limit)}
                      onChange={(e) =>
                        updateTradeline(i, { credit_limit: e.target.value })
                      }
                    />
                  </div>
                  <div>
                    <label className="block font-semibold mb-1">Date Opened</label>
                    <Input
                      type="date"
                      value={safeValue(t.date_opened)}
                      onChange={(e) => updateTradeline(i, { date_opened: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block font-semibold mb-1">Credit Bureau</label>
                    <Select
                      value={safeValue(t.credit_bureau)}
                      onValueChange={(value) => updateTradeline(i, {
                        credit_bureau: value as "equifax" | "transunion" | "experian"
                      })}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select credit bureau" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="equifax">Equifax</SelectItem>
                        <SelectItem value="experian">Experian</SelectItem>
                        <SelectItem value="transunion">TransUnion</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="block font-semibold mb-1">Monthly Payment</label>
                    <Input
                      type="text"
                      value={safeValue(t.monthly_payment)}
                      onChange={(e) =>
                        updateTradeline(i, { monthly_payment: e.target.value })
                      }
                    />
                  </div>
                  <div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => deleteTradeline(i)}
                      className="mt-2"
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="flex justify-end space-x-4">
            <Button onClick={handleProceed} disabled={selectedTradelineIds.size === 0}>
              Proceed to Step 2
            </Button>
          </div>

          {manualModalOpen && (
            <ManualTradelineModal
              onClose={() => setManualModalOpen(false)}
              onAdd={(t) => setTradelines([...tradelines, t])}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CreditReportUploadPage;

function validateCreditBureau(credit_bureau: string | undefined): 'equifax' | 'transunion' | 'experian' | '' {
  if (!credit_bureau) return '';
  const validBureaus = ['equifax', 'transunion', 'experian', ''];
  return validBureaus.includes(credit_bureau) ? credit_bureau as 'equifax' | 'transunion' | 'experian' : '';
}
