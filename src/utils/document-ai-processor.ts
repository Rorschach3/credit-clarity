// src/utils/document-ai-processor.ts

export type ParsedTradeline = {
  creditor_name: string;
  account_number: string;
  account_balance: string;
  credit_limit: string;
  monthly_payment: string;
  date_opened: string;
  account_status: string;
  account_type: string;
  credit_bureau: string;
  is_negative: boolean;
  user_id?: string;
};

export async function processAndSaveTradelines(file: File): Promise<ParsedTradeline[]> {
  const backend = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

  // Step 1: Upload the file
  const formData = new FormData();
  formData.append("file", file);

  const uploadResponse = await fetch(`${backend}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!uploadResponse.ok) {
    const error = await uploadResponse.json();
    throw new Error(error.detail || "Failed to upload file");
  }

  const { job_id } = await uploadResponse.json();

  // Step 2: Trigger normalization
  const normalizeResponse = await fetch(`${backend}/api/llm/normalize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_id,
      document_type: "credit_report",
      confidence_threshold: 0.7,
    }),
  });

  if (!normalizeResponse.ok) {
    const error = await normalizeResponse.json();
    throw new Error(error.detail || "Failed to normalize document");
  }

  const result = await normalizeResponse.json();
  return result.tradelines as ParsedTradeline[];
}

export async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result;
      if (typeof result === "string") {
        const base64 = result.split(",")[1];
        resolve(base64);
      } else {
        reject("Failed to read file as base64 string");
      }
    };
    reader.onerror = (error) => reject(error);
  });
}
