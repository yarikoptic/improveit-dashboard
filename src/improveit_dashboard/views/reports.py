"""Per-user detailed report generation."""

from datetime import UTC, datetime
from pathlib import Path

from improveit_dashboard.models.pull_request import PullRequest
from improveit_dashboard.models.repository import Repository
from improveit_dashboard.utils.logging import get_logger

logger = get_logger(__name__)


def generate_user_reports(
    repositories: dict[str, Repository],
    output_dir: Path,
    tracked_users: list[str],
) -> list[Path]:
    """Generate per-user detailed reports.

    Args:
        repositories: Dict mapping full_name to Repository
        output_dir: Directory for output files
        tracked_users: List of tracked usernames

    Returns:
        List of generated file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_paths: list[Path] = []

    for user in tracked_users:
        path = output_dir / f"{user}.md"
        _generate_user_report(repositories, path, user)
        generated_paths.append(path)

    return generated_paths


def _generate_user_report(
    repositories: dict[str, Repository],
    output_path: Path,
    username: str,
) -> None:
    """Generate detailed report for a single user.

    Args:
        repositories: Dict mapping full_name to Repository
        output_path: Path to output file
        username: GitHub username
    """
    logger.info(f"Generating report for {username}: {output_path}")

    # Collect user's PRs
    user_prs: list[PullRequest] = []
    for repo in repositories.values():
        for pr in repo.prs.values():
            if pr.author == username:
                user_prs.append(pr)

    # Group by status
    draft_prs = [pr for pr in user_prs if pr.status == "draft"]
    open_prs = [pr for pr in user_prs if pr.status == "open"]
    merged_prs = [pr for pr in user_prs if pr.status == "merged"]
    closed_prs = [pr for pr in user_prs if pr.status == "closed"]

    # Sort each group by updated_at descending
    for prs in [draft_prs, open_prs, merged_prs, closed_prs]:
        prs.sort(key=lambda p: p.updated_at, reverse=True)

    # Generate markdown
    lines = [
        f"# PRs by {username}",
        "",
        f"*Last updated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        f"**Total**: {len(user_prs)} PRs | "
        f"**Draft**: {len(draft_prs)} | "
        f"**Open**: {len(open_prs)} | "
        f"**Merged**: {len(merged_prs)} | "
        f"**Closed**: {len(closed_prs)}",
        "",
        "[< Back to Dashboard](../README.md)",
        "",
    ]

    # Needs Response section
    needs_response = [
        pr for pr in user_prs
        if pr.status in ("draft", "open") and pr.response_status == "awaiting_submitter"
    ]
    if needs_response:
        lines.extend([
            "## Needs Your Response",
            "",
            "PRs where maintainers have responded and are waiting for your action:",
            "",
        ])
        for pr in needs_response:
            days = pr.days_awaiting_submitter or 0
            lines.append(
                f"- [{pr.repository}#{pr.number}]({pr.url}): {pr.title} "
                f"(*waiting {days} days*)"
            )
            if pr.last_developer_comment_body:
                # Truncate long comments
                comment = pr.last_developer_comment_body[:200]
                if len(pr.last_developer_comment_body) > 200:
                    comment += "..."
                lines.append(f"  > {comment}")
        lines.append("")

    # Draft PRs
    if draft_prs:
        lines.extend([
            "## Draft PRs",
            "",
        ])
        _add_pr_table(lines, draft_prs)
        lines.append("")

    # Open PRs
    if open_prs:
        lines.extend([
            "## Open PRs",
            "",
        ])
        _add_pr_table(lines, open_prs)
        lines.append("")

    # Merged PRs
    if merged_prs:
        lines.extend([
            "## Merged PRs",
            "",
        ])
        _add_pr_table(lines, merged_prs, show_merged=True)
        lines.append("")

    # Closed PRs (without merge)
    if closed_prs:
        lines.extend([
            "## Closed PRs (Not Merged)",
            "",
        ])
        _add_pr_table(lines, closed_prs)
        lines.append("")

    # Write output
    output_path.write_text("\n".join(lines) + "\n")

    logger.info(f"Generated report for {username} with {len(user_prs)} PRs")


def _add_pr_table(
    lines: list[str],
    prs: list[PullRequest],
    show_merged: bool = False,
) -> None:
    """Add PR table to lines.

    Args:
        lines: List to append to
        prs: List of PRs
        show_merged: Include merged date column
    """
    if show_merged:
        lines.append(
            "| Repository | PR | Title | Tool | Created | Merged | Commits | Files | Automation |"
        )
        lines.append(
            "|------------|----|----|------|---------|--------|---------|-------|------------|"
        )
    else:
        lines.append(
            "| Repository | PR | Title | Tool | Created | Comments | Response | Automation |"
        )
        lines.append(
            "|------------|----|----|------|---------|----------|----------|------------|"
        )

    for pr in prs:
        created = pr.created_at.strftime("%Y-%m-%d")
        automation = ", ".join(pr.automation_types) if pr.automation_types else "-"

        if show_merged:
            merged = pr.merged_at.strftime("%Y-%m-%d") if pr.merged_at else "-"
            lines.append(
                f"| [{pr.repository}](https://github.com/{pr.repository}) "
                f"| [#{pr.number}]({pr.url}) "
                f"| {_truncate(pr.title, 40)} "
                f"| {pr.tool} "
                f"| {created} "
                f"| {merged} "
                f"| {pr.commit_count} "
                f"| {pr.files_changed} "
                f"| {automation} |"
            )
        else:
            comments = f"{pr.total_comments} ({pr.maintainer_comments})"
            response = _format_response_status(pr)
            lines.append(
                f"| [{pr.repository}](https://github.com/{pr.repository}) "
                f"| [#{pr.number}]({pr.url}) "
                f"| {_truncate(pr.title, 40)} "
                f"| {pr.tool} "
                f"| {created} "
                f"| {comments} "
                f"| {response} "
                f"| {automation} |"
            )


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max length."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _format_response_status(pr: PullRequest) -> str:
    """Format response status for display."""
    if pr.response_status == "awaiting_submitter":
        days = pr.days_awaiting_submitter or 0
        return f"You ({days}d)"
    elif pr.response_status == "awaiting_maintainer":
        return "Maintainer"
    else:
        return "No response"
