import { z } from "zod";
const API_BASE_URL = typeof window === "undefined" ? "http://localhost:8000" : "";
const API_ENDPOINT = `${API_BASE_URL}/api/process-credit-report`;

export interface CreditReportData {
  user_id: string;
  credit_score?: number;
  report_data: {
    tradelines?: unknown[];
  };
}

export interface CreditReportProcessingResult {
  success: boolean;
  tradelines: unknown[];
  credit_score?: number;
}

const userIdSchema = z.string().uuid("Invalid user_id format");
const creditScoreSchema = z
  .number()
  .min(300, "Credit score must be between 300 and 850")
  .max(850, "Credit score must be between 300 and 850");

export const validateCreditReportData = (data: CreditReportData): void => {
  if (!data?.report_data) {
    throw new Error("Report data is required");
  }

  const userIdResult = userIdSchema.safeParse(data.user_id);
  if (!userIdResult.success) {
    throw new Error(userIdResult.error.issues[0]?.message || "Invalid user_id format");
  }

  if (data.credit_score !== undefined) {
    const creditScoreResult = creditScoreSchema.safeParse(data.credit_score);
    if (!creditScoreResult.success) {
      throw new Error("Credit score must be between 300 and 850");
    }
  }
};

export const processCreditReport = async (
  file: File,
  userId: string,
  onProgress?: (message: string) => void
): Promise<CreditReportProcessingResult> => {
  if (file.type !== "application/pdf") {
    throw new Error("Only PDF files are supported");
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_id", userId);

  onProgress?.("Uploading credit report...");
  const response = await fetch(API_ENDPOINT, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to process credit report");
  }

  const result = await response.json();

  return {
    success: true,
    tradelines: result.tradelines ?? [],
    credit_score: result.credit_score,
  };
};
