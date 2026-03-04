-- Share token table for public read-only dashboard links
CREATE TABLE IF NOT EXISTS share_token (
    id SERIAL PRIMARY KEY,
    token VARCHAR(64) NOT NULL UNIQUE,
    job_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_share_token_token ON share_token (token);
CREATE INDEX IF NOT EXISTS ix_share_token_job_id ON share_token (job_id);
