// src/types/index.ts
// This file exports types used across the application, including user and document AI response types.
// It also re-exports the ParsedTradeline type for convenience.
import { ParsedTradeline } from "@/utils/tradelineParser";

export interface DocumentAIResponse {
  document?: {
    text?: string;
    entities?: Array<{
      mentionText: string;
      type: string;
      confidence: number;
    }>;
    pages?: Array<{
      pageNumber: number;
      dimension: {
        width: number;
        height: number;
      };
    }>;
  };
  error?: {
    code: number;
    message: string;
    details?: Array<{
      [key: string]: unknown;
    }>;
  };
}

export interface User {
  id: string;
  email?: string;
  name?: string;
  avatar?: string;
  // Add other user properties needed by your application
}

export type { ParsedTradeline };