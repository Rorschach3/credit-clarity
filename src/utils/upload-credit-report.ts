
// src/utils/uploadCreditReport.ts
export async function uploadCreditReport(
  pdfDataUrl: string,
  token: string
) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json"
  };

  // Only add API key if it exists
  if (process.env.SUPABASE_API_KEY) {
    headers.apikey = process.env.SUPABASE_API_KEY;
  }

  const res = await fetch(
    "/functions/add-tradeline",
    {
      method: "POST",
      headers,
      body: JSON.stringify({ file: pdfDataUrl, token }),
    }
  );
  return res.json();
}
