#!/bin/bash

# Deploy Credit Report Processing Edge Function
echo "🚀 Deploying Credit Report Processing Edge Function..."

# Change to the correct directory
cd frontend

# Deploy the Edge Function
echo "📦 Deploying process-credit-report function..."
npx supabase functions deploy process-credit-report

# Check deployment status
if [ $? -eq 0 ]; then
    echo "✅ Edge Function deployed successfully!"
    
    # Set required environment variables (you'll need to update these)
    echo "🔧 Setting environment variables..."
    echo "Note: You need to set these in your Supabase dashboard:"
    echo "  - GOOGLE_CLOUD_PROJECT_ID"
    echo "  - GOOGLE_CLOUD_LOCATION"
    echo "  - DOCUMENT_AI_PROCESSOR_ID"
    echo "  - GOOGLE_APPLICATION_CREDENTIALS_JSON"
    
    # Run database migrations
    echo "🗄️ Running database migrations..."
    npx supabase db push
    
    if [ $? -eq 0 ]; then
        echo "✅ Database migrations completed successfully!"
        echo ""
        echo "🎉 Deployment complete! Your Edge Function is ready to use."
        echo ""
        echo "Next steps:"
        echo "1. Set up Google Cloud Document AI credentials in Supabase Dashboard"
        echo "2. Configure storage triggers (optional - function can be triggered manually)"
        echo "3. Test the integration using the frontend upload form"
        echo ""
        echo "📚 Documentation: frontend/supabase/functions/process-credit-report/README.md"
    else
        echo "❌ Database migration failed. Please check the error messages above."
        exit 1
    fi
else
    echo "❌ Edge Function deployment failed. Please check the error messages above."
    exit 1
fi