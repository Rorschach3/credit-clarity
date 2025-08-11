#!/bin/bash

# Job monitoring script
JOB_ID="8c9cdd2b-edf0-4199-bf2b-e022bd5c0004"
API_URL="http://localhost:8000/api/job"

echo "🔍 Monitoring job: $JOB_ID"
echo "⏰ Started at: $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while true; do
    # Get job status
    RESPONSE=$(curl -s "$API_URL/$JOB_ID")
    
    # Parse JSON response
    STATUS=$(echo "$RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    PROGRESS=$(echo "$RESPONSE" | grep -o '"progress":[0-9]*' | cut -d':' -f2)
    MESSAGE=$(echo "$RESPONSE" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
    
    # Display current status
    TIMESTAMP=$(date "+%H:%M:%S")
    printf "[$TIMESTAMP] Status: %-10s Progress: %3s%% | %s\n" "$STATUS" "$PROGRESS" "$MESSAGE"
    
    # Check if job is complete
    if [[ "$STATUS" == "completed" ]]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ Job completed successfully!"
        
        # Show final results
        TRADELINES_FOUND=$(echo "$RESPONSE" | grep -o '"tradelines_found":[0-9]*' | cut -d':' -f2)
        PROCESSING_TIME=$(echo "$RESPONSE" | grep -o '"processing_time":[0-9.]*' | cut -d':' -f2)
        
        echo "📊 Results:"
        echo "   • Tradelines found: $TRADELINES_FOUND"
        echo "   • Processing time: ${PROCESSING_TIME}s"
        echo "⏰ Completed at: $(date)"
        break
        
    elif [[ "$STATUS" == "failed" ]]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "❌ Job failed!"
        
        ERROR=$(echo "$RESPONSE" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
        echo "💥 Error: $ERROR"
        break
        
    elif [[ "$STATUS" == "cancelled" ]]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🚫 Job was cancelled"
        break
    fi
    
    # Wait 5 seconds before next check
    sleep 5
done

echo "🏁 Monitoring finished"