# Data Model

**Feature**: ImprovIt Dashboard
**Date**: 2025-11-27
**Purpose**: Define data entities, relationships, and validation rules

## Overview

The data model follows the MVC architecture with clear separation between domain entities (models), persistence format (JSON), and presentation (markdown views). All entities are defined as Python dataclasses with type hints for validation and clarity.

**Dashboard Structure**:
- **Top-level README.md**: Summary table with per-user statistics with links to detailed dashboards
  - Columns: User | Total PRs | Draft | Open | Merged | Closed
  - Status counts link to `READMEs/{user}/{status}.md` files
- **READMEs/{user}.md**: Summary for each tracked user
  - Contains only "Needs Your Response" section (PRs awaiting submitter action)
  - Links to per-status files for full listings
- **READMEs/{user}/{status}.md**: Per-status PR tables (draft.md, open.md, merged.md, closed.md)
  - Contains full PR tables for that status
  - Shows: PR title, repository, dates, commit count, files changed, comments, automation types
  - Includes engagement metrics: time-to-first-response, awaiting status
  - Includes CI/merge status: has_conflicts, ci_status, main_branch_ci, codespell_workflow_ci

---

## Entity Definitions

### 1. PullRequest

Represents a single improveit PR submission with all tracked metadata.

**Fields**:
```python
@dataclass
class PullRequest:
    # Identity
    number: int                          # PR number in repository
    repository: str                      # "owner/repo" format
    platform: str                        # "github" (future: "codeberg")
    url: str                             # Full PR URL

    # Classification
    tool: str                            # "codespell", "shellcheck", etc.
    title: str                           # PR title
    author: str                          # GitHub username

    # Timestamps
    created_at: datetime                 # PR submission time
    updated_at: datetime                 # Last activity (for freshness)
    merged_at: datetime | None           # Merge timestamp (if merged)
    closed_at: datetime | None           # Close timestamp (if closed without merge)

    # Status
    status: str                          # "draft", "open", "merged", "closed"
    analysis_status: str                 # "never_analyzed", "analyzed", "needs_reanalysis"

    # Metrics
    commit_count: int                    # Current number of commits in PR
    files_changed: int                   # Current number of files changed in PR
    automation_types: list[str]          # ["github-actions", "pre-commit", ...]
    adoption_level: str                  # "full_automation", "config_only", "typo_fixes", "rejected"

    # Engagement
    total_comments: int                  # Total comment count
    submitter_comments: int              # Comments from PR author
    maintainer_comments: int             # Comments from non-author humans
    bot_comments: int                    # Comments from bots
    last_comment_author: str | None      # Username of last commenter
    last_comment_is_maintainer: bool     # True if last comment from non-author
    last_maintainer_comment_at: datetime | None  # Timestamp of last maintainer comment

    # Research metrics
    time_to_first_response_hours: float | None   # Time until first non-bot comment
    days_awaiting_submitter: int | None          # Days since last maintainer comment (if awaiting)
    response_status: str                         # "awaiting_submitter", "awaiting_maintainer", "no_response"

    # Incremental update support
    etag: str | None                     # GitHub ETag for conditional requests
    last_fetched_at: datetime            # When this PR was last fetched from API

    # Context for AI assistant export
    last_developer_comment_body: str | None  # Text of last non-author comment

    # CI and merge status
    has_conflicts: bool                  # True if PR has merge conflicts
    ci_status: str | None                # Overall CI status: "success", "failure", "pending", None
    main_branch_ci: str | None           # CI status on main/master branch: "success", "failure", "pending", None
    codespell_workflow_ci: str | None    # Codespell workflow status if present: "success", "failure", "pending", None
```

**Validation Rules**:
- `status` must be one of: `"draft"`, `"open"`, `"merged"`, `"closed"`
  - `"draft"`: PR is in draft state (not ready for review)
  - `"open"`: PR is open and ready for review
  - `"merged"`: PR has been merged
  - `"closed"`: PR was closed without merging
