CREATE ROLE vellum_reader LOGIN PASSWORD 'vellum_reader';
CREATE ROLE vellum_seeder LOGIN PASSWORD 'vellum_seeder';

GRANT CONNECT ON DATABASE vellum TO vellum_reader, vellum_seeder;

