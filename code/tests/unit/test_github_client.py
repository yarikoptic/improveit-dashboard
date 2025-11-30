"""Unit tests for GitHub client (mocked)."""

from typing import Any
from unittest.mock import patch

import pytest

from improveit_dashboard.controllers.github_client import GitHubClient
from improveit_dashboard.utils.rate_limit import RateLimitError


class TestGitHubClient:
    """Unit tests for GitHubClient with mocked requests."""

    @pytest.fixture
    def client(self) -> GitHubClient:
        """Create client with fake token."""
        return GitHubClient(token="fake-token")

    @pytest.mark.ai_generated
    def test_client_initialization(self, client: GitHubClient) -> None:
        """Test client initialization."""
        assert client.token == "fake-token"
        assert client.api_calls == 0
        assert "Authorization" in client.session.headers

    @pytest.mark.ai_generated
    def test_fetch_pr_success(
        self,
        client: GitHubClient,
        mock_response: Any,
        sample_pr_data: dict[str, Any],
    ) -> None:
        """Test successful PR fetch."""
        response = mock_response(
            status_code=200,
            json_data=sample_pr_data,
            headers={
                "ETag": 'W/"abc123"',
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Reset": "1700000000",
            },
        )

        with patch.object(client.session, "request", return_value=response):
            pr_data, etag, modified = client.fetch_pr_details(
                owner="kestra-io",
                repo="kestra",
                pr_number=12912,
            )

        assert modified is True
        assert pr_data is not None
        assert pr_data["number"] == 12912
        assert etag == 'W/"abc123"'
        assert client.api_calls == 1

    @pytest.mark.ai_generated
    def test_fetch_pr_not_modified(self, client: GitHubClient, mock_response: Any) -> None:
        """Test PR fetch with 304 response."""
        response = mock_response(status_code=304)

        with patch.object(client.session, "request", return_value=response):
            pr_data, etag, modified = client.fetch_pr_details(
                owner="kestra-io",
                repo="kestra",
                pr_number=12912,
                etag='W/"existing"',
            )

        assert modified is False
        assert pr_data is None
        assert etag == 'W/"existing"'

    @pytest.mark.ai_generated
    def test_fetch_pr_not_found(self, client: GitHubClient, mock_response: Any) -> None:
        """Test PR fetch with 404 response."""
        response = mock_response(status_code=404)

        with patch.object(client.session, "request", return_value=response):
            pr_data, etag, modified = client.fetch_pr_details(
                owner="test",
                repo="repo",
                pr_number=999999,
            )

        assert modified is False
        assert pr_data is None

    @pytest.mark.ai_generated
    def test_search_prs(self, client: GitHubClient, mock_response: Any) -> None:
        """Test PR search."""
        search_results = {
            "total_count": 1,
            "items": [
                {
                    "number": 123,
                    "title": "Add codespell",
                    "repository_url": "https://api.github.com/repos/test/repo",
                }
            ],
        }
        response = mock_response(status_code=200, json_data=search_results)

        with patch.object(client.session, "request", return_value=response):
            results = client.search_user_prs(
                username="testuser",
                keywords=["codespell"],
            )

        assert len(results) == 1
        assert results[0]["number"] == 123

    @pytest.mark.ai_generated
    def test_search_prs_keyword_filter(self, client: GitHubClient, mock_response: Any) -> None:
        """Test PR search filters by keywords."""
        search_results = {
            "total_count": 2,
            "items": [
                {"number": 1, "title": "Add codespell CI"},
                {"number": 2, "title": "Fix typo"},  # Should be filtered out
            ],
        }
        response = mock_response(status_code=200, json_data=search_results)

        with patch.object(client.session, "request", return_value=response):
            results = client.search_user_prs(
                username="testuser",
                keywords=["codespell"],
            )

        assert len(results) == 1
        assert results[0]["number"] == 1

    @pytest.mark.ai_generated
    def test_fetch_comments(
        self, client: GitHubClient, mock_response: Any, sample_comment_data: list
    ) -> None:
        """Test fetching comments."""
        response = mock_response(status_code=200, json_data=sample_comment_data)

        with patch.object(client.session, "request", return_value=response):
            comments = client.fetch_pr_comments(
                owner="test",
                repo="repo",
                pr_number=1,
            )

        assert len(comments) == 3

    @pytest.mark.ai_generated
    def test_fetch_files(
        self, client: GitHubClient, mock_response: Any, sample_files_data: list
    ) -> None:
        """Test fetching files."""
        response = mock_response(status_code=200, json_data=sample_files_data)

        with patch.object(client.session, "request", return_value=response):
            files = client.fetch_pr_files(
                owner="test",
                repo="repo",
                pr_number=1,
            )

        assert len(files) == 2

    @pytest.mark.ai_generated
    def test_rate_limit_handling(
        self, client: GitHubClient, mock_response: Any, sample_pr_data: dict
    ) -> None:
        """Test rate limit is tracked."""
        response = mock_response(
            status_code=200,
            json_data=sample_pr_data,
            headers={
                "X-RateLimit-Remaining": "100",
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Reset": "1700000000",
            },
        )

        with patch.object(client.session, "request", return_value=response):
            client.fetch_pr_details("owner", "repo", 1)

        status = client.get_rate_limit_status()
        assert status["remaining"] == 100

    @pytest.mark.ai_generated
    def test_rate_limit_critical(self, client: GitHubClient, mock_response: Any) -> None:
        """Test rate limit critical threshold raises error."""
        # Set threshold high so it triggers
        client.rate_limit.critical_threshold = 100

        response = mock_response(
            status_code=200,
            json_data={},
            headers={
                "X-RateLimit-Remaining": "5",
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Reset": "1700000000",
            },
        )

        with patch.object(client.session, "request", return_value=response):
            with pytest.raises(RateLimitError):
                client.fetch_pr_details("owner", "repo", 1)