- `analysis_status` must be one of: `"never_analyzed"`, `"analyzed"`, `"needs_reanalysis"`
- `response_status` must be one of: `"awaiting_submitter"`, `"awaiting_maintainer"`, `"no_response"`
- `adoption_level` must be one of: `"full_automation"`, `"config_only"`, `"typo_fixes"`, `"rejected"`
- `tool` must be one of: `"codespell"`, `"shellcheck"`, `"other"`
- If `status == "merged"`, `merged_at` must not be None
- If `status == "closed"`, either `merged_at` or `closed_at` must not be None
- `total_comments >= submitter_comments + maintainer_comments + bot_comments`
- `commit_count` must be >= 1 (all PRs have at least one commit)
- `files_changed` must be >= 1 (all PRs change at least one file)

**Derived Fields** (computed, not stored):
```python
@property
def is_active(self) -> bool:
    """True if PR is draft or open (not merged/closed)."""
    return self.status in ("draft", "open")

@property
def is_ready_for_review(self) -> bool:
    """True if PR is open and ready for review (not draft)."""
    return self.status == "open"

@property
def freshness_score(self) -> int:
    """Timestamp for sorting (higher = more recent)."""
    return int(self.updated_at.timestamp())
```

**State Transitions**:

Analysis status:
```
never_analyzed → analyzed (after first API fetch)
analyzed → needs_reanalysis (when updated_at changes)
needs_reanalysis → analyzed (after re-fetch in force mode)
```

PR status:
```
draft → open (when marked ready for review)
draft → closed (if closed while still draft)
open → merged (when merged)
open → closed (if closed without merge)
open → draft (if converted back to draft)
```

---

### 2. Repository

Represents a repository that received improveit PRs, with aggregate metrics.

**Fields**:
```python
@dataclass
class Repository:
    # Identity
    owner: str                           # Repository owner username/org
    name: str                            # Repository name
    platform: str                        # "github"
    full_name: str                       # "owner/name"
    url: str                             # Repository URL

    # PR tracking (keyed by PR number)
    prs: dict[int, PullRequest]          # All PRs submitted to this repo

    # Per-tool tracking
    codespell_prs: list[int]             # PR numbers for codespell tool
    shellcheck_prs: list[int]            # PR numbers for shellcheck tool
    other_prs: list[int]                 # PR numbers for other tools

    # Access status
    accessible: bool                     # False if repo became private/deleted

    # Research metrics (aggregated)
    avg_time_to_first_response_hours: float | None
    pr_acceptance_rate: float            # merged_count / total_count
    avg_engagement_level: float          # avg comments per PR
    behavior_category: str               # "welcoming", "selective", "unresponsive", "hostile"

    # Incremental update
    last_checked_at: datetime            # When this repo was last queried
    repository_updated_at: datetime      # From GitHub API push timestamp
```

**Validation Rules**:
- `full_name` must equal `f"{owner}/{name}"`
- `pr_acceptance_rate` must be between 0.0 and 1.0
- `behavior_category` must be one of: `"welcoming"`, `"selective"`, `"unresponsive"`, `"hostile"`, `"insufficient_data"`
- Each PR number in `codespell_prs`, `shellcheck_prs`, `other_prs` must exist in `prs` dict

**Derived Fields**:
```python
@property
def total_prs(self) -> int:
    return len(self.prs)

@property
def merged_count(self) -> int:
    return sum(1 for pr in self.prs.values() if pr.status == "merged")

@property
def open_count(self) -> int:
    return sum(1 for pr in self.prs.values() if pr.status == "open")
```

---

### 3. Comment

Represents a comment on a PR (used during analysis, not persisted individually).

**Fields**:
```python
@dataclass
class Comment:
    id: int                              # GitHub comment ID
    author: str                          # Username
    author_type: str                     # "submitter", "maintainer", "bot"
    body: str                            # Comment text
    created_at: datetime                 # Comment timestamp
    is_bot: bool                         # True if author is bot
```

**Validation Rules**:
- `author_type` must be one of: `"submitter"`, `"maintainer"`, `"bot"`
- If `is_bot == True`, `author_type` must be `"bot"`

---

### 4. Configuration

Represents system configuration for discovery and processing.

