-- Run this SQL directly in your Supabase SQL Editor
-- Creates the storage bucket and policies for credit report processing

-- Create storage bucket for credit reports if it doesn't exist
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'credit-reports',
  'credit-reports',
  false,
  10485760, -- 10MB limit
  ARRAY['application/pdf']
)
ON CONFLICT (id) DO NOTHING;

-- Create storage policy for authenticated users to upload their own files
DROP POLICY IF EXISTS "Users can upload their own credit reports" ON storage.objects;
CREATE POLICY "Users can upload their own credit reports" ON storage.objects
FOR INSERT WITH CHECK (
  bucket_id = 'credit-reports' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Create policy for users to read their own files
DROP POLICY IF EXISTS "Users can read their own credit reports" ON storage.objects;
CREATE POLICY "Users can read their own credit reports" ON storage.objects
FOR SELECT USING (
  bucket_id = 'credit-reports' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Create policy for users to delete their own files
DROP POLICY IF EXISTS "Users can delete their own credit reports" ON storage.objects;
CREATE POLICY "Users can delete their own credit reports" ON storage.objects
FOR DELETE USING (
  bucket_id = 'credit-reports' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Ensure the bucket has RLS enabled
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Add credit_report_id column to tradelines table if it doesn't exist
-- This links tradelines to the credit report they came from
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name='tradelines' AND column_name='credit_report_id'
  ) THEN
    ALTER TABLE public.tradelines 
    ADD COLUMN credit_report_id UUID REFERENCES public.credit_reports(id) ON DELETE CASCADE;
    
    -- Add index for better performance
    CREATE INDEX IF NOT EXISTS idx_tradelines_credit_report_id 
    ON public.tradelines(credit_report_id);
    
    RAISE NOTICE 'Added credit_report_id column to tradelines table';
  ELSE
    RAISE NOTICE 'credit_report_id column already exists in tradelines table';
  END IF;
END $$;