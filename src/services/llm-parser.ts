import { HarmCategory, HarmBlockThreshold, GoogleGenerativeAI } from "@google/generative-ai";


// Helper function to clean and validate JSON responses
function cleanJsonResponse(responseText: string): string {
  if (!responseText || !responseText.trim()) {
    throw new Error('Empty response from LLM');
  }

  // Remove markdown code blocks
  let cleaned = responseText.replace(/```json\s*/g, '').replace(/```\s*$/g, '').trim();
  
  // Remove any text before the first { or [
  const jsonStart = Math.max(cleaned.indexOf('{'), cleaned.indexOf('['));
  if (jsonStart > 0) {
    cleaned = cleaned.substring(jsonStart);
  }
  
  // Remove any text after the last } or ]
  const jsonEndBrace = cleaned.lastIndexOf('}');
  const jsonEndBracket = cleaned.lastIndexOf(']');
  const jsonEnd = Math.max(jsonEndBrace, jsonEndBracket);
  
  if (jsonEnd > 0 && jsonEnd < cleaned.length - 1) {
    cleaned = cleaned.substring(0, jsonEnd + 1);
  }

  return cleaned;
}

export async function parseDocumentViaProxy(base64: string): Promise<string> {
  console.log(`📤 Sending to proxy: /parse-tradeline`);

  try {
    const res = await fetch('http://localhost:8000/parse-tradeline', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': import.meta.env.VITE_SUPABASE_API_KEY as string,
        'x-supabase-auth': import.meta.env.VITE_SUPABASE_AUTH_TOKEN as string,
      },
      body: JSON.stringify({ text: base64 }),
    });

    console.log(`📥 Response status: ${res.status}`);
    const responseText = await res.text();
    console.log(`📥 Raw response body: ${responseText.substring(0, 500)}...`);

    if (!res.ok) {
      console.error(`❌ Proxy error: ${responseText}`);
      throw new Error(`Proxy error: ${res.status} - ${responseText}`);
    }

    if (!responseText.trim()) {
      throw new Error('Empty response from proxy server');
    }

    const cleanedJson = cleanJsonResponse(responseText);
    console.log(`📥 Cleaned JSON response: ${cleanedJson.substring(0, 500)}...`);
    return cleanedJson;
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    console.error(`Network or server error in parseDocumentViaProxy: ${errorMessage}`);
    return "";
  }
}
const genAI = new GoogleGenerativeAI(import.meta.env.VITE_GEMINI_API_KEY);

const model = genAI.getGenerativeModel({ 
  model: 'gemini-1.5-flash',
  generationConfig: {
    maxOutputTokens: 2048,
    temperature: 0.2,
    topP: 0.8,
  },
  safetySettings: [
    { category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold: HarmBlockThreshold.BLOCK_NONE },
    { category: HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold: HarmBlockThreshold.BLOCK_NONE },
    { category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold: HarmBlockThreshold.BLOCK_NONE },
    { category: HarmCategory.HARM_CATEGORY_HARASSMENT, threshold: HarmBlockThreshold.BLOCK_NONE }
  ],
});

type GenerationChunk = string;

