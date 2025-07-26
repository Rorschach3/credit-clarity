// src/utils/aiService.ts

import { supabase } from "../../supabase/client";
import type { NegativeItem } from "@/types/document";
import { z } from "zod";

// Vite environment variable for OpenAI key
const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY as string;
const OPENAI_API_URL = "https://api.openai.com/v1/chat/completions";

// Zod schema for an extracted account
export const AccountSchema = z.object({
  accountNumber: z.string(),
  accountName: z.string(),
  creditorName: z.string(),
  accountBalance: z.string().optional(),
  accountStatus: z.string().optional(),
  accountType: z.string().optional(),
  dateOpened: z.string().optional(),
  isNegative: z.boolean().optional(),
});
export type Account = z.infer<typeof AccountSchema>;

// Zod schema for extracted text and structured data
export const ExtractedTextSchema = z.object({
  rawText: z.string(),
  structuredData: z.object({
    personalInfo: z
      .object({
        firstName: z.string().optional(),
        lastName: z.string().optional(),
        address: z.string().optional(),
        city: z.string().optional(),
        state: z.string().optional(),
        zip: z.string().optional(),
        email: z.string().optional(),
        ssnLastFour: z.string().optional(),
      })
      .optional(),
    accounts: z.array(AccountSchema),
  }),
});
export type ExtractedText = z.infer<typeof ExtractedTextSchema>;

// Zod schema for dispute analysis
export const DisputeAnalysisSchema = z.object({
  negativeItems: z.array(AccountSchema),
  recommendedDisputes: z.array(AccountSchema),
  analysisNotes: z.string(),
});
export type DisputeAnalysis = z.infer<typeof DisputeAnalysisSchema>;

// Zod schema for generated letter
export const GeneratedLetterSchema = z.object({
  content: z.string(),
  qualityScore: z.number(),
  suggestions: z.array(z.string()),
});
export type GeneratedLetter = z.infer<typeof GeneratedLetterSchema>;

// Zod schema for user data
export const UserDataSchema = z.object({
  firstName: z.string().optional(),
  lastName: z.string().optional(),
  address1: z.string().optional(),
  address2: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  zip: z.string().optional(),
  phoneNumber: z.string().optional(),
});
export type UserData = z.infer<typeof UserDataSchema>;

// Main AI service
  /**
   * Extract text and structured accounts from a document via Supabase Edge Function
   */
export const aiService = {
  // Extract text and structure data from document using OCR and AI
  async extractTextFromDocument(
    fileUrl: string,
    fileType: string
  ): Promise<ExtractedText> {
    try {
      const { data, error } = await supabase.functions.invoke('ai-document-extraction', {
        body: {
          fileUrl,
          fileType
        }
      });
      
      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error in AI text extraction:', error);
      throw new Error('Failed to extract text from document');
    }
  },

  /**
   * Analyze credit report to identify negative items via Supabase Edge Function
   */
  async analyzeReport(
    extractedText: ExtractedText
  ): Promise<DisputeAnalysis> {
    const { data, error } = await supabase.functions.invoke<DisputeAnalysis>(
      "ai-report-analysis",
      { body: { extractedText } }
    );
    if (error) {
      console.error("Error analyzing report:", error);
      throw new Error(error.message);
    }
    return DisputeAnalysisSchema.parse(data);
  },

  /**
   * Generate dispute letter via Supabase Edge Function
   */
  async generateDisputeLetter(
    items: NegativeItem[],
    bureau: string,
    userData: UserData,
  ): Promise<GeneratedLetter> {
    try {
      const { data, error } = await supabase.functions.invoke('ai-letter-generator', {
        body: {
          items,
          bureau,
          userData
        }
      });

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error in AI letter generation:', error);
      throw new Error('Failed to generate dispute letter');
    }
  },

  /**
   * Review and improve the letter via Supabase Edge Function
   */
  async reviewDisputeLetter(
    letterContent: string,
    bureau: string
  ): Promise<GeneratedLetter> {
    const { data, error } = await supabase.functions.invoke<GeneratedLetter>(
      "ai-letter-review",
      { body: { letterContent, bureau } }
    );
    if (error) {
      console.error("Error reviewing letter:", error);
      throw new Error(error.message);
    }
    return GeneratedLetterSchema.parse(data);
  },

  /**
   * General-purpose chat completion via OpenAI REST API
   */
  async chatCompletion(
    messages: { role: "system" | "user" | "assistant"; content: string }[],
    model: string = "gpt-3.5-turbo-16k",
    maxTokens: number = 2048
  ): Promise<string> {
    const res = await fetch(OPENAI_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({ model, messages, max_tokens: maxTokens, temperature: 0.7 }),
    });
    const json = await res.json();
    if (!res.ok) {
      console.error("OpenAI API error:", json);
      throw new Error(json.error?.message || "OpenAI request failed");
    }
    return json.choices?.[0]?.message?.content;
  },

  /**
   * Classify a single tradeline as negative or not
   */
  async classifyTradeline(
    text: string
  ): Promise<{ isNegative: boolean; reason: string }> {
    try {
      const content = await this.chatCompletion(
        [
          { role: "system", content: "You are a credit analyzer. Given a JSON tradeline, respond with { \"isNegative\": boolean, \"reason\": string }." },
          { role: "user", content: text }
        ],
        "gpt-3.5-turbo-16k"
      );
      return JSON.parse(content);
    } catch (err) {
      console.error("Error classifying tradeline:", err);
      return { isNegative: false, reason: "" };
    }
  }
};
