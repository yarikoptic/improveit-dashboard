"""Command-line interface for improveit-dashboard."""

import argparse
import logging
import sys
from pathlib import Path

from improveit_dashboard import __version__
from improveit_dashboard.controllers.discovery import run_discovery
from improveit_dashboard.controllers.persistence import load_model
from improveit_dashboard.models.config import Configuration
from improveit_dashboard.utils.logging import get_logger, setup_logging
from improveit_dashboard.views.dashboard import generate_dashboard, generate_responsiveness_reports
from improveit_dashboard.views.reports import generate_user_reports

logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="improveit-dashboard",
        description="Dashboard to track improveit tool PRs across GitHub repositories",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress non-error output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Update command
    update_parser = subparsers.add_parser(
        "update",
        help="Discover PRs and update dashboard",
    )
    update_parser.add_argument(
        "--incremental",
        action="store_true",
        default=True,
        help="Only fetch PRs updated since last run (default)",
    )
    update_parser.add_argument(
        "--full",
        action="store_true",
        help="Fetch all PRs, not just updated ones",
    )
    update_parser.add_argument(
        "--force",
        action="store_true",
        help="Re-analyze merged PRs",
    )
    update_parser.add_argument(
        "--max-prs",
        type=int,
        help="Maximum number of PRs to process",
    )
    update_parser.add_argument(
        "--no-generate",
        action="store_true",
        help="Skip view generation after update",
    )
    update_parser.add_argument(
        "--commit",
        action="store_true",
        help="Create git commit with summary of changes",
    )

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Regenerate dashboard views from existing data",
    )
    generate_parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for generated files",
    )

    # Export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export data for AI assistant processing",
    )
    export_parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Export format (default: json)",
    )
    export_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path",
    )
    export_parser.add_argument(
        "--filter",
        choices=["all", "needs-response", "open", "merged"],
        default="all",
        help="Filter PRs to export",
    )

    # Reanalyze command
    reanalyze_parser = subparsers.add_parser(
        "reanalyze",
        help="Force reanalysis of specific PRs",
    )
    reanalyze_parser.add_argument(
        "prs",
        nargs="+",
        help="PRs to reanalyze in format 'owner/repo#number' (e.g., 'kestra-io/kestra#12912')",
    )
    reanalyze_parser.add_argument(
        "--commit",
        action="store_true",
        help="Create git commit with changes",
    )

    return parser


def cmd_update(args: argparse.Namespace, config: Configuration) -> int:
    """Run the update command."""
    # Apply CLI overrides
    if args.force:
        config.force_mode = True
    if args.max_prs:
        config.max_prs_per_run = args.max_prs

    incremental = not args.full

    logger.info("Starting PR discovery...")

    try:
        run = run_discovery(config, incremental=incremental)

        # Print summary
        print("\nDiscovery complete:")
        print(f"  New repositories: {run.new_repositories}")
        print(f"  New PRs: {run.new_prs}")
        print(f"  Updated PRs: {run.updated_prs}")
        print(f"  Newly merged: {run.newly_merged_prs}")
        print(f"  Newly closed: {run.newly_closed_prs}")
        print(f"  Total processed: {run.total_processed}")
        print(f"  API calls: {run.api_calls_made}")

        if run.errors:
            print(f"\n  Errors: {len(run.errors)}")
            for error in run.errors[:5]:
                print(f"    - {error}")

        # Generate views unless --no-generate
        if not args.no_generate:
            logger.info("Generating dashboard views...")
            result = cmd_generate(args, config)
            if result != 0:
                return result

        # Create git commit if requested
        if args.commit:
            logger.info("Creating git commit...")
            result = _create_commit(run.to_commit_message())
            if result != 0:
                return result

        return 0

    except Exception as e:
        logger.error(f"Update failed: {e}")
        return 1


