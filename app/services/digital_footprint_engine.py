"""ENGINE 6 — Digital Footprint Engine.

Analyses a candidate's broader developer presence beyond GitHub code:
  - StackOverflow reputation, answer count, badge count, helper ratio
  - GitHub merged-PR count (as contributor to other repos)
  - GitHub stars aggregation (social proof)
  - Blog / personal-site recency detection
  - Recency scoring (activity freshness across platforms)

=== SCORING DIMENSIONS (total 100) ===

  StackOverflow Presence  (0–25)
    Reputation tiers + helper_ratio bonus.

  Merged PR Contributions (0–20)
    External PRs merged into repos the user does NOT own.

  GitHub Stars Aggregation (0–20)
    Total stars across all owned repos.

  Blog / Site Recency     (0–20)
    Checks GitHub profile ``blog`` field for non-empty URL.

  Activity Recency        (0–15)
    Recent GitHub push + SO activity within 90 days.

=== SEO Tier Classification ===
  Ghost    (0-9)   — No discoverable footprint
  Passive  (10-29) — Minimal traces
  Active   (30-54) — Regular contributor
  Visible  (55-79) — Strong discoverable presence
  Authority(80-100) — Industry-level visibility
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.services.github_client import GitHubClient

_SO_API = "https://api.stackexchange.com/2.3"
_SO_TIMEOUT = 10.0
_GH_SEARCH_TIMEOUT = 12.0


def _classify_seo_tier(score: int) -> str:
    """Map a total footprint score to an SEO visibility tier."""
    if score >= 80:
        return "Authority"
    if score >= 55:
        return "Visible"
    if score >= 30:
        return "Active"
    if score >= 10:
        return "Passive"
    return "Ghost"


class DigitalFootprintEngine:
    """Analyse broader developer presence for trust scoring."""

    def __init__(self) -> None:
        self._github = GitHubClient()

    async def analyze(
        self,
        username: str,
        *,
        repos: Optional[List[Dict[str, Any]]] = None,
        stackoverflow_username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run all five footprint dimensions.

        Args:
            username: GitHub username.
            repos: Pre-fetched list of GitHub repo dicts (avoids re-fetch).
            stackoverflow_username: Optional SO display name to search.
        """
        logger.info(f"Starting Digital Footprint analysis for {username}")

        if repos is None:
            repos = await self._github.get_repos(username)

        # ── Fetch GitHub profile (followers, bio, blog, etc.) ─
        gh_profile = await self._fetch_github_profile(username)

        # ── Dimension scores ─────────────────────────────────
        so_score, so_detail = await self._stackoverflow_score(
            stackoverflow_username or username,
        )
        pr_score, pr_detail = await self._merged_pr_score(username)
        star_score, star_detail = self._stars_score(repos)
        blog_score, blog_detail = await self._blog_score(username, gh_profile=gh_profile)
        recency_score, recency_detail = self._recency_score(repos, so_detail)

        # ── Compute top repos (by stars, non-fork) ───────────
        top_repos = self._compute_top_repos(repos)

        # ── Compute network reach ────────────────────────────
        followers = gh_profile.get("followers", 0) if gh_profile else 0
        following = gh_profile.get("following", 0) if gh_profile else 0
        total_forks = sum(r.get("forks_count", 0) for r in repos if not r.get("fork", False))

        total = min(so_score + pr_score + star_score + blog_score + recency_score, 100)
        seo_tier = _classify_seo_tier(total)

        raw_metrics: Dict[str, Any] = {
            "stackoverflow": so_detail,
            "merged_prs": pr_detail,
            "stars": star_detail,
            "blog": blog_detail,
            "recency": recency_detail,
            "seo_tier": seo_tier,
            "top_repos": top_repos,
            "followers": followers,
            "following": following,
            "total_forks": total_forks,
            "bio": gh_profile.get("bio") if gh_profile else None,
            "company": gh_profile.get("company") if gh_profile else None,
            "location": gh_profile.get("location") if gh_profile else None,
            "twitter_username": gh_profile.get("twitter_username") if gh_profile else None,
            "public_repos_count": gh_profile.get("public_repos", 0) if gh_profile else 0,
        }

        explanation: Dict[str, Any] = {
            "stackoverflow_pts": so_score,
            "merged_pr_pts": pr_score,
            "stars_pts": star_score,
            "blog_pts": blog_score,
            "recency_pts": recency_score,
            "total": total,
            "seo_tier": seo_tier,
        }

        logger.info(
            f"Digital Footprint for {username}: "
            f"so={so_score} pr={pr_score} star={star_score} blog={blog_score} "
            f"recency={recency_score} → {total} ({seo_tier})"
        )

        return {
            "raw_metrics": raw_metrics,
            "normalized_score": float(total),
            "explanation": explanation,
        }

    # ── GitHub Profile ──────────────────────────────────────────

    @staticmethod
    async def _fetch_github_profile(username: str) -> Optional[Dict[str, Any]]:
        """Fetch the GitHub user profile (followers, bio, blog, etc.)."""
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    f"https://api.github.com/users/{username}",
                    headers={
                        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
                        "Accept": "application/vnd.github+json",
                    },
                )
            if resp.status_code != 200:
                logger.warning(f"GitHub profile fetch returned {resp.status_code} for {username}")
                return None
            return resp.json()
        except Exception as exc:
            logger.warning(f"GitHub profile fetch failed for {username}: {exc}")
            return None

    # ── Top repos extraction ──────────────────────────────────

    @staticmethod
    def _compute_top_repos(repos: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Extract top repositories sorted by stars (desc), then by created_at (desc) as tiebreaker."""
        owned = [r for r in repos if not r.get("fork", False)]
        # Primary: stars descending, Secondary: created_at descending (newest first)
        sorted_repos = sorted(
            owned,
            key=lambda r: (r.get("stargazers_count", 0), r.get("created_at", "")),
            reverse=True,
        )[:limit]
        result = []
        for r in sorted_repos:
            lang = r.get("language") or ""
            # Build tags from language + topics
            tags = []
            if lang:
                tags.append(lang)
            for topic in (r.get("topics") or [])[:2]:
                if topic.lower() != lang.lower():
                    tags.append(topic.capitalize())
            result.append({
                "name": r.get("name", ""),
                "stars": r.get("stargazers_count", 0),
                "description": r.get("description") or "",
                "language": lang,
                "tags": tags[:3],
                "forks": r.get("forks_count", 0),
                "url": r.get("html_url", ""),
                "created_at": r.get("created_at", ""),
            })
        return result

    # ── StackOverflow ─────────────────────────────────────────

    async def _stackoverflow_score(
        self, display_name: str
    ) -> tuple[int, Dict[str, Any]]:
        """Search SO for a user by display name and score by reputation + helper ratio."""
        detail: Dict[str, Any] = {
            "searched": display_name, "reputation": 0, "found": False,
            "answer_count": 0, "question_count": 0, "badge_count": 0, "helper_ratio": 0.0,
        }
        try:
            async with httpx.AsyncClient(timeout=_SO_TIMEOUT) as client:
                resp = await client.get(
                    f"{_SO_API}/users",
                    params={
                        "order": "desc",
                        "sort": "reputation",
                        "inname": display_name,
                        "site": "stackoverflow",
                        "pagesize": 1,
                    },
                )
            if resp.status_code in (429, 502):
                logger.warning(f"SO API rate-limited ({resp.status_code})")
                return 0, detail
            if resp.status_code != 200:
                logger.warning(f"SO API returned {resp.status_code}")
                return 0, detail

            items = resp.json().get("items", [])
            if not items:
                return 0, detail

            user = items[0]
            rep = user.get("reputation", 0)
            answer_count = user.get("answer_count", 0)
            question_count = user.get("question_count", 0)
            badge_counts = user.get("badge_counts", {})
            total_badges = sum(badge_counts.values()) if isinstance(badge_counts, dict) else 0

            # Helper ratio = answers / (answers + questions), measures community contribution
            helper_ratio = round(answer_count / max(answer_count + question_count, 1), 2)

            detail.update({
                "reputation": rep,
                "found": True,
                "user_id": user.get("user_id"),
                "profile_url": user.get("link", ""),
                "display_name": user.get("display_name", ""),
                "answer_count": answer_count,
                "question_count": question_count,
                "badge_count": total_badges,
                "helper_ratio": helper_ratio,
                "last_access_date": user.get("last_access_date"),
            })

            # Base score from reputation tiers (0-20)
            if rep >= 10_000:
                base = 20
            elif rep >= 5_000:
                base = 16
            elif rep >= 1_000:
                base = 12
            elif rep >= 200:
                base = 8
            elif rep > 0:
                base = 4
            else:
                base = 0

            # Helper-ratio bonus (0-5): rewards answering over asking
            bonus = 0
            if helper_ratio >= 0.8 and answer_count >= 10:
                bonus = 5
            elif helper_ratio >= 0.6 and answer_count >= 5:
                bonus = 3
            elif helper_ratio >= 0.4 and answer_count >= 2:
                bonus = 1

            return min(base + bonus, 25), detail
        except Exception as exc:
            logger.warning(f"StackOverflow lookup failed for {display_name}: {exc}")
            return 0, detail

    # ── Merged PRs ────────────────────────────────────────────

    async def _merged_pr_score(self, username: str) -> tuple[int, Dict[str, Any]]:
        """Count merged PRs authored by *username* in repos they don't own. (0-20)"""
        detail: Dict[str, Any] = {"merged_count": 0}
        try:
            async with httpx.AsyncClient(timeout=_GH_SEARCH_TIMEOUT) as client:
                resp = await client.get(
                    "https://api.github.com/search/issues",
                    headers={
                        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
                        "Accept": "application/vnd.github+json",
                    },
                    params={
                        "q": f"type:pr author:{username} is:merged -user:{username}",
                        "per_page": 1,
                    },
                )
            if resp.status_code in (403, 429):
                logger.warning(f"GitHub PR search rate-limited ({resp.status_code})")
                return 0, detail
            if resp.status_code != 200:
                logger.warning(f"GitHub PR search returned {resp.status_code}")
                return 0, detail

            total = resp.json().get("total_count", 0)
            detail["merged_count"] = total

            if total >= 20:
                return 20, detail
            if total >= 10:
                return 16, detail
            if total >= 5:
                return 12, detail
            if total >= 2:
                return 8, detail
            if total >= 1:
                return 4, detail
            return 0, detail
        except Exception as exc:
            logger.warning(f"Merged-PR search failed for {username}: {exc}")
            return 0, detail

    # ── Stars ─────────────────────────────────────────────────

    @staticmethod
    def _stars_score(repos: List[Dict[str, Any]]) -> tuple[int, Dict[str, Any]]:
        """Sum ``stargazers_count`` across owned (non-fork) repos. (0-20)"""
        owned = [r for r in repos if not r.get("fork", False)]
        total_stars = sum(r.get("stargazers_count", 0) for r in owned)
        detail: Dict[str, Any] = {"total_stars": total_stars, "owned_repos": len(owned)}

        if total_stars >= 500:
            return 20, detail
        if total_stars >= 100:
            return 16, detail
        if total_stars >= 30:
            return 12, detail
        if total_stars >= 10:
            return 8, detail
        if total_stars >= 1:
            return 4, detail
        return 0, detail

    # ── Blog / Personal Site ──────────────────────────────────

    async def _blog_score(self, username: str, *, gh_profile: Optional[Dict[str, Any]] = None) -> tuple[int, Dict[str, Any]]:
        """Check the ``blog`` field on the GitHub user profile. (0-20)"""
        detail: Dict[str, Any] = {"url": None, "reachable": False}
        try:
            # Use pre-fetched profile if available, otherwise fetch
            profile = gh_profile
            if profile is None:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(
                        f"https://api.github.com/users/{username}",
                        headers={
                            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
                            "Accept": "application/vnd.github+json",
                        },
                    )
                if resp.status_code != 200:
                    return 0, detail
                profile = resp.json()

            blog_url: str = profile.get("blog", "") or ""
            blog_url = blog_url.strip()
            if not blog_url:
                return 0, detail

            if not blog_url.startswith(("http://", "https://")):
                blog_url = f"https://{blog_url}"

            detail["url"] = blog_url

            # Quick reachability check
            try:
                async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                    head = await client.head(blog_url)
                if head.status_code < 400:
                    detail["reachable"] = True
                    return 20, detail
            except Exception:
                pass  # unreachable but URL exists

            return 8, detail

        except Exception as exc:
            logger.warning(f"Blog check failed for {username}: {exc}")
            return 0, detail

    # ── Recency ───────────────────────────────────────────────

    @staticmethod
    def _recency_score(
        repos: List[Dict[str, Any]],
        so_detail: Dict[str, Any],
    ) -> tuple[int, Dict[str, Any]]:
        """Score activity freshness across platforms. (0-15)

        GitHub component (0-10): most recent push within 90 days.
        StackOverflow component (0-5): last_access within 90 days if found.
        """
        now = datetime.now(timezone.utc)
        detail: Dict[str, Any] = {
            "latest_push": None,
            "github_recency_pts": 0,
            "so_recency_pts": 0,
        }

        # ── GitHub push recency ──────────────────────────────
        gh_pts = 0
        latest_push = None
        for repo in repos:
            pushed_at = repo.get("pushed_at")
            if pushed_at:
                try:
                    dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                    if latest_push is None or dt > latest_push:
                        latest_push = dt
                except (ValueError, TypeError):
                    pass

        if latest_push:
            days_ago = (now - latest_push).days
            detail["latest_push"] = latest_push.isoformat()
            if days_ago <= 30:
                gh_pts = 10
            elif days_ago <= 90:
                gh_pts = 7
            elif days_ago <= 180:
                gh_pts = 4
            elif days_ago <= 365:
                gh_pts = 2
        detail["github_recency_pts"] = gh_pts

        # ── StackOverflow recency ────────────────────────────
        so_pts = 0
        last_access = so_detail.get("last_access_date")
        if last_access and isinstance(last_access, (int, float)):
            try:
                so_last = datetime.fromtimestamp(last_access, tz=timezone.utc)
                so_days = (now - so_last).days
                if so_days <= 90:
                    so_pts = 5
                elif so_days <= 180:
                    so_pts = 3
                elif so_days <= 365:
                    so_pts = 1
            except (ValueError, OSError):
                pass
        elif so_detail.get("found"):
            # User found but no access date → minimal credit
            so_pts = 1
        detail["so_recency_pts"] = so_pts

        total = min(gh_pts + so_pts, 15)
        return total, detail
