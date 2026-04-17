-- Run this in Supabase SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.user_credits (
  user_id uuid primary key references auth.users(id) on delete cascade,
  credits integer not null default 50 check (credits >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.ensure_user_credits(target_user_id uuid)
returns integer
language plpgsql
security definer
as $$
declare
  current_credits integer;
begin
  insert into public.user_credits (user_id)
  values (target_user_id)
  on conflict (user_id) do nothing;

  select credits
  into current_credits
  from public.user_credits
  where user_id = target_user_id;

  return coalesce(current_credits, 0);
end;
$$;

create or replace function public.consume_user_credits(
  target_user_id uuid,
  amount integer
)
returns integer
language plpgsql
security definer
as $$
declare
  remaining integer;
begin
  if amount <= 0 then
    raise exception 'Credit amount must be positive';
  end if;

  perform public.ensure_user_credits(target_user_id);

  update public.user_credits
  set
    credits = credits - amount,
    updated_at = now()
  where user_id = target_user_id
    and credits >= amount
  returning credits into remaining;

  if remaining is null then
    raise exception 'Insufficient credits';
  end if;

  return remaining;
end;
$$;

create or replace function public.seed_credits_for_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.user_credits (user_id, credits)
  values (new.id, 50)
  on conflict (user_id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created_seed_credits on auth.users;
create trigger on_auth_user_created_seed_credits
  after insert on auth.users
  for each row execute procedure public.seed_credits_for_new_user();

create table if not exists public.submissions (
  id uuid primary key default gen_random_uuid(),
  challenge_id text not null,
  submitter_id text not null,
  principal_type text not null check (principal_type in ('human', 'agent')),
  run_mode text not null check (run_mode in ('manual', 'autonomous')),
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

create table if not exists public.challenges (
  id text primary key,
  title text not null,
  category text not null check (category in ('research', 'code', 'data', 'decision', 'content')),
  description text not null,
  input_output_spec text not null,
  company text not null,
  status text not null check (status in ('active', 'upcoming', 'completed')),
  bounty integer not null default 0,
  deadline date,
  challenge_input jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.challenge_evaluation_criteria (
  id bigserial primary key,
  challenge_id text not null references public.challenges(id) on delete cascade,
  criterion_key text not null,
  label text not null,
  weight double precision,
  is_reference_only boolean not null default false,
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  unique (challenge_id, criterion_key)
);

create index if not exists challenge_eval_criteria_challenge_sort_idx
  on public.challenge_evaluation_criteria (challenge_id, sort_order, id);

create index if not exists submissions_challenge_created_idx
  on public.submissions (challenge_id, created_at desc);

create index if not exists submissions_challenge_score_idx
  on public.submissions (challenge_id, score desc);

create table if not exists public.leaderboard_entries (
  challenge_id text not null,
  submission_id uuid not null references public.submissions(id) on delete cascade,
  submitter_id text not null,
  principal_type text not null check (principal_type in ('human', 'agent')),
  run_mode text not null check (run_mode in ('manual', 'autonomous')),
  score double precision,
  wall_time_sec double precision not null default 0,
  total_tokens integer not null default 0,
  rank integer not null,
  updated_at timestamptz not null default now(),
  primary key (challenge_id, submission_id)
);

create table if not exists public.submission_criterion_scores (
  submission_id uuid not null references public.submissions(id) on delete cascade,
  challenge_id text not null,
  criterion_key text not null,
  score double precision not null check (score >= 0 and score <= 100),
  weight double precision,
  reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (submission_id, criterion_key)
);

create index if not exists submission_criterion_scores_challenge_submission_idx
  on public.submission_criterion_scores (challenge_id, submission_id);

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
    run_mode,
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
    s.run_mode,
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
-- alter table public.user_credits enable row level security;
-- alter table public.submissions enable row level security;
-- alter table public.leaderboard_entries enable row level security;

-- If you created these tables before `principal_type` existed, run:
-- alter table public.submissions
--   add column if not exists principal_type text not null default 'human'
--     check (principal_type in ('human', 'agent'));
-- alter table public.leaderboard_entries
--   add column if not exists principal_type text not null default 'human'
--     check (principal_type in ('human', 'agent'));
-- alter table public.submissions
--   add column if not exists run_mode text not null default 'manual'
--     check (run_mode in ('manual', 'autonomous'));
-- alter table public.leaderboard_entries
--   add column if not exists run_mode text not null default 'manual'
--     check (run_mode in ('manual', 'autonomous'));
-- Note: Postgres may reject combining DEFAULT + CHECK in one ADD COLUMN on some versions;
-- if so, split into: add column nullable -> backfill -> set not null -> add check.
