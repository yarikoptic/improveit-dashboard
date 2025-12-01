# Feature Specification: ImprovIt Dashboard

**Feature Branch**: `001-improveit-dashboard`
**Created**: 2025-11-27
**Status**: Draft
**Input**: User description: "We are establishing a simple dashboard to review the state of the improveit submitted fixes (codespell and shellcheck CIs etc) and CI to various projects (by @yarikoptic or not).  We need to establish a project with configuration for discovery via github (and potentially later other apis like codeberg etc) API to find repositories where where specified  users (like yarikoptic) submitted PRs for adding codespell or shellcheck support (using codespellit and shellcheckit from https://github.com/yarikoptic/improveit/), and providing overview on their status --  as when they were filed, did they have interactions with humans (or bots), how many comments from original submitter and other humans, when they were merged, how many commits it ended up and how many files were changed as a result, and what types of automations (ci workflow, pre-commit or other) were accepted. Or if a PR was closed without merge. also store the last comment on the PR from the developers (not submitter).  https://github.com/datalad/datalad-usage-dashboard/ is similar in many principles and worth reviewing and potentially adopting some ideas and may be implementations -- it already discovers ALL 'datalad run' invocations it might find on github and other platforms, and stores them in its https://github.com/datalad/datalad-usage-dashboard/blob/master/datalad-repos.json with an entry being '\"run\": true'.  In this repo we would like to establish a very similar functioning with collection of information in similar .json file(s) and dashboarding then via simple README.md etc files.  System should be fully automated, ideally operate incrementally, and on cron on github ci but allow for local execution as well in case of need to debug or extend. Sample recent target PRs like that (e.g. to be used in integration tests etc) are: https://github.com/kestra-io/kestra/pull/12912 https://github.com/pydicom/pydicom/pull/2169"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View PR Status Overview (Priority: P1)

As a maintainer of the improveit tools (codespellit, shellcheckit), I need to see the current status of all submitted PRs across all repositories so that I can understand adoption rates, identify stalled PRs, and prioritize follow-up actions.

**Why this priority**: This is the core value proposition - providing visibility into improveit PR submissions. Without this, the dashboard serves no purpose. It delivers immediate value by answering "What is the state of all my PRs?"

**Independent Test**: Can be fully tested by viewing the generated dashboard (README.md) and verifying it displays a list of PRs with their basic status (open, merged, closed) and delivers the value of quick status overview.

**Acceptance Scenarios**:

1. **Given** the system has discovered 50 PRs across 30 repositories, **When** I view the dashboard, **Then** I see a summary showing total PRs by status (open, merged, closed)
2. **Given** PRs exist with varying ages, **When** I view the dashboard, **Then** I see each PR listed with submission date, repository name, PR number, current status, and link to the PR
3. **Given** the dashboard has been generated, **When** I open the README.md file, **Then** the information is presented in a clear, scannable format (tables or organized sections)

---

### User Story 2 - Track PR Engagement Metrics (Priority: P2)

As a contributor monitoring improveit adoption, I need to see interaction metrics for each PR (comment counts, human vs bot interactions, response times) so that I can identify which repositories are actively engaging with the proposals and which need additional outreach.

**Why this priority**: Once basic status is visible, understanding engagement levels helps prioritize follow-up efforts. This transforms the dashboard from a simple status list to an actionable tool for community management.

**Independent Test**: Can be tested independently by verifying that each PR entry shows comment counts (total, from submitter, from others), identifies bot vs human interactions, and displays the last developer comment. This delivers the value of understanding repository responsiveness.

**Acceptance Scenarios**:

1. **Given** a PR has 5 comments (2 from submitter, 2 from other humans, 1 from bot), **When** I view that PR in the dashboard, **Then** I see the comment breakdown clearly displayed
2. **Given** a PR was merged after 3 days with 4 developer comments, **When** I view the PR details, **Then** I see the time-to-merge duration and interaction summary
3. **Given** a PR has a final developer comment before merge, **When** I view the PR entry, **Then** I see the last non-submitter comment displayed (useful for understanding final feedback)

---

### User Story 3 - Understand Accepted Automation Types (Priority: P3)

As an analyst of tool adoption patterns, I need to see which types of automations (GitHub Actions workflows, pre-commit hooks, other CI systems) were accepted in merged PRs so that I can understand preferences across different projects and refine future contributions.

