"""Integration tests for GitHub API.

These tests require GITHUB_TOKEN environment variable to be set.
They test against real GitHub API with sample PRs.
"""

import os

import pytest

from improveit_dashboard.controllers.github_client import GitHubClient

# Skip all tests if GITHUB_TOKEN not set
pytestmark = pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"),
    reason="GITHUB_TOKEN not set",
)


class TestGitHubClientIntegration:
    """Integration tests for GitHubClient against live API."""

    @pytest.fixture
    def client(self) -> GitHubClient:
        """Create authenticated GitHub client."""
        token = os.environ["GITHUB_TOKEN"]
        return GitHubClient(token=token)

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_fetch_kestra_pr(self, client: GitHubClient) -> None:
        """Test fetching kestra-io/kestra#12912."""
        pr_data, etag, modified = client.fetch_pr_details(
            owner="kestra-io",
            repo="kestra",
            pr_number=12912,
        )

        assert modified is True
        assert pr_data is not None
        assert pr_data["number"] == 12912
        assert "codespell" in pr_data["title"].lower() or "spell" in pr_data["title"].lower()
        assert pr_data["user"]["login"] == "yarikoptic"
        assert etag is not None

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_fetch_pydicom_pr(self, client: GitHubClient) -> None:
        """Test fetching pydicom/pydicom#2169."""
        pr_data, etag, modified = client.fetch_pr_details(
            owner="pydicom",
            repo="pydicom",
            pr_number=2169,
        )

        assert modified is True
        assert pr_data is not None
        assert pr_data["number"] == 2169
        # This PR is about codespell
        assert pr_data["user"]["login"] == "yarikoptic"

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_conditional_request(self, client: GitHubClient) -> None:
        """Test conditional request with ETag."""
        # First request
        pr_data1, etag, _ = client.fetch_pr_details(
            owner="kestra-io",
            repo="kestra",
            pr_number=12912,
        )
        assert etag is not None

        # Second request with ETag - should get 304
        pr_data2, _, modified = client.fetch_pr_details(
            owner="kestra-io",
            repo="kestra",
            pr_number=12912,
            etag=etag,
        )

        # Should not be modified (same ETag)
        assert modified is False
        assert pr_data2 is None

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_fetch_pr_comments(self, client: GitHubClient) -> None:
        """Test fetching PR comments."""
        comments = client.fetch_pr_comments(
            owner="kestra-io",
            repo="kestra",
            pr_number=12912,
        )

        # Should have at least some comments
        assert isinstance(comments, list)
        # Each comment should have required fields
        for comment in comments:
            assert "id" in comment
            assert "user" in comment
            assert "body" in comment
            assert "created_at" in comment

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_fetch_pr_files(self, client: GitHubClient) -> None:
        """Test fetching PR files."""
        files = client.fetch_pr_files(
            owner="kestra-io",
            repo="kestra",
            pr_number=12912,
        )

        assert isinstance(files, list)
        assert len(files) > 0

        # Each file should have required fields
        for file in files:
            assert "filename" in file
            assert "status" in file

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_search_user_prs(self, client: GitHubClient) -> None:
        """Test searching PRs by user."""
        results = client.search_user_prs(
            username="yarikoptic",
            keywords=["codespell"],
        )

        # Should find some PRs
        assert isinstance(results, list)
        # Each result should have PR info
        for item in results:
            assert "number" in item
            assert "title" in item
            assert "user" in item

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_fetch_nonexistent_pr(self, client: GitHubClient) -> None:
        """Test fetching non-existent PR."""
        pr_data, etag, modified = client.fetch_pr_details(
            owner="kestra-io",
            repo="kestra",
            pr_number=999999999,
        )

        assert pr_data is None
        assert modified is False

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_rate_limit_tracking(self, client: GitHubClient) -> None:
        """Test that rate limit is tracked."""
        client.fetch_pr_details(
            owner="kestra-io",
            repo="kestra",
            pr_number=12912,
        )

        status = client.get_rate_limit_status()
        assert "remaining" in status
        assert "limit" in status
        assert status["remaining"] > 0
        assert status["api_calls"] >= 1
