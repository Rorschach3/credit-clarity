import { z } from "zod";
import { supabase } from "../../integrations/supabase/client";
import { ParsedTradeline } from "../../utils/tradelineParser";
import { Tables } from "../../integrations/supabase/types";

const uuidSchema = z.string().uuid();

interface DuplicateCheckResult {
  isDuplicate: boolean;
  existingTradeline?: Tables<'tradelines'>;
  shouldUpdate: boolean;
}

/**
 * Enhanced database operations with custom duplicate detection and progressive enrichment
 */

// Helper function to get first 4 digits of account number
 function getAccountFirst4(accountNumber: string | null | undefined): string {
   if (!accountNumber) return '';
   // Remove non-alphanumeric characters and get first 4
   const cleaned = accountNumber.replace(/[^A-Za-z0-9]/g, '');
   return cleaned.substring(0, 4).toUpperCase();
 }

 type ComparableValue = string | number | null | undefined;

 
 // Helper function to check if a field is empty or should be updated
function shouldUpdateField(existingValue: ComparableValue, newValue: ComparableValue): boolean {
  if (existingValue === null || existingValue === undefined) return true;
  if (existingValue === '') return true;
  if (existingValue === '$0' || existingValue === '$0.00') return true;
  if (existingValue === '0' || existingValue === 0) return true;
  return false;
}

 
 // Custom duplicate detection based on new criteria
 async function findDuplicateTradeline(
   tradeline: ParsedTradeline,
   userId: string
 ): Promise<DuplicateCheckResult> {
   try {
     const accountFirst4 = getAccountFirst4(tradeline.account_number);
     
     // Query for potential duplicates using the new criteria
     const { data: existingTradelines, error } = await supabase
       .from('tradelines')
       .select('*')
       .eq('user_id', userId)
       .eq('creditor_name', tradeline.creditor_name)
       .eq('date_opened', tradeline.date_opened)
       .eq('credit_bureau', tradeline.credit_bureau);
 
     if (error) {
       console.error('Error checking for duplicates:', error);
       return { isDuplicate: false, shouldUpdate: false };
     }
 
     // Check if any existing tradeline has matching first 4 digits
     const duplicate = existingTradelines?.find(existing =>
       getAccountFirst4(existing.account_number) === accountFirst4
     );
 
     if (duplicate) {
       // Check if we should update the existing tradeline
       const fieldsToCheck: Array<keyof Tables<'tradelines'>['Row']> = [
         'account_balance', 'credit_limit', 'monthly_payment',
         'account_status', 'account_type'
       ];
       
       const shouldUpdate = fieldsToCheck.some(field =>
         shouldUpdateField(duplicate[field], tradeline[field])
       );
 
       return {
         isDuplicate: true,
         existingTradeline: duplicate,
         shouldUpdate
       };
     }
 
     return { isDuplicate: false, shouldUpdate: false };
     
   } catch (error) {
     console.error('Error in duplicate detection:', error);
     return { isDuplicate: false, shouldUpdate: false };
   }
 }
 
 // Progressive enrichment: merge new data into existing tradeline
 function enrichExistingTradeline(existing: Tables<'tradelines'>, newTradeline: ParsedTradeline): Tables<'tradelines'>['Update'] {
   const enriched: Tables<'tradelines'>['Update'] = { ...existing };
   
   // Fields that should be progressively enriched
   const enrichableFields: Array<keyof Tables<'tradelines'>['Row']> = [
     'account_balance',
     'credit_limit',
     'monthly_payment',
     'account_status',
     'account_type',
     'account_number' // Update to full account number if we have it
   ];
   
enrichableFields.forEach(field => {
  const oldVal = existing[field];
  const newVal = newTradeline[field];

  if (shouldUpdateField(oldVal, newVal)) {
    enriched[field] = newVal;

    console.log(`🔄 Enriching [${String(field)}]:`, {
      from: oldVal,
      to: newVal,
      confidence: 'high', // Optional: for LLMs scoring enrichment reliability
      source: 'tradeline_merge',
      timestamp: new Date().toISOString(),
    });
  }
});

   
   return enriched;
 }
 
 export async function saveTradelinesWithEnrichment(tradelines: ParsedTradeline[], userId: string) {
   if (!uuidSchema.safeParse(userId).success) {
     console.error("❌ Invalid user_id provided:", userId);
     return;
   }
 
   try {
     // Filter out partial tradelines (missing critical fields)
     const validTradelines = tradelines.filter(tl =>
       tl.creditor_name &&
       tl.account_number &&
       tl.credit_bureau &&
       tl.date_opened
     );
     
     const partialTradelines = tradelines.filter(tl =>
       !tl.creditor_name ||
       !tl.account_number ||
       !tl.credit_bureau ||
       !tl.date_opened
     );
     
     if (partialTradelines.length > 0) {
       console.warn(`⚠️ Skipping ${partialTradelines.length} partial tradelines (missing required fields):`,
         partialTradelines.map(tl => ({
           creditor: tl.creditor_name,
           account: tl.account_number?.substring(0, 4),
           bureau: tl.credit_bureau,
           date_opened: tl.date_opened
         }))
       );
     }
 
     if (validTradelines.length === 0) {
       console.warn("⚠️ No valid tradelines to save after filtering");
       return;
     }
 
     console.log(`🔍 Processing ${validTradelines.length} tradelines with enhanced duplicate detection`);
     
     const results = {
       inserted: [] as Tables<'tradelines'>[],
       updated: [] as Tables<'tradelines'>[],
       skipped: [] as { creditor_name: string; account_prefix: string; credit_bureau: string; reason: string }[]
     };
 
     // Process each tradeline individually with custom duplicate detection
     for (const tradeline of validTradelines) {
       try {
         // Check for duplicates using new criteria
         const duplicateCheck = await findDuplicateTradeline(tradeline, userId);
         
         if (duplicateCheck.isDuplicate && duplicateCheck.existingTradeline) {
           if (duplicateCheck.shouldUpdate) {
             // Update existing tradeline with progressive enrichment
             const enrichedTradeline = enrichExistingTradeline(
               duplicateCheck.existingTradeline,
               tradeline
             );
             
             const { data: updateData, error: updateError } = await supabase
               .from('tradelines')
               .update(enrichedTradeline)
               .eq('id', duplicateCheck.existingTradeline.id)
               .select()
               .single();
 
             if (updateError) {
               console.error('❌ Error updating tradeline:', updateError);
               continue;
             }
 
             results.updated.push(updateData);
             console.log(`✅ Updated existing tradeline for ${tradeline.creditor_name} (${getAccountFirst4(tradeline.account_number)}****)`);
             
           } else {
             // Skip - duplicate exists and no fields need updating
             results.skipped.push({
               creditor_name: tradeline.creditor_name,
               account_prefix: getAccountFirst4(tradeline.account_number),
               credit_bureau: tradeline.credit_bureau,
               reason: 'Duplicate exists with complete data'
             });
             console.log(`⏭️  Skipped duplicate: ${tradeline.creditor_name} (${getAccountFirst4(tradeline.account_number)}****) - no updates needed`);
           }
         } else {
           // Insert new tradeline
           const tradelineToInsert: Tables<'tradelines'>['upsert'] = {
             id: tradeline.id || crypto.randomUUID(),
             user_id: userId,
             creditor_name: tradeline.creditor_name || "",
             account_number: tradeline.account_number || "",
             account_balance: tradeline.account_balance || "$0", // Ensure null for optional fields
             created_at: tradeline.created_at || new Date().toISOString(),
             credit_limit: tradeline.credit_limit || "$0",
             monthly_payment: tradeline.monthly_payment || "$0",
             date_opened: tradeline.date_opened || null,
             is_negative: tradeline.is_negative || false,
             account_type: tradeline.account_type || null,
             account_status: tradeline.account_status || null,
             credit_bureau: tradeline.credit_bureau || null,
             dispute_count: tradeline.dispute_count || 0,
           };
 
           const { data: insertData, error: insertError } = await supabase
             .from('tradelines')
             .upsert(tradelineToInsert)
             .select()
             .single();
 
           if (insertError) {
             // Check if it's a unique constraint violation from our new index
             if (insertError.code === '23505') {
               console.warn(`⚠️ Unique constraint violation for ${tradeline.creditor_name} - may have been inserted concurrently`);
               results.skipped.push({
                 creditor_name: tradeline.creditor_name,
                 account_prefix: getAccountFirst4(tradeline.account_number),
                 credit_bureau: tradeline.credit_bureau,
                 reason: 'Unique constraint violation'
               });
             } else {
               console.error('❌ Error inserting tradeline:', insertError);
             }
             continue;
           }
 
           results.inserted.push(insertData);
           console.log(`✅ Inserted new tradeline: ${tradeline.creditor_name} (${getAccountFirst4(tradeline.account_number)}****)`);
         }
       } catch (error) {
         console.error(`❌ Error processing tradeline ${tradeline.creditor_name}:`, error);
         continue;
       }
     }
 
     console.log(`📊 Processing complete: ${results.inserted.length} inserted, ${results.updated.length} updated, ${results.skipped.length} skipped`);
     
     return {
       success: true,
       inserted: results.inserted,
       updated: results.updated,
       skipped: results.skipped,
       total: results.inserted.length + results.updated.length
     };
 
   } catch (error) {
     console.error("❌ Error in saveTradelinesWithEnrichment:", error);
     throw error;
   }
 }
 
 // Updated fetch function (unchanged from original)
 export const fetchUserTradelinesEnhanced = async (user_id: string): Promise<ParsedTradeline[]> => {
   try {
     console.log("Fetching tradelines for user:", user_id);
     
     const { data, error } = await supabase
       .from('tradelines')
       .select('*')
       .eq('user_id', user_id)
       .order('credit_bureau', { ascending: true })
       .order('creditor_name', { ascending: true });
   
     if (error) {
       console.error("Database fetch error:", error);
       throw error;
     }
     
     console.log("Fetch successful:", { count: data?.length || 0 });
     
     // Validate and transform fetched data to ParsedTradeline schema
     const parsedData = data ? data.map(item => {
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
     
     return parsedData;
   } catch (error) {
     console.error("Error in fetchUserTradelinesEnhanced:", error);
     throw error;
   }
 };
 
 // Export the enhanced version as the main function
 export { saveTradelinesWithEnrichment as saveTradelinesToDatabase };

