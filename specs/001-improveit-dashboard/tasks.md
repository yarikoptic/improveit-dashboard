# Tasks: ImprovIt Dashboard

**Input**: Design documents from `/specs/001-improveit-dashboard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/github-api-contract.md, quickstart.md

**Tests**: Test tasks are included for key functionality per project requirements. Tests are marked with [TEST].

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure per plan.md (`src/improveit_dashboard/`, `tests/unit/`, `tests/integration/`, `data/`)
- [ ] T002 Initialize Python project with `pyproject.toml` (uv, Python 3.11+, dependencies: requests, pytest, tox-uv, ruff, mypy)
- [ ] T003 [P] Create `tox.ini` with environments: py311, lint, type
- [ ] T004 [P] Create `.gitignore` (Python, venv, .env, data/*.json except .gitkeep)
- [ ] T005 [P] Create `data/.gitkeep` placeholder
- [ ] T006 [P] Create empty `src/improveit_dashboard/__init__.py`
- [ ] T007 [P] Create `src/improveit_dashboard/__main__.py` for CLI entry point stub

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Create `src/improveit_dashboard/models/__init__.py`
- [ ] T009 [P] Implement PullRequest dataclass in `src/improveit_dashboard/models/pull_request.py` (all fields from data-model.md)
- [ ] T010 [P] Implement Repository dataclass in `src/improveit_dashboard/models/repository.py` (all fields from data-model.md)
- [ ] T011 [P] Implement Comment dataclass in `src/improveit_dashboard/models/comment.py`
- [ ] T012 [P] Implement Configuration dataclass in `src/improveit_dashboard/models/config.py` (with `from_file()` and `from_env()` methods)
- [ ] T013 [P] Implement DiscoveryRun dataclass in `src/improveit_dashboard/models/discovery_run.py` (with `to_commit_message()` method)
- [ ] T014 Create `src/improveit_dashboard/controllers/__init__.py`
- [ ] T015 Implement GitHubClient class in `src/improveit_dashboard/controllers/github_client.py` (Session setup, auth headers, base URL)
- [ ] T016 Implement rate limit handler in `src/improveit_dashboard/utils/rate_limit.py` (check_and_wait with X-RateLimit headers)
- [ ] T017 [P] Implement logging setup in `src/improveit_dashboard/utils/logging.py`
- [ ] T018 Implement atomic JSON persistence in `src/improveit_dashboard/controllers/persistence.py` (load/save with temp file + rename)
- [ ] T019 [P] Create `src/improveit_dashboard/utils/__init__.py`
- [ ] T020 [P] Create `src/improveit_dashboard/views/__init__.py`
- [ ] T021 Create default `config.yaml` with tracked_users (yarikoptic, DimitriPapadopoulos) and tool_keywords
- [ ] T022 [TEST] Add unit tests for PullRequest model validation in `tests/unit/test_models.py`
- [ ] T023 [TEST] Add unit tests for Repository model validation in `tests/unit/test_models.py`
- [ ] T024 [TEST] Add unit tests for Configuration loading in `tests/unit/test_models.py`
- [ ] T025 [TEST] Add unit tests for atomic persistence in `tests/unit/test_persistence.py`
- [ ] T026 Create `tests/conftest.py` with shared pytest fixtures (mock responses, sample PR data)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 5 - Automated Discovery and Incremental Updates (Priority: P1)

**Goal**: System discovers new improveit PRs and updates existing PR status automatically without manual intervention

**Independent Test**: Run the discovery process, verify new PRs are discovered and stored in `data/repositories.json`. Verify incremental mode only fetches changed PRs.

**Why First**: US5 (automated discovery) must be implemented before US1 (view status) because there's nothing to view without discovered data. Discovery is the data acquisition layer.

### Implementation for User Story 5

- [ ] T027 [US5] Implement search PRs by user in `src/improveit_dashboard/controllers/github_client.py` (GET /search/issues with author filter)
- [ ] T028 [US5] Implement fetch PR details in `src/improveit_dashboard/controllers/github_client.py` (GET /repos/{owner}/{repo}/pulls/{number} with ETag support)
- [ ] T029 [US5] Implement conditional request handling (If-None-Match header, 304 response handling)
- [ ] T030 [US5] Implement discovery orchestration in `src/improveit_dashboard/controllers/discovery.py` (main discovery loop with prioritized processing order)
- [ ] T031 [US5] Implement incremental update logic in discovery.py (track last_updated, filter by updated:>date)
- [ ] T032 [US5] Implement model update from API responses in discovery.py (map GitHub response to PullRequest/Repository models)
- [ ] T033 [US5] Implement periodic model persistence during discovery (save every batch_size PRs)
- [ ] T034 [US5] Implement PR title keyword filtering for tool detection (codespell, shellcheck, codespellit, shellcheckit)
- [ ] T035 [US5] Implement processing order: new PRs first, then unmerged by freshness, merged only in force mode
- [ ] T036 [US5] Implement CLI `update` command in `src/improveit_dashboard/cli.py` (argparse with --incremental, --force flags)
- [ ] T037 [US5] Wire CLI entry point in pyproject.toml (`improveit-dashboard = "improveit_dashboard.cli:main"`)
- [ ] T038 [TEST] [US5] Add unit tests for GitHubClient search/fetch in `tests/unit/test_github_client.py` (mocked requests)
- [ ] T039 [TEST] [US5] Add unit tests for discovery orchestration in `tests/unit/test_discovery.py`
- [ ] T040 [TEST] [US5] Add integration test fetching kestra-io/kestra#12912 in `tests/integration/test_github_api.py`
- [ ] T041 [TEST] [US5] Add integration test fetching pydicom/pydicom#2169 in `tests/integration/test_github_api.py`

**Checkpoint**: Discovery pipeline works. Running `improveit-dashboard update` populates `data/repositories.json` with real PR data.

---

## Phase 4: User Story 1 - View PR Status Overview (Priority: P1)

**Goal**: Maintainers can see current status of all submitted PRs across all repositories

**Independent Test**: After discovery runs, view generated README.md and verify it shows PRs with status (draft, open, merged, closed), submission date, repository, PR number, and links.

### Implementation for User Story 1

- [ ] T042 [US1] Implement summary dashboard generator in `src/improveit_dashboard/views/dashboard.py` (generate README.md with per-user statistics table)
- [ ] T043 [US1] Implement per-user detailed dashboard generator in `src/improveit_dashboard/views/reports.py` (generate READMEs/{user}.md)
- [ ] T044 [US1] Add PR status display (draft, open, merged, closed) with status indicators
- [ ] T045 [US1] Add PR listing with repository name, PR number, title, submission date, and URL
- [ ] T046 [US1] Add summary counts per user (total, draft, open, merged, closed)
- [ ] T047 [US1] Implement CLI `generate` command in cli.py (regenerate views from existing data)
- [ ] T048 [US1] Ensure `update` command runs view generation after model update
- [ ] T049 [TEST] [US1] Add unit tests for dashboard generation in `tests/unit/test_views.py`

**Checkpoint**: Running `improveit-dashboard update` produces README.md with PR status overview.

---

## Phase 5: User Story 6 - Configure Discovery Parameters (Priority: P2)

**Goal**: Administrators can configure which users and PR types to track

**Independent Test**: Modify config.yaml to track a different user or tool keyword, run discovery, verify only matching PRs are included.

### Implementation for User Story 6

- [ ] T050 [US6] Implement config file loading in Configuration.from_file() with YAML support
- [ ] T051 [US6] Implement environment variable overrides in Configuration.from_env()
- [ ] T052 [US6] Add CLI --config flag to specify custom config path
- [ ] T053 [US6] Implement platform selection (github only for now, extensible for future)
- [ ] T054 [US6] Document configuration options in config.yaml comments
- [ ] T055 [TEST] [US6] Add unit tests for configuration parsing in `tests/unit/test_models.py`

**Checkpoint**: Configuration is flexible. Different users/tools can be tracked via config.yaml.

---

## Phase 6: User Story 2 - Track PR Engagement Metrics (Priority: P2)

**Goal**: See interaction metrics for each PR (comment counts, human vs bot, response times)

**Independent Test**: View a PR entry in the dashboard and verify it shows total comments, comments from submitter, comments from maintainers, bot comments, and last developer comment.

### Implementation for User Story 2

- [ ] T056 [US2] Implement fetch PR comments in `src/improveit_dashboard/controllers/github_client.py` (GET /repos/{owner}/{repo}/issues/{number}/comments)
- [ ] T057 [US2] Implement comment classification in `src/improveit_dashboard/controllers/analyzer.py` (submitter, maintainer, bot detection)
- [ ] T058 [US2] Implement bot detection using user.type and [bot] suffix pattern
- [ ] T059 [US2] Implement time-to-first-human-response calculation in analyzer.py
- [ ] T060 [US2] Store last developer (non-submitter, non-bot) comment body in PullRequest model
- [ ] T061 [US2] Update discovery.py to call comment analysis after fetching PR
- [ ] T062 [US2] Update views/reports.py to display engagement metrics (comment breakdown, time-to-response)
- [ ] T063 [TEST] [US2] Add unit tests for comment classification in `tests/unit/test_analyzer.py`
- [ ] T064 [TEST] [US2] Add unit tests for bot detection in `tests/unit/test_analyzer.py`

**Checkpoint**: Dashboard shows engagement metrics for each PR.

---

## Phase 7: User Story 8 - Identify PRs Needing Submitter Response (Priority: P2)

**Goal**: Quickly identify PRs where maintainers have responded and await submitter action

**Independent Test**: View dashboard section showing PRs awaiting submitter response with last maintainer comment and days waiting.

### Implementation for User Story 8

- [ ] T065 [US8] Implement response_status calculation (awaiting_submitter, awaiting_maintainer, no_response) in analyzer.py
- [ ] T066 [US8] Implement days_awaiting_submitter calculation in analyzer.py
- [ ] T067 [US8] Implement last_actor determination (submitter or maintainer based on last non-bot comment)
- [ ] T068 [US8] Add "Needs Response" section to per-user dashboard in views/reports.py
- [ ] T069 [US8] Display days since last maintainer comment for awaiting PRs
- [ ] T070 [US8] Implement CLI `export` command for AI assistant processing (JSON format with discussion context)
- [ ] T071 [TEST] [US8] Add unit tests for response status calculation in `tests/unit/test_analyzer.py`

**Checkpoint**: Dashboard highlights PRs needing submitter response with actionable context.

---

## Phase 8: User Story 7 - Open Source Health Diagnostic (Priority: P2)

**Goal**: Use PR submission patterns as diagnostic tool for measuring open source community health

**Independent Test**: View repository behavior categorization (welcoming, selective, unresponsive) and responsiveness metrics.

### Implementation for User Story 7

- [ ] T072 [US7] Implement repository-level metrics aggregation in analyzer.py (avg time-to-response, acceptance rate, engagement level)
- [ ] T073 [US7] Implement behavior categorization logic (welcoming, selective, unresponsive, hostile, insufficient_data)
- [ ] T074 [US7] Add per-repository statistics to dashboard
- [ ] T075 [US7] Add repository behavior category display in views
- [ ] T076 [TEST] [US7] Add unit tests for behavior categorization in `tests/unit/test_analyzer.py`

**Checkpoint**: Dashboard shows repository health diagnostics for research analysis.

---

## Phase 9: User Story 3 - Understand Accepted Automation Types (Priority: P3)

**Goal**: See which automation types (GitHub Actions, pre-commit, etc.) were accepted in merged PRs

**Independent Test**: View merged PRs and verify they show automation type tags (github-actions, pre-commit, etc.)

### Implementation for User Story 3

- [ ] T077 [US3] Implement fetch PR files in `src/improveit_dashboard/controllers/github_client.py` (GET /repos/{owner}/{repo}/pulls/{number}/files)
- [ ] T078 [US3] Implement automation type detection in analyzer.py (file path pattern matching)
- [ ] T079 [US3] Implement adoption level classification (full_automation, config_only, typo_fixes, rejected)
- [ ] T080 [US3] Update discovery.py to call file analysis for merged PRs
- [ ] T081 [US3] Add automation type tags to PR display in views/reports.py
- [ ] T082 [US3] Add aggregate automation type statistics to dashboard
- [ ] T083 [TEST] [US3] Add unit tests for automation detection in `tests/unit/test_analyzer.py`

**Checkpoint**: Dashboard shows automation types for merged PRs and aggregate statistics.

---

## Phase 10: User Story 4 - Track Merge Impact Metrics (Priority: P3)

**Goal**: See how PRs evolved (commits, files changed) from submission to merge

**Independent Test**: View merged PRs and verify commit count and files-changed metrics are displayed.

### Implementation for User Story 4

- [ ] T084 [US4] Ensure commit_count and files_changed are populated from PR API response (already available in PR details endpoint)
- [ ] T085 [US4] Add commit count and files changed display to PR entries in views/reports.py
- [ ] T086 [US4] Add average commits/files statistics for merged PRs to summary dashboard
- [ ] T087 [TEST] [US4] Add unit tests verifying merge metrics extraction in `tests/unit/test_views.py`

**Checkpoint**: Dashboard shows merge impact metrics for all PRs.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories, CI/CD setup, final validation

- [ ] T088 [P] Create `.github/workflows/ci.yml` for tox-based testing on PR
- [ ] T089 [P] Create `.github/workflows/update-dashboard.yml` for scheduled cron updates (every 6 hours)
- [ ] T090 Implement git commit message generation with change summary (FR-038, FR-039) in discovery.py
- [ ] T091 Add LICENSE file (MIT)
- [ ] T092 Validate quickstart.md instructions work end-to-end
- [ ] T093 Run full test suite (tox) and fix any issues
- [ ] T094 Run type checking (mypy) and fix any issues
- [ ] T095 Run linting (ruff) and fix any issues
- [ ] T096 [TEST] Add integration test for full pipeline (discovery + view generation) in `tests/integration/test_end_to_end.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 5 (Phase 3)**: Depends on Foundational - discovery must work before views
- **User Story 1 (Phase 4)**: Depends on US5 (needs data to display)
- **User Story 6 (Phase 5)**: Can start after Foundational, integrates with US5
- **User Story 2 (Phase 6)**: Depends on US5 (extends discovery with comment analysis)
- **User Story 8 (Phase 7)**: Depends on US2 (uses comment analysis)
- **User Story 7 (Phase 8)**: Depends on US2 (uses engagement metrics)
- **User Story 3 (Phase 9)**: Depends on US5 (extends discovery with file analysis)
- **User Story 4 (Phase 10)**: Can start after US1 (view display only)
- **Polish (Phase 11)**: Depends on all user stories being implemented

