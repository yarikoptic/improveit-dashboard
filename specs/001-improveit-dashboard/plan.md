# Implementation Plan: ImprovIt Dashboard

**Branch**: `001-improveit-dashboard` | **Date**: 2025-11-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-improveit-dashboard/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build an automated dashboard system to track improveit tool PRs (codespellit, shellcheckit) across GitHub repositories. The system will discover PRs via GitHub API, store structured data in JSON files following MVC architecture, generate markdown dashboards, and run incrementally on GitHub Actions cron with local execution support. Primary goals: provide visibility into PR status, engagement metrics, and community responsiveness patterns for research purposes.

## Technical Context

**Language/Version**: Python 3.11+ (for uv and modern type hints support)
**Primary Dependencies**:
  - PyGithub or requests (GitHub API client)
  - pytest (testing framework)
  - tox with tox-uv (test orchestration)
  - ruff or black (linting/formatting)
  - mypy (type checking)
  - NEEDS CLARIFICATION: Best GitHub API library (PyGithub vs requests vs httpx)
  - NEEDS CLARIFICATION: Incremental update strategy (timestamp-based vs event-based)
  - NEEDS CLARIFICATION: Rate limit handling approach (sleep vs backoff vs queue)

**Storage**: JSON files (following datalad-usage-dashboard pattern) + git for versioning
**Testing**: pytest with unit tests and integration tests against live GitHub API (using sample PRs)
**Target Platform**: Linux (GitHub Actions runners + local development)
**Project Type**: Single Python CLI application with scheduled automation
**Performance Goals**:
  - Process 100 unmerged PRs in <5 minutes (incremental mode)
  - Complete view generation for 1000 PRs in <2 minutes
  - Reduce API calls by 80% through incremental updates

**Constraints**:
  - GitHub API rate limits (5000 req/hour authenticated, 60 req/hour unauthenticated)
  - Must support both GitHub Actions (cron) and local execution
  - Crash recovery without data loss (periodic model persistence)
  - Zero manual intervention for 30+ days continuous operation

**Scale/Scope**:
  - Expected: 50-200 tracked PRs across 30-100 repositories initially
  - Design for: Up to 1000 PRs across 500 repositories
  - Multiple tool types per repository (codespell, shellcheck, future additions)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Open Source First ✅
- **Status**: PASS
- **Evidence**: All dependencies (Python, pytest, PyGithub/requests, tox, ruff, mypy) are OSI-approved open source. No proprietary components required.
- **License Plan**: Release under MIT or Apache 2.0 license (following improveit parent project)

### II. Automation by Default ✅
- **Status**: PASS
- **Evidence**:
  - Core requirement: Automated PR discovery and dashboard generation on cron schedule
  - CI/CD: GitHub Actions for scheduled execution and testing
  - Code quality: tox for automated linting (ruff), type checking (mypy), and testing (pytest)
  - Zero manual intervention target (30+ days)
- **Manual Steps**: Initial configuration (API token setup) - documented in quickstart

### III. Contribution Welcoming ✅
- **Status**: PASS
- **Evidence**:
  - Clear quickstart.md for setup (Phase 1 deliverable)
  - Automated test suite for contributor validation
  - Integration tests using real sample PRs for easy verification
  - Good first issue potential: Adding new tool types, new hosting platforms

### IV. Transparency ✅
- **Status**: PASS
- **Evidence**:
  - All data stored in versioned git repository (JSON + markdown)
  - Public GitHub Actions workflows
  - Comprehensive specification and implementation plan
  - Git commits document discovery timeline (FR-038, FR-039)

### V. Minimal Human Dependency ✅
- **Status**: PASS
- **Evidence**:
  - Fully automated discovery, processing, and view generation
  - Incremental updates require no human intervention
  - Crash recovery through periodic model persistence
  - Self-documenting dashboard (README.md generated from data)