**Why this priority**: This provides deeper analytical value for understanding adoption patterns. While valuable for strategy, it's not essential for the basic monitoring and follow-up use cases.

**Independent Test**: Can be tested independently by examining merged PRs and verifying the dashboard categorizes them by automation type (workflow files, pre-commit configs, etc.). Delivers insights into what types of tooling integrations are most successful.

**Acceptance Scenarios**:

1. **Given** a merged PR added GitHub Actions workflow files, **When** I view the PR in the dashboard, **Then** I see it tagged/categorized as "GitHub Actions workflow"
2. **Given** a merged PR added pre-commit configuration, **When** I view the dashboard, **Then** I see it tagged as "pre-commit hook"
3. **Given** multiple merged PRs across different repositories, **When** I view aggregate statistics, **Then** I see a breakdown of which automation types were most commonly accepted

---

### User Story 4 - Track Merge Impact Metrics (Priority: P3)

As a quality analyst, I need to see how PRs evolved from submission to merge (number of commits in the final merge, files changed) so that I can understand the scope of changes and whether PRs typically require significant revisions.

**Why this priority**: This is useful analytical data but not essential for basic monitoring. It helps understand the "cost" of contributions but doesn't directly support action-taking.

**Independent Test**: Can be tested by verifying merged PRs display commit count and files-changed count from the merged result. Delivers insights into contribution complexity.

**Acceptance Scenarios**:

1. **Given** a PR was merged with 3 commits changing 5 files, **When** I view the PR in the dashboard, **Then** I see "3 commits, 5 files changed"
2. **Given** multiple merged PRs, **When** I view summary statistics, **Then** I see average commits per PR and average files changed per PR

---

### User Story 5 - Automated Discovery and Incremental Updates (Priority: P1)

As a system operator, I need the dashboard to automatically discover new improveit PRs and update existing PR status without manual intervention so that the dashboard remains current without ongoing maintenance effort.

**Why this priority**: Automation is critical for long-term viability. A manual dashboard would quickly become stale and lose value. This ensures the dashboard is always current.

**Independent Test**: Can be tested by scheduling automated runs, submitting a new PR, and verifying it appears in the dashboard on the next automated update. Also test that existing PR status updates (e.g., from open to merged). Delivers the value of zero-maintenance operation.

**Acceptance Scenarios**:

1. **Given** the system runs on a schedule (e.g., daily cron), **When** a new improveit PR is submitted by a configured user, **Then** the next scheduled run discovers and adds it to the dashboard
2. **Given** an open PR is merged, **When** the system runs its incremental update, **Then** the PR status is updated from "open" to "merged" with merge date
3. **Given** the system has existing data for 100 PRs, **When** the incremental update runs, **Then** it only queries for changes since the last update rather than re-fetching all data
4. **Given** the system can run locally or on GitHub Actions, **When** executed in either environment, **Then** it produces the same correct output

---

### User Story 6 - Configure Discovery Parameters (Priority: P2)

As a dashboard administrator, I need to configure which users and which types of PRs to track (e.g., codespellit and shellcheckit submissions) so that the dashboard can be adapted for different monitoring needs or expanded to track other improveit tools.

**Why this priority**: Configuration flexibility is important for maintainability and extensibility, but the initial version can work with hardcoded defaults. This becomes more important as usage expands.

**Independent Test**: Can be tested by modifying configuration to track a different user or tool, running discovery, and verifying only matching PRs are included. Delivers flexibility for different use cases.

**Acceptance Scenarios**:

1. **Given** configuration specifies user "yarikoptic", **When** discovery runs, **Then** only PRs authored by yarikoptic are included
2. **Given** configuration specifies tracking codespellit and shellcheckit tools, **When** discovery runs, **Then** only PRs with titles containing keywords like "codespell", "shellcheck", "codespellit", "shellcheckit" are included, with file change analysis to categorize adoption type
3. **Given** configuration can specify multiple code hosting platforms, **When** GitHub is configured, **Then** discovery works against GitHub API (with future extensibility for Codeberg, etc.)

---

### User Story 7 - Open Source Health Diagnostic (Priority: P2)

As a software engineering researcher conducting social studies of open source communities, I need to use mass PR submission patterns as a diagnostic tool (litmus test) to identify which projects claiming to be "open source" actually welcome external contributions and respond constructively, so that I can understand the real openness and health of various open source ecosystems.

