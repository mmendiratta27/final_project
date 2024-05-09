CREATE EXTENSION postgis;

\set ON_ERROR_STOP on

BEGIN;

CREATE TABLE urls (
    id_urls BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE
);

CREATE TABLE users (
    id_users BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT
);

CREATE TABLE tweets (
    id_tweets BIGSERIAL PRIMARY KEY,
    id_users BIGINT,
    created_at TIMESTAMPTZ DEFAULT current_timestamp,
    text TEXT,
    FOREIGN KEY (id_users) REFERENCES users(id_users)
);
CREATE EXTENSION RUM;
CREATE EXTENSION pg_trgm;

CREATE UNIQUE INDEX ON users (username);
CREATE INDEX ON tweets USING rum(to_tsvector('english', text));
CREATE INDEX ON tweets (id_users);
CREATE INDEX ON users (id_users);

COMMIT;
