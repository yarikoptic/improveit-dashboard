# GitHub API Contract

**Feature**: ImprovIt Dashboard
**Date**: 2025-11-27
**Purpose**: Define expected API interactions with GitHub REST API v3

## Overview

This contract defines all GitHub API endpoints used by the improveit-dashboard, including request formats, response schemas, error handling, and rate limiting behavior.

---

## Authentication

**Method**: Personal Access Token (classic) via HTTP header

**Required Scopes**:
- `public_repo` (read access to public repositories)
- `read:user` (for user profile information)

**Request Header**:
```http
Authorization: Bearer ghp_xxxxxxxxxxxxxxxxxxxxx
Accept: application/vnd.github.v3+json
User-Agent: improveit-dashboard/1.0
```

**Rate Limits**:
- Authenticated: 5,000 requests/hour
- Unauthenticated: 60 requests/hour
- Conditional requests (304 Not Modified): Don't count against quota

---

## API Endpoints

### 1. Search for User's Pull Requests

**Purpose**: Discover all PRs authored by tracked users

**Endpoint**: `GET /search/issues`

**Query Parameters**:
```
q: is:pr author:{username} updated:>{last_run_date}
per_page: 100
page: {page_number}
sort: updated
order: desc
```

**Example Request**:
```http
GET https://api.github.com/search/issues?q=is:pr+author:yarikoptic+updated:>2025-11-20&per_page=100&sort=updated&order=desc
Authorization: Bearer ghp_xxxx
Accept: application/vnd.github.v3+json
```

**Response Schema** (200 OK):
```json
{
  "total_count": 42,
  "incomplete_results": false,
  "items": [
    {
      "id": 2122334455,
      "number": 12912,
      "title": "Add codespell support (config+workflow)",
      "state": "open",
      "user": {
        "login": "yarikoptic",
        "type": "User"
      },
      "repository_url": "https://api.github.com/repos/kestra-io/kestra",
      "html_url": "https://github.com/kestra-io/kestra/pull/12912",
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-20T14:30:00Z",
      "closed_at": null,
      "merged_at": null,
      "pull_request": {
        "url": "https://api.github.com/repos/kestra-io/kestra/pulls/12912"
      }
    }
  ]
}
```

**Filtering Logic**:
- Must match tool keywords in title: "codespell", "shellcheck", "codespellit", "shellcheckit"
- Extract `owner/repo` from `repository_url`
- Follow `pull_request.url` to get full PR details

**Pagination**:
- GitHub returns max 100 results per page
- Use `Link` header for pagination: `<https://api.github.com/...?page=2>; rel="next"`
- Stop when no `next` link or empty results

**Error Handling**:
- **403 Forbidden**: Rate limit exceeded → check `X-RateLimit-Reset` and wait
- **422 Unprocessable Entity**: Invalid query syntax → log and skip
- **503 Service Unavailable**: GitHub downtime → retry with exponential backoff

---

### 2. Get Pull Request Details

**Purpose**: Fetch complete PR metadata including merge status, commits, files

**Endpoint**: `GET /repos/{owner}/{repo}/pulls/{number}`

**Conditional Request Headers**:
```http
If-None-Match: W/"abc123def456"  # Use stored ETag for efficiency
```

**Example Request**:
```http
GET https://api.github.com/repos/kestra-io/kestra/pulls/12912
Authorization: Bearer ghp_xxxx
Accept: application/vnd.github.v3+json
If-None-Match: W/"stored-etag"
```

**Response Schema** (200 OK):
```json
{
  "number": 12912,
  "title": "Add codespell support (config+workflow)",
  "state": "open",
  "user": {
    "login": "yarikoptic",
    "type": "User"
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-20T14:30:00Z",
  "closed_at": null,
  "merged_at": null,
  "merged": false,
  "draft": false,
  "commits": 1,                        # Available for all PRs (current count)
  "changed_files": 2,                  # Available for all PRs (current count)
  "html_url": "https://github.com/kestra-io/kestra/pull/12912",
  "base": {
    "repo": {
      "full_name": "kestra-io/kestra",
      "owner": {
        "login": "kestra-io"
      },
      "name": "kestra",
      "updated_at": "2025-01-20T15:00:00Z"
    }
  }
}
```

**Response Headers**:
```http
ETag: W/"abc123def456"
Last-Modified: Mon, 20 Jan 2025 14:30:00 GMT
X-RateLimit-Remaining: 4998
X-RateLimit-Reset: 1732723200
```