### Testing Requirements ✅
- **Status**: PASS
- **Evidence**:
  - Unit tests for all business logic (models, processors, view generators)
  - Integration tests against sample PRs (kestra-io/kestra#12912, pydicom/pydicom#2169)
  - tox configuration for automated test execution
  - Target: >80% coverage

### Summary
**Overall Status**: ✅ PASS - No constitution violations. Project fully aligned with all core principles.

---

## Post-Design Constitution Re-Check

*Re-evaluated after Phase 1 design completion (research.md, data-model.md, contracts/, quickstart.md)*

### I. Open Source First ✅
- **Status**: PASS (confirmed)
- **Evidence**: All design decisions use open source tools:
  - `requests` library (Apache 2.0)
  - GitHub REST API (public, no proprietary dependencies)
  - JSON for data storage (open standard)
  - No proprietary services required

### II. Automation by Default ✅
- **Status**: PASS (confirmed)
- **Evidence**:
  - Incremental update strategy with ETag/timestamp optimization
  - Automated rate limit handling with exponential backoff
  - GitHub Actions workflow for scheduled execution
  - Tox automation for linting, type checking, testing
  - Quick start guide documents setup in <10 minutes

### III. Contribution Welcoming ✅
- **Status**: PASS (confirmed)
- **Evidence**:
  - Comprehensive quickstart.md achieves <10 minute setup
  - Clear API contracts for understanding system behavior
  - Integration tests against real sample PRs (easy verification)
  - Good first issue potential documented (new tools, new platforms)

### IV. Transparency ✅
- **Status**: PASS (confirmed)
- **Evidence**:
  - Detailed research.md documents all technical decisions with rationale
  - Data model fully specified with validation rules
  - API contracts define all external interactions
  - Behavior categorization logic is explicit and auditable
  - Git commits track dashboard evolution (FR-038, FR-039)

### V. Minimal Human Dependency ✅
- **Status**: PASS (confirmed)
- **Evidence**:
  - Crash recovery through periodic model persistence
  - Atomic write strategy prevents data corruption
  - ETag-based incremental updates reduce API dependency
  - Graceful degradation on rate limits
  - Self-service quickstart for setup

### Testing Requirements ✅
- **Status**: PASS (confirmed)
- **Evidence**:
  - Hybrid testing strategy (mocked unit + live integration tests)
  - Clear contracts enable comprehensive unit test coverage
  - Integration tests against sample PRs validate real API behavior
  - Tox orchestration for all test types
  - AI-generated tests marked with `@pytest.mark.ai_generated`

**Post-Design Overall Status**: ✅ PASS - All design artifacts reinforce constitutional compliance. No violations introduced during design phase.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
improveit-dashboard/
├── code/                        # All production code lives here
│   ├── src/
│   │   ├── improveit_dashboard/
│   │   │   ├── __init__.py
│   │   │   ├── models/              # Data models (M in MVC)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pull_request.py  # PullRequest entity
│   │   │   │   ├── repository.py    # Repository entity
│   │   │   │   ├── comment.py       # Comment entity
│   │   │   │   └── config.py        # Configuration entity
│   │   │   ├── controllers/         # Processing logic (C in MVC)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── discovery.py     # PR discovery orchestration
│   │   │   │   ├── github_client.py # GitHub API wrapper
│   │   │   │   ├── analyzer.py      # PR analysis (comments, automation types)
│   │   │   │   └── persistence.py   # Model save/load operations
│   │   │   ├── views/               # Dashboard generation (V in MVC)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dashboard.py     # Main README.md generator
│   │   │   │   └── reports.py       # Per-user README generators
│   │   │   ├── cli.py               # CLI implementation (entry point: improveit-dashboard)
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       ├── rate_limit.py    # Rate limit handling
│   │   │       └── logging.py       # Logging configuration
│   │   └── __main__.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_models.py
│   │   │   ├── test_discovery.py
│   │   │   ├── test_analyzer.py
│   │   │   ├── test_persistence.py
│   │   │   └── test_views.py
│   │   ├── integration/
│   │   │   ├── test_github_api.py   # Tests against sample PRs
│   │   │   └── test_end_to_end.py   # Full pipeline test
│   │   └── conftest.py              # Pytest fixtures
│   │
│   ├── pyproject.toml               # Project metadata + dependencies (uv)
│   ├── tox.ini                      # Tox configuration for testing
│   ├── config.yaml                  # Dashboard configuration
│   └── LICENSE                      # Open source license
│
├── data/                        # Generated data (committed to track history)
│   └── repositories.json        # Model storage (generated)
│
├── .github/
│   └── workflows/
│       ├── ci.yml               # Tox-based testing on PR (runs from code/)
│       └── update-dashboard.yml # Scheduled cron for updates (runs from code/)
│
├── README.md                    # Generated summary dashboard (V output)
├── READMEs/                     # Per-user detailed dashboards (V output)
│   ├── yarikoptic.md            # Detailed PR list for yarikoptic
│   └── DimitriPapadopoulos.md   # Detailed PR list for DimitriPapadopoulos
└── .gitignore
```

**Structure Decision**: Single Python CLI application following MVC architecture as specified in the feature requirements. Code is isolated in `code/` subdirectory to keep root clean for generated dashboard files. The separation ensures:
- **Models** (`code/src/improveit_dashboard/models/`) define data structures independent of storage or presentation
- **Controllers** (`code/src/improveit_dashboard/controllers/`) handle discovery, API interaction, and orchestration
- **Views** (`code/src/improveit_dashboard/views/`) generate markdown dashboards from model data
- **Data persistence** in JSON files under `data/` directory (committed to track PR history evolution)
- **Testing** organized by type (unit vs integration) with pytest and tox
- **Automation** via GitHub Actions workflows for CI and scheduled updates (run from `code/` directory)

## Complexity Tracking

No constitution violations - this section is not applicable.
