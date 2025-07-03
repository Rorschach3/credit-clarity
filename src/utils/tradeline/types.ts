
import { z } from "zod";

// Type definitions for enum values
export type AccountType = "credit_card" | "loan" | "mortgage" | "auto_loan" | "student_loan" | "collection" | "";
export type AccountStatus = "open" | "closed" | "in_collection" | "charged_off" | "disputed" | "";
export type CreditBureau = "equifax" | "transunion" | "experian" | "";

// Enhanced Zod schema with only required database fields
export const ParsedTradelineSchema = z.object({
  id: z.string().uuid().optional(),
  user_id: z.string().uuid().optional(),
  creditor_name: z.string().default(""),
  account_number: z.string().default(""),
  account_balance: z.string().default(""),
  created_at: z.string().datetime().default(() => new Date().toISOString()),
  credit_limit: z.string().default(""),
  monthly_payment: z.string().default(""),
  date_opened: z.string().default(""),
  is_negative: z.boolean().default(false),
  account_type: z.enum(["credit_card", "loan", "mortgage", "auto_loan", "student_loan", "collection", ""]).default(""),
  account_status: z.enum(["open", "closed", "in_collection", "charged_off", "disputed", ""]).default(""),
  credit_bureau: z.enum(["equifax", "transunion", "experian", ""]).default(""),
  dispute_count: z.number().int().min(0).default(0),
});

export type ParsedTradeline = z.infer<typeof ParsedTradelineSchema>;
