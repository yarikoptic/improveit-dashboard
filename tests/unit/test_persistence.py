"""Unit tests for persistence layer."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from improveit_dashboard.controllers.persistence import (
    get_last_updated,
    load_model,
    save_model,
)
from improveit_dashboard.models.discovery_run import DiscoveryRun
from improveit_dashboard.models.pull_request import PullRequest
from improveit_dashboard.models.repository import Repository


class TestPersistence:
    """Tests for persistence functions."""

    @pytest.mark.ai_generated
    def test_save_and_load_empty_model(self, tmp_path: Path) -> None:
        """Test saving and loading empty model."""
        path = tmp_path / "data" / "repositories.json"

        save_model(path, {})

        repositories, last_run = load_model(path)
        assert repositories == {}
        assert last_run is None

    @pytest.mark.ai_generated
    def test_save_and_load_with_data(
        self, tmp_path: Path, sample_repository: Repository
    ) -> None:
        """Test saving and loading model with data."""
        path = tmp_path / "data" / "repositories.json"

        repositories = {sample_repository.full_name: sample_repository}
        run = DiscoveryRun(
            started_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
            new_prs=5,
        )

        save_model(path, repositories, run)

        loaded_repos, loaded_run = load_model(path)

        assert len(loaded_repos) == 1
        assert sample_repository.full_name in loaded_repos
        assert loaded_run is not None
        assert loaded_run.new_prs == 5

    @pytest.mark.ai_generated
    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading from nonexistent file."""
        path = tmp_path / "nonexistent.json"

        repositories, last_run = load_model(path)

        assert repositories == {}
        assert last_run is None

    @pytest.mark.ai_generated
    def test_atomic_save(self, tmp_path: Path, sample_repository: Repository) -> None:
        """Test atomic save doesn't leave temp files."""
        path = tmp_path / "data" / "repositories.json"
        temp_path = path.with_suffix(".json.tmp")

        repositories = {sample_repository.full_name: sample_repository}
        save_model(path, repositories)

        # Main file should exist
        assert path.exists()
        # Temp file should not exist
        assert not temp_path.exists()

    @pytest.mark.ai_generated
    def test_get_last_updated(self, tmp_path: Path, sample_repository: Repository) -> None:
        """Test getting last updated timestamp."""
        path = tmp_path / "data" / "repositories.json"

        # No file yet
        assert get_last_updated(path) is None

        # Save model
        repositories = {sample_repository.full_name: sample_repository}
        save_model(path, repositories)

        # Should have timestamp now
        last_updated = get_last_updated(path)
        assert last_updated is not None
        assert isinstance(last_updated, datetime)

    @pytest.mark.ai_generated
    def test_pr_data_preserved(self, tmp_path: Path) -> None:
        """Test that all PR fields are preserved through save/load."""
        path = tmp_path / "data" / "repositories.json"

        pr = PullRequest(
            number=42,
            repository="test/repo",
            platform="github",
            url="https://github.com/test/repo/pull/42",
            tool="codespell",
            title="Test PR",
            author="testuser",
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
            updated_at=datetime(2025, 1, 2, tzinfo=UTC),
            status="merged",
            merged_at=datetime(2025, 1, 3, tzinfo=UTC),
            commit_count=3,
            files_changed=5,
            automation_types=["github-actions", "pre-commit"],
            adoption_level="full_automation",
            total_comments=10,
            submitter_comments=2,
            maintainer_comments=5,
            bot_comments=3,
            time_to_first_response_hours=24.5,
            response_status="awaiting_maintainer",
            etag='W/"abc123"',
        )

        repo = Repository(
            owner="test",
            name="repo",
            platform="github",
            url="https://github.com/test/repo",
        )
        repo.add_pr(pr)

        save_model(path, {repo.full_name: repo})

        loaded_repos, _ = load_model(path)
        loaded_repo = loaded_repos["test/repo"]
        loaded_pr = loaded_repo.prs[42]

        assert loaded_pr.title == pr.title
        assert loaded_pr.status == pr.status
        assert loaded_pr.merged_at is not None
        assert loaded_pr.automation_types == pr.automation_types
        assert loaded_pr.adoption_level == pr.adoption_level
        assert loaded_pr.time_to_first_response_hours == pr.time_to_first_response_hours
        assert loaded_pr.etag == pr.etag