**Why this priority**: This represents a significant research use case that goes beyond simple tracking. It provides scholarly value and insights into open source community dynamics. While not essential for basic monitoring, it adds substantial analytical depth.

**Independent Test**: Can be tested by generating analysis reports showing response patterns, time-to-first-response, acceptance rates, and engagement quality across different projects. Delivers insights into which projects are truly welcoming vs those with barriers to contribution.

**Acceptance Scenarios**:

1. **Given** the dashboard has tracked 100 PRs across 50 repositories, **When** I view the analysis section, **Then** I see projects ranked by responsiveness (time-to-first-response, engagement level, acceptance rate)
2. **Given** some projects merged PRs quickly with constructive feedback while others ignored or rejected without explanation, **When** I view the social research metrics, **Then** I see categorization of project behavior patterns (welcoming, selective, unresponsive, hostile)
3. **Given** the data spans multiple repositories, **When** I export research data, **Then** I can analyze correlation between project characteristics (size, governance model, activity level) and openness to contributions
4. **Given** PRs have varying response patterns, **When** I view the dashboard, **Then** I see time-to-first-human-response tracked separately from bot responses

---

### User Story 8 - Identify PRs Needing Submitter Response (Priority: P2)

As a busy researcher who submitted many improvement PRs, I need to quickly identify which PRs have received maintainer responses that I haven't yet addressed, so that I can prioritize my follow-up work or delegate these to an AI assistant for review and response.

**Why this priority**: This directly supports the workflow of a busy contributor managing dozens or hundreds of PRs. It transforms the dashboard from passive monitoring to active workflow management and enables AI-assisted PR management.

**Independent Test**: Can be tested by viewing a filtered list of PRs where the last comment is from a maintainer (not the submitter) and the PR remains open. This delivers immediate actionable value by highlighting where attention is needed.

**Acceptance Scenarios**:

1. **Given** 50 open PRs where 15 have maintainer comments awaiting submitter response, **When** I view the "needs my response" section, **Then** I see those 15 PRs highlighted with the last maintainer comment displayed
2. **Given** I am a busy researcher, **When** I review the dashboard, **Then** I can distinguish PRs awaiting maintainer action vs PRs awaiting my response
3. **Given** some PRs have been waiting for my response for weeks, **When** I view the dashboard, **Then** I see how long each PR has been awaiting my response (days since last maintainer comment)
4. **Given** I want to use an AI assistant to help respond, **When** I export data for PRs needing response, **Then** the export includes PR context (last comments, discussion thread) suitable for AI analysis
5. **Given** a PR receives a new maintainer comment, **When** the dashboard updates, **Then** it automatically moves from "awaiting maintainer" to "awaiting submitter" status

---

### Edge Cases

- What happens when the GitHub API rate limit is exceeded during discovery?
- How does the system handle PRs that are converted from draft to ready?
- What happens if a PR is reopened after being closed?
- How does the system distinguish between bot comments and human comments when some bots have human-like usernames?
- What happens when a PR has no comments at all?
- How does the system handle deleted PRs or repositories that become private/inaccessible?
- What happens when a user is mentioned in the PR but is not the author (should these PRs be tracked)?
- How does the system handle PRs with multiple commits where some commits are from other authors (co-authored)?
- How does the system categorize a PR that includes both typo fixes AND automation configs if only the typo fixes were merged (partial acceptance)?
- What happens when a PR title doesn't contain standard keywords but is clearly related to improveit tools based on file changes?
- How does the system identify datalad run command records in PR file changes?
- How does the system determine if a comment is "constructive" vs "hostile" for behavior pattern categorization?
- What happens when the last comment is from a bot but the last human comment is from a maintainer - which determines response status?
- How does the system handle PRs with very long discussion threads (100+ comments) for AI assistant export?
- What defines "no response yet" if there are bot comments but no human maintainer comments?
- How does the system categorize repositories with only one PR submitted vs those with multiple PRs for statistical significance?
- What happens when a maintainer requests changes but the PR is then closed by the submitter - is this considered responsive or unresponsive?
- What happens if view generation fails but model update succeeded - should the model update be preserved?
- How does the system handle a repository that has a merged codespell PR and an open shellcheck PR - which freshness ordering applies?
- What defines "freshness" when a PR has commits pushed but no new comments?
- In force mode, what's the processing order for merged PRs - by original submission date or merge date?
- How does the system handle periodic model persistence if processing is very fast (complete in seconds)?
- What happens if a crash occurs between model persistence and view generation?
- How does the system track which PRs were already analyzed to avoid redundant API calls in incremental mode?

