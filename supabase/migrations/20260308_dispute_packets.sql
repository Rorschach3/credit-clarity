-- Dispute packets table: stores the complete multi-bureau packet generated
-- by the Dispute Wizard (one record per generation run).
create table if not exists public.dispute_packets (
  id                  uuid primary key default gen_random_uuid(),
  user_id             uuid not null references auth.users(id) on delete cascade,
  filename            text not null,
  bureau_count        integer not null default 0,
  tradeline_count     integer not null default 0,
  letters_data        jsonb,
  dispute_letter_url  text,
  packet_status       text not null default 'generated'
    check (packet_status in ('generated', 'ready', 'sent', 'archived')),
  status              text not null default 'generated',
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create index if not exists dispute_packets_user_id_idx
  on public.dispute_packets (user_id, created_at desc);

alter table public.dispute_packets enable row level security;

create policy "Users manage own dispute packets"
  on public.dispute_packets
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
