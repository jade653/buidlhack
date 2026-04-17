-- Run this in Supabase SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.submissions (
  id uuid primary key default gen_random_uuid(),
  challenge_id text not null,
  submitter_id text not null,
  principal_type text not null check (principal_type in ('human', 'agent')),
  source text not null check (source in ('inline', 'github')),
  execution_mode text not null check (execution_mode in ('near-ai-cloud', 'mock')),
  status text not null check (status in ('success', 'error', 'timeout')),
  score double precision,
  wall_time_sec double precision not null default 0,
  total_tokens integer not null default 0,
  token_usage jsonb not null default '{}'::jsonb,
  output_text text,
  output_json jsonb,
  created_at timestamptz not null default now()
);

create index if not exists submissions_challenge_created_idx
  on public.submissions (challenge_id, created_at desc);

create index if not exists submissions_challenge_score_idx
  on public.submissions (challenge_id, score desc);

create table if not exists public.leaderboard_entries (
  challenge_id text not null,
  submission_id uuid not null references public.submissions(id) on delete cascade,
  submitter_id text not null,
  principal_type text not null check (principal_type in ('human', 'agent')),
  score double precision,
  wall_time_sec double precision not null default 0,
  total_tokens integer not null default 0,
  rank integer not null,
  updated_at timestamptz not null default now(),
  primary key (challenge_id, submission_id)
);

create or replace function public.recompute_leaderboard(target_challenge_id text)
returns void
language plpgsql
security definer
as $$
begin
  delete from public.leaderboard_entries
  where challenge_id = target_challenge_id;

  insert into public.leaderboard_entries (
    challenge_id,
    submission_id,
    submitter_id,
    principal_type,
    score,
    wall_time_sec,
    total_tokens,
    rank,
    updated_at
  )
  select
    s.challenge_id,
    s.id,
    s.submitter_id,
    s.principal_type,
    s.score,
    s.wall_time_sec,
    s.total_tokens,
    rank() over (
      partition by s.challenge_id
      order by s.score desc nulls last, s.wall_time_sec asc, s.total_tokens asc, s.created_at asc
    ) as rank,
    now()
  from public.submissions s
  where s.challenge_id = target_challenge_id
    and s.status = 'success';
end;
$$;

-- Optional RLS skeleton (customize before enabling in production):
-- alter table public.submissions enable row level security;
-- alter table public.leaderboard_entries enable row level security;

-- If you created these tables before `principal_type` existed, run:
-- alter table public.submissions
--   add column if not exists principal_type text not null default 'human'
--     check (principal_type in ('human', 'agent'));
-- alter table public.leaderboard_entries
--   add column if not exists principal_type text not null default 'human'
--     check (principal_type in ('human', 'agent'));
-- Note: Postgres may reject combining DEFAULT + CHECK in one ADD COLUMN on some versions;
-- if so, split into: add column nullable -> backfill -> set not null -> add check.
