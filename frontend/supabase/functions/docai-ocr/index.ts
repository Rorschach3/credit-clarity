// supabase/functions/docai-ocr/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { processDocument } from './src/utils/docai-ocr.ts';

const PROJECT_ID = Deno.env.get("PROJECT_ID");
const LOCATION = Deno.env.get("LOCATION");
const PROCESSOR_ID = Deno.env.get("PROCESSOR_ID");
const SERVICE_ACCOUNT_KEY = JSON.parse(Deno.env.get("SERVICE_ACCOUNT_KEY") || '{}');

serve(async (req) => {
  if (req.method !== 'POST') {
    return new Response("Method Not Allowed", { status: 405 });
  }

  try {
    const { file, mimeType } = await req.json();

    if (!file || !mimeType) {
      return new Response("Missing file or mimeType", { status: 400 });
    }

    const text = await processDocument(new Uint8Array(file), mimeType, PROJECT_ID, LOCATION, PROCESSOR_ID, SERVICE_ACCOUNT_KEY);
    return new Response(JSON.stringify({ text }), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error("Function error:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
});