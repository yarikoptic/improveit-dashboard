"""Unit tests for view generation."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from improveit_dashboard.models.pull_request import PullRequest
from improveit_dashboard.models.repository import Repository
from improveit_dashboard.views.dashboard import generate_dashboard
from improveit_dashboard.views.reports import generate_user_reports


class TestDashboardGeneration:
    """Tests for dashboard generation."""

    @pytest.mark.ai_generated
    def test_generate_empty_dashboard(self, tmp_path: Path) -> None:
        """Test generating dashboard with no data."""
        output_path = tmp_path / "README.md"
        generate_dashboard({}, output_path, ["yarikoptic"])

        assert output_path.exists()
        content = output_path.read_text()
        assert "ImprovIt Dashboard" in content
        assert "yarikoptic" in content

    @pytest.mark.ai_generated
    def test_generate_dashboard_with_data(
        self, tmp_path: Path, sample_repository: Repository
    ) -> None:
        """Test generating dashboard with data."""
        output_path = tmp_path / "README.md"
        repositories = {sample_repository.full_name: sample_repository}

        generate_dashboard(repositories, output_path, ["yarikoptic"])

        assert output_path.exists()
        content = output_path.read_text()
        assert "ImprovIt Dashboard" in content
        assert "1" in content  # At least 1 PR

    @pytest.mark.ai_generated
    def test_dashboard_contains_user_link(
        self, tmp_path: Path, sample_repository: Repository
    ) -> None:
        """Test dashboard contains link to user details."""
        output_path = tmp_path / "README.md"
        repositories = {sample_repository.full_name: sample_repository}

        generate_dashboard(repositories, output_path, ["yarikoptic"])

        content = output_path.read_text()
        assert "READMEs/yarikoptic.md" in content


class TestUserReports:
    """Tests for per-user report generation."""

    @pytest.mark.ai_generated
    def test_generate_user_report(self, tmp_path: Path, sample_repository: Repository) -> None:
        """Test generating user report."""
        output_dir = tmp_path / "READMEs"
        repositories = {sample_repository.full_name: sample_repository}

        paths = generate_user_reports(repositories, output_dir, ["yarikoptic"])

        assert len(paths) == 1
        assert paths[0].exists()

        content = paths[0].read_text()
        assert "yarikoptic" in content
        assert "kestra-io/kestra" in content

    @pytest.mark.ai_generated
    def test_report_groups_by_status(self, tmp_path: Path) -> None:
        """Test report groups PRs by status."""
        output_dir = tmp_path / "READMEs"

        # Create PRs with different statuses
        repo = Repository(
            owner="test",
            name="repo",
            platform="github",
            url="https://github.com/test/repo",
        )

        for i, status in enumerate(["open", "merged", "closed"]):
            pr = PullRequest(
                number=i + 1,
                repository="test/repo",
                platform="github",
                url=f"https://github.com/test/repo/pull/{i + 1}",
                tool="codespell",
                title=f"PR {i + 1}",
                author="testuser",
                created_at=datetime(2025, 1, 1 + i, tzinfo=UTC),
                updated_at=datetime(2025, 1, 2 + i, tzinfo=UTC),
                status=status,
            )
            if status == "merged":
                pr.merged_at = datetime(2025, 1, 3, tzinfo=UTC)
            repo.add_pr(pr)

        paths = generate_user_reports({repo.full_name: repo}, output_dir, ["testuser"])

        content = paths[0].read_text()
        assert "Open PRs" in content
        assert "Merged PRs" in content
        assert "Closed PRs" in content

    @pytest.mark.ai_generated
    def test_report_shows_needs_response(self, tmp_path: Path) -> None:
        """Test report shows needs response section."""
        output_dir = tmp_path / "READMEs"

        repo = Repository(
            owner="test",
            name="repo",
            platform="github",
            url="https://github.com/test/repo",
        )

        pr = PullRequest(
            number=1,
            repository="test/repo",
            platform="github",
            url="https://github.com/test/repo/pull/1",
            tool="codespell",
            title="Test PR",
            author="testuser",
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
            updated_at=datetime(2025, 1, 2, tzinfo=UTC),
            status="open",
            response_status="awaiting_submitter",
            days_awaiting_submitter=5,
            last_developer_comment_body="Please update the config",
        )
        repo.add_pr(pr)

        paths = generate_user_reports({repo.full_name: repo}, output_dir, ["testuser"])

        content = paths[0].read_text()
        assert "Needs Your Response" in content
        assert "waiting 5 days" in content
