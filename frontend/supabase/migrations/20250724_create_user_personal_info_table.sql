-- Create user_personal_info table for storing user personal details

CREATE TABLE IF NOT EXISTS public.user_personal_info (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  first_name TEXT,
  last_name TEXT,
  address1 TEXT,
  address2 TEXT,
  city TEXT,
  state TEXT,
  zip_code TEXT,
  phone_number TEXT,
  dob DATE,
  ssn_last_four TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.user_personal_info ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own personal info
CREATE POLICY "Users can view their own personal info"
  ON public.user_personal_info
  FOR SELECT
  USING (auth.uid() = user_id);

-- Policy: Users can insert their own personal info
CREATE POLICY "Users can insert their own personal info"
  ON public.user_personal_info
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own personal info
CREATE POLICY "Users can update their own personal info"
  ON public.user_personal_info
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Trigger to update updated_at on row update
CREATE OR REPLACE FUNCTION update_user_personal_info_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_user_personal_info_updated_at ON public.user_personal_info;

CREATE TRIGGER set_user_personal_info_updated_at
  BEFORE UPDATE ON public.user_personal_info
  FOR EACH ROW
  EXECUTE FUNCTION update_user_personal_info_updated_at();