
import { z } from "zod";
import { supabase } from "@/integrations/supabase/client";

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
      tl.creditor_name && tl.account_number
    );
    
    const partialTradelines = tradelines.filter(tl =>
      !tl.creditor_name || !tl.account_number
    );
    
    if (partialTradelines.length > 0) {
      console.warn(`⚠️ Skipping ${partialTradelines.length} partial tradelines:`, partialTradelines);
    }

    if (validTradelines.length === 0) {
      console.warn("⚠️ No valid tradelines to save after filtering");
      return;
    }

    // Prepare tradelines with only required database fields and default values
    const tradelinesToSave = validTradelines.map(tl => ({
      id: tl.id || crypto.randomUUID(),
      user_id: userId,
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

    console.log('Saving tradelines to database:', tradelinesToSave);
    
    const { data, error } = await supabase
      .from('tradelines')
      .upsert(tradelinesToSave, {
        onConflict: 'user_id, creditor_name, account_number, account_type',
        ignoreDuplicates: false
      })
      .select();

    if (error) {
      console.error("Database insert error:", error);
      throw error;
    }

    console.log("Tradeline save successful:", data);
    return data;
  } catch (error) {
    console.error("Error in saveTradelinesToDatabase:", error);
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
        account_balance: item.account_balance || "",
        created_at: item.created_at || new Date().toISOString(),
        credit_limit: item.credit_limit || "",
        monthly_payment: item.monthly_payment || "",
        date_opened: item.date_opened || "",
        is_negative: item.is_negative || false,
        account_type: item.account_type || "",
        account_status: item.account_status || "",
        credit_bureau: item.credit_bureau || "",
        dispute_count: item.dispute_count || 0,
      } as ParsedTradeline;
    }) : [];
    
    // Filter out partial tradelines (missing critical fields)
    return parsedData.filter(tl =>
      tl.creditor_name && tl.account_number
    );
  } catch (error) {
    console.error("Error in fetchUserTradelines:", error);
    throw error;
  }
};
