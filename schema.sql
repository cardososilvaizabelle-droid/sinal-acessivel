CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    accessibility_needs TEXT[] NOT NULL DEFAULT '{}',
    extra_seconds INTEGER NOT NULL DEFAULT 10
        CHECK (extra_seconds BETWEEN 0 AND 30),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE intersections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(160) NOT NULL,
    location_description TEXT,
    normal_crossing_seconds INTEGER NOT NULL DEFAULT 20
        CHECK (normal_crossing_seconds BETWEEN 5 AND 120),
    max_extra_seconds INTEGER NOT NULL DEFAULT 30
        CHECK (max_extra_seconds BETWEEN 0 AND 60),
    simulation_enabled BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE crossing_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    intersection_id UUID NOT NULL REFERENCES intersections(id),
    requested_extra_seconds INTEGER NOT NULL
        CHECK (requested_extra_seconds BETWEEN 0 AND 30),
    status VARCHAR(20) NOT NULL DEFAULT 'simulated'
        CHECK (status IN ('simulated', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO intersections (
    name,
    location_description,
    normal_crossing_seconds
)
VALUES (
    'Cruzamento de demonstração',
    'Local virtual, sem conexão com um semáforo real',
    20
);