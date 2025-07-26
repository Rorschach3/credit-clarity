<<<<<<< Updated upstream:src/components/OCRAccountDisplay.tsx
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { parsePdfDocument } from "@/utils/pdf-parser";
import { extractAccounts, ParsedAccount } from "@/utils/ocr-parser";

interface OCRAccountDisplayProps {
  rawOcrText?: string;
  filePath?: string;
}

interface UpstageAccount {
  account_name?: string;
  account_number?: string;
}

type Account = ParsedAccount | UpstageAccount;

export const OCRAccountDisplay = async ({ rawOcrText, filePath }: OCRAccountDisplayProps) => {
  let accounts: Account[] = [];
  let errorMessage: string | null = null;

  if (filePath) {
    const apiKey = process.env.NEXT_PUBLIC_UPSTAGE_API_KEY;
    if (!apiKey) {
      errorMessage = "Upstage API key not found in environment variables.";
    } else {
      try {
        const parsedData = await parsePdfDocument(filePath, apiKey);
        if (parsedData) {
          accounts = [parsedData];
        }
      } catch (error: unknown) {
        errorMessage = `Error parsing PDF document: ${(error as Error).message}`;
      }
    }
  } else if (rawOcrText) {
    const cleanedText = rawOcrText
      .replace(/\n/g, ' ')
      .replace(/\s{2,}/g, ' ')
      .trim();
    accounts = extractAccounts(cleanedText);
  }

  return (
    <div>
      {errorMessage && <p className="text-sm text-red-500">{errorMessage}</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {accounts.map((account, index) => (
          <Card key={index}>
            <CardContent>
              <CardTitle>{(account as UpstageAccount).account_name || (account as ParsedAccount).accountName || "Unknown Account"}</CardTitle>
              <p className="text-sm text-muted-foreground">
                Account Number: {(account as UpstageAccount).account_number || (account as ParsedAccount).accountNumber || "N/A"}
              </p>
            </CardContent>
          </Card>
        ))}
        {accounts.length === 0 && !errorMessage && (
          <p className="text-sm text-gray-500">No accounts found.</p>
        )}
      </div>
    </div>
  );
};
=======
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { processPdfFile } from "@/utils/pdf-processor";
import { ParsedAccount, parseAccountNumbers } from "@/utils/ocr-parser";

interface OCRAccountDisplayProps {
  rawOcrText?: string;
  filePath?: string;
}

interface ProcessedAccount {
  account_name?: string;
  account_number?: string;
}

type Account = ParsedAccount | ProcessedAccount;

export const OCRAccountDisplay = async ({ rawOcrText, filePath }: OCRAccountDisplayProps) => {
  let accounts: Account[] = [];
  let errorMessage: string | null = null;

  if (filePath) {
    try {
      // Convert file path to File object for processing
      const response = await fetch(filePath);
      const blob = await response.blob();
      const file = new File([blob], 'credit-report.pdf', { type: 'application/pdf' });
      
      const result = await processPdfFile(file);
      if (result.text.length > 0) {
        // Parse the extracted text to find accounts
        const parsedAccounts = parseAccountNumbers(result.text);
        accounts = parsedAccounts;
      }
    } catch (error: unknown) {
      console.error("PDF processing error:", (error as Error).message);
      errorMessage = `Error processing PDF document: ${(error as Error).message}`;
    }
  } else if (rawOcrText) {
    const cleanedText = rawOcrText
      .replace(/\n/g, ' ')
      .replace(/\s{2,}/g, ' ')
      .trim();
    accounts = parseAccountNumbers(cleanedText);
  }

  return (
    <div>
      {errorMessage && <p className="text-sm text-red-500">{errorMessage}</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {accounts.map((account, index) => (
          <Card key={index}>
            <CardContent>
              <CardTitle>{(account as ProcessedAccount).account_name || (account as ParsedAccount).raw || "Unknown Account"}</CardTitle>
              <p className="text-sm text-muted-foreground">
                Account Number: {(account as ProcessedAccount).account_number || (account as ParsedAccount).normalized || "N/A"}
              </p>
            </CardContent>
          </Card>
        ))}
        {accounts.length === 0 && !errorMessage && (
          <p className="text-sm text-gray-500">No accounts found.</p>
        )}
      </div>
    </div>
  );
};
>>>>>>> Stashed changes:frontend/src/components/OCRAccountDisplay.tsx
