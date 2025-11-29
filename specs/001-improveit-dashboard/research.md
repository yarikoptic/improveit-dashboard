# Research & Technical Decisions

**Feature**: ImprovIt Dashboard
**Date**: 2025-11-27
**Purpose**: Resolve technical unknowns from Technical Context and establish best practices

## Research Tasks

### 1. GitHub API Library Selection

**Decision**: Use **requests** library with direct GitHub REST API v3 calls

**Rationale**:
- **Simplicity**: Direct HTTP calls give full control over API interactions without library abstraction overhead
- **Flexibility**: Easy to handle custom scenarios (pagination, rate limiting, conditional requests)
- **Minimal dependencies**: `requests` is universally available and well-understood
- **Documentation**: GitHub REST API v3 is well-documented with clear examples
- **Type safety**: Can define our own typed response models matching our domain needs
- **Incremental updates**: Easier to implement `If-Modified-Since` headers and ETags for efficient polling

**Alternatives Considered**:
- **PyGithub**: Higher-level abstraction but adds complexity, less control over rate limiting, heavier dependency, less transparent caching
- **httpx**: Modern async support but adds async complexity we don't need for scheduled batch processing
- **ghapi**: Lightweight but less mature, smaller community

**Implementation Notes**:
- Use `requests.Session()` for connection pooling and header defaults
- Implement custom `GitHubClient` class wrapping `requests` with rate limit handling
- Set `Accept: application/vnd.github.v3+json` header for API version pinning
- Store ETag and Last-Modified headers for incremental updates

---

### 2. Incremental Update Strategy

**Decision**: **Timestamp-based polling with ETag/Last-Modified caching**

**Rationale**:
- **Simplicity**: No webhook infrastructure needed, works locally and on GitHub Actions
- **Efficiency**: Conditional requests (`If-Modified-Since`, `If-None-Match`) return 304 Not Modified, consuming minimal rate limit quota
- **Reliability**: Polling guarantees eventual consistency without webhook delivery concerns
- **State management**: Track last successful run timestamp in model JSON
- **Multi-PR tracking**: Can efficiently check multiple PRs per repository by checking repository last push time first
- **Crash recovery**: On restart, resume from last persisted timestamp

**Alternatives Considered**:
- **GitHub Webhooks**: Requires public endpoint, complex setup, not suitable for local execution, overkill for batch processing
- **Event-based (GraphQL timeline)**: More API calls, more complex pagination, harder to ensure we catch all events
- **Full re-scan**: Simple but wasteful of API quota and processing time

**Implementation Strategy**:
1. Store `last_updated` timestamp in model
2. For each tracked PR:
   - Check repository `updated_at` first (cheap API call)
   - If repo updated since last run, fetch PR details with `If-None-Match: <etag>`
   - If 304 response, skip processing (no changes)
   - If 200 response, update model and store new ETag
3. For discovery: Search API with `updated:>YYYY-MM-DD` filter
4. Prioritize processing: new PRs → recently updated PRs → unchanged PRs (skip in normal mode)

**Performance Impact**:
- 80%+ reduction in API calls through 304 responses
- 90%+ reduction in processing time for unchanged PRs

---

### 3. Rate Limit Handling Approach

**Decision**: **Exponential backoff with rate limit budget tracking**

**Rationale**:
- **Proactive**: Check `X-RateLimit-Remaining` header after each request
- **Predictive**: Calculate time until reset using `X-RateLimit-Reset` header
- **Adaptive**: Slow down when approaching limit, avoid hard failures
- **Transparent**: Log rate limit status for monitoring
- **GitHub Actions friendly**: Can pause execution and resume within workflow timeout

**Implementation**:
```python
class RateLimitHandler:
    def check_and_wait(self, response):
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        reset_timestamp = int(response.headers.get('X-RateLimit-Reset', 0))

        if remaining < 100:  # Low threshold
            wait_time = reset_timestamp - time.time()
            if wait_time > 0:
                logger.warning(f"Rate limit low ({remaining}), waiting {wait_time}s")
                time.sleep(wait_time)

        if remaining < 10:  # Critical threshold
            raise RateLimitError("Rate limit critically low, aborting run")
```

