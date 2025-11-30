"""PR discovery orchestration."""

from datetime import UTC, datetime
from typing import Any, cast

from improveit_dashboard.controllers.analyzer import (
    analyze_engagement,
    classify_comments,
    detect_automation_types,
    determine_adoption_level,
)
from improveit_dashboard.controllers.github_client import GitHubClient
from improveit_dashboard.controllers.persistence import load_model, save_model
from improveit_dashboard.models.config import Configuration
from improveit_dashboard.models.discovery_run import DiscoveryRun
from improveit_dashboard.models.pull_request import PRStatus, PullRequest, ToolType
from improveit_dashboard.models.repository import Repository
from improveit_dashboard.utils.logging import get_logger

logger = get_logger(__name__)


def determine_pr_status(pr_data: dict[str, Any]) -> PRStatus:
    """Determine PR status from GitHub API response.

    Args:
        pr_data: PR data from GitHub API

    Returns:
        Status string: "draft", "open", "merged", "closed"
    """
    if pr_data.get("merged"):
        return "merged"
    elif pr_data.get("state") == "closed":
        return "closed"
    elif pr_data.get("draft", False):
        return "draft"
    else:
        return "open"


def parse_datetime(dt_str: str | None) -> datetime | None:
    """Parse ISO datetime string from GitHub API."""
    if not dt_str:
        return None
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def run_discovery(
    config: Configuration,
    incremental: bool = True,
) -> DiscoveryRun:
    """Run the PR discovery process.

    Args:
        config: Configuration object
        incremental: If True, only fetch PRs updated since last run

    Returns:
        DiscoveryRun with execution metadata
    """
    run = DiscoveryRun(
        started_at=datetime.now(UTC),
        mode="force" if config.force_mode else "normal",
    )

    # Initialize client
    client = GitHubClient(
        token=config.github_token,
        rate_limit_threshold=config.rate_limit_threshold,
    )

    # Load existing model
    repositories, last_run = load_model(config.data_file)

    # Determine update cutoff
    updated_since = None
    if incremental and last_run and last_run.started_at:
        updated_since = last_run.started_at
        logger.info(f"Incremental mode: fetching PRs updated since {updated_since}")

    # Get all keywords for filtering
    all_keywords = config.get_all_keywords()

    # Track PRs to process
    prs_to_process: list[tuple[str, int, dict[str, Any]]] = []  # (repo, pr_num, search_data)

    # Search for PRs from each tracked user
    for username in config.tracked_users:
        try:
            results = client.search_user_prs(
                username=username,
                updated_since=updated_since,
                keywords=all_keywords,
            )
            for item in results:
                # Extract repo from repository_url
                repo_url = item.get("repository_url", "")
                # Format: https://api.github.com/repos/owner/repo
                parts = repo_url.rstrip("/").split("/")
                if len(parts) >= 2:
                    repo_full_name = f"{parts[-2]}/{parts[-1]}"
                    pr_number = item.get("number", 0)
                    prs_to_process.append((repo_full_name, pr_number, item))

        except Exception as e:
            error_msg = f"Failed to search PRs for {username}: {e}"
            logger.error(error_msg)
            run.errors.append(error_msg)

    logger.info(f"Found {len(prs_to_process)} PRs to process")

    # Sort PRs by processing priority:
    # 1. New PRs (not in model)
    # 2. Unmerged PRs by freshness (most recent first)
    # 3. Merged PRs (skip in normal mode)
    def get_priority(item: tuple[str, int, dict[str, Any]]) -> tuple[int, int]:
        repo_name, pr_num, data = item
        repo = repositories.get(repo_name)
        existing_pr = repo.prs.get(pr_num) if repo else None

        # New PRs get highest priority (0)
        if existing_pr is None:
            return (0, 0)

        # Merged PRs get lowest priority (2)
        if existing_pr.status == "merged":
            return (2, -existing_pr.freshness_score)

        # Unmerged PRs sorted by freshness (1)
        return (1, -existing_pr.freshness_score)

    prs_to_process.sort(key=get_priority)

    # Process PRs
    processed = 0
    for repo_name, pr_number, search_data in prs_to_process:
        # Check max PRs limit
        if config.max_prs_per_run and processed >= config.max_prs_per_run:
            logger.info(f"Reached max PRs limit ({config.max_prs_per_run})")
            break

        # Skip merged PRs in normal mode
        repo = repositories.get(repo_name)
        existing_pr = repo.prs.get(pr_number) if repo else None
        if existing_pr and existing_pr.status == "merged" and not config.force_mode:
            logger.debug(f"Skipping merged PR: {repo_name}#{pr_number}")
            continue

        try:
            # Process this PR
            was_new = _process_pr(
                client=client,
                config=config,
                repositories=repositories,
                repo_name=repo_name,
                pr_number=pr_number,
                search_data=search_data,
                run=run,
            )

            processed += 1
            run.total_processed += 1

            if was_new:
                run.new_prs += 1
            else:
                run.updated_prs += 1

        except Exception as e:
            error_msg = f"Failed to process {repo_name}#{pr_number}: {e}"
            logger.error(error_msg)
            run.errors.append(error_msg)

        # Periodic save
        if processed > 0 and processed % config.batch_size == 0:
            logger.info(f"Periodic save after {processed} PRs")
            save_model(config.data_file, repositories, run)

    # Final save
    run.completed_at = datetime.now(UTC)
    run.api_calls_made = client.api_calls
    run.rate_limit_remaining = client.rate_limit.remaining

    save_model(config.data_file, repositories, run)

    logger.info(
        f"Discovery complete: {run.new_prs} new PRs, "
        f"{run.updated_prs} updated, {run.newly_merged_prs} merged"
    )

    return run


