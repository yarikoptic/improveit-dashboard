"""PR analysis for engagement metrics and automation detection."""

from datetime import UTC, datetime
from typing import Any

from improveit_dashboard.models.comment import Comment
from improveit_dashboard.models.pull_request import (
    AdoptionLevel,
    PullRequest,
    ResponseStatus,
)
from improveit_dashboard.utils.logging import get_logger

logger = get_logger(__name__)


def classify_comments(
    comments_data: list[dict[str, Any]],
    pr_author: str,
) -> list[Comment]:
    """Parse and classify comments from GitHub API response.

    Args:
        comments_data: List of comment data from GitHub API
        pr_author: Username of the PR author

    Returns:
        List of Comment objects
    """
    comments = []
    for data in comments_data:
        try:
            comment = Comment.from_github_response(data, pr_author)
            comments.append(comment)
        except Exception as e:
            logger.warning(f"Failed to parse comment {data.get('id')}: {e}")
    return comments


def analyze_engagement(
    comments: list[Comment],
    pr: PullRequest,
) -> None:
    """Analyze PR engagement metrics from comments.

    Updates the PullRequest object in place with:
    - Comment counts by type
    - Time to first response
    - Response status
    - Last developer comment

    Args:
        comments: List of Comment objects
        pr: PullRequest to update
    """
    pr.total_comments = len(comments)
    pr.submitter_comments = sum(1 for c in comments if c.author_type == "submitter")
    pr.maintainer_comments = sum(1 for c in comments if c.author_type == "maintainer")
    pr.bot_comments = sum(1 for c in comments if c.author_type == "bot")

    # Sort comments by time
    sorted_comments = sorted(comments, key=lambda c: c.created_at)

    # Find first maintainer (non-bot, non-submitter) response
    first_maintainer = None
    for comment in sorted_comments:
        if comment.author_type == "maintainer":
            first_maintainer = comment
            break

    if first_maintainer:
        # Calculate time to first response in hours
        delta = first_maintainer.created_at - pr.created_at
        pr.time_to_first_response_hours = delta.total_seconds() / 3600

    # Find last comment and last maintainer comment
    last_comment = None
    last_maintainer_comment = None
    last_developer_comment = None  # Non-submitter (can be bot for this field? No, spec says "developer")

    for comment in reversed(sorted_comments):
        if last_comment is None:
            last_comment = comment

        if last_maintainer_comment is None and comment.author_type == "maintainer":
            last_maintainer_comment = comment

        # Last developer = last non-submitter, non-bot
        if last_developer_comment is None and comment.author_type == "maintainer":
            last_developer_comment = comment

        if last_comment and last_maintainer_comment and last_developer_comment:
            break

    # Update PR with last comment info
    if last_comment:
        pr.last_comment_author = last_comment.author
        pr.last_comment_is_maintainer = last_comment.author_type == "maintainer"

    if last_maintainer_comment:
        pr.last_maintainer_comment_at = last_maintainer_comment.created_at

    if last_developer_comment:
        pr.last_developer_comment_body = last_developer_comment.body

    # Determine response status
    pr.response_status = _determine_response_status(
        pr, last_comment, last_maintainer_comment
    )

    # Calculate days awaiting submitter
    if pr.response_status == "awaiting_submitter" and last_maintainer_comment:
        now = datetime.utcnow()
        if last_maintainer_comment.created_at.tzinfo:
            # Make now timezone-aware
            now = datetime.now(UTC)
        delta = now - last_maintainer_comment.created_at
        pr.days_awaiting_submitter = delta.days


def _determine_response_status(
    pr: PullRequest,
    last_comment: Comment | None,
    last_maintainer_comment: Comment | None,
) -> ResponseStatus:
    """Determine response status based on comments and PR state.

    Args:
        pr: PullRequest being analyzed
        last_comment: Most recent comment
        last_maintainer_comment: Most recent maintainer comment

    Returns:
        Response status
    """
    # Closed/merged PRs don't need response tracking
    if pr.status in ("merged", "closed"):
        if last_maintainer_comment:
            return "awaiting_submitter"  # Historical - maintainer had last word
        return "no_response"

    # No comments at all
    if not last_comment:
        return "no_response"

    # No maintainer comments (only bots or submitter)
    if not last_maintainer_comment:
        return "awaiting_maintainer"

    # Check if last non-bot comment is from maintainer
    if last_comment.author_type == "maintainer":
        return "awaiting_submitter"
    elif last_comment.author_type == "submitter":
        return "awaiting_maintainer"
    else:
        # Last comment is bot - look at last human
        # If maintainer commented after submitter, awaiting submitter
        # This requires comparing timestamps of last submitter vs maintainer
        return "awaiting_maintainer"


def detect_automation_types(files: list[dict[str, Any]]) -> list[str]:
    """Detect automation types from PR file changes.

    Args:
        files: List of file data from GitHub API

    Returns:
        List of automation type strings
    """
    types: set[str] = set()

    for file_data in files:
        path = file_data.get("filename", "")
        path_lower = path.lower()

        # GitHub Actions workflows
        if ".github/workflows/" in path and path.endswith((".yml", ".yaml")):
            types.add("github-actions")

        # Pre-commit configuration
        if path == ".pre-commit-config.yaml":
            types.add("pre-commit")

        # Codespell config
        if path in (".codespellrc", "setup.cfg", "pyproject.toml", "tox.ini"):
            # Check if it's actually codespell related
            if "codespell" in path_lower or path in (".codespellrc",):
                types.add("codespell-config")

        # Shellcheck config
        if "shellcheck" in path_lower or path == ".shellcheckrc":
            types.add("shellcheck-config")

        # Other CI systems
        if path == ".travis.yml":
            types.add("travis-ci")
        if path in ("Jenkinsfile", "jenkins.yml"):
            types.add("jenkins")
        if path == ".gitlab-ci.yml":
            types.add("gitlab-ci")
        if "circleci" in path_lower:
            types.add("circleci")

    return sorted(types)


def determine_adoption_level(
    automation_types: list[str],
    pr_status: str,
) -> AdoptionLevel:
    """Determine adoption level from automation types and PR status.

    Args:
        automation_types: List of detected automation types
        pr_status: PR status (merged, closed, etc.)

    Returns:
        Adoption level classification
    """
    if pr_status == "closed":
        return "rejected"

    # Full automation if has workflow or pre-commit
    full_auto_types = {"github-actions", "pre-commit", "travis-ci", "jenkins", "gitlab-ci"}
    if any(t in full_auto_types for t in automation_types):
        return "full_automation"

    # Config only if has config files but no workflows
    config_types = {"codespell-config", "shellcheck-config"}
    if any(t in config_types for t in automation_types):
        return "config_only"

    # No automation detected - likely just typo fixes
    return "typo_fixes"
