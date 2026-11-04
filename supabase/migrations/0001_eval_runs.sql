-- One schema per app. Writes come from CI with the service key; the dashboard reads.
create schema if not exists evals;

create table evals.runs (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  name text not null,
  git_sha text,
  total int not null,
  passed int not null,
  pass_rate double precision not null,
  avg_latency_s double precision not null default 0,
  trace_url text
);

create table evals.run_cases (
  id bigint generated always as identity primary key,
  run_id uuid not null references evals.runs(id) on delete cascade,
  case_id text not null,
  passed boolean not null,
  output text,
  detail text,
  latency_s double precision
);

create index on evals.run_cases (run_id);
create index on evals.runs (name, created_at desc);

alter table evals.runs enable row level security;
alter table evals.run_cases enable row level security;
-- No policies: only the service role (CI) can write or read. Add a read policy for the
-- dashboard when it needs anon access to public demo data.
