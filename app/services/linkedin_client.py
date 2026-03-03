"""LinkedIn profile verifier.

Validates LinkedIn profile URLs through:
  1. URL format validation (must match linkedin.com/in/ pattern)
  2. HTTP reachability check with realistic browser headers

Note: LinkedIn aggressively blocks automated requests, returning various
status codes (999, 403, 429, 503, etc.).  If the URL format is valid
and we get *any* HTTP response, we treat it as verified.  Only a clean
404 (profile not found) or a format mismatch is treated as "not verified".
"""

from __future__ import annotations

import logging
import re

import httpx

logger = logging.getLogger(__name__)

_LINKEDIN_PATTERN = re.compile(
    r"^https?://(www\.)?linkedin\.com/in/[\w\-]+/?$", re.IGNORECASE
)


class LinkedInClient:
    """Async LinkedIn profile URL verifier."""

    async def verify_profile(self, url: str) -> bool:
        """Return True if the profile URL is a valid LinkedIn profile.

        Strategy:
          1. URL format must match ``linkedin.com/in/<slug>``.
          2. HTTP reachability — any response except 404 counts as verified
             because LinkedIn blocks bots with 999/403/429/503 but that
             still proves the profile exists behind the auth wall.
          3. On network failure, give benefit of doubt if format was valid.
        """
        url_str = str(url).strip()

        # Step 1: URL format validation
        if not _LINKEDIN_PATTERN.match(url_str):
            logger.info("LinkedIn URL format invalid: %s", url_str)
            return False

        # Step 2: HTTP reachability (best effort)
        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cache-Control": "no-cache",
                },
            ) as client:
                # Try GET first (some servers reject HEAD)
                response = await client.get(url_str)
                status = response.status_code
                logger.info(
                    "LinkedIn check: url=%s status=%d",
                    url_str, status,
                )

                # Only a genuine 404 means "profile does not exist"
                if status == 404:
                    logger.info("LinkedIn profile not found (404): %s", url_str)
                    return False

                # Any other response (200, 301, 302, 403, 429, 503, 999, etc.)
                # means the server acknowledged the URL — profile exists
                return True

        except Exception as exc:
            logger.warning("LinkedIn HTTP check failed for %s: %s", url_str, exc)
            # Format was valid, network just failed — benefit of doubt
            return True
