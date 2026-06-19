-- 0001_init_schema.sql — MetSyn · Sprint 2 (persistencia en Supabase/PostgreSQL).
--
-- Tabla `clinical_records`: espejo de ml.contracts.ClinicalRecord (fuente de
-- verdad del registro clínico anonimizado). Clave primaria compuesta
-- (patient_id, period) para permitir UPSERT idempotente por período.
--
-- Eje temporal CATEGÓRICO discreto: 2021/2023/2024/2025 (2022 no existe).

create table if not exists public.clinical_records (
    patient_id    text        not null,
    period        text        not null check (period in ('2021', '2023', '2024', '2025')),
    sexo          text        not null check (sexo in ('M', 'F')),
    edad          numeric,
    perabd        numeric,
    trig          numeric,
    hdl           numeric,
    glu           numeric,
    presion_sis   numeric,
    presion_dia   numeric,
    criterios_n   smallint    not null check (criterios_n between 0 and 5),
    metsyn_flag   boolean     not null,
    imputed_flags jsonb       not null default '[]'::jsonb,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now(),
    primary key (patient_id, period)
);

comment on table public.clinical_records is
    'Registros clínicos anonimizados (espejo de ClinicalRecord). Eje temporal categórico: 2021/2023/2024/2025.';

-- Índices para las consultas del dashboard (prevalencia/filtros, Sprint 3).
create index if not exists idx_clinical_records_period      on public.clinical_records (period);
create index if not exists idx_clinical_records_metsyn_flag on public.clinical_records (metsyn_flag);
create index if not exists idx_clinical_records_sexo        on public.clinical_records (sexo);

-- updated_at automático en cada UPDATE (incluido el UPDATE que hace un upsert).
create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    new.updated_at := now();
    return new;
end;
$$;

drop trigger if exists trg_clinical_records_updated_at on public.clinical_records;
create trigger trg_clinical_records_updated_at
    before update on public.clinical_records
    for each row execute function public.set_updated_at();

-- RLS habilitado desde el día 1.
--   · El backend usa la SERVICE KEY (rol `service_role`), que OMITE RLS para
--     escribir y leer — la ingesta funciona sin políticas adicionales.
--   · El acceso directo de clientes (frontend, Sprint 3/4) queda restringido a
--     usuarios autenticados con permiso de SÓLO LECTURA sobre datos ya
--     anonimizados. No se concede ningún permiso al rol `anon`.
alter table public.clinical_records enable row level security;

drop policy if exists "lectura para usuarios autenticados" on public.clinical_records;
create policy "lectura para usuarios autenticados"
    on public.clinical_records
    for select
    to authenticated
    using (true);

-- Privilegios de tabla (independientes de RLS).
--   · service_role: acceso total (lo usa el backend; además omite RLS).
--   · authenticated: sólo SELECT, acotado por la política de lectura anterior.
--   · anon: sin privilegios (no se concede nada).
grant all privileges on public.clinical_records to service_role;
grant select on public.clinical_records to authenticated;
