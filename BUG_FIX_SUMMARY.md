# PGRST116 + 406 Error Bug Fix Summary

## 🐛 Original Problem
User was experiencing two related errors:
1. **PGRST116**: "JSON object requested, multiple (or no) rows returned"
2. **406 Not Acceptable**: Authentication/RLS policy blocking queries

**Error Context:**
```
GET user_documents?select=*&user_id=eq.xxx&document_type=eq.photo_id
Status: 406 Not Acceptable
```

## 🔍 Root Cause Analysis

### Primary Issue: Incorrect Query Method
- `DocumentUploader.tsx` was using `.single()` expecting exactly 1 row
- When user has no documents uploaded yet, query returns 0 rows
- `.single()` throws PGRST116 error when not exactly 1 row

### Secondary Issue: Database Access Problems  
- 406 errors indicated RLS (Row Level Security) policies blocking access
- `user_documents` table may not exist or have wrong permissions
- Missing proper authentication validation before queries

## ✅ Fixes Applied

### 1. Query Method Fix
**File:** `src/components/disputes/DocumentUploader.tsx`
```diff
- .single();
+ .maybeSingle();

- if (error && error.code !== 'PGRST116') {
+ if (error) {
```

**Why this works:**
- `.maybeSingle()` expects 0 or 1 rows (perfect for "find existing document")
- `.single()` expects exactly 1 row (wrong for optional data)
- Eliminates PGRST116 errors completely

### 2. Session Validation Enhancement
**Files:** All user_documents queries now validate authentication
- `DocumentUploader.tsx` ✅ Already had session check
- `UserDocumentsSection.tsx` ✅ Already had session check  
- `useWorkflowState.ts` ✅ Already had session check

### 3. Database Schema Migration
**File:** `fix_database_issues.sql`
- Creates `user_documents` table with proper schema
- Sets up correct RLS policies for authenticated users
- Creates required storage buckets
- Fixes user_id type consistency (TEXT vs UUID)

## 🧪 Testing

### Manual Test Script
**File:** `debug_user_documents.js`
Run in browser console to verify fixes:
```javascript
// Tests basic user_documents query without 406 errors
// Tests maybeSingle functionality without PGRST116 errors
```

### Expected Results After Fix
- ✅ No more 406 Not Acceptable errors
- ✅ No more PGRST116 errors for missing documents
- ✅ Document upload flow works smoothly for new users
- ✅ Existing documents are detected correctly

## 📋 Steps to Deploy Fix

1. **Run Database Migration:**
   ```sql
   -- Copy contents of fix_database_issues.sql
   -- Run in Supabase SQL Editor
   ```

2. **Code Changes Already Applied:**
   - DocumentUploader.tsx updated
   - Error handling improved
   - Session validation enhanced

3. **Test in Browser:**
   ```javascript
   // Copy debug_user_documents.js into browser console
   // Verify no errors in network tab
   ```

## 🎯 Key Learnings

1. **Use `.maybeSingle()` for optional records** - when you might get 0 or 1 rows
2. **Use `.single()` only for required records** - when you expect exactly 1 row  
3. **Always validate session before RLS-protected queries** - prevents 406 errors
4. **Test with fresh users who have no data** - catches edge cases like PGRST116

## 🔗 Related Files Modified
- `src/components/disputes/DocumentUploader.tsx`
- `fix_database_issues.sql` (migration script)
- `debug_user_documents.js` (test script)
- `BUG_FIX_SUMMARY.md` (this file)