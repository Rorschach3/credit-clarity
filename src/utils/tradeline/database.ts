
import { z } from "zod";
import { supabase } from "@/integrations/supabase/client";
import { ParsedTradeline } from "./types";

const uuidSchema = z.string().uuid();

// Enhanced database save with better error handling
export async function saveTradelinesToDatabase(tradelines: ParsedTradeline[], userId: string) {
  if (!uuidSchema.safeParse(userId).success) {
    console.error("❌ Invalid user_id provided:", userId);
    return;
  }

  try {
    // Filter out partial tradelines (missing critical fields)
    const validTradelines = tradelines.filter(tl =>
      tl.creditor_name && tl.account_number && tl.account_type
    );
    
    const partialTradelines = tradelines.filter(tl =>
      !tl.creditor_name || !tl.account_number || !tl.account_type
    );
    
    if (partialTradelines.length > 0) {
      console.warn(`⚠️ Skipping ${partialTradelines.length} partial tradelines:`, partialTradelines);
    }

    if (validTradelines.length === 0) {
      console.warn("⚠️ No valid tradelines to save after filtering");
      return;
    }

    // Deduplicate tradelines using the same composite key as backend
    const dedupedTradelines = validTradelines.reduce((acc, current) => {
      const key = `${current.user_id}|${current.creditor_name}|${current.account_number}|${current.account_type}`;
      
      // Only add if we haven't seen this combination before
      if (!acc.has(key)) {
        acc.set(key, current);
      } else {
        console.log(`⚠️ Skipping duplicate tradeline: ${key}`);
      }
      
      return acc;
    }, new Map<string, ParsedTradeline>());

    const uniqueTradelines = Array.from(dedupedTradelines.values());
    
    if (uniqueTradelines.length < validTradelines.length) {
      console.warn(`⚠️ Removed ${validTradelines.length - uniqueTradelines.length} duplicate tradelines`);
    }

    console.log('Saving tradelines to database:', uniqueTradelines);
    console.log("Attempting to save tradelines via Edge Function:", { count: uniqueTradelines.length, userId });
    
    const payload = { tradelines: uniqueTradelines.map(tl => ({ ...tl, user_id: userId })) };
    console.log("Payload sent to Edge Function:", JSON.stringify(payload, null, 2));

    const response = await fetch('https://gywohmbqohytziwsjrps.supabase.co/functions/v1/add-tradeline', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`,
      },
      body: JSON.stringify(payload),
    });

    console.log(`Edge Function response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Edge Function error response body:", errorData);
      throw new Error(`Failed to save tradelines via Edge Function: ${errorData.message || response.statusText}`);
    }

    const result = await response.json();
    console.log("Tradeline save successful via Edge Function:", result);
    return result;
  } catch (error) {
    console.error("Error in saveTradelinesToDatabase (Edge Function call):", error);
    throw error;
  }
}

// Add logging to your fetch function
export const fetchUserTradelines = async (user_id: string): Promise<ParsedTradeline[]> => {
  try {
    console.log("Fetching tradelines for user:", user_id);
    
    const { data, error } = await supabase
      .from('tradelines')
      .select('*')
      .eq('user_id', user_id);
  
    if (error) {
      console.error("Database fetch error:", error);
      throw error;
    }
    
    console.log("Fetch successful:", { count: data?.length || 0, data });
    
    // Validate and transform fetched data to ParsedTradeline schema
    const parsedData = data ? data.map(item => {
      // Convert the raw database row to ParsedTradeline format
      return {
        id: item.id,
        user_id: item.user_id,
        creditor_name: item.creditor_name || "",
        account_number: item.account_number || "",
        account_balance: item.account_balance || "$0",
        created_at: item.created_at || new Date().toISOString(),
        credit_limit: item.credit_limit || "$0",
        monthly_payment: item.monthly_payment || "$0",
        date_opened: item.date_opened || "",
        is_negative: item.is_negative || false,
        account_type: item.account_type || "credit_card",
        account_status: item.account_status || "open",
        credit_bureau: item.credit_bureau || "",
        dispute_count: item.dispute_count || 0,
        raw_text: item.raw_text || "",
      } as ParsedTradeline;
    }) : [];
    
    // Filter out partial tradelines (missing critical fields)
    return parsedData.filter(tl =>
      tl.creditor_name && tl.account_number && tl.account_type
    );
  } catch (error) {
    console.error("Error in fetchUserTradelines:", error);
    throw error;
  }
};
