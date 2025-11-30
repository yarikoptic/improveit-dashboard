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

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_fetch_merged_pr_has_merged_by(self, client: GitHubClient) -> None:
        """Test that merged PRs have merged_by field."""
        # pydicom/pydicom#2169 is a merged PR
        pr_data, _, modified = client.fetch_pr_details(
            owner="pydicom",
            repo="pydicom",
            pr_number=2169,
        )

        assert modified is True
        assert pr_data is not None
        assert pr_data["merged"] is True
        assert "merged_by" in pr_data
        assert pr_data["merged_by"] is not None
        assert "login" in pr_data["merged_by"]

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_fetch_pr_status_for_open_pr(self, client: GitHubClient) -> None:
        """Test fetching CI/merge status for an open PR (if one exists)."""
        # Search for an open PR to test
        results = client.search_user_prs(
            username="yarikoptic",
            keywords=["codespell"],
        )

        # Find an open PR
        open_pr = None
        for item in results:
            if item.get("state") == "open":
                # Extract repo from repository_url
                repo_url = item.get("repository_url", "")
                parts = repo_url.rstrip("/").split("/")
                if len(parts) >= 2:
                    owner = parts[-2]
                    repo = parts[-1]
                    pr_number = item["number"]

                    # Fetch details to get head SHA
                    pr_data, _, _ = client.fetch_pr_details(owner, repo, pr_number)
                    if pr_data:
                        open_pr = (owner, repo, pr_number, pr_data)
                        break

        if open_pr is None:
            pytest.skip("No open PRs found to test CI status")

        owner, repo, pr_number, pr_data = open_pr
        head_sha = pr_data.get("head", {}).get("sha")

        if head_sha:
            status = client.fetch_pr_status(owner, repo, pr_number, head_sha)
            assert "has_conflicts" in status
            assert "ci_status" in status
            # CI status should be one of success, failure, pending, or None
            assert status["ci_status"] in ("success", "failure", "pending", None)

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_fetch_branch_status(self, client: GitHubClient) -> None:
        """Test fetching main branch CI status."""
        status = client.fetch_branch_status(
            owner="pydicom",
            repo="pydicom",
        )

        # Status should be success, failure, pending, or None
        assert status in ("success", "failure", "pending", None)
