# ImprovIt Dashboard

Dashboard to track improveit tool PRs (codespell, shellcheck) across GitHub repositories.

## Installation

```bash
# Clone repository
git clone https://github.com/yarikoptic/improveit-dashboard.git
cd improveit-dashboard

# Install with uv
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Usage

```bash
# Set GitHub token
export GITHUB_TOKEN="ghp_your_token"

# Run full update
improveit-dashboard update

# Regenerate views only
improveit-dashboard generate
```

## Configuration

Edit `config.yaml` to configure tracked users and tools.

## License

MIT License - see LICENSE file.
