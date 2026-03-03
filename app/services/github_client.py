"""Async GitHub REST API client.

All requests are authenticated via Bearer token.
Rate-limit headers are tracked and respected.
Every response is validated before returning.
No unauthenticated calls — enforced by design.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import settings
from app.core.logging import logger

BASE_URL = "https://api.github.com"

# Shared client singleton (module-level)
_shared_client: Optional[httpx.AsyncClient] = None


async def _get_shared_client() -> httpx.AsyncClient:
    """Return (and lazily create) a module-level persistent httpx client."""
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _shared_client


class GitHubAPIError(Exception):
    """Raised on non-recoverable GitHub API errors."""

    def __init__(self, status_code: int, url: str, body: str) -> None:
        self.status_code = status_code
        self.url = url
        super().__init__(f"GitHub API {status_code} for {url}: {body[:300]}")


class GitHubRateLimitError(GitHubAPIError):
    """Raised when the rate limit is exhausted."""
    pass


class GitHubClient:
    """Fully async GitHub REST v3 client.

    Usage::

        client = GitHubClient()
        repos = await client.get_repos("torvalds")
    """

    def __init__(self) -> None:
        self.headers: Dict[str, str] = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self._rate_remaining: int = 5000
        self._rate_limit: int = 5000
        self._rate_reset: int = 0

    # ── internal ────────────────────────────────────────────

    def _handle_rate_limit(
        self, response: httpx.Response, url: str = ""
    ) -> None:
        """Raise immediately if GitHub rate limit is exhausted."""
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")

        if remaining == "0":
            raise GitHubRateLimitError(
                status_code=403,
                url=url or str(response.url),
                body=f"Rate limit exceeded. Resets at UNIX time {reset}",
            )

    def _track_rate_limit(self, headers: httpx.Headers) -> None:
        self._rate_limit = int(headers.get("x-ratelimit-limit", self._rate_limit))
        self._rate_remaining = int(headers.get("x-ratelimit-remaining", self._rate_remaining))
        self._rate_reset = int(headers.get("x-ratelimit-reset", self._rate_reset))
        if self._rate_remaining <= 50:
            logger.warning(
                "GitHub rate limit low: %d/%d remaining (resets at epoch %d)",
                self._rate_remaining,
                self._rate_limit,
                self._rate_reset,
            )

    async def _get_json(
        self,
        url: str,
        params: Dict[str, Any] | None = None,
        *,
        allow_empty: bool = False,
    ) -> Any:
        """Perform an authenticated GET and return parsed JSON.

        Args:
            url: Full URL to request.
            params: Optional query parameters.
            allow_empty: If True, return [] on 204/409 instead of raising.
        """
        client = await _get_shared_client()
        response = await client.get(url, headers=self.headers, params=params)

        self._handle_rate_limit(response)
        self._track_rate_limit(response.headers)

        if response.status_code == 403 and self._rate_remaining == 0:
            raise GitHubRateLimitError(
                status_code=403, url=url, body="Rate limit exceeded"
            )

        if allow_empty and response.status_code in (204, 409):
            return []

        if response.status_code == 404:
            return None

        if response.status_code != 200:
            raise GitHubAPIError(
                status_code=response.status_code,
                url=url,
                body=response.text,
            )

        return response.json()

    async def _get_paginated(
        self,
        url: str,
        per_page: int = 100,
        max_pages: int = 10,
        *,
        allow_empty: bool = False,
    ) -> List[Dict[str, Any]]:
        """Fetch all pages from a paginated endpoint.

        Stops when a page returns fewer items than per_page or max_pages is hit.
        """
        items: List[Dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            batch = await self._get_json(
                url,
                params={"per_page": per_page, "page": page},
                allow_empty=allow_empty,
            )
            if batch is None or not batch:
                break
            items.extend(batch)
            if len(batch) < per_page:
                break
        return items

    # ── public API ──────────────────────────────────────────

    async def get_repos(self, username: str) -> List[Dict[str, Any]]:
        """Fetch all public repos for *username* (up to 1 000)."""
        return await self._get_paginated(
            f"{BASE_URL}/users/{username}/repos",
            per_page=100,
            max_pages=10,
        )

    async def get_commits(
        self, username: str, repo: str, max_commits: int = 300
    ) -> List[Dict[str, Any]]:
        """Fetch commits for *username/repo* with full pagination.

        Supports pagination, stops after *max_commits*.  Handles empty
        repos (HTTP 409) and prevents infinite loops.
        """
        commits: List[Dict[str, Any]] = []
        page = 1
        url = f"{BASE_URL}/repos/{username}/{repo}/commits"
        client = await _get_shared_client()

        while len(commits) < max_commits:
            response = await client.get(
                url,
                headers=self.headers,
                params={"per_page": 100, "page": page},
            )

            self._handle_rate_limit(response, url)

            if response.status_code == 409:
                break

            if response.status_code != 200:
                raise GitHubAPIError(
                    status_code=response.status_code,
                    url=url,
                    body=response.text,
                )

            data = response.json()

            if not data:
                break

            commits.extend(data)

            if len(data) < 100:
                break

            page += 1

        return commits[:max_commits]

    async def get_branches(self, username: str, repo: str) -> List[Dict[str, Any]]:
        """Fetch branches for *username/repo*."""
        result = await self._get_json(
            f"{BASE_URL}/repos/{username}/{repo}/branches",
            params={"per_page": 100},
            allow_empty=True,
        )
        return result if isinstance(result, list) else []

    async def get_commit_detail(
        self, username: str, repo: str, sha: str
    ) -> Dict[str, Any]:
        """Fetch full commit detail including additions/deletions."""
        url = f"{BASE_URL}/repos/{username}/{repo}/commits/{sha}"
        client = await _get_shared_client()
        response = await client.get(url, headers=self.headers)

        self._handle_rate_limit(response, url)

        if response.status_code != 200:
            raise GitHubAPIError(
                status_code=response.status_code,
                url=url,
                body=response.text,
            )

        return response.json()

    async def batch_get_commit_details(
        self,
        username: str,
        repo: str,
        shas: List[str],
        concurrency: int = 10,
    ) -> List[Dict[str, Any]]:
        """Fetch multiple commit details concurrently with a semaphore."""
        sem = asyncio.Semaphore(concurrency)
        results: List[Dict[str, Any]] = []

        async def _fetch(sha: str) -> Optional[Dict[str, Any]]:
            async with sem:
                try:
                    return await self.get_commit_detail(username, repo, sha)
                except Exception:
                    return None

        tasks = [_fetch(sha) for sha in shas]
        raw = await asyncio.gather(*tasks)
        results = [r for r in raw if r is not None]
        return results

    async def get_contributors(self, username: str, repo: str) -> List[Dict[str, Any]]:
        """Fetch contributors for *username/repo*.

        Returns [] for repos with no contribution data (HTTP 204).
        """
        result = await self._get_json(
            f"{BASE_URL}/repos/{username}/{repo}/contributors",
            params={"per_page": 100},
            allow_empty=True,
        )
        return result if isinstance(result, list) else []
