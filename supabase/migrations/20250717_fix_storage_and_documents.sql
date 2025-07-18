-- Fix storage buckets and user_documents table columns
-- This migration addresses the missing dispute_documents bucket and missing columns

-- 1. Create the missing dispute_documents storage bucket
INSERT INTO storage.buckets (id, name, public) 
VALUES ('dispute_documents', 'dispute_documents', false)
ON CONFLICT (id) DO NOTHING;

-- 2. Add missing columns to user_documents table
ALTER TABLE public.user_documents 
ADD COLUMN IF NOT EXISTS file_name TEXT,
ADD COLUMN IF NOT EXISTS content_type TEXT,
ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT false;

-- 3. Create storage policies for dispute_documents bucket
CREATE POLICY "Users can manage their own dispute documents" 
  ON storage.objects 
  FOR ALL 
  TO authenticated 
  USING (bucket_id = 'dispute_documents' AND auth.uid()::text = (storage.foldername(name))[1])
  WITH CHECK (bucket_id = 'dispute_documents' AND auth.uid()::text = (storage.foldername(name))[1]);

-- 4. Create dispute_packets table if it doesn't exist (for the DisputeWizardPage)
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

-- Create policies for dispute_packets
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

-- 5. Update user_documents policies to be more permissive if needed
DROP POLICY IF EXISTS "Users can view their own documents" ON public.user_documents;
DROP POLICY IF EXISTS "Users can insert their own documents" ON public.user_documents;
DROP POLICY IF EXISTS "Users can update their own documents" ON public.user_documents;
DROP POLICY IF EXISTS "Users can delete their own documents" ON public.user_documents;

CREATE POLICY "Users can manage their own documents" 
  ON public.user_documents 
  FOR ALL 
  USING (auth.uid()::text = user_id)
  WITH CHECK (auth.uid()::text = user_id);