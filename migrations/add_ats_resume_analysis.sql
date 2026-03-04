-- ATS Resume Intelligence Engine table
CREATE TABLE IF NOT EXISTS ats_resume_analysis (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    run_id VARCHAR(36),
    analysis_version INTEGER,
    normalized_score FLOAT NOT NULL,
    structure_score FLOAT NOT NULL,
    parse_score FLOAT NOT NULL,
    skill_authenticity_score FLOAT NOT NULL,
    role_alignment_score FLOAT NOT NULL,
    career_consistency_score FLOAT NOT NULL,
    keyword_stuffing_risk VARCHAR(20) NOT NULL,
    recruiter_readability VARCHAR(20) NOT NULL,
    cross_validation_penalty FLOAT NOT NULL DEFAULT 0.0,
    raw_metrics JSONB NOT NULL,
    explanation JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ats_resume_analysis_username ON ats_resume_analysis (username);
CREATE INDEX IF NOT EXISTS ix_ats_resume_analysis_run_id ON ats_resume_analysis (run_id);
