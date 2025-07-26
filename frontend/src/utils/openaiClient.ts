import { z } from "zod";

/**
 * Type for OpenAI chat messages.
 */
export type ChatMessage = {
  role: "system" | "user" | "assistant";
  content: string;
};

const OPENAI_API_URL = "https://api.openai.com/v1/chat/completions";
// Load OpenAI API key from environment (Vite env or Node/Deno env for Supabase Edge Functions)
const OPENAI_API_KEY = 
  // Vite environment variable (compile-time)
  import.meta.env.VITE_OPENAI_API_KEY ||
  // Node.js environment variable (if running in Node context)
  (typeof process !== "undefined" ? process.env.OPENAI_API_KEY : undefined) ||
  // Deno environment variable (if running in Supabase Edge Function)
  (typeof Deno !== "undefined" ? Deno.env.get("OPENAI_API_KEY") : undefined);

if (!OPENAI_API_KEY) {
  console.error("Error: OpenAI API key is not set in the environment.");
}

/**
 * Generic helper to call OpenAI's Chat Completion API and parse the result into a Zod-validated type.
 * @param schema Zod schema to validate the expected response structure.
 * @param messages Array of chat messages (with roles and content) to send to the OpenAI API.
 * @param model (optional) The OpenAI model to use (defaults to gpt-3.5-turbo).
 * @returns Parsed response of type T, as defined by the provided Zod schema.
 * @throws Will throw an error if the HTTP request fails, or if the response cannot be parsed/validated.
 */
export async function fetchOpenAIChat<T>(schema: z.ZodSchema<T>, messages: ChatMessage[], model: string = "gpt-3.5-turbo-16k"): Promise<T> {
  // Make sure the API key is available
  if (!OPENAI_API_KEY) {
    throw new Error("OpenAI API key is not configured. Cannot call OpenAI API.");
  }

  // Send the request to OpenAI's Chat Completion API
  const response = await fetch(OPENAI_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${OPENAI_API_KEY}`
    },
    body: JSON.stringify({
      model,
      messages,
      temperature: 0, // use deterministic output for consistent JSON structure
      top_p: 1
    })
  });

  if (!response.ok) {
    // Include status code and message in error for easier debugging
    throw new Error(`OpenAI API request failed: ${response.status} ${response.statusText}`);
  }

  const result = await response.json();
  const rawContent: string | undefined = result?.choices?.[0]?.message?.content;
  if (!rawContent) {
    throw new Error("OpenAI response did not contain any content.");
  }

  // Clean up the content to ensure valid JSON (remove any markdown formatting if present)
  let content = rawContent.trim();
  if (content.startsWith("```")) {
    // Remove wrapping triple backticks or ```json``` if present
    content = content.replace(/^```(?:json)?\s*([\s\S]*?)\s*```$/, "$1").trim();
  }

  // Parse the content string as JSON
  let data: unknown;
  try {
    data = JSON.parse(content);
  } catch (parseErr) {
    console.error("Failed to parse OpenAI content as JSON:", content);
    throw new Error("OpenAI response was not valid JSON.");
  }

  // Validate and return the parsed data against the expected schema
  return schema.parse(data);
}
