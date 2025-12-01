"""Per-user detailed report generation."""

from datetime import UTC, datetime
from pathlib import Path

from improveit_dashboard.models.pull_request import PullRequest
from improveit_dashboard.models.repository import Repository
from improveit_dashboard.utils.logging import get_logger
from improveit_dashboard.utils.markdown import sanitize_and_truncate

logger = get_logger(__name__)

# Status display names and file names
STATUS_INFO = {
    "draft": {"display": "Draft", "file": "draft.md"},
    "open": {"display": "Open", "file": "open.md"},
    "merged": {"display": "Merged", "file": "merged.md"},
    "closed": {"display": "Closed", "file": "closed.md"},
}


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
        paths = _generate_user_report(repositories, output_dir, user)
        generated_paths.extend(paths)

    return generated_paths


def _generate_user_report(
    repositories: dict[str, Repository],
    output_dir: Path,
    username: str,
) -> list[Path]:
    """Generate detailed report for a single user.

    Creates:
    - {output_dir}/{username}.md - Summary with "Needs Your Response" section
    - {output_dir}/{username}/draft.md - Draft PRs table
    - {output_dir}/{username}/open.md - Open PRs table
    - {output_dir}/{username}/merged.md - Merged PRs table
    - {output_dir}/{username}/closed.md - Closed PRs table

    Args:
        repositories: Dict mapping full_name to Repository
        output_dir: Directory for output files
        username: GitHub username

    Returns:
        List of generated file paths
    """
    logger.info(f"Generating reports for {username}")
    generated_paths: list[Path] = []

    # Create user subdirectory
    user_dir = output_dir / username
    user_dir.mkdir(parents=True, exist_ok=True)

    # Collect user's PRs
    user_prs: list[PullRequest] = []
    for repo in repositories.values():
        for pr in repo.prs.values():
            if pr.author == username:
                user_prs.append(pr)

    # Group by status
    prs_by_status: dict[str, list[PullRequest]] = {
        "draft": [],
        "open": [],
        "merged": [],
        "closed": [],
    }

    for pr in user_prs:
        prs_by_status[pr.status].append(pr)

    # Sort each group by updated_at descending
    for prs in prs_by_status.values():
        prs.sort(key=lambda p: p.updated_at, reverse=True)

    # Generate main summary file
    main_path = output_dir / f"{username}.md"
    _generate_summary_file(main_path, username, prs_by_status, user_dir.name)
    generated_paths.append(main_path)

    # Generate per-status files
    for status, prs in prs_by_status.items():
        status_path = user_dir / STATUS_INFO[status]["file"]
        _generate_status_file(status_path, username, status, prs)
        generated_paths.append(status_path)

    logger.info(f"Generated {len(generated_paths)} files for {username} with {len(user_prs)} PRs")
    return generated_paths


def _generate_summary_file(
    output_path: Path,
    username: str,
    prs_by_status: dict[str, list[PullRequest]],
    user_subdir: str,
) -> None:
    """Generate main user summary file with Needs Response section only.

    Args:
        output_path: Path to output file
        username: GitHub username
        prs_by_status: PRs grouped by status
        user_subdir: Name of user subdirectory for links
    """
    total = sum(len(prs) for prs in prs_by_status.values())

    lines = [
        f"# PRs by {username}",
        "",
        f"*Last updated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "[< Back to Dashboard](../README.md)",
        "",
        "## Summary",
        "",
    ]

    # Status summary with links
    for status in ["draft", "open", "merged", "closed"]:
        count = len(prs_by_status[status])
        display = STATUS_INFO[status]["display"]
        file = STATUS_INFO[status]["file"]
        if count > 0:
            lines.append(f"- **[{display}]({user_subdir}/{file})**: {count} PRs")
        else:
            lines.append(f"- **{display}**: {count} PRs")

    lines.append(f"- **Total**: {total} PRs")
    lines.append("")

    # Needs Response section (only active PRs awaiting submitter)
    needs_response = []
    for status in ["draft", "open"]:
        for pr in prs_by_status[status]:
            if pr.response_status == "awaiting_submitter":
                needs_response.append(pr)

    if needs_response:
        lines.extend(
            [
                "## Needs Your Response",
                "",
                "PRs where maintainers have responded and are waiting for your action:",
                "",
            ]
        )
        for pr in needs_response:
            days = pr.days_awaiting_submitter or 0
            status_icons = _get_status_icons(pr)
            lines.append(
                f"- [{pr.repository}#{pr.number}]({pr.url}): {pr.title} "
                f"(*waiting {days} days*) {status_icons}"
            )
            if pr.last_developer_comment_body:
                # Truncate long comments
                comment = pr.last_developer_comment_body[:200]
                if len(pr.last_developer_comment_body) > 200:
                    comment += "..."
                lines.append(f"  > {comment}")
        lines.append("")
    else:
        lines.extend(
            [
                "## Needs Your Response",
                "",
                "*No PRs currently awaiting your response.*",
                "",
            ]
        )

    # Write output
    output_path.write_text("\n".join(lines) + "\n")


