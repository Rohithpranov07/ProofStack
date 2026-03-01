"""API key authentication for ProofStack.

Simple header-based auth using X-API-Key.
All endpoints except /health and /api/dashboard/shared/{token} require a valid key.

Usage in routers:
    from app.core.auth import require_api_key
    router = APIRouter(dependencies=[Depends(require_api_key)])
"""

from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Query, Request, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    api_key: str | None = Security(_API_KEY_HEADER),
    api_key_query: str | None = Query(None, alias="api_key"),
) -> str:
    """Validate X-API-Key header (or ?api_key= query param) against configured key.

    Query param fallback allows browser-initiated requests like PDF downloads
    where custom headers can't be set (window.open / anchor tags).

    Returns the validated key on success.
    Raises 401 if missing, 403 if invalid.
    """
    key = api_key or api_key_query
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    if not secrets.compare_digest(key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return key