**Fields**:
```python
@dataclass
class Configuration:
    # Discovery settings
    tracked_users: list[str]             # GitHub usernames to track
    tool_keywords: dict[str, list[str]]  # {"codespell": ["codespell", "codespellit"], ...}
    platforms: list[str]                 # ["github"] (future: ["github", "codeberg"])

    # API settings
    github_token: str                    # GitHub personal access token
    rate_limit_threshold: int            # Remaining calls before pausing (default: 100)

    # Processing settings
    force_mode: bool                     # If True, re-analyze merged PRs
    batch_size: int                      # PRs to process between saves (default: 10)
    max_prs_per_run: int | None          # Limit for testing (None = unlimited)

    # Paths
    data_file: Path                      # Path to repositories.json
    output_readme: Path                  # Path to generated summary README.md
    output_readmes_dir: Path             # Directory for per-user READMEs/{user}.md

    @classmethod
    def from_file(cls, path: Path) -> "Configuration":
        """Load from YAML/JSON config file."""
        pass

    @classmethod
    def from_env(cls) -> "Configuration":
        """Load from environment variables."""
        pass
```

**Default Values**:
```python
DEFAULT_CONFIG = Configuration(
    tracked_users=["yarikoptic", "DimitriPapadopoulos"],
    tool_keywords={
        "codespell": ["codespell", "codespellit"],
        "shellcheck": ["shellcheck", "shellcheckit"],
    },
    platforms=["github"],
    github_token=os.getenv("GITHUB_TOKEN", ""),
    rate_limit_threshold=100,
    force_mode=False,
    batch_size=10,
    max_prs_per_run=None,
    data_file=Path("data/repositories.json"),
    output_readme=Path("README.md"),
    output_readmes_dir=Path("READMEs"),
)
```

---

### 5. DiscoveryRun

Represents metadata about a single execution (for commit messages and logging).

**Fields**:
```python
@dataclass
class DiscoveryRun:
    # Execution metadata
    started_at: datetime
    completed_at: datetime | None
    mode: str                            # "normal" or "force"

    # Discovered changes
    new_repositories: int
    new_prs: int
    updated_prs: int
    newly_merged_prs: int
    newly_closed_prs: int
    total_processed: int

    # API usage
    api_calls_made: int
    rate_limit_remaining: int

    # Errors
    errors: list[str]                    # Error messages

    def to_commit_message(self) -> str:
        """Generate git commit message summarizing this run."""
        return f"""Update dashboard: {self.new_prs} new PRs, {self.newly_merged_prs} merged

- Discovered {self.new_repositories} new repositories
- Found {self.new_prs} new PRs across tracked repositories
- Updated {self.updated_prs} existing PRs with new data
- {self.newly_merged_prs} PRs newly merged since last run
- {self.newly_closed_prs} PRs closed without merge
- Processed {self.total_processed} PRs total
- API calls: {self.api_calls_made}, remaining quota: {self.rate_limit_remaining}

Mode: {self.mode}
Run: {self.started_at.isoformat()}"""
```

---

## Relationships

```
Configuration
    ↓ (configures)
DiscoveryRun
    ↓ (creates/updates)
Repository (1) ←→ (many) PullRequest
    ↓ (analyzes)
Comment (transient, used during analysis)
```

**Key Relationships**:
- One `Repository` contains many `PullRequest` objects (1:N)
- One `Repository` may have multiple PRs for different tools (e.g., codespell PR + shellcheck PR)
- Each `PullRequest` belongs to exactly one `Repository`
- `Comment` objects are fetched during analysis but not persisted; summary data is stored in `PullRequest`

---

## Persistence Format

### JSON Structure (repositories.json)