def _create_commit(message: str) -> int:
    """Create a git commit with the given message.

    Returns 0 on success, 1 if no changes to commit, 2 on error.
    """
    import subprocess

    try:
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--quiet"],
            capture_output=True,
        )
        staged_result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True,
        )

        # If both exit 0, there are no changes
        if result.returncode == 0 and staged_result.returncode == 0:
            print("No changes to commit")
            return 0

        # Stage all changes
        subprocess.run(["git", "add", "-A"], check=True)

        # Create commit
        subprocess.run(
            ["git", "commit", "-m", message],
            check=True,
        )

        print("Created commit with summary:")
        # Print first line of commit message
        print(f"  {message.split(chr(10))[0]}")

        return 0

    except subprocess.CalledProcessError as e:
        logger.error(f"Git commit failed: {e}")
        return 2
    except FileNotFoundError:
        logger.error("Git not found in PATH")
        return 2


def cmd_generate(args: argparse.Namespace, config: Configuration) -> int:
    """Run the generate command."""
    logger.info("Generating dashboard views...")

    try:
        # Load model
        repositories, _ = load_model(config.data_file)

        if not repositories:
            logger.warning("No data to generate views from")
            print("No PR data found. Run 'improveit-dashboard update' first.")
            return 0

        # Generate main dashboard
        generate_dashboard(
            repositories=repositories,
            output_path=config.output_readme,
            tracked_users=config.tracked_users,
        )
        print(f"Generated: {config.output_readme}")

        # Generate per-user reports
        user_reports = generate_user_reports(
            repositories=repositories,
            output_dir=config.output_readmes_dir,
            tracked_users=config.tracked_users,
        )
        for path in user_reports:
            print(f"Generated: {path}")

        # Generate responsiveness reports
        responsiveness_reports = generate_responsiveness_reports(
            repositories=repositories,
            output_dir=config.output_summaries_dir,
        )
        for path in responsiveness_reports:
            print(f"Generated: {path}")

        return 0

    except Exception as e:
        logger.error(f"Generate failed: {e}")
        return 1


def cmd_export(args: argparse.Namespace, config: Configuration) -> int:
    """Run the export command."""
    import json

    logger.info("Exporting data...")

    try:
        # Load model
        repositories, _ = load_model(config.data_file)

        if not repositories:
            logger.warning("No data to export")
            return 0

        # Collect PRs based on filter
        prs = []
        for repo in repositories.values():
            for pr in repo.prs.values():
                if args.filter == "all":
                    prs.append(pr)
                elif args.filter == "needs-response" and pr.response_status == "awaiting_submitter":
                    prs.append(pr)
                elif args.filter == "open" and pr.status in ("draft", "open"):
                    prs.append(pr)
                elif args.filter == "merged" and pr.status == "merged":
                    prs.append(pr)

        # Export
        if args.format == "json":
            output = [pr.to_dict() for pr in prs]
            content = json.dumps(output, indent=2)
        else:
            # CSV format
            import csv
            import io

            buffer = io.StringIO()
            writer = csv.writer(buffer)

            # Header
            writer.writerow(
                [
                    "repository",
                    "number",
                    "title",
                    "author",
                    "status",
                    "tool",
                    "created_at",
                    "merged_at",
                    "response_status",
                    "last_developer_comment_body",
                ]
            )

            # Data
            for pr in prs:
                writer.writerow(
                    [
                        pr.repository,
                        pr.number,
                        pr.title,
                        pr.author,
                        pr.status,
                        pr.tool,
                        pr.created_at.isoformat(),
                        pr.merged_at.isoformat() if pr.merged_at else "",
                        pr.response_status,
                        pr.last_developer_comment_body or "",
                    ]
                )

            content = buffer.getvalue()

        # Output
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content)
            print(f"Exported {len(prs)} PRs to {args.output}")
        else:
            print(content)

        return 0

    except Exception as e:
        logger.error(f"Export failed: {e}")
        return 1


