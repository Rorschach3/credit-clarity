import { z } from "zod";

/**
 * Schema for a credit report tradeline (account) and its dispute-relevant info.
 */
export const AccountSchema = z.object({
  creditorName: z.string(),
  accountNumber: z.string(),
  accountStatus: z.string(),
  accountBalance: z.number().optional(),       // balance might be absent or zero if not provided
  dateOpened: z.string().optional(),    // date opened as a string (e.g. "Jan 2020"), if available
  isNegative: z.boolean(),
  negativeReason: z.string().optional() // reason why the item is negative/disputed (if any)
});
export type Account = z.infer<typeof AccountSchema>;

/**
 * Schema for raw extracted text (e.g. from OCR of a credit report PDF).
 */
export const ExtractedTextSchema = z.object({
  text: z.string()
});
export type ExtractedText = z.infer<typeof ExtractedTextSchema>;

/**
 * Schema for analysis of a credit report's disputed items.
 * Contains a list of accounts (tradelines) and a summary of findings.
 */
export const DisputeAnalysisSchema = z.object({
  accounts: z.array(AccountSchema),      // all accounts identified (with dispute info)
  summary: z.string()                    // a summary of negative items or findings
});
export type DisputeAnalysis = z.infer<typeof DisputeAnalysisSchema>;

/**
 * Schema for a generated dispute letter.
 */
export const GeneratedLetterSchema = z.object({
  letter: z.string()  // the full text content of the dispute letter
});
export type GeneratedLetter = z.infer<typeof GeneratedLetterSchema>;

/**
 * Schema for user data required in AI tasks (e.g. letter generation).
 */
export const UserDataSchema = z.object({
  name: z.string(),
  address: z.string()
});
export type UserData = z.infer<typeof UserDataSchema>;
