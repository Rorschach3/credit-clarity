#!/usr/bin/env node

import { createClient } from '@supabase/supabase-js';
import { readFileSync } from 'fs';
import { join } from 'path';

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.VITE_SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase credentials');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function applyStorageFix() {
  try {
    console.log('Reading SQL file...');
    const sqlContent = readFileSync(join(process.cwd(), 'fix_storage_issues.sql'), 'utf8');
    
    console.log('Applying storage fixes...');
    const { data, error } = await supabase.rpc('exec_sql', { sql: sqlContent });
    
    if (error) {
      console.error('Error applying fixes:', error);
      return;
    }
    
    console.log('✅ Storage fixes applied successfully!');
    console.log('The following have been created:');
    console.log('- dispute_documents storage bucket');
    console.log('- avatars storage bucket');
    console.log('- user_documents table columns: file_name, content_type, verified');
    console.log('- dispute_packets table');
    console.log('- Proper RLS policies for all buckets');
    
  } catch (error) {
    console.error('Error reading SQL file:', error);
  }
}

applyStorageFix();