**Conditional Response** (304 Not Modified):
- No body, just headers
- Indicates PR hasn't changed since last fetch
- Does NOT count against rate limit

**Status Determination**:
```python
def determine_pr_status(pr_data):
    """Determine PR status from GitHub API response."""
    if pr_data['merged']:
        return 'merged'
    elif pr_data['state'] == 'closed':
        return 'closed'
    elif pr_data.get('draft', False):
        return 'draft'
    else:
        return 'open'  # Ready for review
```

**Error Handling**:
- **404 Not Found**: PR or repository deleted/private → mark as inaccessible
- **304 Not Modified**: No changes → skip processing
- **403 Forbidden**: Rate limit → wait

---

### 3. Get Pull Request Comments

**Purpose**: Fetch all comments to analyze engagement and identify last maintainer comment

**Endpoint**: `GET /repos/{owner}/{repo}/issues/{number}/comments`

**Note**: Use `/issues/{number}/comments` not `/pulls/{number}/comments` to get issue comments (PR comments are in issue comments API)

**Example Request**:
```http
GET https://api.github.com/repos/kestra-io/kestra/issues/12912/comments?per_page=100
Authorization: Bearer ghp_xxxx
Accept: application/vnd.github.v3+json
```

**Response Schema** (200 OK):
```json
[
  {
    "id": 998877665,
    "user": {
      "login": "maintainer-user",
      "type": "User"
    },
    "body": "Thanks for the contribution! LGTM.",
    "created_at": "2025-01-20T14:25:00Z",
    "updated_at": "2025-01-20T14:25:00Z"
  },
  {
    "id": 998877666,
    "user": {
      "login": "github-actions[bot]",
      "type": "Bot"
    },
    "body": "All checks passed ✅",
    "created_at": "2025-01-20T14:20:00Z",
    "updated_at": "2025-01-20T14:20:00Z"
  }
]
```

**Processing Logic**:
```python
def classify_comment(comment, pr_author):
    user = comment['user']
    if user['type'] == 'Bot' or user['login'].endswith('[bot]'):
        return 'bot'
    elif user['login'] == pr_author:
        return 'submitter'
    else:
        return 'maintainer'
```

**Metrics Extraction**:
- Count comments by type (submitter, maintainer, bot)
- Find last comment where `user.type != 'Bot'` and `user.login != pr_author`
- Calculate `time_to_first_response` = first maintainer comment timestamp - PR created_at

**Pagination**: Same as search endpoint (100 per page, use `Link` header)

---

### 4. Get Pull Request Files

**Purpose**: Detect automation types by analyzing changed files

**Endpoint**: `GET /repos/{owner}/{repo}/pulls/{number}/files`

**Example Request**:
```http
GET https://api.github.com/repos/kestra-io/kestra/pulls/12912/files
Authorization: Bearer ghp_xxxx
Accept: application/vnd.github.v3+json
```

**Response Schema** (200 OK):
```json
[
  {
    "filename": ".github/workflows/codespell.yml",
    "status": "added",
    "additions": 20,
    "deletions": 0,
    "patch": "@@ -0,0 +1,20 @@\n+name: Codespell\n..."
  },
  {
    "filename": ".codespellrc",
    "status": "added",
    "additions": 5,
    "deletions": 0
  }
]
```

**Automation Detection Logic**:
```python
def detect_automation_types(files):
    types = set()
    for file in files:
        path = file['filename']
        if '.github/workflows/' in path and path.endswith('.yml'):
            types.add('github-actions')
        if path == '.pre-commit-config.yaml':
            types.add('pre-commit')
        if path in ['.codespellrc', 'setup.cfg', 'pyproject.toml', 'tox.ini']:
            types.add('config-file')
        if 'shellcheck' in path.lower():
            types.add('shellcheck-config')
    return list(types)
```

**Adoption Level Logic**:
- `github-actions` in types → `"full_automation"`
- `pre-commit` in types → `"full_automation"`
- Only `config-file` → `"config_only"`
- No automation files but other changes → `"typo_fixes"`
- PR closed without merge → `"rejected"`

---

### 5. Get Repository Metadata

**Purpose**: Check if repository is still accessible and get last update timestamp

**Endpoint**: `GET /repos/{owner}/{repo}`

**Example Request**:
```http
GET https://api.github.com/repos/kestra-io/kestra
Authorization: Bearer ghp_xxxx
Accept: application/vnd.github.v3+json
```

