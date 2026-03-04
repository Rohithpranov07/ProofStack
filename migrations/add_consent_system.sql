-- Migration: Legal Consent & Authorization Gate
-- Creates the user_consent table and adds consent_recorded column to analysis_job.
-- Safe to run multiple times (IF NOT EXISTS / IF NOT EXISTS guard).

BEGIN;

-- 1. user_consent audit table
CREATE TABLE IF NOT EXISTS user_consent (
    id              SERIAL PRIMARY KEY,
    job_id          VARCHAR(36) NOT NULL UNIQUE,
    consent_version VARCHAR(20) NOT NULL,
    consent_text_snapshot TEXT NOT NULL,
    consent_given   BOOLEAN NOT NULL DEFAULT FALSE,
    recruiter_confirmation BOOLEAN,
    ip_address      VARCHAR(45) NOT NULL,
    user_agent      VARCHAR(500) NOT NULL DEFAULT 'unknown',
    jurisdiction_hint VARCHAR(10),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_user_consent_job_id ON user_consent (job_id);

-- 2. Add consent_recorded flag to analysis_job
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'analysis_job'
          AND column_name = 'consent_recorded'
    ) THEN
        ALTER TABLE analysis_job
            ADD COLUMN consent_recorded BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

COMMIT;
