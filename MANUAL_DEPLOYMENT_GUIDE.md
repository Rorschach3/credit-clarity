# Manual Deployment Guide for Edge Function

If the automated deployment script doesn't work, follow these manual steps:

## 📋 Prerequisites

1. **Supabase CLI** - Make sure you can run `npx supabase --version`
2. **Supabase Project** - Ensure you're connected to your Supabase project
3. **Google Cloud Account** - With Document AI API enabled

## 🚀 Step-by-Step Deployment

### Step 1: Initialize Supabase (if not already done)
```bash
cd frontend
npx supabase init
```

### Step 2: Login to Supabase
```bash
npx supabase login
```

### Step 3: Link to your project
```bash
npx supabase link --project-ref YOUR_PROJECT_REF
```

### Step 4: Deploy the Edge Function
```bash
npx supabase functions deploy process-credit-report
```

### Step 5: Apply Database Migrations
```bash
npx supabase db push
```

### Step 6: Set Environment Variables

Go to your Supabase Dashboard → Edge Functions → process-credit-report → Settings

Add these environment variables:

```
GOOGLE_CLOUD_PROJECT_ID=your_gcp_project_id
GOOGLE_CLOUD_LOCATION=us
DOCUMENT_AI_PROCESSOR_ID=your_processor_id
GOOGLE_APPLICATION_CREDENTIALS_JSON={
  "type": "service_account",
  "project_id": "your_project",
  "private_key_id": "key_id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "service-account@project.iam.gserviceaccount.com",
  "client_id": "client_id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/service-account%40project.iam.gserviceaccount.com"
}
```

## 🧪 Testing the Deployment

### Test 1: Check Edge Function Status
```bash
npx supabase functions list
```

### Test 2: Manual Function Invoke (Optional)
```bash
npx supabase functions invoke process-credit-report --data '{
  "record": {
    "bucket": "credit-reports",
    "name": "test-file.pdf",
    "metadata": {
      "user_id": "test-user-id"
    }
  }
}'
```

### Test 3: Frontend Integration Test
1. Go to your credit report upload page
2. Select "Edge Function (Document AI)" processing method
3. Upload a PDF file
4. Check browser console for logs
5. Verify tradelines appear in the UI

## 🔧 Common Issues and Solutions

### Issue 1: "Command not found" for npx supabase
**Solution:** Install Node.js and npm, then try again

### Issue 2: "Project not linked"
**Solution:** Run `npx supabase link --project-ref YOUR_PROJECT_REF`

### Issue 3: "Permission denied" for Google Cloud
**Solution:** Verify your service account has Document AI permissions

### Issue 4: "Storage bucket not found"
**Solution:** Run the database migration to create the bucket:
```bash
npx supabase db push
```

### Issue 5: Edge Function times out
**Solution:** Check Google Cloud credentials and Document AI processor ID

## 📊 Verification Checklist

- [ ] Edge Function deployed successfully
- [ ] Database migrations applied
- [ ] Environment variables set in Supabase Dashboard
- [ ] Storage bucket `credit-reports` exists
- [ ] Frontend shows "Edge Function (Document AI)" option
- [ ] File upload works and shows progress
- [ ] Tradelines are extracted and displayed
- [ ] Database contains new credit_reports and tradelines records

## 🆘 Troubleshooting Commands

```bash
# Check Supabase status
npx supabase status

# View function logs
npx supabase functions logs process-credit-report

# Reset database (USE WITH CAUTION)
npx supabase db reset

# Check storage buckets
npx supabase storage list
```

## 📞 Support

If you encounter issues:

1. Check the browser console for JavaScript errors
2. Check Supabase Dashboard → Edge Functions → Logs
3. Verify all environment variables are set correctly
4. Test with a small, simple PDF file first

The Edge Function integration should work seamlessly with your existing Credit Clarity application once properly deployed!