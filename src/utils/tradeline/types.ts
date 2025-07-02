
import { z } from "zod";

// Type definitions for enum values
export type AccountType = "credit_card" | "loan" | "mortgage" | "auto_loan" | "student_loan" | "collection" | "";
export type AccountStatus = "open" | "closed" | "in_collection" | "charged_off" | "disputed" | "";
export type CreditBureau = "equifax" | "transunion" | "experian";

// Enhanced Zod schema with better validation and error handling
export const ParsedTradelineSchema = z.object({
  id: z.string().uuid().optional(),
  user_id: z.string().uuid().optional(),
  creditor_name: z.string().min(1).default(""),
  account_number: z.string().min(1).default(""),
  account_balance: z.string().default("$0"),
  created_at: z.string().datetime().default(() => new Date().toISOString()),
  credit_limit: z.string().default("$0"),
  monthly_payment: z.string().default("$0"),
  date_opened: z.string().default(""),
  is_negative: z.boolean().default(false),
  account_type: z.enum(["credit_card", "loan", "mortgage", "auto_loan", "student_loan", "collection", ""]).default("credit_card"),
  account_status: z.enum(["open", "closed", "in_collection", "charged_off", "disputed", ""]).default("open"),
  credit_bureau: z.enum(["equifax", "transunion", "experian", ""]).default(""),
  dispute_count: z.number().int().min(0).default(0),
  raw_text: z.string().default(""),
});

export type ParsedTradeline = z.infer<typeof ParsedTradelineSchema>;
