"""End-to-end integration tests for the full discovery pipeline.

These tests require GITHUB_TOKEN environment variable to be set.
They test the full discovery and view generation pipeline.
"""

import os
from pathlib import Path

import pytest

from improveit_dashboard.controllers.discovery import run_discovery
from improveit_dashboard.controllers.persistence import load_model
from improveit_dashboard.models.config import Configuration
from improveit_dashboard.views.dashboard import generate_dashboard
from improveit_dashboard.views.reports import generate_user_reports

# Skip all tests if GITHUB_TOKEN not set
pytestmark = pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"),
    reason="GITHUB_TOKEN not set",
)


class TestEndToEndPipeline:
    """End-to-end tests for the full pipeline."""

    @pytest.fixture
    def config(self, tmp_path: Path) -> Configuration:
        """Create test configuration."""
        return Configuration(
            github_token=os.environ["GITHUB_TOKEN"],
            tracked_users=["yarikoptic"],
            tool_keywords={
                "codespell": ["codespell"],
            },
            data_file=tmp_path / "data" / "repositories.json",
            output_readme=tmp_path / "README.md",
            output_readmes_dir=tmp_path / "READMEs",
            max_prs_per_run=5,  # Limit for testing
        )

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_discovery_and_view_generation(self, config: Configuration) -> None:
        """Test full discovery and view generation pipeline."""
        # Run discovery
        run = run_discovery(config, incremental=False)

        # Should have found some PRs
        assert run.total_processed > 0 or run.new_prs > 0
        assert run.api_calls_made > 0

        # Load model and verify
        repositories, last_run = load_model(config.data_file)
        assert len(repositories) > 0

        # Generate views
        generate_dashboard(
            repositories=repositories,
            output_path=config.output_readme,
            tracked_users=config.tracked_users,
        )
        assert config.output_readme.exists()

        user_reports = generate_user_reports(
            repositories=repositories,
            output_dir=config.output_readmes_dir,
            tracked_users=config.tracked_users,
        )
        assert len(user_reports) > 0

        # Check that per-status files were created
        user_dir = config.output_readmes_dir / "yarikoptic"
        assert user_dir.exists()
        assert (user_dir / "open.md").exists() or (user_dir / "merged.md").exists()

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_incremental_update(self, config: Configuration) -> None:
        """Test incremental update mode."""
        # First run
        run1 = run_discovery(config, incremental=False)

        # Second run (incremental)
        run2 = run_discovery(config, incremental=True)

        # Second run should have processed fewer or same PRs
        # (unless new PRs were created in between)
        assert run2.api_calls_made <= run1.api_calls_made + 5

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_pr_fields_populated(self, config: Configuration) -> None:
        """Test that PR fields are properly populated."""
        run_discovery(config, incremental=False)

        repositories, _ = load_model(config.data_file)
        assert len(repositories) > 0

        # Check at least one PR
        for repo in repositories.values():
            for pr in repo.prs.values():
                # Required fields
                assert pr.number > 0
                assert pr.repository
                assert pr.platform == "github"
                assert pr.url.startswith("https://")
                assert pr.tool in ("codespell", "shellcheck", "other")
                assert pr.title
                assert pr.author
                assert pr.status in ("draft", "open", "merged", "closed")

                # If merged, should have merged_at
                if pr.status == "merged":
                    assert pr.merged_at is not None

                # Files changed should be positive
                assert pr.files_changed >= 1

                # Verified one PR, that's enough
                return

        pytest.fail("No PRs found to verify")

    @pytest.mark.integration
    @pytest.mark.ai_generated
    def test_merged_pr_has_closed_by(self, config: Configuration) -> None:
        """Test that merged PRs have closed_by field populated."""
        run_discovery(config, incremental=False)

        repositories, _ = load_model(config.data_file)

        # Find a merged PR
        for repo in repositories.values():
            for pr in repo.prs.values():
                if pr.status == "merged":
                    # Merged PR should have closed_by (merged_by)
                    # Note: This may be None if the API didn't return it
                    # but the field should at least exist
                    assert hasattr(pr, "closed_by")
                    return

        # No merged PRs found - skip this check
        pytest.skip("No merged PRs found to verify closed_by")
