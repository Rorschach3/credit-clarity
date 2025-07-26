import { supabase } from '../../supabase/client';

async function testRLS() {
  // Get the authenticated user's ID
  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user) {
    console.error('Failed to get authenticated user:', userError);
    return;
  }

  const userId = user.id;

  console.log('Authenticated user ID:', userId);

  // Attempt to insert a credit report with matching user_id
  const { data: insertData, error: insertError } = await supabase
    .from('credit_reports')
    .insert([{
      user_id: userId,
      file_path: 'test/path',
      file_name: 'testfile.pdf',
      upload_date: new Date().toISOString(),
      status: 'pending',
      analysis_summary: null,
      error_message: null
    }]);

  if (insertError) {
    console.error('Insert with matching user_id failed:', insertError);
  } else {
    console.log('Insert with matching user_id succeeded:', insertData);
  }

  // Attempt to insert a credit report with non-matching user_id
  const fakeUserId = '00000000-0000-0000-0000-000000000000';
  const { data: insertDataFail, error: insertErrorFail } = await supabase
    .from('credit_reports')
    .insert([{
      user_id: fakeUserId,
      file_path: 'test/path',
      file_name: 'testfile.pdf',
      upload_date: new Date().toISOString(),
      status: 'pending',
      analysis_summary: null,
      error_message: null
    }]);

  if (insertErrorFail) {
    console.log('Insert with non-matching user_id correctly failed:', insertErrorFail.message);
  } else {
    console.error('Insert with non-matching user_id unexpectedly succeeded:', insertDataFail);
  }
}

testRLS();