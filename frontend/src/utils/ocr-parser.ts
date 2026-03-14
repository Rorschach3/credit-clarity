export interface ParsedAccount {
  raw: string;
  normalized: string;
}

// Extracts account-number-like sequences from OCR text.
// Matches 4–20 digit strings, optionally separated by spaces or dashes.
export function parseAccountNumbers(text: string): ParsedAccount[] {
  const pattern = /\b(\d[\d\s-]{2,18}\d)\b/g;
  const seen = new Set<string>();
  const accounts: ParsedAccount[] = [];

  let match;
  while ((match = pattern.exec(text)) !== null) {
    const raw = match[1];
    const normalized = raw.replace(/[\s-]/g, '');
    if (normalized.length >= 4 && normalized.length <= 20 && !seen.has(normalized)) {
      seen.add(normalized);
      accounts.push({ raw, normalized });
    }
  }

  return accounts;
}