### User Story Priority Order

1. **US5 (Automated Discovery)**: P1 - Core data acquisition (REQUIRED FIRST)
2. **US1 (View Status)**: P1 - Core value display
3. **US6 (Configure)**: P2 - Flexibility
4. **US2 (Engagement)**: P2 - Actionable insights
5. **US8 (Needs Response)**: P2 - Workflow management
6. **US7 (Health Diagnostic)**: P2 - Research value
7. **US3 (Automation Types)**: P3 - Analytical depth
8. **US4 (Merge Metrics)**: P3 - Additional metrics

### Within Each User Story

- Models before services/controllers
- Controllers before views
- Core implementation before integration
- Tests alongside or after implementation

### Parallel Opportunities

**Phase 1 (all tasks T003-T007 can run in parallel)**:
```
Task T003: Create tox.ini
Task T004: Create .gitignore
Task T005: Create data/.gitkeep
Task T006: Create __init__.py
Task T007: Create __main__.py
```

**Phase 2 (model tasks T009-T013 can run in parallel)**:
```
Task T009: PullRequest dataclass
Task T010: Repository dataclass
Task T011: Comment dataclass
Task T012: Configuration dataclass
Task T013: DiscoveryRun dataclass
```

**Phase 11 (CI tasks T088-T089 can run in parallel)**:
```
Task T088: Create ci.yml
Task T089: Create update-dashboard.yml
```

