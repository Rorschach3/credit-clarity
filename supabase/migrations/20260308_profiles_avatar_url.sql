-- Add avatar_url column to profiles if it doesn't exist
alter table public.profiles
  add column if not exists avatar_url text;
