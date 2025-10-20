-- Script para criar as tabelas do banco de dados PostgreSQL para o projeto NBA Score
DROP TABLE IF EXISTS standings, player_statistics, team_statistics, game_statistics, games, players, teams, leagues, seasons, users CASCADE;
DROP TYPE IF EXISTS user_role;

CREATE TYPE user_role AS ENUM ('admin', 'user');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    cpf VARCHAR(14) UNIQUE,
    birth_date DATE,
    hashed_password TEXT NOT NULL,
    role user_role NOT NULL DEFAULT 'user',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seasons (
    season INTEGER PRIMARY KEY,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE leagues (
    id INTEGER PRIMARY KEY, -- ID da API
    name VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50),
    logo_url TEXT,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_hash VARCHAR(64) NOT NULL
);

CREATE TABLE teams (
    id INTEGER PRIMARY KEY, -- ID da API
    name VARCHAR(255) UNIQUE NOT NULL,
    nickname VARCHAR(255),
    code VARCHAR(10),
    city VARCHAR(255),
    logo_url TEXT,
    is_nba_franchise BOOLEAN,
    is_all_star BOOLEAN,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_hash VARCHAR(64) NOT NULL
);

CREATE TABLE players (
    id INTEGER PRIMARY KEY, -- ID da API
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    birth_date DATE,
    birth_country VARCHAR(255),
    nba_start_year INTEGER,
    pro_years INTEGER,
    height_meters NUMERIC(4, 2),
    weight_kilograms NUMERIC(5, 2),
    college VARCHAR(255),
    affiliation VARCHAR(255),
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_hash VARCHAR(64) NOT NULL
);

CREATE TABLE games (
    id INTEGER PRIMARY KEY, -- ID da API
    league_id INTEGER REFERENCES leagues(id) ON DELETE SET NULL,
    season INTEGER REFERENCES seasons(season) ON DELETE CASCADE,
    game_date TIMESTAMPTZ,
    status VARCHAR(100),
    home_team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    visitor_team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    home_score INTEGER,
    visitor_score INTEGER,
    arena_name VARCHAR(255),
    arena_city VARCHAR(255),
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_hash VARCHAR(64) NOT NULL
);

CREATE TABLE game_statistics (
    game_id INTEGER PRIMARY KEY REFERENCES games(id) ON DELETE CASCADE,
    -- Campos agregados, se a API fornecer, podem ser adicionados aqui
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_hash VARCHAR(64) NOT NULL
);

CREATE TABLE team_statistics (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    season INTEGER NOT NULL REFERENCES seasons(season) ON DELETE CASCADE,
    points INTEGER,
    fgm INTEGER,
    fga INTEGER,
    fgp NUMERIC(5, 2),
    ftm INTEGER,
    fta INTEGER,
    ftp NUMERIC(5, 2),
    tpm INTEGER,
    tpa INTEGER,
    tpp NUMERIC(5, 2),
    off_reb INTEGER,
    def_reb INTEGER,
    tot_reb INTEGER,
    assists INTEGER,
    p_fouls INTEGER,
    steals INTEGER,
    turnovers INTEGER,
    blocks INTEGER,
    plus_minus VARCHAR(10),
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_hash VARCHAR(64) NOT NULL,
    UNIQUE(team_id, game_id)
);

CREATE TABLE player_statistics (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    season INTEGER NOT NULL REFERENCES seasons(season) ON DELETE CASCADE,
    points INTEGER,
    pos VARCHAR(50),
    min_played VARCHAR(10),
    fgm INTEGER,
    fga INTEGER,
    fgp NUMERIC(5, 2),
    ftm INTEGER,
    fta INTEGER,
    ftp NUMERIC(5, 2),
    tpm INTEGER,
    tpa INTEGER,
    tpp NUMERIC(5, 2),
    off_reb INTEGER,
    def_reb INTEGER,
    tot_reb INTEGER,
    assists INTEGER,
    p_fouls INTEGER,
    steals INTEGER,
    turnovers INTEGER,
    blocks INTEGER,
    plus_minus VARCHAR(10),
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_hash VARCHAR(64) NOT NULL,
    UNIQUE(player_id, game_id)
);

CREATE TABLE standings (
    id SERIAL PRIMARY KEY,
    league_id INTEGER NOT NULL REFERENCES leagues(id) ON DELETE CASCADE,
    season INTEGER NOT NULL REFERENCES seasons(season) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    conference_name VARCHAR(100),
    conference_rank INTEGER,
    division_name VARCHAR(100),
    division_rank INTEGER,
    win INTEGER,
    loss INTEGER,
    games_behind VARCHAR(10),
    streak INTEGER,
    win_streak BOOLEAN,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_hash VARCHAR(64) NOT NULL,
    UNIQUE(league_id, season, team_id) -- Chave de negócio para standings
);

CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_timestamp BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp BEFORE UPDATE ON leagues FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();


DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'trigger_set_timestamp') THEN
        CREATE OR REPLACE FUNCTION trigger_set_timestamp()
        RETURNS TRIGGER AS $func$
        BEGIN
          NEW.updated_at = NOW();
          RETURN NEW;
        END;
        $func$ LANGUAGE plpgsql;
    END IF;
END;
$$;

DROP TRIGGER IF EXISTS set_timestamp ON seasons;
CREATE TRIGGER set_timestamp
BEFORE UPDATE ON seasons
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();