---

## Implementation Strategy

### MVP First (US5 + US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 5 (Discovery)
4. Complete Phase 4: User Story 1 (View Status)
5. **STOP and VALIDATE**: Test discovery and dashboard generation work end-to-end
6. Deploy/demo with basic dashboard

### Suggested MVP Scope

- **MVP**: Setup + Foundational + US5 + US1 = Phases 1-4
- **MVP delivers**: Automated PR discovery and basic status dashboard
- **Task count**: ~49 tasks for MVP

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US5 → Test independently → PR discovery works
3. Add US1 → Test independently → Deploy/Demo (MVP!)
4. Add US6 → Configurable tracking
5. Add US2 + US8 → Engagement insights and response tracking
6. Add US7 → Research diagnostics
7. Add US3 + US4 → Full metrics
8. Polish → Production ready

---

## Task Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| 1 | Setup | 7 |
| 2 | Foundational | 19 |
| 3 | US5 - Discovery (P1) | 15 |
| 4 | US1 - View Status (P1) | 8 |
| 5 | US6 - Configuration (P2) | 6 |
| 6 | US2 - Engagement (P2) | 9 |
| 7 | US8 - Needs Response (P2) | 7 |
| 8 | US7 - Health Diagnostic (P2) | 5 |
| 9 | US3 - Automation Types (P3) | 7 |
| 10 | US4 - Merge Metrics (P3) | 4 |
| 11 | Polish | 9 |
| **Total** | | **96** |

### Task Breakdown by Type

- Setup/Infrastructure: 7 tasks
- Model Implementation: 5 tasks
- Controller Implementation: ~25 tasks
- View Implementation: ~10 tasks
- CLI Implementation: ~5 tasks
- Unit Tests: ~15 tasks
- Integration Tests: ~5 tasks
- CI/CD & Polish: ~9 tasks

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- [TEST] marks test tasks
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All tests should be marked with `@pytest.mark.ai_generated` per project conventions
