"""Unit tests for view generation."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from improveit_dashboard.models.pull_request import PullRequest
from improveit_dashboard.models.repository import Repository
from improveit_dashboard.utils.markdown import (
    sanitize_and_truncate,
    sanitize_for_table,
    truncate,
    write_if_changed,
)
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
        """Test generating user report with per-status files."""
        output_dir = tmp_path / "READMEs"
        repositories = {sample_repository.full_name: sample_repository}

        paths = generate_user_reports(repositories, output_dir, ["yarikoptic"])

        # Should generate 5 files: main + 4 status files
        assert len(paths) == 5
        assert all(p.exists() for p in paths)

        # Check main summary file
        main_path = output_dir / "yarikoptic.md"
        assert main_path.exists()
        content = main_path.read_text()
        assert "yarikoptic" in content

        # Check per-status files exist
        user_dir = output_dir / "yarikoptic"
        assert (user_dir / "draft.md").exists()
        assert (user_dir / "open.md").exists()
        assert (user_dir / "merged.md").exists()
        assert (user_dir / "closed.md").exists()

        # PR should be in the open status file (sample_repository has an open PR)
        open_content = (user_dir / "open.md").read_text()
        assert "kestra-io/kestra" in open_content

    @pytest.mark.ai_generated
    def test_report_groups_by_status(self, tmp_path: Path) -> None:
        """Test report creates separate files for each status."""
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

        generate_user_reports({repo.full_name: repo}, output_dir, ["testuser"])

        # Main file should have links to per-status files
        main_content = (output_dir / "testuser.md").read_text()
        assert "testuser/open.md" in main_content
        assert "testuser/merged.md" in main_content
        assert "testuser/closed.md" in main_content

        # Per-status files should have the PR tables
        user_dir = output_dir / "testuser"
        open_content = (user_dir / "open.md").read_text()
        assert "Open PRs" in open_content
        assert "PR 1" in open_content

        merged_content = (user_dir / "merged.md").read_text()
        assert "Merged PRs" in merged_content
        assert "PR 2" in merged_content

        closed_content = (user_dir / "closed.md").read_text()
        assert "Closed PRs" in closed_content
        assert "PR 3" in closed_content

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


class TestMarkdownSanitization:
    """Tests for markdown sanitization utilities."""

    @pytest.mark.ai_generated
    def test_sanitize_removes_newlines(self) -> None:
        """Test that newlines are converted to spaces."""
        text = "Line 1\nLine 2\r\nLine 3\rLine 4"
        result = sanitize_for_table(text)
        assert "\n" not in result
        assert "\r" not in result
        assert result == "Line 1 Line 2 Line 3 Line 4"

    @pytest.mark.ai_generated
    def test_sanitize_escapes_pipe_characters(self) -> None:
        """Test that pipe characters are escaped."""
        text = "Column 1 | Column 2 | Column 3"
        result = sanitize_for_table(text)
        assert result == "Column 1 \\| Column 2 \\| Column 3"

    @pytest.mark.ai_generated
    def test_sanitize_collapses_whitespace(self) -> None:
        """Test that multiple spaces are collapsed."""
        text = "Word1    Word2     Word3"
        result = sanitize_for_table(text)
        assert result == "Word1 Word2 Word3"

    @pytest.mark.ai_generated
    def test_sanitize_strips_leading_trailing(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        text = "  content  "
        result = sanitize_for_table(text)
        assert result == "content"

    @pytest.mark.ai_generated
    def test_sanitize_complex_markdown_comment(self) -> None:
        """Test sanitization of complex markdown from GitHub comment."""
        # Real-world example with blockquotes, newlines, and markdown
        text = "> > * Sign DCO\r\n> \r\n> done\r\n\r\nThanks"
        result = sanitize_for_table(text)
        # Should be single line with no newlines
        assert "\n" not in result
        assert "\r" not in result
        # Should preserve the content
        assert "Sign DCO" in result
        assert "done" in result
        assert "Thanks" in result

    @pytest.mark.ai_generated
    def test_truncate_short_text(self) -> None:
        """Test truncation of short text does nothing."""
        text = "short"
        result = truncate(text, 10)
        assert result == "short"

    @pytest.mark.ai_generated
    def test_truncate_long_text(self) -> None:
        """Test truncation adds ellipsis."""
        text = "this is a very long text"
        result = truncate(text, 10)
        assert result == "this is..."
        assert len(result) == 10

    @pytest.mark.ai_generated
    def test_truncate_exact_length(self) -> None:
        """Test text at exact max length is not truncated."""
        text = "exactly10!"
        result = truncate(text, 10)
        assert result == "exactly10!"

    @pytest.mark.ai_generated
    def test_sanitize_and_truncate_combined(self) -> None:
        """Test combined sanitization and truncation."""
        text = "Line 1\nLine 2 | more content here that is long"
        result = sanitize_and_truncate(text, 20)
        # Should be sanitized and truncated
        assert "\n" not in result
        assert len(result) <= 20
        assert result.endswith("...")

    @pytest.mark.ai_generated
    def test_sanitize_empty_string(self) -> None:
        """Test sanitization of empty string."""
        result = sanitize_for_table("")
        assert result == ""

    @pytest.mark.ai_generated
    def test_sanitize_preserves_markdown_links(self) -> None:
        """Test that markdown links are preserved but made safe."""
        # Links in comments should work but | inside would break tables
        text = "[link](https://example.com)"
        result = sanitize_for_table(text)
        assert result == "[link](https://example.com)"


class TestWriteIfChanged:
    """Tests for write_if_changed utility."""

    @pytest.mark.ai_generated
    def test_write_new_file(self, tmp_path: Path) -> None:
        """Test writing a new file always succeeds."""
        file_path = tmp_path / "new.md"
        content = "# Title\n\n*Last updated: 2025-01-01 12:00 UTC*\n\nContent\n"

        result = write_if_changed(file_path, content)

        assert result is True
        assert file_path.exists()
        assert file_path.read_text() == content

    @pytest.mark.ai_generated
    def test_skip_when_only_timestamp_changed(self, tmp_path: Path) -> None:
        """Test file is not written when only timestamp changed."""
        file_path = tmp_path / "test.md"
        original = "# Title\n\n*Last updated: 2025-01-01 12:00 UTC*\n\nContent\n"
        file_path.write_text(original)

        new_content = "# Title\n\n*Last updated: 2025-12-02 18:30 UTC*\n\nContent\n"
        result = write_if_changed(file_path, new_content)

        assert result is False
        # File should still have original content
        assert file_path.read_text() == original

    @pytest.mark.ai_generated
    def test_write_when_content_changed(self, tmp_path: Path) -> None:
        """Test file is written when actual content changed."""
        file_path = tmp_path / "test.md"
        original = "# Title\n\n*Last updated: 2025-01-01 12:00 UTC*\n\nOld content\n"
        file_path.write_text(original)

        new_content = "# Title\n\n*Last updated: 2025-12-02 18:30 UTC*\n\nNew content\n"
        result = write_if_changed(file_path, new_content)

        assert result is True
        assert file_path.read_text() == new_content

    @pytest.mark.ai_generated
    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Test parent directories are created if they don't exist."""
        file_path = tmp_path / "nested" / "dir" / "file.md"
        content = "# Content\n"

        result = write_if_changed(file_path, content)

        assert result is True
        assert file_path.exists()
        assert file_path.read_text() == content
