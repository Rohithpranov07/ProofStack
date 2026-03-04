-- Migration: Add analysis_version column to all engine tables
-- Run against the ProofStack PostgreSQL database
-- Safe to run multiple times (IF NOT EXISTS / column-exists guards)

DO $$
BEGIN
    -- github_analysis
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='github_analysis' AND column_name='analysis_version') THEN
        ALTER TABLE github_analysis ADD COLUMN analysis_version INTEGER;
    END IF;

    -- profile_consistency
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='profile_consistency' AND column_name='analysis_version') THEN
        ALTER TABLE profile_consistency ADD COLUMN analysis_version INTEGER;
    END IF;

    -- leetcode_analysis
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='leetcode_analysis' AND column_name='analysis_version') THEN
        ALTER TABLE leetcode_analysis ADD COLUMN analysis_version INTEGER;
    END IF;

    -- red_flag_analysis
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='red_flag_analysis' AND column_name='analysis_version') THEN
        ALTER TABLE red_flag_analysis ADD COLUMN analysis_version INTEGER;
    END IF;

    -- product_mindset_analysis
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='product_mindset_analysis' AND column_name='analysis_version') THEN
        ALTER TABLE product_mindset_analysis ADD COLUMN analysis_version INTEGER;
    END IF;

    -- digital_footprint_analysis
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='digital_footprint_analysis' AND column_name='analysis_version') THEN
        ALTER TABLE digital_footprint_analysis ADD COLUMN analysis_version INTEGER;
    END IF;

    -- pst_report
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='pst_report' AND column_name='analysis_version') THEN
        ALTER TABLE pst_report ADD COLUMN analysis_version INTEGER;
    END IF;

    -- recruiter_report
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='recruiter_report' AND column_name='analysis_version') THEN
        ALTER TABLE recruiter_report ADD COLUMN analysis_version INTEGER;
    END IF;

    -- advanced_github_analysis
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='advanced_github_analysis' AND column_name='analysis_version') THEN
        ALTER TABLE advanced_github_analysis ADD COLUMN analysis_version INTEGER;
    END IF;
END $$;