```json
{
  "meta": {
    "version": "1.0",
    "last_updated": "2025-11-27T12:00:00Z",
    "last_run": {
      "started_at": "2025-11-27T12:00:00Z",
      "mode": "normal",
      "new_prs": 5,
      "newly_merged": 2
    }
  },
  "repositories": {
    "kestra-io/kestra": {
      "owner": "kestra-io",
      "name": "kestra",
      "platform": "github",
      "full_name": "kestra-io/kestra",
      "url": "https://github.com/kestra-io/kestra",
      "accessible": true,
      "last_checked_at": "2025-11-27T12:00:00Z",
      "repository_updated_at": "2025-11-20T08:30:00Z",
      "codespell_prs": [12912],
      "shellcheck_prs": [],
      "other_prs": [],
      "avg_time_to_first_response_hours": 24.5,
      "pr_acceptance_rate": 1.0,
      "avg_engagement_level": 3.0,
      "behavior_category": "welcoming",
      "prs": {
        "12912": {
          "number": 12912,
          "repository": "kestra-io/kestra",
          "platform": "github",
          "url": "https://github.com/kestra-io/kestra/pull/12912",
          "tool": "codespell",
          "title": "Add codespell support (config+workflow)",
          "author": "yarikoptic",
          "created_at": "2025-01-15T10:00:00Z",
          "updated_at": "2025-01-20T14:30:00Z",
          "merged_at": "2025-01-20T14:30:00Z",
          "closed_at": null,
          "status": "merged",
          "analysis_status": "analyzed",
          "commit_count": 1,
          "files_changed": 2,
          "automation_types": ["github-actions", "codespell-config"],
          "adoption_level": "full_automation",
          "total_comments": 3,
          "submitter_comments": 1,
          "maintainer_comments": 2,
          "bot_comments": 0,
          "last_comment_author": "maintainer-user",
          "last_comment_is_maintainer": true,
          "last_maintainer_comment_at": "2025-01-20T14:25:00Z",
          "time_to_first_response_hours": 24.5,
          "days_awaiting_submitter": null,
          "response_status": "awaiting_maintainer",
          "etag": "W/\"abc123def456\"",
          "last_fetched_at": "2025-11-27T12:00:00Z",
          "last_developer_comment_body": "LGTM, merging. Thanks!"
        }
      }
    }
  }
}
```

### Atomic Write Strategy

To ensure crash safety:
1. Write updated model to `repositories.json.tmp`
2. `fsync()` to flush to disk
3. Atomic rename `repositories.json.tmp` → `repositories.json`

This ensures we never have a corrupted or partially-written model file.

---

## Behavior Categorization Logic

Repository behavior categories are computed based on aggregate metrics:

```python
def categorize_behavior(repo: Repository) -> str:
    """Categorize repository responsiveness."""
    if repo.total_prs < 2:
        return "insufficient_data"

    # Welcoming: fast response, high acceptance
    if (repo.avg_time_to_first_response_hours and
        repo.avg_time_to_first_response_hours < 72 and
        repo.pr_acceptance_rate > 0.7):
        return "welcoming"

    # Selective: slow response but some acceptance
    if repo.pr_acceptance_rate > 0.3:
        return "selective"

    # Unresponsive: very slow or no responses
    if (repo.avg_time_to_first_response_hours is None or
        repo.avg_time_to_first_response_hours > 168):  # 1 week
        return "unresponsive"

    # Hostile: quick rejection or closure without merge
    if repo.pr_acceptance_rate == 0 and repo.avg_time_to_first_response_hours < 24:
        return "hostile"

    return "unresponsive"
```

---

## Model Evolution

### Version 1.0 (Initial)
- Basic PR tracking with status, comments, automation types
- Repository aggregation with behavior categorization
- Incremental update support via ETag and timestamps

### Future Versions
- **1.1**: Add multi-platform support (Codeberg, GitLab)
- **1.2**: Add sentiment analysis for comments
- **2.0**: Add user-level aggregation (track all PRs across repositories per user)

Version is stored in `meta.version` field for migration detection.

---

## Testing Data Model

Unit tests validate:
- Dataclass field types and required fields
- Validation rules enforcement
- Derived field calculations
- State transition logic
- JSON serialization/deserialization
- Behavior categorization logic

Integration tests validate:
- Real GitHub API data maps correctly to model
- Sample PRs (kestra-io/kestra#12912, pydicom/pydicom#2169) parse successfully
- Persistence format loads and saves correctly
