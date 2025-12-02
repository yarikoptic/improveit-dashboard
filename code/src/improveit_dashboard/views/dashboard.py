"""Main dashboard (README.md) generation."""

from datetime import UTC, datetime
from pathlib import Path

from improveit_dashboard.models.pull_request import PullRequest
from improveit_dashboard.models.repository import Repository
from improveit_dashboard.utils.logging import get_logger
from improveit_dashboard.utils.markdown import sanitize_and_truncate, write_if_changed

logger = get_logger(__name__)

# Behavior category metadata
BEHAVIOR_INFO = {
    "welcoming": {
        "display": "Welcoming",
        "description": "Fast response (<48h), high acceptance rate (>70%)",
        "file": "welcoming.md",
    },
    "selective": {
        "display": "Selective",
        "description": "Moderate response time, reviews carefully before accepting",
        "file": "selective.md",
    },
    "unresponsive": {
        "display": "Unresponsive",
        "description": "Slow or no response (>7 days average)",
        "file": "unresponsive.md",
    },
    "hostile": {
        "display": "Hostile",
        "description": "Quick rejection without engagement",
        "file": "hostile.md",
    },
    "insufficient_data": {
        "display": "Insufficient Data",
        "description": "Not enough PRs to categorize reliably",
        "file": "insufficient_data.md",
    },
}


def generate_dashboard(
    repositories: dict[str, Repository],
    output_path: Path,
    tracked_users: list[str],
    behavior_overrides: dict[str, str] | None = None,
) -> None:
    """Generate the main README.md dashboard.

    Args:
        repositories: Dict mapping full_name to Repository
        output_path: Path to output README.md
        tracked_users: List of tracked usernames
        behavior_overrides: Optional dict mapping repo full_name to behavior category override
    """
    overrides = behavior_overrides or {}
    logger.info(f"Generating dashboard: {output_path}")

    # Collect stats per user
    user_stats: dict[str, dict[str, int]] = {}
    for user in tracked_users:
        user_stats[user] = {
            "total": 0,
            "draft": 0,
            "open": 0,
            "merged": 0,
            "closed": 0,
        }

    for repo in repositories.values():
        for pr in repo.prs.values():
            if pr.author in user_stats:
                stats = user_stats[pr.author]
                stats["total"] += 1
                stats[pr.status] += 1

    # Generate markdown
    lines = [
        "# ImprovIt Dashboard",
        "",
        "Tracking improveit tool PRs (codespell, shellcheck) across GitHub repositories.",
        "",
        "## Summary",
        "",
        f"*Last updated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
    ]

    # Overall stats
    total_repos = len(repositories)
    total_prs = sum(len(repo.prs) for repo in repositories.values())
    total_merged = sum(repo.merged_count for repo in repositories.values())
    total_open = sum(repo.open_count for repo in repositories.values())

    lines.extend(
        [
            f"- **Repositories tracked**: {total_repos}",
            f"- **Total PRs**: {total_prs}",
            f"- **Merged**: {total_merged}",
            f"- **Open**: {total_open}",
            "",
        ]
    )

    # Per-user summary table
    lines.extend(
        [
            "## Contributors",
            "",
            "| User | Total | Draft | Open | Merged | Closed |",
            "|------|-------|-------|------|--------|--------|",
        ]
    )

    for user in sorted(tracked_users):
        stats = user_stats.get(user, {"total": 0, "draft": 0, "open": 0, "merged": 0, "closed": 0})

        # Format counts as links if > 0
        def link_count(count: int, status: str, username: str) -> str:
            if count > 0:
                return f"[{count}](READMEs/{username}/{status}.md)"
            return str(count)

        total_link = f"[{stats['total']}](READMEs/{user}.md)" if stats["total"] > 0 else "0"
        draft_link = link_count(stats["draft"], "draft", user)
        open_link = link_count(stats["open"], "open", user)
        merged_link = link_count(stats["merged"], "merged", user)
        closed_link = link_count(stats["closed"], "closed", user)

        lines.append(
            f"| [{user}](https://github.com/{user}) "
            f"| {total_link} "
            f"| {draft_link} "
            f"| {open_link} "
            f"| {merged_link} "
            f"| {closed_link} |"
        )

    lines.append("")

    # Repository behavior summary (with overrides applied)
    behavior_counts: dict[str, int] = {
        "welcoming": 0,
        "selective": 0,
        "unresponsive": 0,
        "hostile": 0,
        "insufficient_data": 0,
    }
    for repo in repositories.values():
        # Use override if present, otherwise use calculated category
        category = overrides.get(repo.full_name, repo.behavior_category)
        behavior_counts[category] += 1

    if any(v > 0 for k, v in behavior_counts.items() if k != "insufficient_data"):
        lines.extend(
            [
                "## Repository Responsiveness",
                "",
                "Repositories are categorized based on their response patterns to improveit PRs.",
                "Categories are determined by response time (time to first maintainer comment) and",
                "acceptance rate (percentage of PRs merged vs closed without merge).",
                "",
                "| Category | Count | Description |",
                "|----------|-------|-------------|",
            ]
        )

        for category in ["welcoming", "selective", "unresponsive", "hostile", "insufficient_data"]:
            count = behavior_counts[category]
            info = BEHAVIOR_INFO[category]
            if count > 0:
                link = f"[{count}](Summaries/responsiveness/{info['file']})"
            else:
                link = str(count)
            lines.append(f"| {info['display']} | {link} | {info['description']} |")

        lines.append("")

    # Footer
    lines.extend(
        [
            "---",
            "",
            "*Generated by [improveit-dashboard](https://github.com/yarikoptic/improveit-dashboard)*",
        ]
    )

    # Write output only if there are meaningful changes
    write_if_changed(output_path, "\n".join(lines) + "\n")

    logger.info(f"Generated dashboard with {len(tracked_users)} users, {total_prs} PRs")


