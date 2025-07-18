-- Add missing columns to dispute_packets table
ALTER TABLE public.dispute_packets 
ADD COLUMN IF NOT EXISTS filename TEXT,
ADD COLUMN IF NOT EXISTS bureau_count INTEGER,
ADD COLUMN IF NOT EXISTS tradeline_count INTEGER,
ADD COLUMN IF NOT EXISTS letters_data JSONB;