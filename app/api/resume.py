"""API router for Resume Parsing.

POST /api/resume/parse  — Upload a resume file and get structured data back.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.resume_parser import ResumeParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resume", tags=["resume"])

ACCEPTED_EXTENSIONS = {"pdf", "docx", "txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

_parser = ResumeParser()


@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)) -> dict:
    """Upload a resume file (PDF, DOCX, TXT) and return structured data.

    Returns:
        {
            "filename": str,
            "skills": [ { "name": str, "years": float }, ... ],
            "experience": [ { "company": str, "role": str, "start_date": str, "end_date": str }, ... ],
            "projects": [ { "name": str, "tech": str, "description": str }, ... ],
        }
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ACCEPTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Accepted: {', '.join(ACCEPTED_EXTENSIONS)}",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum 10 MB.")
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")

    logger.info(f"Resume upload: {file.filename} ({len(file_bytes)} bytes)")

    try:
        result = _parser.parse(file_bytes, file.filename)
    except Exception as e:
        logger.exception(f"Resume parsing failed for {file.filename}")
        raise HTTPException(status_code=422, detail=f"Failed to parse resume: {str(e)}")

    return {
        "filename": file.filename,
        "raw_text": result["raw_text"],
        "skills": result["skills"],
        "experience": result["experience"],
        "projects": result["projects"],
    }
