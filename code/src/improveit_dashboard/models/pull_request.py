"""PullRequest model representing an improveit PR submission."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

PRStatus = Literal["draft", "open", "merged", "closed"]
AnalysisStatus = Literal["never_analyzed", "analyzed", "needs_reanalysis"]
ResponseStatus = Literal["awaiting_submitter", "awaiting_maintainer", "no_response"]
AdoptionLevel = Literal["full_automation", "config_only", "typo_fixes", "rejected"]
ToolType = Literal["codespell", "shellcheck", "other"]
CIStatus = Literal["success", "failure", "pending"]


@dataclass
class PullRequest:
    """Represents a single improveit PR submission with all tracked metadata."""

    # Identity
    number: int
    repository: str  # "owner/repo" format
    platform: str  # "github" (future: "codeberg")
    url: str

    # Classification
    tool: ToolType
    title: str
    author: str

    # Timestamps
    created_at: datetime
    updated_at: datetime
    merged_at: datetime | None = None
    closed_at: datetime | None = None

    # Status
    status: PRStatus = "open"
    analysis_status: AnalysisStatus = "never_analyzed"

    # Metrics
    commit_count: int = 1
    files_changed: int = 1
    automation_types: list[str] = field(default_factory=list)
    adoption_level: AdoptionLevel = "typo_fixes"

    # Engagement
    total_comments: int = 0
    submitter_comments: int = 0
    maintainer_comments: int = 0
    bot_comments: int = 0
    last_comment_author: str | None = None
    last_comment_is_maintainer: bool = False
    last_maintainer_comment_at: datetime | None = None

    # Research metrics
    time_to_first_response_hours: float | None = None
    days_awaiting_submitter: int | None = None
    response_status: ResponseStatus = "no_response"

    # Incremental update support
    etag: str | None = None
    last_fetched_at: datetime | None = None

    # Context for AI assistant export
    last_developer_comment_body: str | None = None

    # CI and merge status
    has_conflicts: bool = False
    ci_status: CIStatus | None = None
    main_branch_ci: CIStatus | None = None
    codespell_workflow_ci: CIStatus | None = None

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

    def validate(self) -> list[str]:
        """Validate model constraints. Returns list of error messages."""
        errors: list[str] = []

        # Status validation
        if self.status not in ("draft", "open", "merged", "closed"):
            errors.append(f"Invalid status: {self.status}")

        if self.analysis_status not in ("never_analyzed", "analyzed", "needs_reanalysis"):
            errors.append(f"Invalid analysis_status: {self.analysis_status}")

        if self.response_status not in ("awaiting_submitter", "awaiting_maintainer", "no_response"):
            errors.append(f"Invalid response_status: {self.response_status}")

        if self.adoption_level not in ("full_automation", "config_only", "typo_fixes", "rejected"):
            errors.append(f"Invalid adoption_level: {self.adoption_level}")

        if self.tool not in ("codespell", "shellcheck", "other"):
            errors.append(f"Invalid tool: {self.tool}")

        # Merged PR must have merged_at
        if self.status == "merged" and self.merged_at is None:
            errors.append("Merged PR must have merged_at timestamp")

        # Comment count validation
        counted_comments = self.submitter_comments + self.maintainer_comments + self.bot_comments
        if self.total_comments < counted_comments:
            errors.append(
                f"total_comments ({self.total_comments}) < sum of categories ({counted_comments})"
            )

        # Commit and file counts
        if self.commit_count < 1:
            errors.append(f"commit_count must be >= 1, got {self.commit_count}")
        if self.files_changed < 1:
            errors.append(f"files_changed must be >= 1, got {self.files_changed}")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "number": self.number,
            "repository": self.repository,
            "platform": self.platform,
            "url": self.url,
            "tool": self.tool,
            "title": self.title,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "merged_at": self.merged_at.isoformat() if self.merged_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "status": self.status,
            "analysis_status": self.analysis_status,
            "commit_count": self.commit_count,
            "files_changed": self.files_changed,
            "automation_types": self.automation_types,
            "adoption_level": self.adoption_level,
            "total_comments": self.total_comments,
            "submitter_comments": self.submitter_comments,
            "maintainer_comments": self.maintainer_comments,
            "bot_comments": self.bot_comments,
            "last_comment_author": self.last_comment_author,
            "last_comment_is_maintainer": self.last_comment_is_maintainer,
            "last_maintainer_comment_at": (
                self.last_maintainer_comment_at.isoformat()
                if self.last_maintainer_comment_at
                else None
            ),
            "time_to_first_response_hours": self.time_to_first_response_hours,
            "days_awaiting_submitter": self.days_awaiting_submitter,
            "response_status": self.response_status,
            "etag": self.etag,
            "last_fetched_at": (self.last_fetched_at.isoformat() if self.last_fetched_at else None),
            "last_developer_comment_body": self.last_developer_comment_body,
            "has_conflicts": self.has_conflicts,
            "ci_status": self.ci_status,
            "main_branch_ci": self.main_branch_ci,
            "codespell_workflow_ci": self.codespell_workflow_ci,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PullRequest":
        """Create from dictionary (JSON deserialization)."""

        def parse_dt(val: str | None) -> datetime | None:
            if val is None:
                return None
            return datetime.fromisoformat(val.replace("Z", "+00:00"))

        return cls(
            number=data["number"],
            repository=data["repository"],
            platform=data["platform"],
            url=data["url"],
            tool=data["tool"],
            title=data["title"],
            author=data["author"],
            created_at=parse_dt(data["created_at"]),  # type: ignore[arg-type]
            updated_at=parse_dt(data["updated_at"]),  # type: ignore[arg-type]
            merged_at=parse_dt(data.get("merged_at")),
            closed_at=parse_dt(data.get("closed_at")),
            status=data.get("status", "open"),
            analysis_status=data.get("analysis_status", "never_analyzed"),
            commit_count=data.get("commit_count", 1),
            files_changed=data.get("files_changed", 1),
            automation_types=data.get("automation_types", []),
            adoption_level=data.get("adoption_level", "typo_fixes"),
            total_comments=data.get("total_comments", 0),
            submitter_comments=data.get("submitter_comments", 0),
            maintainer_comments=data.get("maintainer_comments", 0),
            bot_comments=data.get("bot_comments", 0),
            last_comment_author=data.get("last_comment_author"),
            last_comment_is_maintainer=data.get("last_comment_is_maintainer", False),
            last_maintainer_comment_at=parse_dt(data.get("last_maintainer_comment_at")),
            time_to_first_response_hours=data.get("time_to_first_response_hours"),
            days_awaiting_submitter=data.get("days_awaiting_submitter"),
            response_status=data.get("response_status", "no_response"),
            etag=data.get("etag"),
            last_fetched_at=parse_dt(data.get("last_fetched_at")),
            last_developer_comment_body=data.get("last_developer_comment_body"),
            has_conflicts=data.get("has_conflicts", False),
            ci_status=data.get("ci_status"),
            main_branch_ci=data.get("main_branch_ci"),
            codespell_workflow_ci=data.get("codespell_workflow_ci"),
        )