def _generate_status_file(
    output_path: Path,
    username: str,
    status: str,
    prs: list[PullRequest],
) -> None:
    """Generate per-status file with full PR table.

    Args:
        output_path: Path to output file
        username: GitHub username
        status: PR status (draft, open, merged, closed)
        prs: List of PRs with this status
    """
    display = STATUS_INFO[status]["display"]

    lines = [
        f"# {display} PRs by {username}",
        "",
        f"*Last updated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        f"[< Back to {username} summary](../{username}.md) | [< Back to Dashboard](../../README.md)",
        "",
        f"**Total**: {len(prs)} PRs",
        "",
    ]

    if not prs:
        lines.append(f"*No {display.lower()} PRs.*")
    else:
        _add_pr_table(lines, prs, status=status)

    lines.append("")

    # Write output
    output_path.write_text("\n".join(lines) + "\n")


def _add_pr_table(
    lines: list[str],
    prs: list[PullRequest],
    status: str = "open",
) -> None:
    """Add PR table to lines.

    Args:
        lines: List to append to
        prs: List of PRs
        status: PR status (draft, open, merged, closed)
    """
    if status == "merged":
        lines.append(
            "| Repository | PR | Title | Tool | Created | Merged | "
            "Merged By | Commits | Files | Automation | Last Comment |"
        )
        lines.append(
            "|------------|----|----|------|---------|--------|"
            "----------|---------|-------|------------|--------------|"
        )
    elif status == "closed":
        lines.append(
            "| Repository | PR | Title | Tool | Created | Closed | "
            "Closed By | Files | Last Comment |"
        )
        lines.append(
            "|------------|----|----|------|---------|--------|----------|-------|--------------|"
        )
    else:
        # draft or open
        lines.append(
            "| Repository | PR | Title | Tool | Created | Files | Comments | "
            "Response | CI | Conflicts | Automation | Last Comment |"
        )
        lines.append(
            "|------------|----|----|------|---------|-------|----------|"
            "----------|----|-----------|-----------| --------------|"
        )

    for pr in prs:
        created = pr.created_at.strftime("%Y-%m-%d")
        automation = ", ".join(pr.automation_types) if pr.automation_types else "-"
        # Sanitize comment text to prevent markdown from breaking table
        last_comment = sanitize_and_truncate(pr.last_developer_comment_body or "-", 50)
        # Also sanitize title in case it contains special characters
        title = sanitize_and_truncate(pr.title, 40)

        if status == "merged":
            merged = pr.merged_at.strftime("%Y-%m-%d") if pr.merged_at else "-"
            merged_by = f"@{pr.closed_by}" if pr.closed_by else "-"
            lines.append(
                f"| [{pr.repository}](https://github.com/{pr.repository}) "
                f"| [#{pr.number}]({pr.url}) "
                f"| {title} "
                f"| {pr.tool} "
                f"| {created} "
                f"| {merged} "
                f"| {merged_by} "
                f"| {pr.commit_count} "
                f"| {pr.files_changed} "
                f"| {automation} "
                f"| {last_comment} |"
            )
        elif status == "closed":
            closed = pr.closed_at.strftime("%Y-%m-%d") if pr.closed_at else "-"
            closed_by = f"@{pr.closed_by}" if pr.closed_by else "-"
            lines.append(
                f"| [{pr.repository}](https://github.com/{pr.repository}) "
                f"| [#{pr.number}]({pr.url}) "
                f"| {title} "
                f"| {pr.tool} "
                f"| {created} "
                f"| {closed} "
                f"| {closed_by} "
                f"| {pr.files_changed} "
                f"| {last_comment} |"
            )
        else:
            # draft or open
            comments = f"{pr.total_comments} ({pr.maintainer_comments})"
            response = _format_response_status(pr)
            ci = _format_ci_status(pr)
            conflicts = "Yes" if pr.has_conflicts else "-"
            lines.append(
                f"| [{pr.repository}](https://github.com/{pr.repository}) "
                f"| [#{pr.number}]({pr.url}) "
                f"| {title} "
                f"| {pr.tool} "
                f"| {created} "
                f"| {pr.files_changed} "
                f"| {comments} "
                f"| {response} "
                f"| {ci} "
                f"| {conflicts} "
                f"| {automation} "
                f"| {last_comment} |"
            )


def _format_response_status(pr: PullRequest) -> str:
    """Format response status for display."""
    if pr.response_status == "awaiting_submitter":
        days = pr.days_awaiting_submitter or 0
        return f"You ({days}d)"
    elif pr.response_status == "awaiting_maintainer":
        return "Maintainer"
    else:
        return "No response"


def _format_ci_status(pr: PullRequest) -> str:
    """Format CI status for display."""
    parts = []

    # Overall CI
    if pr.ci_status == "success":
        parts.append("CI:OK")
    elif pr.ci_status == "failure":
        parts.append("CI:FAIL")
    elif pr.ci_status == "pending":
        parts.append("CI:...")

    # Codespell workflow specifically
    if pr.codespell_workflow_ci == "success":
        parts.append("CS:OK")
    elif pr.codespell_workflow_ci == "failure":
        parts.append("CS:FAIL")
    elif pr.codespell_workflow_ci == "pending":
        parts.append("CS:...")

    # Main branch CI
    if pr.main_branch_ci == "success":
        parts.append("Main:OK")
    elif pr.main_branch_ci == "failure":
        parts.append("Main:FAIL")

    return " ".join(parts) if parts else "-"


def _get_status_icons(pr: PullRequest) -> str:
    """Get status indicator icons for a PR."""
    icons = []

    if pr.has_conflicts:
        icons.append("[conflicts]")

    if pr.ci_status == "failure":
        icons.append("[CI failing]")
    elif pr.ci_status == "pending":
        icons.append("[CI pending]")

    return " ".join(icons)