def cmd_reanalyze(args: argparse.Namespace, config: Configuration) -> int:
    """Force reanalysis of specific PRs."""
    from improveit_dashboard.controllers.analyzer import analyze_engagement, classify_comments
    from improveit_dashboard.controllers.github_client import GitHubClient

    logger.info(f"Reanalyzing {len(args.prs)} PRs...")

    # Initialize client
    client = GitHubClient(
        token=config.github_token,
        rate_limit_threshold=config.rate_limit_threshold,
    )

    # Load existing model
    repositories, last_run = load_model(config.data_file)

    reanalyzed = 0
    for pr_spec in args.prs:
        try:
            # Parse PR spec: owner/repo#number
            if "#" not in pr_spec:
                logger.error(f"Invalid PR format: {pr_spec} (expected owner/repo#number)")
                continue

            repo_part, number_part = pr_spec.rsplit("#", 1)
            pr_number = int(number_part)

            if "/" not in repo_part:
                logger.error(f"Invalid repo format: {repo_part} (expected owner/repo)")
                continue

            owner, repo_name = repo_part.split("/", 1)
            full_name = f"{owner}/{repo_name}"

            # Find PR in model
            if full_name not in repositories:
                logger.warning(f"Repository {full_name} not found in model")
                continue

            repo = repositories[full_name]
            if pr_number not in repo.prs:
                logger.warning(f"PR {pr_spec} not found in model")
                continue

            pr = repo.prs[pr_number]
            logger.info(f"Reanalyzing {pr_spec}: {pr.title}")

            # Fetch and reclassify comments
            comments_data = client.fetch_pr_comments(owner, repo_name, pr_number)
            comments = classify_comments(comments_data, pr.author)
            analyze_engagement(comments, pr)

            print(f"  Reanalyzed {pr_spec}:")
            print(f"    Total comments: {pr.total_comments}")
            print(f"    Bot comments: {pr.bot_comments}")
            print(f"    Maintainer comments: {pr.maintainer_comments}")
            print(f"    Response status: {pr.response_status}")
            if pr.last_developer_comment_body:
                snippet = pr.last_developer_comment_body[:100]
                if len(pr.last_developer_comment_body) > 100:
                    snippet += "..."
                print(f"    Last developer comment: {snippet}")

            reanalyzed += 1

        except Exception as e:
            logger.error(f"Failed to reanalyze {pr_spec}: {e}")

    if reanalyzed > 0:
        # Save updated model
        from improveit_dashboard.controllers.persistence import save_model

        save_model(config.data_file, repositories, last_run)
        print(f"\nReanalyzed {reanalyzed} PRs")

        # Regenerate views
        logger.info("Regenerating views...")
        generate_dashboard(
            repositories=repositories,
            output_path=config.output_readme,
            tracked_users=config.tracked_users,
        )
        generate_user_reports(
            repositories=repositories,
            output_dir=config.output_readmes_dir,
            tracked_users=config.tracked_users,
        )
        generate_responsiveness_reports(
            repositories=repositories,
            output_dir=config.output_summaries_dir,
        )

        # Commit if requested
        if args.commit:
            pr_list = ", ".join(args.prs[:3])
            if len(args.prs) > 3:
                pr_list += f" (+{len(args.prs) - 3} more)"
            message = f"Reanalyze PRs: {pr_list}\n\nForced reanalysis with updated bot detection."
            result = _create_commit(message)
            if result != 0:
                return result

    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Setup logging
    if args.quiet:
        level = logging.ERROR
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    setup_logging(level=level)

    # Load configuration
    config = Configuration.from_file(args.config)
    # Apply environment variable overrides
    env_config = Configuration.from_env()
    if env_config.github_token:
        config.github_token = env_config.github_token
    if env_config.force_mode:
        config.force_mode = env_config.force_mode
    if env_config.max_prs_per_run:
        config.max_prs_per_run = env_config.max_prs_per_run

    # Validate config
    errors = config.validate()
    if errors:
        for error in errors:
            logger.error(f"Configuration error: {error}")
        return 1

    # Check for token
    if not config.github_token:
        logger.error("GITHUB_TOKEN not set. Set it via environment variable or config file.")
        return 1

    # Dispatch command
    if args.command == "update":
        return cmd_update(args, config)
    elif args.command == "generate":
        return cmd_generate(args, config)
    elif args.command == "export":
        return cmd_export(args, config)
    elif args.command == "reanalyze":
        return cmd_reanalyze(args, config)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
