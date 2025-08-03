#!/bin/bash
# export-vercel-env.sh

ENVIRONMENT="production"
ENV_FILE=".env.production"

echo "🚀 Bulk importing environment variables to Vercel ($ENVIRONMENT)..."

# Use vercel env pull to get current vars, then push the new ones
vercel env ls

echo "Adding variables from $ENV_FILE..."
while IFS='=' read -r key value || [[ -n "$key" ]]; do
  # Skip comments and empty lines
  [[ "$key" =~ ^[[:space:]]*# || -z "$key" ]] && continue
  
  # Clean up key and value
  key=$(echo "$key" | xargs)
  value=$(echo "$value" | xargs | sed 's/^"//; s/"$//')
  
  echo "Setting $key..."
  printf "%s" "$value" | vercel env add "$key" "$ENVIRONMENT" --force
  
done < "$ENV_FILE"

echo "✅ Environment variables added to Vercel!"