# ImprovIt Dashboard - Source Code

This directory contains the source code for the ImprovIt Dashboard tool.

## Installation

```bash
cd code

# Install with uv
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Usage

```bash
# Set GitHub token
export GITHUB_TOKEN="ghp_your_token"

# Run full update (discovers PRs, generates views, commits changes)
improveit-dashboard update --commit

# Run update without committing
improveit-dashboard update

# Regenerate views only (from existing data)
improveit-dashboard generate

# Export data for external analysis
improveit-dashboard export --format json -o export.json
improveit-dashboard export --filter needs-response
```

## Configuration

Edit `config.yaml` to configure:
- `tracked_users`: GitHub usernames whose PRs to track
- `tool_keywords`: Keywords to identify improveit PRs (codespell, shellcheck, etc.)
- `platforms`: Code hosting platforms (currently: github)

## Development

```bash
# Run tests
uv run pytest tests/unit -v

# Run linting
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Run type checking
uv run mypy src/improveit_dashboard

# Run all checks via tox
uv pip install tox tox-uv
tox
```

## Project Structure

- `src/improveit_dashboard/` - Main package
  - `models/` - Data models (PullRequest, Repository, etc.)
  - `controllers/` - Business logic (discovery, GitHub API, persistence)
  - `views/` - Dashboard generation (README.md, per-user reports)
  - `cli.py` - Command-line interface
- `tests/` - Test suite
- `config.yaml` - Configuration file

## Output Files

The tool generates files in the repository root (parent directory):
- `../README.md` - Main dashboard summary
- `../READMEs/` - Per-user detailed reports
- `../data/repositories.json` - Raw data store

## License

MIT License - see LICENSE file.
