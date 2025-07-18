// Test script for complete dispute packet generation
// Run this in browser console when logged in and dispute letters are generated

console.log('🧪 Testing Complete Dispute Packet Generation');

async function testCompletePacket() {
  try {
    // Get modules
    const { supabase } = await import('./src/integrations/supabase/client.js');
    const { fetchUserDocuments, downloadDocumentBlobs } = await import('./src/utils/documentPacketUtils.js');
    const { generateCompletePacket } = await import('./src/utils/disputeUtils.js');
    
    // Check session
    const { data: session } = await supabase.auth.getSession();
    if (!session?.session) {
      console.error('❌ No active session');
      return;
    }
    
    const userId = session.session.user.id;
    console.log('✅ User ID:', userId);
    
    // Test 1: Fetch user documents
    console.log('\n📋 Test 1: Fetching user documents...');
    const userDocuments = await fetchUserDocuments(userId);
    console.log(`✅ Found ${userDocuments.length} user documents`);
    
    userDocuments.forEach(doc => {
      console.log(`  📄 ${doc.document_type}: ${doc.file_name}`);
    });
    
    // Test 2: Download document blobs
    console.log('\n📥 Test 2: Downloading document blobs...');
    const documentBlobs = await downloadDocumentBlobs(userDocuments);
    console.log(`✅ Downloaded ${documentBlobs.length} document blobs`);
    
    documentBlobs.forEach(blob => {
      console.log(`  📎 ${blob.document.document_type}: ${blob.type} (${blob.blob.size} bytes)`);
    });
    
    // Test 3: Check for mock dispute letters (you'll need to have these generated)
    console.log('\n📝 Test 3: Checking for dispute letters...');
    const mockLetters = [
      {
        id: 'test-experian',
        creditBureau: 'Experian',
        tradelines: [],
        letterContent: 'Test dispute letter content for Experian...',
        disputeCount: 1
      }
    ];
    console.log(`✅ Using ${mockLetters.length} mock dispute letters`);
    
    // Test 4: Generate complete packet
    console.log('\n🔄 Test 4: Generating complete packet...');
    const mockProgress = (progress) => {
      console.log(`  📊 ${progress.step} (${progress.progress}%): ${progress.message}`);
    };
    
    const completePacket = await generateCompletePacket(
      mockLetters,
      documentBlobs,
      mockProgress
    );
    
    console.log(`✅ Complete packet generated: ${completePacket.size} bytes`);
    
    // Test 5: Test download
    console.log('\n⬇️ Test 5: Testing download...');
    const url = URL.createObjectURL(completePacket);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test-complete-packet-${Date.now()}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log('✅ Download triggered successfully');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Test utility functions
async function testUtilityFunctions() {
  try {
    console.log('\n🔧 Testing utility functions...');
    
    const { getDocumentTitle, hasRequiredDocuments, getMissingDocuments } = await import('./src/utils/documentPacketUtils.js');
    
    // Test document title function
    console.log('✅ Document titles:');
    console.log('  photo_id:', getDocumentTitle('photo_id'));
    console.log('  ssn_card:', getDocumentTitle('ssn_card'));
    console.log('  utility_bill:', getDocumentTitle('utility_bill'));
    
    // Test document validation
    const testDocs = [
      { document_type: 'photo_id' },
      { document_type: 'ssn_card' }
    ];
    
    console.log(`✅ Has required documents: ${hasRequiredDocuments(testDocs)}`);
    console.log(`✅ Missing documents: ${getMissingDocuments(testDocs).join(', ')}`);
    
  } catch (error) {
    console.error('❌ Utility test failed:', error);
  }
}

// Run tests
console.log('🚀 Starting tests...\n');
testUtilityFunctions();
testCompletePacket();

console.log('\n🏁 Tests completed. Check results above and download folder for PDF.');