def generate_responsiveness_reports(
    repositories: dict[str, Repository],
    output_dir: Path,
    behavior_overrides: dict[str, str] | None = None,
) -> list[Path]:
    """Generate per-category responsiveness detail files.

    Creates:
    - {output_dir}/responsiveness/welcoming.md
    - {output_dir}/responsiveness/selective.md
    - {output_dir}/responsiveness/unresponsive.md
    - {output_dir}/responsiveness/hostile.md
    - {output_dir}/responsiveness/insufficient_data.md

    Args:
        repositories: Dict mapping full_name to Repository
        output_dir: Base output directory (e.g., Summaries/)
        behavior_overrides: Optional dict mapping repo full_name to behavior category override

    Returns:
        List of generated file paths
    """
    overrides = behavior_overrides or {}
    responsiveness_dir = output_dir / "responsiveness"
    responsiveness_dir.mkdir(parents=True, exist_ok=True)
    generated_paths: list[Path] = []

    # Group repositories by behavior category (with overrides applied)
    repos_by_category: dict[str, list[Repository]] = {
        "welcoming": [],
        "selective": [],
        "unresponsive": [],
        "hostile": [],
        "insufficient_data": [],
    }

    for repo in repositories.values():
        # Use override if present, otherwise use calculated category
        category = overrides.get(repo.full_name, repo.behavior_category)
        repos_by_category[category].append(repo)

    # Sort repos in each category by name
    for repos in repos_by_category.values():
        repos.sort(key=lambda r: r.full_name.lower())

    # Generate a file for each category
    for category, repos in repos_by_category.items():
        info = BEHAVIOR_INFO[category]
        output_path = responsiveness_dir / info["file"]

        lines = [
            f"# {info['display']} Repositories",
            "",
            f"*Last updated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
            "[< Back to Dashboard](../../README.md)",
            "",
            f"**Category**: {info['display']}",
            f"**Description**: {info['description']}",
            f"**Count**: {len(repos)} repositories",
            "",
        ]

        if not repos:
            lines.append("*No repositories in this category.*")
        else:
            # Repository table
            lines.extend(
                [
                    "## Repositories",
                    "",
                    "| Repository | PRs | Merged | Closed | Acceptance | Avg Response |",
                    "|------------|-----|--------|--------|------------|--------------|",
                ]
            )

            for repo in repos:
                merged = repo.merged_count
                closed = sum(1 for pr in repo.prs.values() if pr.status == "closed")
                total = len(repo.prs)

                # Calculate acceptance rate
                decided = merged + closed
                if decided > 0:
                    acceptance = f"{(merged / decided * 100):.0f}%"
                else:
                    acceptance = "-"

                # Calculate average response time
                response_times = [
                    pr.time_to_first_response_hours
                    for pr in repo.prs.values()
                    if pr.time_to_first_response_hours is not None
                ]
                if response_times:
                    avg_hours = sum(response_times) / len(response_times)
                    if avg_hours < 24:
                        avg_response = f"{avg_hours:.0f}h"
                    else:
                        avg_response = f"{avg_hours / 24:.1f}d"
                else:
                    avg_response = "-"

                lines.append(
                    f"| [{repo.full_name}](https://github.com/{repo.full_name}) "
                    f"| {total} | {merged} | {closed} | {acceptance} | {avg_response} |"
                )

            lines.append("")

            # PR details section
            lines.extend(
                [
                    "## PRs in These Repositories",
                    "",
                ]
            )

            # Collect all PRs from repos in this category
            all_prs: list[tuple[Repository, PullRequest]] = []
            for repo in repos:
                for pr in repo.prs.values():
                    all_prs.append((repo, pr))

            # Sort by updated_at descending
            all_prs.sort(key=lambda x: x[1].updated_at, reverse=True)

            if all_prs:
                lines.extend(
                    [
                        "| Repository | PR | Status | Tool | Response Time | Last Comment |",
                        "|------------|----|--------|------|---------------|--------------|",
                    ]
                )

                for repo, pr in all_prs[:50]:  # Limit to 50 most recent
                    # Response time
                    if pr.time_to_first_response_hours is not None:
                        hours = pr.time_to_first_response_hours
                        if hours < 24:
                            response_time = f"{hours:.0f}h"
                        else:
                            response_time = f"{hours / 24:.1f}d"
                    else:
                        response_time = "-"

                    # Last comment (sanitized and truncated)
                    last_comment = sanitize_and_truncate(pr.last_developer_comment_body or "-", 40)

                    lines.append(
                        f"| [{repo.full_name}](https://github.com/{repo.full_name}) "
                        f"| [#{pr.number}]({pr.url}) "
                        f"| {pr.status} "
                        f"| {pr.tool} "
                        f"| {response_time} "
                        f"| {last_comment} |"
                    )

                if len(all_prs) > 50:
                    lines.append(f"\n*Showing 50 of {len(all_prs)} PRs*")

        lines.append("")

        # Write output only if there are meaningful changes
        if write_if_changed(output_path, "\n".join(lines) + "\n"):
            generated_paths.append(output_path)
            logger.info(f"Generated {output_path} with {len(repos)} repositories")

    return generated_paths
