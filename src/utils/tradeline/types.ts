
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



export const ProfilesSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  first_name: z.string().min(1, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
  address1: z.string().nullable().optional(),
  address2: z.string().nullable().optional(),
  city: z.string().nullable().optional(),
  state: z.string().nullable().optional(),
  zip_code: z.string().nullable().optional(),
  phone_number: z.string().nullable().optional(),
  last_four_of_ssn: z.string().nullable().optional(),
  dob: z.string().nullable().optional(),
  created_at: z.string().datetime().default(() => new Date().toISOString()),
  updated_at: z.string().datetime().default(() => new Date().toISOString()),
  });
  
