"""Legal Consent & Authorization — versioned consent definitions.

This module is the single source of truth for consent text shown to users
and validated on the backend. NEVER modify past versions — only append new ones.
"""

from __future__ import annotations

CONSENT_VERSION = "v1.0.0"

# ── Checkbox text displayed to the user ───────────────────
CONSENT_CHECKBOX_1 = (
    "I confirm that I am submitting information that I am authorized to provide, "
    "and that the details supplied are accurate to the best of my knowledge."
)

CONSENT_CHECKBOX_2 = (
    "I consent to ProofStack processing the submitted information and any publicly "
    "available professional data associated with it for the purpose of generating "
    "an automated technical and authenticity analysis report. I understand that "
    "this analysis is algorithmic, probabilistic in nature, and should not be "
    "relied upon as the sole basis for employment decisions."
)

CONSENT_CHECKBOX_3 = (
    "I acknowledge that the information will be processed and retained in "
    "accordance with the Privacy Policy, and that I may request access to or "
    "deletion of my data as described therein."
)

RECRUITER_CHECKBOX = (
    "I confirm that the candidate has provided consent for this analysis."
)

# Full snapshot text stored alongside each consent record
CONSENT_TEXT_SNAPSHOT = (
    f"[Checkbox 1] {CONSENT_CHECKBOX_1}\n\n"
    f"[Checkbox 2] {CONSENT_CHECKBOX_2}\n\n"
    f"[Checkbox 3] {CONSENT_CHECKBOX_3}"
)

# ── Version history (append-only — never mutate) ─────────
# v1.0.0 — 2026-03-01 — Initial three-checkbox consent gate
