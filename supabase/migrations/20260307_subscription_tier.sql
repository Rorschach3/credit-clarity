-- Migration: Add subscription_tier, CROA disclosure fields to profiles table

ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'premium'));

ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS croa_disclosure_accepted BOOLEAN DEFAULT false;

ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS croa_disclosure_timestamp TIMESTAMPTZ;
