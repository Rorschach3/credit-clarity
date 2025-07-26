import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from '@supabase/supabase-js';
import { getGoogleCloudAccessToken } from './jwt-helper.ts';

// Document AI types
interface DocumentAIEntity {
  type: string;
  mentionText: string;
  properties: Array<{
    type: string;
    mentionText: string;
  }>;
}

interface TradelineData {
  creditor_name: string;
  account_number: string;
  account_balance: string;
  credit_limit: string;
  monthly_payment: string;
  date_opened: string;
  account_type: string;
  account_status: string;
  credit_bureau: string;
  is_negative: boolean;
}

serve(async (req) => {
  console.log('🚀 Process Credit Report function triggered');
  
  try {
    // Initialize Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '', // Using service role for storage access
      {
        global: { headers: { 'x-supabase-user-agent': 'supabase-edge-function' } },
        auth: { persistSession: false },
      }
    );

    // Parse the storage event payload
    const payload = await req.json();
    console.log('📄 Storage event payload:', payload);

    // Extract file information from the storage event
    const { bucket, name: filePath, metadata } = payload.record;
    const userId = metadata?.user_id;

    if (!userId) {
      console.error('❌ No user_id found in file metadata');
      return new Response(JSON.stringify({ error: 'No user_id in metadata' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    console.log(`📁 Processing file: ${filePath} for user: ${userId}`);

    // Download file from Supabase Storage
    const { data: fileData, error: downloadError } = await supabaseClient.storage
      .from(bucket)
      .download(filePath);

    if (downloadError || !fileData) {
      console.error('❌ Failed to download file:', downloadError);
      return new Response(JSON.stringify({ error: 'Failed to download file' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    console.log('✅ File downloaded successfully');

    // Convert file to buffer for Document AI processing
    const fileBuffer = await fileData.arrayBuffer();
    const fileBytes = new Uint8Array(fileBuffer);

    // Process document with Document AI
    const extractedTradelines = await processDocumentWithAI(fileBytes);
    console.log(`🔍 Extracted ${extractedTradelines.length} tradelines`);

    // Create credit report record first
    const { data: creditReport, error: reportError } = await supabaseClient
      .from('credit_reports')
      .insert({
        user_id: userId,
        report_date: new Date().toISOString(),
        // Add other fields as needed based on your schema
      })
      .select('id')
      .single();

    if (reportError || !creditReport) {
      console.error('❌ Failed to create credit report:', reportError);
      return new Response(JSON.stringify({ error: 'Failed to create credit report' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const reportId = creditReport.id;
    console.log(`📊 Created credit report with ID: ${reportId}`);

    // Insert tradelines into the existing tradelines table
    const tradelinesToInsert = extractedTradelines.map(tradeline => ({
      id: crypto.randomUUID(),
      user_id: userId,
      credit_report_id: reportId, // Link to the credit report
      creditor_name: tradeline.creditor_name || '',
      account_number: tradeline.account_number || '',
      account_balance: tradeline.account_balance || '',
      credit_limit: tradeline.credit_limit || '',
      monthly_payment: tradeline.monthly_payment || '',
      date_opened: tradeline.date_opened || '',
      account_type: tradeline.account_type || '',
      account_status: tradeline.account_status || '',
      credit_bureau: tradeline.credit_bureau || '',
      is_negative: tradeline.is_negative || false,
      dispute_count: 0,
      created_at: new Date().toISOString(),
    }));

    // Use upsert to handle potential duplicates
    const { data: insertedTradelines, error: tradelinesError } = await supabaseClient
      .from('tradelines')
      .upsert(tradelinesToInsert, {
        onConflict: 'user_id, account_number, creditor_name, credit_bureau',
        ignoreDuplicates: false
      })
      .select();

    if (tradelinesError) {
      console.error('❌ Failed to insert tradelines:', tradelinesError);
      return new Response(JSON.stringify({ error: 'Failed to insert tradelines' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    console.log(`✅ Successfully inserted ${insertedTradelines?.length || 0} tradelines`);

    return new Response(JSON.stringify({
      message: 'Credit report processed successfully',
      credit_report_id: reportId,
      tradelines_count: insertedTradelines?.length || 0,
      file_path: filePath
    }), {
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('❌ Function error:', error);
    return new Response(JSON.stringify({ 
      error: 'Internal server error',
      details: error.message 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
});

async function processDocumentWithAI(fileBytes: Uint8Array): Promise<TradelineData[]> {
  console.log('🤖 Starting Document AI processing');
  
  try {
    // Get Google Cloud credentials from environment
    const projectId = Deno.env.get('GOOGLE_CLOUD_PROJECT_ID');
    const location = Deno.env.get('GOOGLE_CLOUD_LOCATION') || 'us';
    const processorId = Deno.env.get('DOCUMENT_AI_PROCESSOR_ID');
    const credentials = Deno.env.get('GOOGLE_APPLICATION_CREDENTIALS_JSON');

    if (!projectId || !processorId || !credentials) {
      throw new Error('Missing required Google Cloud configuration');
    }

    // Parse credentials
    const credentialsObj = JSON.parse(credentials);

    // Create Document AI request
    const endpoint = `https://${location}-documentai.googleapis.com/v1/projects/${projectId}/locations/${location}/processors/${processorId}:process`;
    
    // Get access token
    const accessToken = await getGoogleCloudAccessToken(credentialsObj);

    const requestBody = {
      rawDocument: {
        content: btoa(String.fromCharCode(...fileBytes)),
        mimeType: 'application/pdf'
      }
    };

    // Call Document AI API
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw new Error(`Document AI API error: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();
    console.log('✅ Document AI processing completed');

    // Parse tradeline entities from Document AI response
    return parseTradelineEntities(result);

  } catch (error) {
    console.error('❌ Document AI processing failed:', error);
    throw error;
  }
}

function parseTradelineEntities(documentAIResponse: any): TradelineData[] {
  console.log('🔄 Parsing tradeline entities');
  
  const tradelines: TradelineData[] = [];
  
  try {
    const document = documentAIResponse.document;
    
    if (!document || !document.entities) {
      console.log('⚠️ No entities found in document');
      return tradelines;
    }

    // Look for tradeline entities
    for (const entity of document.entities) {
      if (entity.type === 'tradeline' || entity.type === 'account' || entity.type === 'credit_account') {
        const tradeline = extractTradelineFromEntity(entity, document.text);
        if (tradeline) {
          tradelines.push(tradeline);
        }
      }
    }

    // If no specific tradeline entities, try to extract from form fields
    if (tradelines.length === 0 && document.pages) {
      console.log('🔍 No tradeline entities found, trying form fields extraction');
      const formTradelines = extractFromFormFields(document.pages, document.text);
      tradelines.push(...formTradelines);
    }

    console.log(`📋 Parsed ${tradelines.length} tradeline entities`);
    return tradelines;

  } catch (error) {
    console.error('❌ Error parsing tradeline entities:', error);
    return tradelines;
  }
}

function extractTradelineFromEntity(entity: DocumentAIEntity, fullText: string): TradelineData | null {
  try {
    const tradeline: Partial<TradelineData> = {
      creditor_name: '',
      account_number: '',
      account_balance: '',
      credit_limit: '',
      monthly_payment: '',
      date_opened: '',
      account_type: '',
      account_status: '',
      credit_bureau: '',
      is_negative: false
    };

    // Extract properties from the entity
    if (entity.properties) {
      for (const property of entity.properties) {
        const value = property.mentionText?.trim() || '';
        
        switch (property.type) {
          case 'creditor_name':
          case 'company_name':
            tradeline.creditor_name = value;
            break;
          case 'account_number':
            tradeline.account_number = value;
            break;
          case 'balance':
          case 'account_balance':
            tradeline.account_balance = value;
            break;
          case 'credit_limit':
          case 'limit':
            tradeline.credit_limit = value;
            break;
          case 'monthly_payment':
          case 'payment':
            tradeline.monthly_payment = value;
            break;
          case 'date_opened':
          case 'open_date':
            tradeline.date_opened = value;
            break;
          case 'account_type':
          case 'type':
            tradeline.account_type = normalizeAccountType(value);
            break;
          case 'account_status':
          case 'status':
            tradeline.account_status = normalizeAccountStatus(value);
            break;
          case 'credit_bureau':
          case 'bureau':
            tradeline.credit_bureau = normalizeBureau(value);
            break;
        }
      }
    }

    // Determine if tradeline is negative based on status or other indicators
    tradeline.is_negative = isNegativeTradeline(tradeline);

    // Only return if we have at least creditor name or account number
    if (tradeline.creditor_name || tradeline.account_number) {
      return tradeline as TradelineData;
    }

    return null;
  } catch (error) {
    console.error('❌ Error extracting tradeline from entity:', error);
    return null;
  }
}

function extractFromFormFields(pages: any[], fullText: string): TradelineData[] {
  // Fallback extraction from form fields if no entities found
  // This would implement pattern matching for common credit report formats
  console.log('🔄 Extracting tradelines from form fields');
  
  const tradelines: TradelineData[] = [];
  
  // Implementation would depend on the specific structure of your credit reports
  // This is a simplified version - you'd need to adapt based on your data
  
  return tradelines;
}

function normalizeAccountType(type: string): string {
  const normalized = type.toLowerCase().trim();
  const typeMap: { [key: string]: string } = {
    'credit card': 'credit_card',
    'installment': 'loan',
    'mortgage': 'mortgage',
    'auto': 'auto_loan',
    'student': 'student_loan',
    'collection': 'collection'
  };
  
  return typeMap[normalized] || normalized;
}

function normalizeAccountStatus(status: string): string {
  const normalized = status.toLowerCase().trim();
  const statusMap: { [key: string]: string } = {
    'current': 'open',
    'paid': 'closed',
    'collection': 'in_collection',
    'charge off': 'charged_off',
    'charged off': 'charged_off'
  };
  
  return statusMap[normalized] || normalized;
}

function normalizeBureau(bureau: string): string {
  const normalized = bureau.toLowerCase().trim();
  if (normalized.includes('equifax')) return 'equifax';
  if (normalized.includes('transunion')) return 'transunion';
  if (normalized.includes('experian')) return 'experian';
  return normalized;
}

function isNegativeTradeline(tradeline: Partial<TradelineData>): boolean {
  const negativeStatuses = ['in_collection', 'charged_off', 'disputed'];
  const negativeTypes = ['collection'];
  
  return negativeStatuses.includes(tradeline.account_status || '') ||
         negativeTypes.includes(tradeline.account_type || '');
}

