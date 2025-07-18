-- Combined migration script to fix database schema issues
-- This fixes the missing filename column and RLS policy issues

-- 1. Create dispute_packets storage bucket (from 20250717_create_dispute_packets_bucket.sql)
INSERT INTO storage.buckets (id, name, public) 
VALUES ('dispute_packets', 'dispute_packets', false)
ON CONFLICT (id) DO NOTHING;

-- Create storage policies for dispute_packets bucket
CREATE POLICY "Users can upload their own dispute packets" 
  ON storage.objects 
  FOR INSERT 
  TO authenticated 
  WITH CHECK (bucket_id = 'dispute_packets' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view their own dispute packets" 
  ON storage.objects 
  FOR SELECT 
  TO authenticated 
  USING (bucket_id = 'dispute_packets' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can update their own dispute packets" 
  ON storage.objects 
  FOR UPDATE 
  TO authenticated 
  USING (bucket_id = 'dispute_packets' AND auth.uid()::text = (storage.foldername(name))[1])
  WITH CHECK (bucket_id = 'dispute_packets' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can delete their own dispute packets" 
  ON storage.objects 
  FOR DELETE 
  TO authenticated 
  USING (bucket_id = 'dispute_packets' AND auth.uid()::text = (storage.foldername(name))[1]);

-- 2. Fix storage buckets and user_documents table (from 20250717_fix_storage_and_documents.sql)
-- Create the missing dispute_documents storage bucket
INSERT INTO storage.buckets (id, name, public) 
VALUES ('dispute_documents', 'dispute_documents', false)
ON CONFLICT (id) DO NOTHING;

-- Add missing columns to user_documents table
ALTER TABLE public.user_documents 
ADD COLUMN IF NOT EXISTS file_name TEXT,
ADD COLUMN IF NOT EXISTS content_type TEXT,
ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT false;

-- Create storage policies for dispute_documents bucket
CREATE POLICY "Users can manage their own dispute documents" 
  ON storage.objects 
  FOR ALL 
  TO authenticated 
  USING (bucket_id = 'dispute_documents' AND auth.uid()::text = (storage.foldername(name))[1])
  WITH CHECK (bucket_id = 'dispute_documents' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Create dispute_packets table if it doesn't exist (for the DisputeWizardPage)
CREATE TABLE IF NOT EXISTS public.dispute_packets (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  document_urls JSONB DEFAULT '[]'::jsonb,
  dispute_letter_url TEXT,
  packet_status TEXT DEFAULT 'draft',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS on dispute_packets
ALTER TABLE public.dispute_packets ENABLE ROW LEVEL SECURITY;

-- Create policies for dispute_packets (drop existing first to avoid conflicts)
DROP POLICY IF EXISTS "Users can view their own dispute packets" ON public.dispute_packets;
DROP POLICY IF EXISTS "Users can insert their own dispute packets" ON public.dispute_packets;
DROP POLICY IF EXISTS "Users can update their own dispute packets" ON public.dispute_packets;

CREATE POLICY "Users can view their own dispute packets" 
  ON public.dispute_packets 
  FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own dispute packets" 
  ON public.dispute_packets 
  FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own dispute packets" 
  ON public.dispute_packets 
  FOR UPDATE 
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Update user_documents policies to be more permissive if needed
DROP POLICY IF EXISTS "Users can view their own documents" ON public.user_documents;
DROP POLICY IF EXISTS "Users can insert their own documents" ON public.user_documents;
DROP POLICY IF EXISTS "Users can update their own documents" ON public.user_documents;
DROP POLICY IF EXISTS "Users can delete their own documents" ON public.user_documents;
DROP POLICY IF EXISTS "Users can manage their own documents" ON public.user_documents;

CREATE POLICY "Users can manage their own documents" 
  ON public.user_documents 
  FOR ALL 
  USING (auth.uid()::text = user_id)
  WITH CHECK (auth.uid()::text = user_id);

-- 3. Add missing columns to dispute_packets table (from 20250717_update_dispute_packets_table.sql)
ALTER TABLE public.dispute_packets 
ADD COLUMN IF NOT EXISTS filename TEXT,
ADD COLUMN IF NOT EXISTS bureau_count INTEGER,
ADD COLUMN IF NOT EXISTS tradeline_count INTEGER,
ADD COLUMN IF NOT EXISTS letters_data JSONB;

-- Refresh schema cache by updating table comment
COMMENT ON TABLE public.dispute_packets IS 'Updated schema cache refresh';
COMMENT ON TABLE public.user_documents IS 'Updated schema cache refresh';