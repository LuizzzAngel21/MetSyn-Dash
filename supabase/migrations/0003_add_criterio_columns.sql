-- 0003_add_criterio_columns.sql — MetSyn · Sprint 3 (consulta de criterios).
--
-- Persiste los 5 criterios ATP-III por fila (ya calculados por
-- backend/domain/atp3.py::calcular_flags) para alimentar GET /api/criterios.
-- Booleanos NOT NULL con default false (idempotente y compatible con filas
-- preexistentes).

alter table public.clinical_records
    add column if not exists criterio_perabd  boolean not null default false,
    add column if not exists criterio_trig    boolean not null default false,
    add column if not exists criterio_hdl     boolean not null default false,
    add column if not exists criterio_presion boolean not null default false,
    add column if not exists criterio_glu     boolean not null default false;
