"""Shared pytest fixtures for improveit-dashboard tests."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock

import pytest

from improveit_dashboard.models.pull_request import PullRequest
from improveit_dashboard.models.repository import Repository


@pytest.fixture
def sample_pr_data() -> dict[str, Any]:
    """Sample PR data as returned by GitHub API."""
    return {
        "number": 12912,
        "title": "Add codespell support (config+workflow)",
        "state": "open",
        "draft": False,
        "merged": False,
        "user": {
            "login": "yarikoptic",
            "type": "User",
        },
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-20T14:30:00Z",
        "merged_at": None,
        "closed_at": None,
        "commits": 1,
        "changed_files": 2,
        "html_url": "https://github.com/kestra-io/kestra/pull/12912",
        "base": {
            "repo": {
                "full_name": "kestra-io/kestra",
                "owner": {"login": "kestra-io"},
                "name": "kestra",
            }
        },
    }


@pytest.fixture
def sample_merged_pr_data(sample_pr_data: dict[str, Any]) -> dict[str, Any]:
    """Sample merged PR data."""
    data = sample_pr_data.copy()
    data.update(
        {
            "state": "closed",
            "merged": True,
            "merged_at": "2025-01-20T14:30:00Z",
        }
    )
    return data


@pytest.fixture
def sample_comment_data() -> list[dict[str, Any]]:
    """Sample comment data as returned by GitHub API."""
    return [
        {
            "id": 1001,
            "user": {"login": "yarikoptic", "type": "User"},
            "body": "This PR adds codespell support.",
            "created_at": "2025-01-15T10:05:00Z",
            "updated_at": "2025-01-15T10:05:00Z",
        },
        {
            "id": 1002,
            "user": {"login": "maintainer-user", "type": "User"},
            "body": "Looks good! Can you add a config file?",
            "created_at": "2025-01-16T09:00:00Z",
            "updated_at": "2025-01-16T09:00:00Z",
        },
        {
            "id": 1003,
            "user": {"login": "github-actions[bot]", "type": "Bot"},
            "body": "All checks passed!",
            "created_at": "2025-01-16T09:05:00Z",
            "updated_at": "2025-01-16T09:05:00Z",
        },
    ]


@pytest.fixture
def sample_files_data() -> list[dict[str, Any]]:
    """Sample file data as returned by GitHub API."""
    return [
        {
            "filename": ".github/workflows/codespell.yml",
            "status": "added",
            "additions": 20,
            "deletions": 0,
        },
        {
            "filename": ".codespellrc",
            "status": "added",
            "additions": 5,
            "deletions": 0,
        },
    ]


@pytest.fixture
def sample_pull_request() -> PullRequest:
    """Sample PullRequest model instance."""
    return PullRequest(
        number=12912,
        repository="kestra-io/kestra",
        platform="github",
        url="https://github.com/kestra-io/kestra/pull/12912",
        tool="codespell",
        title="Add codespell support (config+workflow)",
        author="yarikoptic",
        created_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
        updated_at=datetime(2025, 1, 20, 14, 30, 0, tzinfo=UTC),
        status="open",
        commit_count=1,
        files_changed=2,
    )


@pytest.fixture
def sample_repository(sample_pull_request: PullRequest) -> Repository:
    """Sample Repository model instance."""
    repo = Repository(
        owner="kestra-io",
        name="kestra",
        platform="github",
        url="https://github.com/kestra-io/kestra",
    )
    repo.add_pr(sample_pull_request)
    return repo


@pytest.fixture
def mock_response() -> Mock:
    """Create a mock requests.Response."""

    def _make_response(
        status_code: int = 200,
        json_data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Mock:
        response = Mock()
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.headers = headers or {
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Reset": "1700000000",
        }
        response.raise_for_status = Mock()
        return response

    return _make_response
