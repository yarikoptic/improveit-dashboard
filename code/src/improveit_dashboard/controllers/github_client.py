"""GitHub API client for PR discovery and data fetching."""

from datetime import datetime
from typing import Any, Literal
from urllib.parse import urljoin

import requests

from improveit_dashboard.utils.logging import get_logger
from improveit_dashboard.utils.rate_limit import RateLimitHandler

CIStatus = Literal["success", "failure", "pending"]

logger = get_logger(__name__)


class GitHubClient:
    """Client for GitHub REST API v3.

    Handles authentication, rate limiting, pagination, and conditional requests.
    """

    BASE_URL = "https://api.github.com"
    USER_AGENT = "improveit-dashboard/0.1.0"

    def __init__(
        self,
        token: str,
        rate_limit_threshold: int = 100,
    ):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token
            rate_limit_threshold: Pause when remaining calls fall below this
        """
        self.token = token
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": self.USER_AGENT,
            }
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

        self.rate_limit = RateLimitHandler(threshold=rate_limit_threshold)
        self.api_calls = 0

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        """Make an API request.

        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base URL)
            params: Query parameters
            headers: Additional headers

        Returns:
            Response object

        Raises:
            requests.HTTPError: On API errors (except rate limit)
        """
        url = urljoin(self.BASE_URL + "/", endpoint.lstrip("/"))

        req_headers = {}
        if headers:
            req_headers.update(headers)

        response = self.session.request(
            method,
            url,
            params=params,
            headers=req_headers,
        )

        self.api_calls += 1

        # Update rate limit (don't wait yet - caller decides)
        self.rate_limit.update_from_response(response)

        return response

    def search_user_prs(
        self,
        username: str,
        updated_since: datetime | None = None,
        keywords: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for PRs authored by a user.

        Args:
            username: GitHub username
            updated_since: Only return PRs updated after this date
            keywords: Filter by title keywords (any match)

        Returns:
            List of PR search results
        """
        # Build search query
        query_parts = [
            "is:pr",
            f"author:{username}",
        ]

        if updated_since:
            date_str = updated_since.strftime("%Y-%m-%d")
            query_parts.append(f"updated:>{date_str}")

        query = " ".join(query_parts)

        logger.info(f"Searching PRs for user {username}: {query}")

        all_items: list[dict[str, Any]] = []
        page = 1

        while True:
            response = self._request(
                "GET",
                "/search/issues",
                params={
                    "q": query,
                    "per_page": 100,
                    "page": page,
                    "sort": "updated",
                    "order": "desc",
                },
            )

            # Check rate limit after each request
            self.rate_limit.check_and_wait(response)

            if response.status_code == 422:
                logger.warning(f"Invalid search query: {query}")
                break

            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])

            if not items:
                break

            # Filter by keywords if specified
            if keywords:
                filtered = []
                for item in items:
                    title_lower = item.get("title", "").lower()
                    if any(kw.lower() in title_lower for kw in keywords):
                        filtered.append(item)
                items = filtered

            all_items.extend(items)
            logger.debug(f"Page {page}: found {len(items)} matching PRs")

            # Check for next page
            if len(data.get("items", [])) < 100:
                break
            page += 1

        logger.info(f"Found {len(all_items)} PRs for {username}")
        return all_items

    def fetch_pr_details(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        etag: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, bool]:
        """Fetch PR details with conditional request support.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            etag: Previous ETag for conditional request

        Returns:
            Tuple of (pr_data, new_etag, modified)
            - pr_data: PR data dict or None if not modified
            - new_etag: New ETag value
            - modified: True if data was modified, False if 304
        """
        headers = {}
        if etag:
            headers["If-None-Match"] = etag

        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pr_number}",
            headers=headers,
        )

        self.rate_limit.check_and_wait(response)

        # Not modified
        if response.status_code == 304:
            return None, etag, False

        # Not found
        if response.status_code == 404:
            logger.warning(f"PR not found: {owner}/{repo}#{pr_number}")
            return None, None, False

        response.raise_for_status()

        new_etag = response.headers.get("ETag")
        return response.json(), new_etag, True

    def fetch_pr_comments(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> list[dict[str, Any]]:
        """Fetch all comments on a PR.

        Uses the issues API endpoint as PR comments are issue comments.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            List of comment data dicts
        """
        all_comments: list[dict[str, Any]] = []
        page = 1

        while True:
            response = self._request(
                "GET",
                f"/repos/{owner}/{repo}/issues/{pr_number}/comments",
                params={
                    "per_page": 100,
                    "page": page,
                },
            )

            self.rate_limit.check_and_wait(response)

            if response.status_code == 404:
                logger.warning(f"Comments not found: {owner}/{repo}#{pr_number}")
                break

            response.raise_for_status()

            comments = response.json()
            if not comments:
                break

            all_comments.extend(comments)

            if len(comments) < 100:
                break
            page += 1

        return all_comments

    def fetch_pr_files(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> list[dict[str, Any]]:
        """Fetch files changed in a PR.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            List of file data dicts
        """
        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
            params={"per_page": 100},
        )

        self.rate_limit.check_and_wait(response)

        if response.status_code == 404:
            logger.warning(f"PR files not found: {owner}/{repo}#{pr_number}")
            return []

        response.raise_for_status()

        result: list[dict[str, Any]] = response.json()
        return result

    def fetch_repository(
        self,
        owner: str,
        repo: str,
    ) -> dict[str, Any] | None:
        """Fetch repository metadata.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository data dict or None if not accessible
        """
        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}",
        )

        self.rate_limit.check_and_wait(response)

        if response.status_code == 404:
            logger.warning(f"Repository not found: {owner}/{repo}")
            return None

        if response.status_code == 403:
            logger.warning(f"Repository access denied: {owner}/{repo}")
            return None

        response.raise_for_status()

        result: dict[str, Any] | None = response.json()
        return result

    def fetch_pr_status(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        head_sha: str,
    ) -> dict[str, Any]:
        """Fetch CI/check status for a PR.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            head_sha: SHA of the PR head commit

        Returns:
            Dict with ci_status, main_branch_ci, codespell_workflow_ci, has_conflicts
        """
        result: dict[str, Any] = {
            "ci_status": None,
            "main_branch_ci": None,
            "codespell_workflow_ci": None,
            "has_conflicts": False,
        }

        # Get combined status (legacy status API)
        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/commits/{head_sha}/status",
        )
        self.rate_limit.check_and_wait(response)

        if response.status_code == 200:
            data = response.json()
            state = data.get("state")
            if state == "success":
                result["ci_status"] = "success"
            elif state == "failure" or state == "error":
                result["ci_status"] = "failure"
            elif state == "pending":
                result["ci_status"] = "pending"

        # Get check runs (GitHub Actions, etc.)
        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/commits/{head_sha}/check-runs",
            params={"per_page": 100},
        )
        self.rate_limit.check_and_wait(response)

        if response.status_code == 200:
            data = response.json()
            check_runs = data.get("check_runs", [])

            # Determine overall CI status from check runs
            if check_runs:
                conclusions = [cr.get("conclusion") for cr in check_runs if cr.get("conclusion")]
                statuses = [cr.get("status") for cr in check_runs]

                if all(c == "success" for c in conclusions if c):
                    if result["ci_status"] != "failure":
                        result["ci_status"] = "success"
                elif any(c in ("failure", "cancelled", "timed_out") for c in conclusions):
                    result["ci_status"] = "failure"
                elif any(s in ("queued", "in_progress") for s in statuses):
                    if result["ci_status"] is None:
                        result["ci_status"] = "pending"

                # Look for codespell workflow specifically
                for cr in check_runs:
                    name = cr.get("name", "").lower()
                    if "codespell" in name:
                        conclusion = cr.get("conclusion")
                        if conclusion == "success":
                            result["codespell_workflow_ci"] = "success"
                        elif conclusion in ("failure", "cancelled", "timed_out"):
                            result["codespell_workflow_ci"] = "failure"
                        elif cr.get("status") in ("queued", "in_progress"):
                            result["codespell_workflow_ci"] = "pending"
                        break

        # Get PR mergeable state (for conflicts)
        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pr_number}",
        )
        self.rate_limit.check_and_wait(response)

        if response.status_code == 200:
            data = response.json()
            # mergeable can be null if GitHub is still computing
            mergeable = data.get("mergeable")
            mergeable_state = data.get("mergeable_state")

            if mergeable is False or mergeable_state == "dirty":
                result["has_conflicts"] = True

        return result

    def fetch_branch_status(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
    ) -> CIStatus | None:
        """Fetch CI status of a branch.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (default: main)

        Returns:
            CI status: "success", "failure", "pending", or None
        """
        # Get branch info to find head SHA
        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/branches/{branch}",
        )
        self.rate_limit.check_and_wait(response)

        if response.status_code == 404:
            # Try "master" as fallback
            if branch == "main":
                return self.fetch_branch_status(owner, repo, "master")
            return None

        if response.status_code != 200:
            return None

        data = response.json()
        head_sha = data.get("commit", {}).get("sha")
        if not head_sha:
            return None

        # Get combined status
        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/commits/{head_sha}/status",
        )
        self.rate_limit.check_and_wait(response)

        if response.status_code != 200:
            return None

        data = response.json()
        state = data.get("state")

        if state == "success":
            return "success"
        elif state in ("failure", "error"):
            return "failure"
        elif state == "pending":
            return "pending"

        return None

    def get_rate_limit_status(self) -> dict[str, int]:
        """Get current rate limit status.

        Returns:
            Dict with remaining, limit, reset_timestamp, api_calls
        """
        status = self.rate_limit.get_status()
        status["api_calls"] = self.api_calls
        return status
