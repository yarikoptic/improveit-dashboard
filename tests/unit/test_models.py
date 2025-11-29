"""Unit tests for data models."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from improveit_dashboard.models.comment import Comment
from improveit_dashboard.models.config import Configuration
from improveit_dashboard.models.discovery_run import DiscoveryRun
from improveit_dashboard.models.pull_request import PullRequest
from improveit_dashboard.models.repository import Repository


class TestPullRequest:
    """Tests for PullRequest model."""

    @pytest.mark.ai_generated
    def test_create_basic_pr(self) -> None:
        """Test creating a basic PR."""
        pr = PullRequest(
            number=123,
            repository="owner/repo",
            platform="github",
            url="https://github.com/owner/repo/pull/123",
            tool="codespell",
            title="Add codespell",
            author="testuser",
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
            updated_at=datetime(2025, 1, 2, tzinfo=UTC),
        )
        assert pr.number == 123
        assert pr.repository == "owner/repo"
        assert pr.status == "open"
        assert pr.is_active is True

    @pytest.mark.ai_generated
    def test_pr_validation_valid(self, sample_pull_request: PullRequest) -> None:
        """Test validation passes for valid PR."""
        errors = sample_pull_request.validate()
        assert errors == []

    @pytest.mark.ai_generated
    def test_pr_validation_invalid_status(self, sample_pull_request: PullRequest) -> None:
        """Test validation fails for invalid status."""
        sample_pull_request.status = "invalid"  # type: ignore
        errors = sample_pull_request.validate()
        assert any("Invalid status" in e for e in errors)

    @pytest.mark.ai_generated
    def test_pr_validation_merged_without_date(self, sample_pull_request: PullRequest) -> None:
        """Test validation fails for merged PR without merged_at."""
        sample_pull_request.status = "merged"
        sample_pull_request.merged_at = None
        errors = sample_pull_request.validate()
        assert any("merged_at" in e for e in errors)

    @pytest.mark.ai_generated
    def test_pr_to_dict_roundtrip(self, sample_pull_request: PullRequest) -> None:
        """Test serialization/deserialization roundtrip."""
        data = sample_pull_request.to_dict()
        restored = PullRequest.from_dict(data)

        assert restored.number == sample_pull_request.number
        assert restored.repository == sample_pull_request.repository
        assert restored.tool == sample_pull_request.tool
        assert restored.status == sample_pull_request.status

    @pytest.mark.ai_generated
    def test_pr_is_active(self) -> None:
        """Test is_active property."""
        pr = PullRequest(
            number=1,
            repository="test/repo",
            platform="github",
            url="https://github.com/test/repo/pull/1",
            tool="codespell",
            title="Test",
            author="user",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        pr.status = "open"
        assert pr.is_active is True

        pr.status = "draft"
        assert pr.is_active is True

        pr.status = "merged"
        assert pr.is_active is False

        pr.status = "closed"
        assert pr.is_active is False

    @pytest.mark.ai_generated
    def test_pr_freshness_score(self, sample_pull_request: PullRequest) -> None:
        """Test freshness_score property."""
        score = sample_pull_request.freshness_score
        assert isinstance(score, int)
        assert score > 0


class TestRepository:
    """Tests for Repository model."""

    @pytest.mark.ai_generated
    def test_create_repository(self) -> None:
        """Test creating a repository."""
        repo = Repository(
            owner="test-org",
            name="test-repo",
            platform="github",
            url="https://github.com/test-org/test-repo",
        )
        assert repo.full_name == "test-org/test-repo"
        assert repo.total_prs == 0

    @pytest.mark.ai_generated
    def test_add_pr(self, sample_repository: Repository, sample_pull_request: PullRequest) -> None:
        """Test adding PR to repository."""
        # sample_repository already has one PR
        assert sample_repository.total_prs == 1
        assert 12912 in sample_repository.codespell_prs

    @pytest.mark.ai_generated
    def test_repository_validation(self, sample_repository: Repository) -> None:
        """Test repository validation."""
        errors = sample_repository.validate()
        assert errors == []

    @pytest.mark.ai_generated
    def test_repository_to_dict_roundtrip(self, sample_repository: Repository) -> None:
        """Test serialization/deserialization roundtrip."""
        data = sample_repository.to_dict()
        restored = Repository.from_dict(data)

        assert restored.owner == sample_repository.owner
        assert restored.name == sample_repository.name
        assert restored.total_prs == sample_repository.total_prs

    @pytest.mark.ai_generated
    def test_behavior_categorization_insufficient_data(self) -> None:
        """Test behavior categorization with insufficient data."""
        repo = Repository(
            owner="test",
            name="repo",
            platform="github",
            url="https://github.com/test/repo",
        )
        repo.recalculate_metrics()
        assert repo.behavior_category == "insufficient_data"


class TestComment:
    """Tests for Comment model."""

    @pytest.mark.ai_generated
    def test_from_github_response_human(self) -> None:
        """Test parsing human comment."""
        data = {
            "id": 123,
            "user": {"login": "maintainer", "type": "User"},
            "body": "LGTM!",
            "created_at": "2025-01-15T10:00:00Z",
        }
        comment = Comment.from_github_response(data, pr_author="submitter")

        assert comment.id == 123
        assert comment.author == "maintainer"
        assert comment.author_type == "maintainer"
        assert comment.is_bot is False

    @pytest.mark.ai_generated
    def test_from_github_response_submitter(self) -> None:
        """Test parsing submitter comment."""
        data = {
            "id": 123,
            "user": {"login": "submitter", "type": "User"},
            "body": "Fixed!",
            "created_at": "2025-01-15T10:00:00Z",
        }
        comment = Comment.from_github_response(data, pr_author="submitter")

        assert comment.author_type == "submitter"
        assert comment.is_bot is False

    @pytest.mark.ai_generated
    def test_from_github_response_bot(self) -> None:
        """Test parsing bot comment."""
        data = {
            "id": 123,
            "user": {"login": "github-actions[bot]", "type": "Bot"},
            "body": "Checks passed!",
            "created_at": "2025-01-15T10:00:00Z",
        }
        comment = Comment.from_github_response(data, pr_author="submitter")

        assert comment.author_type == "bot"
        assert comment.is_bot is True


class TestConfiguration:
    """Tests for Configuration model."""

    @pytest.mark.ai_generated
    def test_default_configuration(self) -> None:
        """Test default configuration values."""
        config = Configuration()

        assert "yarikoptic" in config.tracked_users
        assert "codespell" in config.tool_keywords
        assert config.batch_size == 10

    @pytest.mark.ai_generated
    def test_configuration_validation(self) -> None:
        """Test configuration validation."""
        config = Configuration()
        errors = config.validate()
        # Token is empty by default but we don't validate that here
        # Other validations should pass
        assert all("tracked_users" not in e for e in errors)

    @pytest.mark.ai_generated
    def test_get_all_keywords(self) -> None:
        """Test getting all keywords."""
        config = Configuration()
        keywords = config.get_all_keywords()

        assert "codespell" in keywords
        assert "codespellit" in keywords
        assert "shellcheck" in keywords

    @pytest.mark.ai_generated
    def test_get_tool_for_title(self) -> None:
        """Test tool detection from title."""
        config = Configuration()

        assert config.get_tool_for_title("Add codespell CI") == "codespell"
        assert config.get_tool_for_title("Add shellcheck workflow") == "shellcheck"
        assert config.get_tool_for_title("Fix typo") == "other"

    @pytest.mark.ai_generated
    def test_from_file_missing(self, tmp_path: Path) -> None:
        """Test loading from missing file returns defaults."""
        config = Configuration.from_file(tmp_path / "nonexistent.yaml")
        assert "yarikoptic" in config.tracked_users


class TestDiscoveryRun:
    """Tests for DiscoveryRun model."""

    @pytest.mark.ai_generated
    def test_create_discovery_run(self) -> None:
        """Test creating a discovery run."""
        run = DiscoveryRun(
            started_at=datetime.now(UTC),
        )
        assert run.new_prs == 0
        assert run.mode == "normal"

    @pytest.mark.ai_generated
    def test_to_commit_message(self) -> None:
        """Test commit message generation."""
        run = DiscoveryRun(
            started_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
            new_repositories=2,
            new_prs=5,
            newly_merged_prs=1,
        )
        message = run.to_commit_message()

        assert "5 new PRs" in message
        assert "1 merged" in message
        assert "2 new repositories" in message

    @pytest.mark.ai_generated
    def test_discovery_run_roundtrip(self) -> None:
        """Test serialization/deserialization roundtrip."""
        run = DiscoveryRun(
            started_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
            new_prs=3,
            errors=["Error 1", "Error 2"],
        )
        data = run.to_dict()
        restored = DiscoveryRun.from_dict(data)

        assert restored.new_prs == run.new_prs
        assert restored.errors == run.errors