export async function generateContent(
  contents: { role: string; parts: { text: string }[] }[],
  onChunk?: (chunk: GenerationChunk) => void
): Promise<string> {
  const maxRetries = 3;
  let lastError: Error | null = null;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const result = await model.generateContentStream({
        contents: contents
      });
        const chunks: string[] = [];
        for await (const chunk of result.stream) {
          const text = chunk.text();
          chunks.push(text);
          onChunk?.(text);
        }

      const finalResult = chunks.join('');
      if (!finalResult.trim()) {
        throw new Error('Empty response from Gemini API');
      }

      return finalResult;
    } catch (err: unknown) {
      lastError = err instanceof Error ? err : new Error('Unknown error');
      console.warn(`Attempt ${attempt + 1} failed:`, lastError.message);

      if (lastError.message.includes('429') || lastError.message.toLowerCase().includes('rate')) {
        const delay = Math.pow(2, attempt) * 1000 + Math.random() * 1000;
        console.log(`Rate limited. Waiting ${delay}ms before retry...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }

      if (attempt < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  }

  throw lastError || new Error('Max retries exceeded');
}

export async function sendChatMessage(
  message: string,
  onChunk?: (chunk: GenerationChunk) => void
): Promise<string> {
  const maxRetries = 3;
  let lastError: Error | null = null;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const chat = model.startChat();
      const result = await chat.sendMessageStream(message);
      const chunks: string[] = [];
      for await (const chunk of result.stream) {
        const text = chunk.text();
        chunks.push(text);
        onChunk?.(text);
      }

      const finalResult = chunks.join('');
      if (!finalResult.trim()) {
        throw new Error('Empty response from chat API');
      }

      return finalResult;
    } catch (err: unknown) {
      lastError = err instanceof Error ? err : new Error('Unknown error');
      console.warn(`Chat attempt ${attempt + 1} failed:`, lastError.message);
      if (attempt < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
      }
    }
  }

  throw lastError || new Error('Max chat retries exceeded');
}

// FIXED: Return the parsed object instead of JSON string
export async function extractTradelineData(
  text: string,
  onChunk?: (chunk: GenerationChunk) => void
): Promise<string> { // Changed return type to string
  if (!text || !text.trim()) {
    throw new Error('Input text is empty');
  }

  const prompt = `You are a financial document parser. Extract the following fields from this credit report tradeline section and return ONLY a valid JSON object with no additional text, markdown, or explanations.
  
 Required JSON format:
 {
   "creditor_name": "string",
   "account_number": "string",
   "account_balance": "string",
   "created_at": "string (ISO format)",
   "credit_limit": "string",
   "monthly_payment": "string",
   "date_opened": "string",
   "is_negative": boolean,
   "account_type": "credit_card|loan|mortgage|auto_loan|student_loan|collection",
   "account_status": "open|closed|in_collection|charged_off|disputed|unknown",
   "dispute_count": number
 }
 
 Field constraints:
 - created_at should be today's date in ISO format if not found in text
 - account_type must be one of: "credit_card", "loan", "mortgage", "auto_loan", "student_loan", "collection"
 - account_status must be one of: "open", "closed", "in_collection", "charged_off", "disputed", "unknown"
 - is_negative should be true for negative accounts, false otherwise
 - Remove any markdown code blocks from your response
 - creditor_name must not be empty - use "Unknown" if not found
 - account_number must not be empty - use "0000" if not found
 - account_type must not be empty - use "other" if not found
 - credit_limit, account_balance, and monthly_payment default to "$0" if not found
 - date_opened defaults to "Unknown" if not found
 - dispute_count should be a number, default to 0
 
 Tradeline text to parse:
 \`\`\`
 ${text}
 \`\`\`
 
 Return only the JSON object, no other text:`;
 
   try {
     const result = await sendChatMessage(prompt, onChunk);
     console.log('Raw LLM response:', result);
     
     const cleanedJson = cleanJsonResponse(result);
     console.log('Cleaned JSON:', cleanedJson);
     
     // No longer validate structure here, return cleanedJson string
     return cleanedJson;
   } catch (err: unknown) {
     const errorMessage = err instanceof Error ? err.message : 'Unknown error';
     console.error(`Tradeline extraction failed: ${errorMessage}`);
 
     // For a fallback, return an empty JSON string or a string with a known error structure
     // The calling function (parseTradelineWithRetry) handles the fallback Tradeline creation
     return "";
   }
 }

export class GoogleGeminiParser {
  constructor(private apiKey = import.meta.env.VITE_GEMINI_API_KEY) {
    if (!this.apiKey) {
      throw new Error('Missing Gemini API Key');
    }
  }

  async parseTradelineWithGemini(text: string) {
    if (!text || !text.trim()) {
      throw new Error('Input text is required');
    }

    return extractTradelineData(text);
  }
}

export async function parseDocumentAndGenerate(
  base64: string,
  prompt: string,
  onChunk?: (chunk: GenerationChunk) => void
): Promise<string> {
  if (!base64 || !prompt) {
    throw new Error('Both base64 data and prompt are required');
  }

  try {
    const parsed = await parseDocumentViaProxy(base64);
    
    // Extract text from parsed response safely
    const documentText = typeof parsed === 'string' ? parsed : JSON.stringify(parsed);

    if (!documentText.trim()) {
      throw new Error('No text content found in parsed document');
    }

    const fullPrompt = `${prompt}\n\nDocument content:\n${documentText}`;    
    return generateContent([
      {
        role: "user",
        parts: [{ text: fullPrompt }]
      }
    ], onChunk);
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    console.error(`Document parsing and generation failed: ${errorMessage}`);
    throw err;
  }
}