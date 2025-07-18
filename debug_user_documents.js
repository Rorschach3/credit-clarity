// Debug script to test user_documents functionality
// Run this in browser console when logged in to test the fixes

console.log('🔍 Testing user_documents fixes...');

// Test 1: Check if we can query user_documents without errors
async function testUserDocumentsQuery() {
  try {
    const { supabase } = await import('./src/integrations/supabase/client.js');
    
    // Check session first
    const { data: session } = await supabase.auth.getSession();
    if (!session?.session) {
      console.log('❌ No active session');
      return;
    }
    
    console.log('✅ Active session found:', session.session.user.id);
    
    // Test basic query (should not get 406 error)
    const { data, error } = await supabase
      .from('user_documents')
      .select('document_type')
      .eq('user_id', session.session.user.id);
    
    if (error) {
      console.log('❌ Query error:', error);
      return;
    }
    
    console.log('✅ Query successful, documents found:', data?.length || 0);
    console.log('📄 Document types:', data?.map(d => d.document_type) || []);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Test 2: Check maybeSingle functionality
async function testMaybeSingleQuery() {
  try {
    const { supabase } = await import('./src/integrations/supabase/client.js');
    
    const { data: session } = await supabase.auth.getSession();
    if (!session?.session) {
      console.log('❌ No active session for maybeSingle test');
      return;
    }
    
    // Test maybeSingle for specific document type (should not get PGRST116)
    const { data, error } = await supabase
      .from('user_documents')
      .select('*')
      .eq('user_id', session.session.user.id)
      .eq('document_type', 'photo_id')
      .maybeSingle();
    
    if (error) {
      console.log('❌ maybeSingle error:', error);
      return;
    }
    
    console.log('✅ maybeSingle successful');
    console.log('📄 Photo ID document:', data ? 'Found' : 'Not found');
    
  } catch (error) {
    console.error('❌ maybeSingle test failed:', error);
  }
}

// Run tests
testUserDocumentsQuery();
testMaybeSingleQuery();

console.log('🏁 Debug tests completed. Check results above.');