<!--
  ============================================================================
  SYNC IMPACT REPORT
  ============================================================================
  Version Change: 1.0.0 → 2.0.0

  Modified Principles:
  - I. Open Source First → I. Open Source First (refined: emphasize upstream focus)
  - II. Automation by Default → II. Automation by Default (refined: project-specific)
  - III. Contribution Welcoming → III. Be a Good Guest (reframed for upstream PRs)
  - IV. Transparency → merged into other principles
  - V. Minimal Human Dependency → merged into II. Automation by Default

  Added Sections:
  - IV. Code Hygiene as a Service
  - V. Welcoming Community

  Removed Sections:
  - IV. Transparency (folded into I and V)
  - V. Minimal Human Dependency (folded into II)
  - Development Standards (overly generic, replaced with project-specific guidance)
  - Contribution Guidelines (overly generic, replaced with focused section)

  Templates Requiring Updates:
  - ⚠ .specify/templates/plan-template.md (Constitution Check references need review)
  - ⚠ .specify/templates/spec-template.md (pending validation)
  - ⚠ .specify/templates/tasks-template.md (pending validation)

  Follow-up TODOs:
  - None
  ============================================================================
-->

# ImproveIt Dashboard Constitution

## Mission

ImproveIt Dashboard tracks and coordinates automated code quality improvements
(codespell, shellcheck, and similar tools) across open source repositories.
We send PRs to projects we do not own, which makes respectful community
engagement and automation hygiene central to everything we do.

## Core Principles

### I. Open Source First

All code, data, and processes in this project MUST be open source under
OSI-approved licenses. The dashboard itself is MIT-licensed.

This project exists to improve the open source ecosystem. Every dependency
MUST have a compatible open source license. Generated data (PR tracking,
responsiveness metrics) MUST be publicly accessible so other contributors
and communities can benefit.

**Rationale**: We ask other projects to accept our contributions. We MUST
hold ourselves to at least the same openness standard we expect from them.

### II. Automation by Default

All repeatable operations MUST be automated. Manual steps are technical debt.

**Mandatory automation areas**:
- Dashboard data collection and report generation (GitHub Actions)
- Code quality checks on our own code (linting, formatting, type checking)
- PR creation and tracking across upstream repositories
- Dependency updates and security scanning
- Release and deployment processes

**Self-sufficiency**: The project MUST function with minimal ongoing human
intervention. Automated tests MUST catch regressions. Bots and scheduled
workflows MUST handle routine maintenance. The dashboard MUST update itself
without manual triggers.

**Rationale**: We send improvement PRs to hundreds of repositories. This
only works at scale through automation. Our own project MUST exemplify
the automation practices we advocate for.

### III. Be a Good Guest

When we send PRs to repositories we do not own, we are guests in someone
else's project. This privilege requires:

- **Respect maintainer decisions**: If a PR is closed without merge, accept
  it gracefully. Do not reopen or argue. Track the outcome and move on.
- **Minimal noise**: PRs MUST be small, focused, and self-explanatory.
  Each PR SHOULD fix one category of issue (e.g., only typos, or only
  shellcheck warnings). Do not bundle unrelated changes.
- **Responsive follow-up**: When maintainers request changes, respond
  within 48 hours. Stale PRs waste maintainer attention.
- **No pressure**: Never ping, nag, or publicly pressure maintainers to
  merge. Their project, their timeline.
- **Accurate descriptions**: PR descriptions MUST explain what tool found
  the issue and why the fix is correct. Maintainers SHOULD be able to
  evaluate the PR without running the tool themselves.
- **Track responsiveness, do not judge**: The dashboard categorizes
  repositories by response patterns (welcoming, selective, unresponsive).
  These categories are descriptive, not judgmental. Every project has
  different priorities and bandwidth.

**Rationale**: Our ability to contribute depends on maintainers trusting
that our PRs are helpful, not burdensome. One bad interaction can close
doors across an entire community.

### IV. Code Hygiene as a Service

The core mission is improving code quality across the open source ecosystem.
This means:

- **Tool accuracy**: Fixes we propose MUST be correct. A false positive
  that breaks a build destroys trust. When in doubt, skip the fix.
- **Tool transparency**: PR descriptions MUST identify which tool and
  version produced the suggestion so maintainers can evaluate and
  reproduce.
- **Incremental improvement**: Small, correct fixes are better than
  ambitious changes. A single typo fix that merges cleanly is worth more
  than a sweeping refactor that sits unreviewed.
- **Eat our own cooking**: This project MUST pass all the same quality
  checks (codespell, ruff, mypy, shellcheck) that we recommend to others.
  Our CI pipeline MUST enforce this.

**Rationale**: We are in the business of code hygiene. If our own code
does not meet the standards we advocate, we lose credibility.

### V. Welcoming Community

This project MUST actively lower barriers to participation:

- **Clear setup**: README MUST include a quick-start guide achievable in
  under 10 minutes. Development environment setup MUST be automated
  (`uv` + `tox`).
- **Good first issues**: Maintain labeled issues suitable for new
  contributors, with mentorship offers where appropriate.
- **Constructive review**: Code review MUST be specific, actionable, and
  kind. Nitpicks MUST be labeled as such and MUST NOT block merging.
  Approve PRs that improve the codebase, even if not perfect.
- **Fast feedback**: Target initial response to PRs and issues within
  48 hours. Automated checks MUST provide actionable feedback so
  contributors do not wait for humans.
- **Equal treatment**: PRs from new contributors receive the same
  priority and respect as those from core team members.
- **Public decisions**: Design discussions and architecture decisions
  MUST happen in public channels (issues, PRs, discussions). No private
  channels for project decisions.

**Rationale**: A healthy open source project depends on community
contributions. Making contribution easy and welcoming grows the
contributor base and distributes maintenance burden. We also model the
community behavior we hope to see in projects we contribute to.

## Governance

### Constitution Authority

This constitution supersedes all other project documentation in cases of
conflict. All PRs, issues, and decisions MUST be evaluated against these
principles. Violations of core principles (I-V) MUST be rejected unless
the constitution is formally amended first.

### Amendment Process

1. Propose amendment via GitHub issue with "constitution-amendment" label
2. Community discussion period (minimum 14 days)
3. Address feedback and refine proposal
4. Maintainer approval (requires consensus among active maintainers)
5. Update constitution with new version and rationale
6. Cascade changes to all dependent templates and documentation

### Versioning Policy

Constitution follows semantic versioning:
- **MAJOR**: Removal or fundamental redefinition of a core principle
- **MINOR**: Addition of new principle or material expansion of guidance
- **PATCH**: Clarifications, wording improvements, typo fixes

### Compliance Review

- Every PR MUST pass automated quality checks (ruff, mypy, codespell)
- Quarterly review of upstream PR responsiveness metrics
- Annual audit of automation coverage

### Complexity Justification

Any introduction of complexity MUST be explicitly justified with:
- Why the complexity is necessary
- What simpler alternatives were considered
- A plan for future simplification if possible

**Version**: 2.0.0 | **Ratified**: 2025-11-27 | **Last Amended**: 2026-03-21