## Architectural Principles *(mandatory)*

The system follows a clear separation of concerns pattern with three distinct layers:

### Data Layer (Model)
- **Purpose**: Persistent storage of all discovered PR data, metrics, and analysis results
- **Format**: Structured data files (e.g., JSON) that represent the complete state of all tracked PRs and repositories
- **Independence**: Model can be updated, queried, and persisted without any dependency on presentation format
- **Crash Recovery**: Model is periodically saved during updates to ensure no data loss on system failures
- **Incremental Updates**: Model supports efficient incremental updates without full reprocessing

### Presentation Layer (View)
- **Purpose**: Human-readable dashboard representation of the model data
- **Format**: Generated markdown files (README.md and related documentation)
- **Derivation**: Views are derived entirely from the model; views contain no unique data
- **Independence**: View generation can be triggered independently from model updates
- **Regeneration**: Views can be completely regenerated from the model at any time

### Processing Layer (Controller)
- **Purpose**: Orchestrates data discovery, model updates, and view generation
- **Separation**: Updates the model independently from view generation
- **Persistence**: Periodically dumps model to disk during processing for crash recovery
- **Triggerable Steps**: Supports independent execution of:
  - Model update (discovery + analysis)
  - View generation (render dashboard from model)
  - Full pipeline (update + generate)

### Processing Strategy

The system supports efficient incremental and batched operations:

1. **Prioritized Processing Order**:
   - First: Newly discovered PRs (never analyzed before)
   - Second: Previously seen unmerged/open PRs, ordered by decreasing freshness (most recently updated first)
   - Third: Merged PRs (only in "force" mode for reprocessing)

2. **Multi-Tool Awareness**:
   - Same repository may receive multiple independent PRs for different tools (codespell, shellcheck, future additions)
   - Each tool contribution is tracked separately with its own lifecycle
   - A repository can have one tool's PR merged while another tool's PR is still open
   - Incremental updates efficiently handle repositories with multiple tool PRs

