-- =============================================================================
-- ProjetIA-DevPro — Schéma initial
-- Appliqué automatiquement au premier démarrage du container postgres
-- (via /docker-entrypoint-initdb.d/)
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- batches : un batch = une requête utilisateur = N images
-- -----------------------------------------------------------------------------
CREATE TABLE batches (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject         TEXT NOT NULL,                      -- saisie utilisateur brute
    style           TEXT NOT NULL,                      -- 'anime' | 'semi-realiste' | 'illustration' | 'peinture'
    ambiance        TEXT NOT NULL,                      -- 'neutre' | 'douce' | 'dramatique' | 'mysterieuse'
    cadrage         TEXT NOT NULL,                      -- 'portrait' | 'carre' | 'paysage'
    prompt_enriched TEXT,                               -- rempli par le worker
    negative_prompt TEXT,
    image_count     INT NOT NULL DEFAULT 4,
    state           TEXT NOT NULL DEFAULT 'queued',     -- 'queued' | 'processing' | 'completed' | 'failed'
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,

    CONSTRAINT batches_state_check CHECK (state IN ('queued', 'processing', 'completed', 'failed')),
    CONSTRAINT batches_style_check CHECK (style IN ('anime', 'semi-realiste', 'illustration', 'peinture')),
    CONSTRAINT batches_ambiance_check CHECK (ambiance IN ('neutre', 'douce', 'dramatique', 'mysterieuse')),
    CONSTRAINT batches_cadrage_check CHECK (cadrage IN ('portrait', 'carre', 'paysage'))
);

CREATE INDEX idx_batches_state ON batches(state);
CREATE INDEX idx_batches_created_at ON batches(created_at DESC);

-- -----------------------------------------------------------------------------
-- images : une ligne par image générée, rattachée à un batch
-- -----------------------------------------------------------------------------
CREATE TABLE images (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id    UUID NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    seed        BIGINT NOT NULL,
    file_path   TEXT NOT NULL,                          -- chemin relatif à /data/images
    width       INT,
    height      INT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_images_batch_id ON images(batch_id);