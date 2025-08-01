// Shared tradeline types to avoid circular imports
import { z } from 'zod';

// Zod schemas for validation - Updated to match backend normalized data
export const APITradelineSchema = z.object({
  creditor_name: z.string().min(1, "Creditor name is required"),
  account_number: z.string().default(""), // Allow empty strings
  account_balance: z.string().default("$0"),
  account_status: z.string().default(""), // Allow empty strings
  account_type: z.string().min(1, "Account type is required"),
  date_opened: z.string().nullable().default(""), // Allow null after normalization
  credit_limit: z.string().default("$0"),
  credit_bureau: z.string().default(""), // Allow empty strings
  monthly_payment: z.string().default("$0"),
  is_negative: z.boolean().default(false),
  dispute_count: z.number().int().min(0).default(0)
});

export const ParsedTradelineSchema = z.object({
  id: z.string().uuid("Invalid UUID format"),
  user_id: z.string().uuid("Invalid user ID format"),
  creditor_name: z.string().min(1, "Creditor name is required"),
  account_number: z.string().default(""), // Allow empty strings
  account_balance: z.string().default("$0"),
  account_status: z.string().default(""), // Allow empty strings  
  account_type: z.string().min(1, "Account type is required"),
  date_opened: z.string().nullable().default(""), // Allow null after normalization
  is_negative: z.boolean().default(false),
  dispute_count: z.number().int().min(0).default(0),
  created_at: z.string().datetime("Invalid datetime format"),
  credit_limit: z.string().default("$0"),
  credit_bureau: z.string().default(""), // Allow empty strings
  monthly_payment: z.string().default("$0"),
});

// TypeScript interfaces inferred from Zod schemas
export type APITradeline = z.infer<typeof APITradelineSchema>;
export type ParsedTradeline = z.infer<typeof ParsedTradelineSchema>;

// Type for raw Supabase tradeline data (with nullable fields)
export interface DatabaseTradeline {
  id: string | null;
  user_id: string | null;
  creditor_name: string | null;
  account_number: string | null;
  account_balance: string | null;
  account_status: string | null;
  account_type: string | null;
  date_opened: string | null;
  is_negative: boolean | null;
  dispute_count: number | null;
  created_at: string | null;
  credit_limit: string | null;
  credit_bureau: string | null;
  monthly_payment: string | null;
}

// Interface for update operations
export interface TradelineUpdate {
  id: string;
  updates: Partial<ParsedTradeline>;
}

// Pagination options interface
export interface PaginationOptions {
  page?: number;
  pageSize?: number;
  sortBy?: 'created_at' | 'creditor_name' | 'account_balance';
  sortOrder?: 'asc' | 'desc';
}

// Paginated response interface
export interface PaginatedTradelinesResponse {
  data: ParsedTradeline[];
  pagination: {
    page: number;
    pageSize: number;
    totalCount: number;
    totalPages: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
}