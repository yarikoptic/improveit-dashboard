# Quick Start Guide

**Feature**: ImprovIt Dashboard
**Target Time**: < 10 minutes from zero to running dashboard
**Prerequisites**: Python 3.11+, git, GitHub account

---

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/yarikoptic/improveit-dashboard.git
cd improveit-dashboard
```

### 2. Set Up Python Environment

Using **uv** (recommended):
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate

# Install dependencies (installs 'improveit-dashboard' CLI entry point)
uv pip install -e ".[dev]"
```

Alternative using standard Python:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Configure GitHub Token

Create a GitHub personal access token (classic):
1. Go to https://github.com/settings/tokens/new
2. Set description: "improveit-dashboard read access"
3. Select scopes: `public_repo`, `read:user`
4. Click "Generate token"
5. Copy the token (starts with `ghp_`)

Set the token as an environment variable:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

For persistence, add to `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Verify Installation
```bash
# Run tests to verify everything works
tox -e py311

# Or run directly with pytest
pytest tests/unit -v
```

---

## Basic Usage

### Run Full Update (Discovery + Dashboard Generation)
```bash
improveit-dashboard update
```

This will:
1. Search for improveit PRs from configured users (yarikoptic, DimitriPapadopoulos)
2. Fetch PR details, comments, and files
3. Analyze engagement metrics and automation types
4. Save data to `data/repositories.json`
5. Generate dashboards:
   - `README.md` - Summary table with per-user statistics
   - `READMEs/yarikoptic.md` - Detailed PR list for yarikoptic
   - `READMEs/DimitriPapadopoulos.md` - Detailed PR list for DimitriPapadopoulos

### Run Incremental Update
```bash
improveit-dashboard update --incremental
```

Only fetches PRs updated since last run (much faster).

### Regenerate Dashboards from Existing Data
```bash
improveit-dashboard generate
```

Rebuilds `README.md` and all `READMEs/{user}.md` files from `data/repositories.json` without API calls.

### Force Mode (Re-analyze Merged PRs)
```bash
improveit-dashboard update --force
```

Re-analyzes all PRs including previously merged ones.

---

## Configuration

### Config File (Optional)

Create `config.yaml` in repository root:
```yaml
tracked_users:
  - yarikoptic
  - DimitriPapadopoulos

tool_keywords:
  codespell:
    - codespell
    - codespellit
  shellcheck:
    - shellcheck
    - shellcheckit

platforms:
  - github

rate_limit_threshold: 100
batch_size: 10
```

### Environment Variables

Override config with environment variables:
```bash
export GITHUB_TOKEN="ghp_xxxxx"              # Required
export IMPROVEIT_CONFIG_PATH="config.yaml"   # Optional
export IMPROVEIT_FORCE_MODE="true"           # Optional
export IMPROVEIT_MAX_PRS="50"                # Optional (for testing)
```

---

## Local Development Workflow

### 1. Make Changes
```bash
# Edit code in src/improveit_dashboard/
vim src/improveit_dashboard/controllers/discovery.py
```

### 2. Run Tests
```bash
# Run all tests with tox (recommended)
tox

# Or run specific test suites
pytest tests/unit -v                # Unit tests only
pytest tests/integration -v -m integration  # Integration tests only
```

### 3. Lint and Format
```bash
# Run linting
tox -e lint

# Or use ruff directly
ruff check src/ tests/
ruff format src/ tests/
```

### 4. Type Check
```bash
# Run mypy
tox -e type

# Or directly
mypy src/improveit_dashboard
```

### 5. Test Against Live API
```bash
# Requires GITHUB_TOKEN set
pytest tests/integration/test_github_api.py -v
```

---

## GitHub Actions Setup (Automated Scheduled Updates)

### 1. Add Secret to Repository

1. Go to your GitHub repository settings
2. Navigate to Secrets and Variables → Actions
3. Click "New repository secret"
4. Name: `GH_DASHBOARD_TOKEN`
5. Value: Your GitHub token (from Installation step 3)

### 2. Workflow is Pre-configured

The repository includes `.github/workflows/update-dashboard.yml` (similar to [datalad-usage-dashboard](https://github.com/datalad/datalad-usage-dashboard/)):
- Runs every 6 hours on cron schedule
- Executes `improveit-dashboard update --incremental`
- Commits updated data and dashboards
- Pushes to `main` branch

### 3. Enable Workflow

1. Go to repository Actions tab
2. Enable workflows if disabled
3. Workflow will run automatically on schedule

### 4. Manual Trigger

You can manually trigger the workflow:
1. Go to Actions tab
2. Select "Update Dashboard" workflow
3. Click "Run workflow"

---

## Troubleshooting

### "Bad credentials" Error
**Problem**: GitHub token is invalid or not set.

**Solution**:
```bash
# Verify token is set
echo $GITHUB_TOKEN

# If empty, set it:
export GITHUB_TOKEN="ghp_your_token_here"
```

### "Rate limit exceeded"
**Problem**: Made too many API requests.

**Solution**:
```bash
# Check current rate limit status
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# Wait for reset (shown in response), or run with smaller batch:
python -m improveit_dashboard update --max-prs 20
```

### "No PRs found"
**Problem**: Search returned no results.

**Solution**:
- Verify `tracked_users` in config matches PR authors
- Check tool keywords match PR titles
- Try broader search date range: `--since 2024-01-01`

### Integration Tests Fail
**Problem**: Live API tests fail.

**Solution**:
```bash
# Ensure token is set
export GITHUB_TOKEN="ghp_xxxx"

# Run integration tests separately
pytest tests/integration -v -m integration

# Skip integration tests if no token
pytest tests/unit -v
```

### Import Errors
**Problem**: `ModuleNotFoundError: No module named 'improveit_dashboard'`

**Solution**:
```bash
# Ensure installed in editable mode
pip install -e .

# Or reinstall with uv
uv pip install -e ".[dev]"
```

---

## Next Steps

### Add More Tools
Edit `config.yaml` to track additional improvement tools:
```yaml
tool_keywords:
  codespell:
    - codespell
  shellcheck:
    - shellcheck
  mypy:
    - mypy
    - type hints
```

### Customize Dashboard
Edit `src/improveit_dashboard/views/dashboard.py` to change dashboard format:
- Add new sections (e.g., per-repository summaries)
- Change sorting (by date, by repo, by tool)
- Add charts/graphs (using markdown tables)

### Add New Platform Support (Future)
1. Implement new client in `controllers/` (e.g., `codeberg_client.py`)
2. Update `Configuration` model to support new platform
3. Extend discovery logic to query new API
4. Add integration tests for new platform

### Export Data for Research
```bash
# JSON data is in data/repositories.json
cat data/repositories.json | jq '.repositories[] | select(.behavior_category == "welcoming")'

# Generate CSV for analysis
improveit-dashboard export --format csv --output research.csv
```

---

## Support and Contributing

- **Issues**: https://github.com/yarikoptic/improveit-dashboard/issues
- **Contributing**: See `CONTRIBUTING.md` for guidelines
- **License**: MIT (see `LICENSE`)
- **Documentation**: See `specs/001-improveit-dashboard/` for full design docs

---

**Quick Reference Commands**:
```bash
# Full update
improveit-dashboard update

# Incremental update
improveit-dashboard update --incremental

# Regenerate dashboards only
improveit-dashboard generate

# Run tests
tox

# Check rate limit
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit
```
