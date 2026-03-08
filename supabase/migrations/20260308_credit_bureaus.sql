-- Credit bureaus reference table (replaces hardcoded addresses in frontend)
create table if not exists public.credit_bureaus (
  id         uuid primary key default gen_random_uuid(),
  name       text not null unique check (name in ('Experian', 'TransUnion', 'Equifax')),
  address    text not null
);

-- Row-level security (read-only for all authenticated users)
alter table public.credit_bureaus enable row level security;

create policy "Authenticated users can read credit bureaus"
  on public.credit_bureaus for select
  to authenticated
  using (true);

-- Seed with official dispute mailing addresses
insert into public.credit_bureaus (name, address) values
(
  'Experian',
  E'Experian\nP.O. Box 4500\nAllen, TX 75013'
),
(
  'TransUnion',
  E'TransUnion LLC\nConsumer Dispute Center\nP.O. Box 2000\nChester, PA 19016'
),
(
  'Equifax',
  E'Equifax Information Services LLC\nP.O. Box 740256\nAtlanta, GA 30374'
)
on conflict (name) do update
  set address = excluded.address;
