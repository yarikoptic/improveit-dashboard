# improveit-dashboard Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-29

## Active Technologies

- Python 3.11+ (for uv and modern type hints support) (001-improveit-dashboard)

## Project Structure

```text
code/           # All source code lives here
  src/          # Python package
  tests/        # Test suite
  pyproject.toml
  tox.ini
  config.yaml
data/           # Generated JSON data (committed)
README.md       # Generated dashboard (auto-updated)
READMEs/        # Per-user reports (auto-updated)
```

## Commands

```bash
# All commands run from code/ directory
cd code

# Run tests
uv run pytest tests/unit -v

# Lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type check
uv run mypy src/improveit_dashboard

# Run dashboard update
GITHUB_TOKEN=... improveit-dashboard update --commit
```

## Code Style

Python 3.11+ (for uv and modern type hints support): Follow standard conventions

## Recent Changes

- 001-improveit-dashboard: Added Python 3.11+ (for uv and modern type hints support)
- Moved all code to code/ subdirectory to keep root clean for generated dashboard

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
