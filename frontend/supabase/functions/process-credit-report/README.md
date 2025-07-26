# Process Credit Report Edge Function

This Supabase Edge Function automatically processes uploaded credit report files using Google Document AI and extracts tradeline data into your existing `tradelines` table.

## Features

- **Storage Trigger**: Automatically triggered when files are uploaded to Supabase Storage
- **Document AI Integration**: Uses Google Cloud Document AI to extract structured data from PDFs
- **Tradeline Extraction**: Parses credit report entities and extracts tradeline information
- **Database Integration**: Inserts data into existing `credit_reports` and `tradelines` tables
- **Error Handling**: Comprehensive logging and error handling throughout the process

## Setup

### 1. Environment Variables

Set the following environment variables in your Supabase dashboard:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your_gcp_project_id
GOOGLE_CLOUD_LOCATION=us  # or your preferred location
DOCUMENT_AI_PROCESSOR_ID=your_document_ai_processor_id
GOOGLE_APPLICATION_CREDENTIALS_JSON='{
  "type": "service_account",
  "project_id": "your_project_id",
  "private_key_id": "your_private_key_id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "your_service_account@your_project.iam.gserviceaccount.com",
  "client_id": "your_client_id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}'
```

### 2. Google Cloud Setup

1. **Create a Document AI Processor**:
   - Go to Google Cloud Console → Document AI
   - Create a new processor (choose "Form Parser" or "Document OCR")
   - Note the Processor ID

2. **Service Account Setup**:
   - Create a service account with Document AI permissions
   - Download the JSON credentials
   - Set the JSON content as `GOOGLE_APPLICATION_CREDENTIALS_JSON`

### 3. Storage Bucket Configuration

Configure your storage bucket to trigger this function:

1. In Supabase Dashboard → Storage
2. Create a bucket for credit reports (e.g., 'credit-reports')
3. Set up storage triggers to call this function on file uploads

### 4. Deploy the Function

```bash
supabase functions deploy process-credit-report
```

## Usage

### File Upload with Metadata

When uploading files to trigger this function, include the user ID in metadata:

```javascript
const { data, error } = await supabase.storage
  .from('credit-reports')
  .upload(`reports/${fileName}`, file, {
    metadata: {
      user_id: currentUser.id
    }
  });
```

### Storage Event Trigger

Set up a storage trigger in your Supabase dashboard:

```sql
-- Example trigger setup (adjust table names as needed)
CREATE OR REPLACE FUNCTION handle_storage_upload()
RETURNS TRIGGER AS $$
BEGIN
  -- Call the edge function
  PERFORM net.http_post(
    url := 'https://your-project.supabase.co/functions/v1/process-credit-report',
    headers := jsonb_build_object('Content-Type', 'application/json'),
    body := jsonb_build_object('record', to_jsonb(NEW))
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_credit_report_upload
  AFTER INSERT ON storage.objects
  FOR EACH ROW
  WHEN (NEW.bucket_id = 'credit-reports')
  EXECUTE FUNCTION handle_storage_upload();
```

## Data Flow

1. **File Upload**: User uploads PDF to Supabase Storage with metadata
2. **Trigger**: Storage event triggers the Edge Function
3. **Download**: Function downloads the file from storage
4. **Document AI**: File is processed using Google Document AI
5. **Parse**: AI response is parsed to extract tradeline entities
6. **Database**: 
   - Creates a new record in `credit_reports` table
   - Inserts extracted tradelines into `tradelines` table
7. **Response**: Returns processing results

## Database Schema

### credit_reports Table
```sql
CREATE TABLE credit_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users,
  report_date TIMESTAMP WITH TIME ZONE DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### tradelines Table (existing)
Uses your existing `tradelines` table with fields:
- `user_id`, `creditor_name`, `account_number`, `account_balance`
- `credit_limit`, `monthly_payment`, `date_opened`
- `account_type`, `account_status`, `credit_bureau`
- `is_negative`, `dispute_count`, etc.

## Error Handling

The function includes comprehensive error handling for:
- Missing environment variables
- File download failures
- Document AI API errors
- Database insertion errors
- JWT authentication issues

All errors are logged with descriptive messages for debugging.

## Monitoring

Monitor function execution in:
- Supabase Dashboard → Edge Functions → Logs
- Google Cloud Console → Document AI → Usage metrics

## Security

- Uses Supabase Service Role Key for database operations
- Google Cloud authentication via proper JWT signing
- File access restricted to authorized storage buckets
- User ID validation from file metadata