DO
$$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vellum_seeder') THEN
        CREATE ROLE vellum_seeder LOGIN PASSWORD 'vellum_seeder';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vellum_readonly') THEN
        CREATE ROLE vellum_readonly LOGIN PASSWORD 'vellum_readonly';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vellum_auditor') THEN
        CREATE ROLE vellum_auditor LOGIN PASSWORD 'vellum_auditor';
    END IF;
END
$$;

ALTER ROLE vellum_readonly SET statement_timeout = '15s';
ALTER ROLE vellum_readonly SET work_mem = '16MB';

GRANT CONNECT ON DATABASE vellum TO vellum_seeder, vellum_readonly, vellum_auditor;