**Response Schema** (200 OK):
```json
{
  "full_name": "kestra-io/kestra",
  "owner": {
    "login": "kestra-io"
  },
  "name": "kestra",
  "private": false,
  "updated_at": "2025-01-20T15:00:00Z",
  "pushed_at": "2025-01-20T14:35:00Z"
}
```

**Error Handling**:
- **404 Not Found**: Repository deleted or made private → mark `accessible: false`
- **403 Forbidden**: DMCA takedown or access restrictions → mark `accessible: false`

---

## Rate Limiting Strategy

### Monitoring

After **every** API request, check response headers:
```python
def check_rate_limit(response):
    remaining = int(response.headers.get('X-RateLimit-Remaining', 5000))
    reset_timestamp = int(response.headers.get('X-RateLimit-Reset', 0))
    limit = int(response.headers.get('X-RateLimit-Limit', 5000))

    logger.info(f"Rate limit: {remaining}/{limit} remaining, resets at {reset_timestamp}")

    if remaining < 100:  # Low threshold
        wait_seconds = reset_timestamp - time.time()
        logger.warning(f"Rate limit low ({remaining}), waiting {wait_seconds}s until reset")
        time.sleep(max(0, wait_seconds))

    if remaining < 10:  # Critical threshold
        raise RateLimitError("Rate limit critically low, aborting run")
```

### Optimization Techniques

1. **Conditional Requests**: Always send `If-None-Match` header with stored ETag
2. **Incremental Discovery**: Use `updated:>YYYY-MM-DD` in search queries
3. **Batch Persistence**: Save model every 10 PRs to allow resume on rate limit abort
4. **Repository-First**: Check repo `updated_at` before fetching all PR details

---

## Error Response Examples

### Rate Limit Exceeded (403)
```json
{
  "message": "API rate limit exceeded for user ID 12345.",
  "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"
}
```
**Headers**:
```
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1732723200
Retry-After: 3600
```

**Handling**: Sleep until `X-RateLimit-Reset`, then retry

---

### Invalid Token (401)
```json
{
  "message": "Bad credentials",
  "documentation_url": "https://docs.github.com/rest"
}
```

**Handling**: Fatal error, log and exit with clear message to user

---

### Repository Not Found (404)
```json
{
  "message": "Not Found",
  "documentation_url": "https://docs.github.com/rest/reference/repos#get-a-repository"
}
```

**Handling**: Mark repository as `accessible: false`, skip further processing

---

## Testing Strategy

### Unit Tests (Mocked)
```python
@pytest.mark.ai_generated
def test_github_client_fetch_pr_success(mock_requests):
    mock_response = Mock(
        status_code=200,
        json=lambda: {"number": 12912, "title": "Add codespell", ...},
        headers={'ETag': 'W/"abc123"', 'X-RateLimit-Remaining': '4999'}
    )
    mock_requests.get.return_value = mock_response

    client = GitHubClient(token="fake-token")
    pr_data = client.fetch_pr("kestra-io/kestra", 12912)

    assert pr_data['number'] == 12912
    mock_requests.get.assert_called_once()
```

### Integration Tests (Live API)
```python
@pytest.mark.integration
@pytest.mark.ai_generated
def test_fetch_real_kestra_pr():
    """Test against actual kestra-io/kestra#12912"""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        pytest.skip("GITHUB_TOKEN not set")

    client = GitHubClient(token=token)
    pr_data = client.fetch_pr("kestra-io/kestra", 12912)

    assert pr_data['number'] == 12912
    assert 'codespell' in pr_data['title'].lower()
    assert pr_data['user']['login'] == 'yarikoptic'
```

---

## API Call Budget Estimate

For processing 100 PRs across 30 repositories:

| Operation | Calls | Notes |
|-----------|-------|-------|
| Search user PRs | 1-3 | Paginated, max 3 pages for 100 PRs |
| Fetch PR details | 100 | One per PR (304 responses don't count) |
| Fetch comments | 100 | One per PR |
| Fetch files | 100 | One per PR |
| Check repository | 30 | One per unique repo |
| **Total** | **~330** | Well under 5000/hour limit |

With incremental updates and ETags:
- 80% of PRs return 304 → only ~100 calls for unchanged PRs
- **Optimized total**: ~130 calls per run

---

## Contract Versioning

**Version**: 1.0 (GitHub REST API v3)

**Future Extensions**:
- GraphQL API for batch operations (fetch multiple PRs in one call)
- GitHub App authentication for higher rate limits
- Webhook support for real-time updates
