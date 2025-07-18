-- Fix current database issues for dispute wizard
-- Run this script in Supabase SQL Editor

-- 1. Create user_documents table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.user_documents (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  document_type TEXT NOT NULL,
  file_name TEXT,
  file_path TEXT,
  content_type TEXT,
  verified BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS on user_documents
ALTER TABLE public.user_documents ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to recreate them
DROP POLICY IF EXISTS "Users can view their own documents" ON public.user_documents;
DROP POLICY IF EXISTS "Users can insert their own documents" ON public.user_documents;
DROP POLICY IF EXISTS "Users can update their own documents" ON public.user_documents;
DROP POLICY IF EXISTS "Users can delete their own documents" ON public.user_documents;
DROP POLICY IF EXISTS "Users can manage their own documents" ON public.user_documents;

-- Create proper RLS policies for user_documents
CREATE POLICY "Users can view their own documents" 
  ON public.user_documents 
  FOR SELECT 
  USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own documents" 
  ON public.user_documents 
  FOR INSERT 
  WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own documents" 
  ON public.user_documents 
  FOR UPDATE 
  USING (auth.uid()::text = user_id)
  WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own documents" 
  ON public.user_documents 
  FOR DELETE 
  USING (auth.uid()::text = user_id);

-- 2. Create dispute_packets table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.dispute_packets (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  filename TEXT,
  bureau_count INTEGER,
  tradeline_count INTEGER,
  letters_data JSONB,
  document_urls JSONB DEFAULT '[]'::jsonb,
  dispute_letter_url TEXT,
  packet_status TEXT DEFAULT 'draft',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS on dispute_packets
ALTER TABLE public.dispute_packets ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to recreate them
DROP POLICY IF EXISTS "Users can view their own dispute packets" ON public.dispute_packets;
DROP POLICY IF EXISTS "Users can insert their own dispute packets" ON public.dispute_packets;
DROP POLICY IF EXISTS "Users can update their own dispute packets" ON public.dispute_packets;
DROP POLICY IF EXISTS "Users can delete their own dispute packets" ON public.dispute_packets;

-- Create proper RLS policies for dispute_packets
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

CREATE POLICY "Users can delete their own dispute packets" 
  ON public.dispute_packets 
  FOR DELETE 
  USING (auth.uid() = user_id);

-- 3. Create storage buckets if they don't exist
INSERT INTO storage.buckets (id, name, public) 
VALUES ('user_documents', 'user_documents', false)
ON CONFLICT (id) DO NOTHING;

INSERT INTO storage.buckets (id, name, public) 
VALUES ('dispute_documents', 'dispute_documents', false)
ON CONFLICT (id) DO NOTHING;

INSERT INTO storage.buckets (id, name, public) 
VALUES ('dispute_packets', 'dispute_packets', false)
ON CONFLICT (id) DO NOTHING;

-- 4. Create storage policies
-- User documents bucket policies
CREATE POLICY "Users can upload their own user documents" 
  ON storage.objects 
  FOR INSERT 
  TO authenticated 
  WITH CHECK (bucket_id = 'user_documents' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view their own user documents" 
  ON storage.objects 
  FOR SELECT 
  TO authenticated 
  USING (bucket_id = 'user_documents' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can update their own user documents" 
  ON storage.objects 
  FOR UPDATE 
  TO authenticated 
  USING (bucket_id = 'user_documents' AND auth.uid()::text = (storage.foldername(name))[1])
  WITH CHECK (bucket_id = 'user_documents' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can delete their own user documents" 
  ON storage.objects 
  FOR DELETE 
  TO authenticated 
  USING (bucket_id = 'user_documents' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Dispute packets bucket policies
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

-- Refresh schema cache
COMMENT ON TABLE public.user_documents IS 'User uploaded documents for dispute process';
COMMENT ON TABLE public.dispute_packets IS 'Generated dispute packets for users';