"""Unit tests for analyzer module."""

from typing import Any

import pytest

from improveit_dashboard.controllers.analyzer import (
    analyze_engagement,
    classify_comments,
    detect_automation_types,
    determine_adoption_level,
)
from improveit_dashboard.models.pull_request import PullRequest


class TestClassifyComments:
    """Tests for comment classification."""

    @pytest.mark.ai_generated
    def test_classify_submitter_comment(self) -> None:
        """Test classifying submitter comment."""
        data = [
            {
                "id": 1,
                "user": {"login": "author", "type": "User"},
                "body": "Test",
                "created_at": "2025-01-15T10:00:00Z",
            }
        ]
        comments = classify_comments(data, pr_author="author")

        assert len(comments) == 1
        assert comments[0].author_type == "submitter"

    @pytest.mark.ai_generated
    def test_classify_maintainer_comment(self) -> None:
        """Test classifying maintainer comment."""
        data = [
            {
                "id": 1,
                "user": {"login": "maintainer", "type": "User"},
                "body": "LGTM",
                "created_at": "2025-01-15T10:00:00Z",
            }
        ]
        comments = classify_comments(data, pr_author="author")

        assert len(comments) == 1
        assert comments[0].author_type == "maintainer"

    @pytest.mark.ai_generated
    def test_classify_bot_comment_by_type(self) -> None:
        """Test classifying bot by type field."""
        data = [
            {
                "id": 1,
                "user": {"login": "some-bot", "type": "Bot"},
                "body": "Automated check",
                "created_at": "2025-01-15T10:00:00Z",
            }
        ]
        comments = classify_comments(data, pr_author="author")

        assert len(comments) == 1
        assert comments[0].author_type == "bot"
        assert comments[0].is_bot is True

    @pytest.mark.ai_generated
    def test_classify_bot_comment_by_suffix(self) -> None:
        """Test classifying bot by [bot] suffix."""
        data = [
            {
                "id": 1,
                "user": {"login": "github-actions[bot]", "type": "User"},
                "body": "Check passed",
                "created_at": "2025-01-15T10:00:00Z",
            }
        ]
        comments = classify_comments(data, pr_author="author")

        assert len(comments) == 1
        assert comments[0].author_type == "bot"
        assert comments[0].is_bot is True


class TestAnalyzeEngagement:
    """Tests for engagement analysis."""

    @pytest.mark.ai_generated
    def test_analyze_empty_comments(self, sample_pull_request: PullRequest) -> None:
        """Test analyzing PR with no comments."""
        analyze_engagement([], sample_pull_request)

        assert sample_pull_request.total_comments == 0
        # No comments = no response yet
        assert sample_pull_request.response_status == "no_response"

    @pytest.mark.ai_generated
    def test_analyze_with_comments(
        self,
        sample_pull_request: PullRequest,
        sample_comment_data: list[dict[str, Any]],
    ) -> None:
        """Test analyzing PR with comments."""
        comments = classify_comments(sample_comment_data, pr_author="yarikoptic")
        analyze_engagement(comments, sample_pull_request)

        assert sample_pull_request.total_comments == 3
        assert sample_pull_request.submitter_comments == 1
        assert sample_pull_request.maintainer_comments == 1
        assert sample_pull_request.bot_comments == 1

    @pytest.mark.ai_generated
    def test_time_to_first_response(self, sample_pull_request: PullRequest) -> None:
        """Test calculating time to first response."""
        # PR created at 2025-01-15T10:00:00Z
        # Maintainer responds at 2025-01-16T10:00:00Z (24 hours later)
        comments_data = [
            {
                "id": 1,
                "user": {"login": "maintainer", "type": "User"},
                "body": "LGTM",
                "created_at": "2025-01-16T10:00:00Z",
            }
        ]
        comments = classify_comments(comments_data, pr_author="yarikoptic")
        analyze_engagement(comments, sample_pull_request)

        assert sample_pull_request.time_to_first_response_hours is not None
        # Should be approximately 24 hours
        assert 23 < sample_pull_request.time_to_first_response_hours < 25

    @pytest.mark.ai_generated
    def test_response_status_awaiting_submitter(self, sample_pull_request: PullRequest) -> None:
        """Test detecting awaiting submitter status."""
        comments_data = [
            {
                "id": 1,
                "user": {"login": "maintainer", "type": "User"},
                "body": "Please fix this",
                "created_at": "2025-01-16T10:00:00Z",
            }
        ]
        comments = classify_comments(comments_data, pr_author="yarikoptic")
        analyze_engagement(comments, sample_pull_request)

        assert sample_pull_request.response_status == "awaiting_submitter"
        assert sample_pull_request.last_comment_is_maintainer is True


class TestDetectAutomationTypes:
    """Tests for automation type detection."""

    @pytest.mark.ai_generated
    def test_detect_github_actions(self) -> None:
        """Test detecting GitHub Actions workflow."""
        files = [{"filename": ".github/workflows/codespell.yml"}]
        types = detect_automation_types(files)
        assert "github-actions" in types

    @pytest.mark.ai_generated
    def test_detect_pre_commit(self) -> None:
        """Test detecting pre-commit config."""
        files = [{"filename": ".pre-commit-config.yaml"}]
        types = detect_automation_types(files)
        assert "pre-commit" in types

    @pytest.mark.ai_generated
    def test_detect_codespell_config(self) -> None:
        """Test detecting codespell config."""
        files = [{"filename": ".codespellrc"}]
        types = detect_automation_types(files)
        assert "codespell-config" in types

    @pytest.mark.ai_generated
    def test_detect_multiple_types(self, sample_files_data: list[dict[str, Any]]) -> None:
        """Test detecting multiple automation types."""
        types = detect_automation_types(sample_files_data)
        assert "github-actions" in types
        assert "codespell-config" in types

    @pytest.mark.ai_generated
    def test_detect_empty_files(self) -> None:
        """Test with no files."""
        types = detect_automation_types([])
        assert types == []


class TestDetermineAdoptionLevel:
    """Tests for adoption level determination."""

    @pytest.mark.ai_generated
    def test_full_automation_github_actions(self) -> None:
        """Test full automation with GitHub Actions."""
        level = determine_adoption_level(["github-actions"], "merged")
        assert level == "full_automation"

    @pytest.mark.ai_generated
    def test_full_automation_pre_commit(self) -> None:
        """Test full automation with pre-commit."""
        level = determine_adoption_level(["pre-commit"], "merged")
        assert level == "full_automation"

    @pytest.mark.ai_generated
    def test_config_only(self) -> None:
        """Test config only adoption."""
        level = determine_adoption_level(["codespell-config"], "merged")
        assert level == "config_only"

    @pytest.mark.ai_generated
    def test_typo_fixes(self) -> None:
        """Test typo fixes only."""
        level = determine_adoption_level([], "merged")
        assert level == "typo_fixes"

    @pytest.mark.ai_generated
    def test_rejected(self) -> None:
        """Test rejected PR."""
        level = determine_adoption_level(["github-actions"], "closed")
        assert level == "rejected"
