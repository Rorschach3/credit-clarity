-- Extend disputes table with letter-tracking fields
alter table public.disputes
  add column if not exists creditor_name         text,
  add column if not exists account_number_masked text,
  add column if not exists bureau               text check (bureau in ('Experian', 'TransUnion', 'Equifax')),
  add column if not exists dispute_reason       text,
  add column if not exists letter_text          text;
