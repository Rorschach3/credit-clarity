-- User documents table for identity verification uploads (photo ID, SSN card, utility bill)
CREATE TABLE IF NOT EXISTS public.user_documents (
  id            uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  document_type text NOT NULL CHECK (document_type IN ('photo_id', 'ssn_card', 'utility_bill')),
  file_path     text NOT NULL,
  file_name     text NOT NULL,
  content_type  text,
  verified      boolean DEFAULT false,
  created_at    timestamptz DEFAULT now(),
  updated_at    timestamptz DEFAULT now(),
  UNIQUE (user_id, document_type)
);

-- Index for fast user lookups
CREATE INDEX IF NOT EXISTS idx_user_documents_user_id ON public.user_documents (user_id);

-- RLS
ALTER TABLE public.user_documents ENABLE ROW LEVEL SECURITY;

-- Users can read their own documents
CREATE POLICY "Users can view own documents"
  ON public.user_documents FOR SELECT
  USING (auth.uid() = user_id);

-- Users can insert their own documents
CREATE POLICY "Users can insert own documents"
  ON public.user_documents FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can update their own documents
CREATE POLICY "Users can update own documents"
  ON public.user_documents FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Users can delete their own documents
CREATE POLICY "Users can delete own documents"
  ON public.user_documents FOR DELETE
  USING (auth.uid() = user_id);
