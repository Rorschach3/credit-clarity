
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from 'supabase/';
import { z } from 'zod/';

// Replicate the ParsedTradelineSchema for validation within the Edge Function
const ParsedTradelineSchema = z.object({
  id: z.string().uuid().optional(),
  user_id: z.string().uuid(),
  creditor_name: z.string().default(""),
  account_number: z.string().default(""),
  account_balance: z.string().default(""),
  created_at: z.string().datetime().default(() => new Date().toISOString()),
  credit_limit: z.string().default(""),
  monthly_payment: z.string().default(""),
  date_opened: z.string().default(""),
  is_negative: z.boolean().default(false),
  account_type: z.enum(["credit_card", "loan", "mortgage", "auto_loan", "student_loan", "collection", ""]).default(""),
  account_status: z.enum(["open", "closed", "in_collection", "charged_off", "disputed", ""]).default(""),
  credit_bureau: z.enum(["equifax", "transunion", "experian", ""]).default(""),
  dispute_count: z.number().int().min(0).default(0),
});

const RequestBodySchema = z.object({
  tradelines: z.array(ParsedTradelineSchema),
});

serve(async (req) => {
  if (req.method !== 'POST') {
    return new Response("Method Not Allowed", { status: 405 });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      {
        global: { headers: { 'x-supabase-user-agent': 'supabase-edge-function' } },
        auth: { persistSession: false },
      }
    );

    // Get the user from the Supabase auth header
    const { data: { user } } = await supabaseClient.auth.getUser();

    if (!user) {
      return new Response(JSON.stringify({ error: 'Unauthorized: No user found' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const { tradelines } = await req.json();

    const validationResult = RequestBodySchema.safeParse({ tradelines });

    if (!validationResult.success) {
      console.error("Validation errors:", validationResult.error.errors);
      return new Response(JSON.stringify({
        error: "Invalid data format",
        details: validationResult.error.errors
      }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Prepare tradelines for UPSERT operation with default values
    const tradelinesToUpsert = validationResult.data.tradelines.map(tl => ({
      id: tl.id || crypto.randomUUID(),
      user_id: user.id,
      creditor_name: tl.creditor_name || "",
      account_number: tl.account_number || "",
      account_balance: tl.account_balance || "",
      created_at: tl.created_at || new Date().toISOString(),
      credit_limit: tl.credit_limit || "",
      monthly_payment: tl.monthly_payment || "",
      date_opened: tl.date_opened || "",
      is_negative: tl.is_negative || false,
      account_type: tl.account_type || "",
      account_status: tl.account_status || "",
      credit_bureau: tl.credit_bureau || "",
      dispute_count: tl.dispute_count || 0,
    }));

    // Use upsert to handle duplicates based on a composite unique key
    const { data, error } = await supabaseClient
      .from('tradelines')
      .upsert(tradelinesToUpsert, {
        onConflict: 'user_id, creditor_name, account_number, account_type',
        ignoreDuplicates: false
      })
      .select();

    if (error) {
      console.error("Database insert error:", error);
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({ message: "Tradelines added successfully", data }), {
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
