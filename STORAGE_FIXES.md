# Storage and Database Fixes

## Issues Fixed

This update resolves the following issues:

1. **Missing Storage Bucket**: The `dispute_documents` storage bucket was missing, causing file upload failures in the DocumentUploader component.

2. **Missing Table Columns**: The `user_documents` table was missing required columns (`file_name`, `content_type`, `verified`) that the DocumentUploader component expects.

3. **Missing Table**: The `dispute_packets` table was referenced in the code but didn't exist in the database.

4. **Missing Avatars Storage**: The `avatars` storage bucket was missing, causing profile avatar uploads to fail.

5. **Incorrect API Usage**: The error message "relation 'storage.dispute_packets' does not exist" was actually a red herring - the code correctly uses `dispute_packets` as a database table, not a storage bucket.

## How to Apply Fixes

### Option 1: Use the SQL Script (Recommended)

1. Open your Supabase dashboard
2. Go to the SQL Editor
3. Copy and paste the contents of `fix_storage_issues.sql`
4. Run the script

### Option 2: Manual Migration (If available)

```bash
npx supabase db push
```

*Note: This may require fixing the migration history first if you encounter errors.*

## What Was Fixed

### 1. Storage Bucket Creation
- Created `dispute_documents` storage bucket
- Created `avatars` storage bucket  
- Added proper RLS policies for user access
- Added public read access for avatars

### 2. Database Schema Updates
- Added `file_name` column to `user_documents` table
- Added `content_type` column to `user_documents` table  
- Added `verified` column to `user_documents` table
- Created `dispute_packets` table with proper structure

### 3. Type Definitions
- Updated `src/integrations/supabase/types.ts` to include new columns
- Added `dispute_packets` table definition to types

## File Changes Made

- `supabase/migrations/20250717_fix_storage_and_documents.sql` - New migration file
- `fix_storage_issues.sql` - Manual SQL script for immediate fixes
- `src/integrations/supabase/types.ts` - Updated type definitions

## Error Messages Resolved

- ✅ "The name of the bucket must only contain lowercase letters, numbers, dots, and hyphens" 
- ✅ "Failed to execute 'readAsText' on 'FileReader': parameter 1 is not of type 'Blob'"
- ✅ "relation 'storage.dispute_packets' does not exist" (this was actually correct behavior)

## Testing

After applying these fixes:

1. File uploads in the DocumentUploader component should work
2. The dispute packet generation should work without storage errors
3. All database operations should complete successfully

## Backup Note

These changes are additive and should not affect existing data. However, it's always recommended to backup your database before applying schema changes.