3. **Force Mode**:
   - Normal mode: Skip analysis of already-merged PRs (they're "done")
   - Force mode: Re-analyze all PRs including merged ones (for data corrections or metric recalculation)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST discover PRs from specified users (e.g., yarikoptic) across all accessible repositories on configured code hosting platforms
- **FR-002**: System MUST store discovered PR data in structured JSON files following a format similar to datalad-usage-dashboard
- **FR-003**: System MUST track PR submission date, current status (open, merged, closed), and links to the source PR
- **FR-004**: System MUST count comments on each PR and categorize them by author type (PR submitter, other humans, bots)
- **FR-005**: System MUST record the last comment from a developer (non-submitter) on each PR
- **FR-006**: System MUST record merge details for merged PRs including merge date, number of commits, and number of files changed
- **FR-007**: System MUST identify and categorize the types of automation added by the PR (GitHub Actions workflows, pre-commit hooks, other CI configurations)
- **FR-008**: System MUST generate human-readable dashboard views (README.md files) from the stored JSON data
- **FR-009**: System MUST support incremental updates that only query for changes since the last run to minimize API usage
- **FR-010**: System MUST run automatically on a schedule via GitHub Actions cron jobs
- **FR-011**: System MUST support local execution for debugging and development purposes
- **FR-012**: System MUST authenticate with code hosting platform APIs to access PR data
- **FR-013**: System MUST handle API rate limiting gracefully by respecting rate limit headers and pausing/retrying when limits are approached
- **FR-014**: System MUST support configuration of which users to track and which types of improvements to monitor
- **FR-015**: System MUST be extensible to support additional code hosting platforms beyond GitHub (e.g., Codeberg)
- **FR-016**: System MUST identify improveit tool PRs by searching for keywords (codespell, shellcheck, codespellit, shellcheckit) in PR titles
- **FR-017**: System MUST record PR titles for all tracked PRs
- **FR-018**: System MUST analyze file changes in PRs to categorize adoption level (automation configs added, datalad run records present, typo fixes only, or rejected without merge)
- **FR-019**: System MUST track time-to-first-human-response from maintainers (excluding bot responses) for each PR
- **FR-020**: System MUST identify whether the last comment on an open PR is from the submitter or from a maintainer
- **FR-021**: System MUST calculate days elapsed since the last maintainer comment for PRs awaiting submitter response
- **FR-022**: System MUST provide a filtered view or section showing PRs that need submitter response
- **FR-023**: System MUST export PR data including discussion thread context in a format suitable for AI assistant processing
- **FR-024**: System MUST calculate and display acceptance rates, average response times, and engagement metrics per repository for research analysis
- **FR-025**: System MUST categorize repository behavior patterns based on response metrics (e.g., welcoming, selective, unresponsive)
- **FR-026**: System MUST maintain clear separation between data storage (model) and presentation generation (view)
- **FR-027**: System MUST allow model updates to execute independently from view generation
- **FR-028**: System MUST allow view generation to execute independently from model updates
- **FR-029**: System MUST periodically persist the model to disk during processing to prevent data loss on crashes or interruptions
- **FR-030**: System MUST support complete regeneration of all views from the persisted model at any time
- **FR-031**: System MUST process PRs in priority order: new discoveries first, then unmerged PRs by decreasing freshness, then merged PRs only in force mode
- **FR-032**: System MUST track multiple improvement tool types (codespell, shellcheck, others) independently per repository
- **FR-033**: System MUST recognize that a single repository may have separate PRs for different tools with different states (one merged, another open)
- **FR-034**: System MUST support a "force mode" that re-analyzes previously processed merged PRs for data correction or metric recalculation
- **FR-035**: System MUST support "normal mode" that skips re-analysis of merged PRs to optimize performance
- **FR-036**: System MUST order unmerged PRs by their last update timestamp (freshness) when processing incrementally
- **FR-037**: System MUST maintain efficiency of incremental updates even when repositories have PRs for multiple different tools
- **FR-038**: System MUST create git commits with informative messages summarizing the changes discovered in each update (e.g., number of new repositories found, number of new PRs discovered, number of PRs newly merged, number of PRs closed)
- **FR-039**: System MUST include sufficient detail in commit messages to understand the timeline and evolution of tracked PRs through git history
- **FR-040**: View generation (`generate`) and data export (`export`) commands MUST NOT require GitHub API credentials since they operate only on local persisted data
- **FR-041**: System MUST support manual overrides for repository behavior categories via configuration file
- **FR-042**: Manual overrides MUST take precedence over automatically calculated behavior categories
- **FR-043**: System SHOULD support optional notes/reasons for manual overrides to document why the override was applied

### Key Entities *(include if feature involves data)*

- **Pull Request**: Represents a submitted improvement PR with attributes including:
  - Repository identifier (owner/name)
  - PR number, title, and URL
  - Author username
  - Tool type (codespell, shellcheck, or other improvement tool)
  - Submission date
  - Last updated timestamp (for freshness ordering)
  - Current status (open, merged, closed)
  - Merge date (if merged)
  - Close date (if closed without merge)
  - Number of commits (in final merged state)
  - Number of files changed
  - Improvement type (codespell, shellcheck, other)
  - Automation types added (workflow files, pre-commit configs, etc.)
  - Adoption level (full automation accepted, datalad run records only, typo fixes only, rejected)
  - Time to first human response from maintainers (in hours/days)
  - Last actor (submitter or maintainer)
  - Days since last maintainer comment (for PRs awaiting submitter response)
  - Response status (awaiting submitter, awaiting maintainer, no response yet)
  - Analysis status (never analyzed, analyzed, needs reanalysis)

- **Comment**: Represents a comment on a PR with attributes including:
  - Author username
  - Author type (PR submitter, other human, bot)
  - Comment date
  - Comment body text (especially for last developer comment)

- **Repository**: Represents a target repository that received improveit PRs with attributes including:
  - Platform (GitHub, Codeberg, etc.)
  - Owner and name
  - List of related PRs (may include multiple PRs for different tools)
  - Per-tool PR tracking (separate lists for codespell PRs, shellcheck PRs, etc.)
  - Access status (public, private, deleted)
  - Average time-to-first-response (research metric)
  - PR acceptance rate (merged / total submitted, overall and per-tool)
  - Average engagement level (comments per PR)
  - Behavior pattern category (welcoming, selective, unresponsive, hostile)

- **Configuration**: Represents system configuration with attributes including:
  - List of users to track
  - List of improvement types to monitor
  - List of platforms to query
  - API credentials/tokens
  - Update schedule settings

- **Discovery Run**: Represents a single execution of the discovery process with attributes including:
  - Run timestamp
  - Processing mode (normal or force)
  - Number of new repositories discovered
  - Number of new PRs discovered
  - Number of PRs updated (status changes, new comments, etc.)
  - Number of PRs newly merged since last run
  - Number of PRs newly closed since last run
  - Number of PRs processed (total in this run)
  - API calls made
  - Rate limit status
  - Errors encountered
  - Commit message generated (summarizing above metrics)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dashboard successfully discovers and tracks at least 95% of improveit PRs submitted by configured users (validated against known sample PRs)
- **SC-002**: Dashboard data updates complete within 10 minutes for repositories with up to 100 tracked PRs
- **SC-003**: Incremental updates reduce API calls by at least 80% compared to full re-discovery for unchanged PRs
- **SC-004**: Generated dashboard views are readable and actionable without requiring data manipulation or external tools
- **SC-005**: System operates continuously for 30 days on automated schedule without manual intervention
- **SC-006**: System correctly categorizes at least 90% of bot vs human comments (validated against manual review)
- **SC-007**: Local execution produces identical results to GitHub Actions execution for the same data set
- **SC-008**: System respects API rate limits and completes discovery without triggering rate limit failures in 99% of runs
- **SC-009**: Researchers can identify PRs needing their response within 30 seconds of viewing the dashboard
- **SC-010**: Time-to-first-response metrics are accurate within 1 hour for at least 95% of PRs (validated against manual review)
- **SC-011**: Repository behavior categorization provides meaningful differentiation between welcoming and unresponsive projects (validated through researcher review)
- **SC-012**: Exported data for AI assistant processing includes sufficient context for at least 90% of PRs to generate appropriate responses without additional API calls
- **SC-013**: Views can be completely regenerated from the model in under 2 minutes for up to 1000 tracked PRs
- **SC-014**: Model updates and view generation can be executed independently without errors or data inconsistency
- **SC-015**: System recovers from crashes without data loss by using the most recent persisted model (within last processing batch)
- **SC-016**: Incremental updates in normal mode process 100 unmerged PRs in under 5 minutes (excluding merged PRs)
- **SC-017**: Force mode successfully re-analyzes all PRs including merged ones, completing 100 PRs in under 15 minutes
- **SC-018**: System correctly tracks and processes repositories with multiple tool PRs (codespell + shellcheck) without conflation
- **SC-019**: Git commit messages provide clear summary of changes allowing humans to understand dashboard evolution from git log alone
- **SC-020**: Processing order prioritizes new PRs, with all new discoveries analyzed before any previously-seen unmerged PRs

### Assumptions

- GitHub is the primary platform for initial implementation; Codeberg and other platforms are future extensions
- API credentials with sufficient permissions will be available (read access to public repositories at minimum)
- PR identification criteria for improveit tools can be determined by examining PR titles, descriptions, or file changes
- "Incremental" operation means tracking last successful run time and querying only for events since that time
- Dashboard viewers have basic familiarity with markdown-rendered tables and lists
- The reference implementation at datalad/datalad-usage-dashboard provides suitable patterns for data storage and incremental operation
- Social research use case assumes that mass PR submissions serve as a legitimate diagnostic tool for measuring open source community health and responsiveness
- AI assistant integration assumes external tools will consume exported data; the dashboard itself does not include AI capabilities
- Behavior pattern categorization uses heuristics based on response metrics; manual researcher validation may be needed for nuanced cases
- Model data and generated views are tracked in git, with commits serving as both versioning and change logging mechanism
- "Freshness" is defined by last PR update timestamp (comments, commits, status changes, etc.) from the platform API
- Multiple tools (codespell, shellcheck) can target the same repository; they are tracked as separate contributions even if submitted by the same user

### Out of Scope

- Real-time notifications or alerts when PR status changes
- Interactive web interface (dashboard is static markdown files)
- Authentication or access control for dashboard viewers (dashboard is public)
- Editing or managing PRs through the dashboard (read-only view)
- Historical analytics beyond what can be derived from stored JSON data
- Tracking PRs from users not explicitly configured
- Deep code analysis of PR contents (only high-level file type categorization)
- Automated AI-powered PR response generation (dashboard only exports data for external AI tools)
- Sentiment analysis or natural language processing of comments beyond basic categorization
- Statistical significance testing or advanced research analytics (raw metrics provided for external analysis)
- Integration with external communication tools (email, Slack, etc.) for notifications
- Automated PR follow-up actions or reminders