**Alternatives Considered**:
- **Sleep after every request**: Too slow, wastes time when quota is abundant
- **Queue-based throttling**: Overengineered for sequential batch processing
- **Ignore until failure**: Risky, causes failed runs and missed updates

**Best Practices**:
- Use authenticated requests (5000/hour vs 60/hour unauthenticated)
- Leverage conditional requests (304 responses don't count against quota)
- Batch operations where possible (GraphQL for multiple items, but we're using REST for simplicity)
- Monitor quota in logs for debugging

---

### 4. Bot Detection Strategy

**Decision**: Use GitHub's `[bot]` suffix convention and user type API field

**Rationale**:
- GitHub API returns `user.type` field: `"User"`, `"Bot"`, or `"Organization"`
- Most bots have `[bot]` suffix in username (e.g., `dependabot[bot]`, `github-actions[bot]`)
- Combination provides 99%+ accuracy

**Implementation**:
```python
def is_bot_comment(comment_data):
    user = comment_data['user']
    return (
        user['type'] == 'Bot' or
        user['login'].endswith('[bot]')
    )
```

**Known Edge Cases**:
- Legacy bots without `[bot]` suffix: Maintain allowlist if needed
- Humans with "[bot]" in username: Rare, acceptable false positive
- Organization accounts: Treated as non-bot (human maintainers)

---

### 5. Automation Type Detection

**Decision**: File path pattern matching on PR changed files

**Rationale**:
- GitHub API provides `files` list in PR response
- File paths clearly indicate automation type:
  - `.github/workflows/*.yml` → GitHub Actions
  - `.pre-commit-config.yaml` → pre-commit hooks
  - `.codespellrc`, `pyproject.toml` with `[tool.codespell]` → codespell config
  - `tox.ini`, `.travis.yml`, `Jenkinsfile` → other CI

**Implementation**:
```python
def detect_automation_types(pr_files):
    types = set()
    for file in pr_files:
        path = file['filename']
        if '.github/workflows/' in path:
            types.add('github-actions')
        elif path == '.pre-commit-config.yaml':
            types.add('pre-commit')
        elif any(x in path for x in ['.codespellrc', 'setup.cfg', 'pyproject.toml']):
            types.add('codespell-config')
        # Add more patterns as needed
    return list(types)
```

---

### 6. Testing Strategy with Live GitHub API

**Decision**: Hybrid approach - mocked unit tests + live integration tests with sample PRs

**Rationale**:
- **Unit tests**: Mock `requests` responses, fast, no API quota usage, test edge cases
- **Integration tests**: Use real sample PRs (kestra-io/kestra#12912, pydicom/pydicom#2169), validate against actual API behavior
- **CI execution**: Integration tests run on CI to verify GitHub authentication works
- **Local execution**: Developers can skip integration tests if no token available

**Implementation**:
```python
# tests/unit/test_github_client.py (mocked)
@pytest.mark.ai_generated
def test_fetch_pr_details_success(mock_requests):
    mock_requests.get.return_value = Mock(status_code=200, json=lambda: {...})
    # ... test logic

# tests/integration/test_github_api.py (live)
@pytest.mark.integration
@pytest.mark.ai_generated
def test_fetch_real_pr():
    """Test against kestra-io/kestra#12912"""
    client = GitHubClient(token=os.getenv('GITHUB_TOKEN'))
    pr = client.fetch_pr('kestra-io/kestra', 12912)
    assert pr['number'] == 12912
    assert 'codespell' in pr['title'].lower()
```

**Tox configuration**:
```ini
[testenv]
commands =
    pytest tests/unit -v
    pytest tests/integration -v -m "not integration or integration and env_github_token"
```

---

### 7. Model Persistence Format

**Decision**: Single JSON file with nested structure, similar to datalad-usage-dashboard

**Rationale**:
- **Simple**: One file, easy to read, version, and backup
- **Atomic writes**: Write to temp file, then rename for crash safety
- **Git-friendly**: JSON diffs are readable in git history
- **Proven**: datalad-usage-dashboard pattern validated in production

**Schema**:
```json
{
  "meta": {
    "last_updated": "2025-11-27T12:00:00Z",
    "version": "1.0"
  },
  "repositories": {
    "owner/repo": {
      "platform": "github",
      "prs": {
        "123": {
          "number": 123,
          "title": "Add codespell CI",
          "status": "merged",
          "tool": "codespell",
          "created_at": "2025-01-15T10:00:00Z",
          "merged_at": "2025-01-20T14:30:00Z",
          "comments": [...],
          "automation_types": ["github-actions"],
          "etag": "W/\"abc123\""
        }
      }
    }
  }
}
```

**Alternatives Considered**:
- **One file per PR**: Too many files, harder to query across PRs
- **SQLite database**: Overkill, less transparent, harder to version in git
- **Multiple JSON files by status**: Complicates atomic updates

---

## Best Practices Summary

### Python Development (from user preferences)
- Use `uv` for dependency management (`uv venv`, `uv pip install`, `uv run`)
- Use `tox` with `tox-uv` for test orchestration
- Mark AI-generated tests with `@pytest.mark.ai_generated`
- Avoid process `chdir` in tests, use `cwd` parameter instead
- Use type hints throughout (Python 3.11+ syntax)

### GitHub Actions
- Use `secrets.GITHUB_TOKEN` for authentication
- Set `permissions: pull-requests: read` and `contents: read`
- Schedule cron job (e.g., `0 */6 * * *` for every 6 hours)
- Commit generated dashboard with `git config` for bot identity

### Error Handling
- Log all API errors with context (repo, PR number, operation)
- Persist model before any long operation
- On crash: Resume from last persisted state, re-process only failed items
- Surface errors in dashboard (e.g., "Last update: PARTIAL - 3 PRs failed")

### Configuration
- Store config in `config.yaml` (tracked) and `.env` (gitignored for secrets)
- Support environment variables: `GITHUB_TOKEN`, `IMPROVEIT_CONFIG_PATH`
- Default values for local development convenience

---

## Design Decisions Finalized

1. **Dashboard format**: ✅ **Multi-file structure**
   - Top-level `README.md`: Summary table with per-user statistics (total PRs, open, draft, merged, closed)
   - Per-user `READMEs/{user}.md`: Detailed PR listings with engagement metrics and automation types
   - **Rationale**: Scalability - allows each user's dashboard to grow independently, easier to navigate, better git diffs

2. **Tool detection**: ✅ **Both title keywords and file analysis**
   - Title keywords for initial discovery during search
   - File analysis for categorization and automation type detection
   - **Rationale**: Search API requires keywords, but file analysis provides accurate categorization

3. **Commit strategy**: ✅ **Commit both data and views**
   - `data/repositories.json` - source of truth
   - `README.md` and `READMEs/*.md` - generated views
   - **Rationale**: JSON provides queryability, markdown provides visibility in browser

4. **Multi-repository support**: ✅ **Single repository for all data**
   - All tracked users and their PRs in one repository
   - **Rationale**: Simplifies maintenance, unified search, single cron job

5. **Status tracking**: ✅ **Four-state model**
   - `draft` - PR not ready for review
   - `open` - PR ready for review
   - `merged` - PR accepted and merged
   - `closed` - PR closed without merge
   - **Rationale**: Draft PRs need different treatment than open PRs ready for review

6. **Metrics availability**: ✅ **All PRs have commit_count and files_changed**
   - Available from GitHub API for all PR states (not just merged)
   - **Rationale**: Useful for tracking PR evolution even before merge

7. **CLI entry point**: ✅ **`improveit-dashboard` command**
   - Installed via pyproject.toml console_scripts entry point
   - Commands: `update`, `generate`, `export`
   - **Rationale**: Clean user interface, follows Python packaging best practices

8. **Automation platform**: ✅ **GitHub Actions CI cron only**
   - No systemd or Docker deployment needed
   - Follows [datalad-usage-dashboard](https://github.com/datalad/datalad-usage-dashboard/) pattern
   - **Rationale**: Simplicity, zero server maintenance, free on GitHub