def _process_pr(
    client: GitHubClient,
    config: Configuration,
    repositories: dict[str, Repository],
    repo_name: str,
    pr_number: int,
    search_data: dict[str, Any],
    run: DiscoveryRun,
) -> bool:
    """Process a single PR.

    Args:
        client: GitHub client
        config: Configuration
        repositories: Repositories dict to update
        repo_name: Repository full name
        pr_number: PR number
        search_data: Data from search API
        run: Discovery run to update

    Returns:
        True if this was a new PR, False if update
    """
    logger.debug(f"Processing {repo_name}#{pr_number}")

    # Get or create repository
    if repo_name not in repositories:
        owner, name = repo_name.split("/", 1)
        repositories[repo_name] = Repository(
            owner=owner,
            name=name,
            platform="github",
            url=f"https://github.com/{repo_name}",
        )
        run.new_repositories += 1

    repo = repositories[repo_name]

    # Check if PR exists
    existing_pr = repo.prs.get(pr_number)
    was_new = existing_pr is None

    # Get existing etag for conditional request
    etag = existing_pr.etag if existing_pr else None

    # Fetch PR details
    pr_data, new_etag, modified = client.fetch_pr_details(
        owner=repo.owner,
        repo=repo.name,
        pr_number=pr_number,
        etag=etag,
    )

    if not modified and existing_pr:
        # No changes, keep existing
        logger.debug(f"No changes for {repo_name}#{pr_number}")
        return False

    if not pr_data:
        # Deleted or inaccessible
        logger.warning(f"Could not fetch {repo_name}#{pr_number}")
        return False

    # Determine tool type from title
    title = pr_data.get("title", "")
    tool = cast(ToolType, config.get_tool_for_title(title))

    # Determine status
    old_status = existing_pr.status if existing_pr else None
    new_status = determine_pr_status(pr_data)

    # Track newly merged/closed
    if old_status and old_status != new_status:
        if new_status == "merged":
            run.newly_merged_prs += 1
        elif new_status == "closed":
            run.newly_closed_prs += 1

    # Create/update PR model
    now = datetime.now(UTC)
    pr = PullRequest(
        number=pr_number,
        repository=repo_name,
        platform="github",
        url=pr_data.get("html_url", f"https://github.com/{repo_name}/pull/{pr_number}"),
        tool=tool,
        title=title,
        author=pr_data.get("user", {}).get("login", "unknown"),
        created_at=parse_datetime(pr_data.get("created_at")) or now,
        updated_at=parse_datetime(pr_data.get("updated_at")) or now,
        merged_at=parse_datetime(pr_data.get("merged_at")),
        closed_at=parse_datetime(pr_data.get("closed_at")),
        status=new_status,
        analysis_status="analyzed",
        commit_count=pr_data.get("commits", 1),
        files_changed=pr_data.get("changed_files", 1),
        etag=new_etag,
        last_fetched_at=now,
    )

    # Fetch and analyze comments
    try:
        comments_data = client.fetch_pr_comments(repo.owner, repo.name, pr_number)
        comments = classify_comments(comments_data, pr.author)
        analyze_engagement(comments, pr)
    except Exception as e:
        logger.warning(f"Failed to analyze comments for {repo_name}#{pr_number}: {e}")

    # Fetch and analyze files
    try:
        files_data = client.fetch_pr_files(repo.owner, repo.name, pr_number)
        pr.automation_types = detect_automation_types(files_data)
        pr.adoption_level = determine_adoption_level(pr.automation_types, pr.status)
    except Exception as e:
        logger.warning(f"Failed to analyze files for {repo_name}#{pr_number}: {e}")

    # Fetch CI/merge status for active PRs
    if pr.is_active:
        try:
            head_sha = pr_data.get("head", {}).get("sha")
            if head_sha:
                status_data = client.fetch_pr_status(repo.owner, repo.name, pr_number, head_sha)
                pr.has_conflicts = status_data.get("has_conflicts", False)
                pr.ci_status = status_data.get("ci_status")
                pr.codespell_workflow_ci = status_data.get("codespell_workflow_ci")

                # Fetch main branch CI status
                main_branch_ci = client.fetch_branch_status(repo.owner, repo.name)
                pr.main_branch_ci = main_branch_ci
        except Exception as e:
            logger.warning(f"Failed to fetch CI status for {repo_name}#{pr_number}: {e}")

    # Add PR to repository
    repo.add_pr(pr)

    # Recalculate repository metrics
    repo.recalculate_metrics()
    repo.last_checked_at = now

    return was_new
