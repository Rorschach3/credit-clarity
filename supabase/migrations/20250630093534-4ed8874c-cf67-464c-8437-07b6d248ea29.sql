
-- Create the user_roles enum (handle if exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'app_role') THEN
        CREATE TYPE public.app_role AS ENUM ('admin', 'moderator', 'user');
    END IF;
END $$;

-- Create user_roles table
CREATE TABLE IF NOT EXISTS public.user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  role app_role NOT NULL,
  email TEXT NOT NULL,
  assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE (user_id, role)
);

-- Enable RLS on user_roles
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

-- Create security definer function to check roles
CREATE OR REPLACE FUNCTION public.has_role(_user_id uuid, _role app_role)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.user_roles
    WHERE user_id = _user_id
      AND role = _role
  )
$$;

-- Add missing columns to profiles table for personal information
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS last_name TEXT,
ADD COLUMN IF NOT EXISTS address1 TEXT,
ADD COLUMN IF NOT EXISTS city TEXT,
ADD COLUMN IF NOT EXISTS state TEXT,
ADD COLUMN IF NOT EXISTS zip_code TEXT,
ADD COLUMN IF NOT EXISTS phone_number TEXT,
ADD COLUMN IF NOT EXISTS ssn_last_four TEXT;

-- Create audit_history table for admin functionality
CREATE TABLE IF NOT EXISTS public.audit_history (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  table_name TEXT NOT NULL,
  record_id UUID NOT NULL,
  operation TEXT NOT NULL,
  old_values JSONB,
  new_values JSONB,
  performed_by UUID REFERENCES auth.users,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS on audit_history
ALTER TABLE public.audit_history ENABLE ROW LEVEL SECURITY;

-- Create policy for audit_history (admin only)
CREATE POLICY "Only admins can view audit history" 
  ON public.audit_history 
  FOR ALL
  USING (public.has_role(auth.uid(), 'admin'));

-- Create credit_reports storage bucket
INSERT INTO storage.buckets (id, name, public) 
VALUES ('credit_reports', 'credit_reports', false)
ON CONFLICT (id) DO NOTHING;

-- Create credit_reports table
CREATE TABLE IF NOT EXISTS public.credit_reports (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users,
  encrypted_content TEXT,
  encryption_key_id TEXT,
  report_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS on credit_reports
ALTER TABLE public.credit_reports ENABLE ROW LEVEL SECURITY;

-- Create policies for credit_reports
CREATE POLICY "Users can view their own credit reports" 
  ON public.credit_reports 
  FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own credit reports" 
  ON public.credit_reports 
  FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

-- Create storage policy for credit_reports bucket
CREATE POLICY "Users can upload their own credit reports" 
  ON storage.objects 
  FOR INSERT 
  WITH CHECK (bucket_id = 'credit_reports' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view their own credit reports in storage" 
  ON storage.objects 
  FOR SELECT 
  USING (bucket_id = 'credit_reports' AND auth.uid()::text = (storage.foldername(name))[1]);
