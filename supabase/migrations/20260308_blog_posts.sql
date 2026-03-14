-- Blog posts table for dynamic content management
create table if not exists public.blog_posts (
  id          uuid primary key default gen_random_uuid(),
  title       text not null,
  slug        text not null unique,
  excerpt     text,
  content     text not null,
  published   boolean not null default false,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Index for fast slug lookups and published feed
create index if not exists blog_posts_slug_idx on public.blog_posts (slug);
create index if not exists blog_posts_published_created_idx on public.blog_posts (published, created_at desc);

-- Row-level security
alter table public.blog_posts enable row level security;

-- Anyone can read published posts
create policy "Public can read published posts"
  on public.blog_posts for select
  using (published = true);

-- Seed with placeholder posts so the page renders immediately
insert into public.blog_posts (title, slug, excerpt, content, published) values
(
  'How to Dispute Errors on Your Credit Report',
  'how-to-dispute-credit-report-errors',
  'Learn the step-by-step process for disputing inaccurate information on your credit report and protecting your financial future.',
  'Errors on your credit report can drag down your score and cost you money in higher interest rates. Under the Fair Credit Reporting Act (FCRA), you have the right to dispute any information you believe is inaccurate. Here''s how to get started...',
  true
),
(
  'Understanding the Three Major Credit Bureaus',
  'understanding-three-major-credit-bureaus',
  'Experian, TransUnion, and Equifax each maintain separate files on you. Here''s what you need to know about each one.',
  'Most people don''t realize that each of the three major credit bureaus — Experian, TransUnion, and Equifax — operates independently. That means an error at one bureau won''t automatically appear at the others, but a negative item reported by a creditor often shows up at all three...',
  true
),
(
  '5 Factors That Affect Your Credit Score',
  '5-factors-that-affect-credit-score',
  'Your credit score is calculated from five key factors. Understanding each one is the first step toward improving your score.',
  'Your FICO® score, used by 90% of top lenders, is calculated using five weighted factors: payment history (35%), amounts owed (30%), length of credit history (15%), new credit (10%), and credit mix (10%). Let''s break down each one...',
  true
)
on conflict (slug) do nothing;
