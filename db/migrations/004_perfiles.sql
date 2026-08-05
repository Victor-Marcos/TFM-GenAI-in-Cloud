CREATE TABLE perfiles (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    avatar_color TEXT DEFAULT '#4A90D9'
);

ALTER TABLE tickets ADD COLUMN perfil_id INTEGER REFERENCES perfiles(id);

INSERT INTO perfiles (nombre) VALUES ('Victor');

UPDATE tickets SET perfil_id = (SELECT id FROM perfiles WHERE nombre = 'Victor');

CREATE INDEX idx_tickets_perfil ON tickets(perfil_id);