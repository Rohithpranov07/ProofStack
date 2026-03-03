"""Async LeetCode GraphQL client.

Fetches user profile, submission stats, and recent submissions
from LeetCode's public GraphQL endpoint.  No authentication required.
All responses are validated before returning.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"

# The GraphQL query fetches:
#   - matchedUser → submitStats (solved counts by difficulty)
#   - matchedUser → profile → ranking (contest ranking)
#   - recentSubmissionList (last 20 submissions with timestamps)
_PROFILE_QUERY = """
query userProfile($username: String!) {
  matchedUser(username: $username) {
    username
    submitStats {
      acSubmissionNum {
        difficulty
        count
        submissions
      }
    }
    profile {
      ranking
    }
  }
  recentSubmissionList(username: $username, limit: 50) {
    timestamp
  }
}
"""


class LeetCodeAPIError(Exception):
    """Raised when LeetCode GraphQL returns an unexpected response."""

    def __init__(self, message: str) -> None:
        super().__init__(f"LeetCode API error: {message}")


class LeetCodeClient:
    """Fully async LeetCode GraphQL client."""

    async def fetch_profile(self, username: str) -> Dict[str, Any]:
        """Fetch profile stats and recent submissions for *username*.

        Returns the raw GraphQL response dict with structure:
        {
            "data": {
                "matchedUser": { ... } | null,
                "recentSubmissionList": [ ... ]
            }
        }

        Raises:
            LeetCodeAPIError: On HTTP errors or malformed responses.
        """
        payload = {
            "query": _PROFILE_QUERY,
            "variables": {"username": username},
        }

        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                headers={
                    "Content-Type": "application/json",
                    "Referer": "https://leetcode.com",
                },
            ) as client:
                response = await client.post(LEETCODE_GRAPHQL, json=payload)

            if response.status_code != 200:
                raise LeetCodeAPIError(
                    f"HTTP {response.status_code}: {response.text[:300]}"
                )

            data = response.json()

            if "errors" in data and data["errors"]:
                error_msg = data["errors"][0].get("message", "Unknown error")
                raise LeetCodeAPIError(error_msg)

            if "data" not in data:
                raise LeetCodeAPIError("Missing 'data' key in response")

            return data

        except httpx.HTTPError as exc:
            raise LeetCodeAPIError(f"Network error: {exc}") from exc
