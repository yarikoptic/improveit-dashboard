"""Repository model representing a target repository that received improveit PRs."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from improveit_dashboard.models.pull_request import PullRequest

BehaviorCategory = Literal["welcoming", "selective", "unresponsive", "hostile", "insufficient_data"]


@dataclass
class Repository:
    """Represents a repository that received improveit PRs with aggregate metrics."""

    # Identity
    owner: str
    name: str
    platform: str  # "github"
    url: str

    # PR tracking (keyed by PR number)
    prs: dict[int, PullRequest] = field(default_factory=dict)

    # Per-tool tracking (PR numbers)
    codespell_prs: list[int] = field(default_factory=list)
    shellcheck_prs: list[int] = field(default_factory=list)
    other_prs: list[int] = field(default_factory=list)

    # Access status
    accessible: bool = True

    # Research metrics (aggregated)
    avg_time_to_first_response_hours: float | None = None
    pr_acceptance_rate: float = 0.0
    avg_engagement_level: float = 0.0
    behavior_category: BehaviorCategory = "insufficient_data"

    # Incremental update
    last_checked_at: datetime | None = None
    repository_updated_at: datetime | None = None

    @property
    def full_name(self) -> str:
        """Return owner/name format."""
        return f"{self.owner}/{self.name}"

    @property
    def total_prs(self) -> int:
        """Return total number of PRs."""
        return len(self.prs)

    @property
    def merged_count(self) -> int:
        """Return count of merged PRs."""
        return sum(1 for pr in self.prs.values() if pr.status == "merged")

    @property
    def open_count(self) -> int:
        """Return count of open PRs."""
        return sum(1 for pr in self.prs.values() if pr.status == "open")

    @property
    def draft_count(self) -> int:
        """Return count of draft PRs."""
        return sum(1 for pr in self.prs.values() if pr.status == "draft")

    @property
    def closed_count(self) -> int:
        """Return count of closed (not merged) PRs."""
        return sum(1 for pr in self.prs.values() if pr.status == "closed")

    def add_pr(self, pr: PullRequest) -> None:
        """Add a PR to this repository."""
        self.prs[pr.number] = pr

        # Update tool-specific lists
        if pr.tool == "codespell" and pr.number not in self.codespell_prs:
            self.codespell_prs.append(pr.number)
        elif pr.tool == "shellcheck" and pr.number not in self.shellcheck_prs:
            self.shellcheck_prs.append(pr.number)
        elif pr.tool == "other" and pr.number not in self.other_prs:
            self.other_prs.append(pr.number)

    def recalculate_metrics(self) -> None:
        """Recalculate aggregate metrics from PRs."""
        if not self.prs:
            self.avg_time_to_first_response_hours = None
            self.pr_acceptance_rate = 0.0
            self.avg_engagement_level = 0.0
            self.behavior_category = "insufficient_data"
            return

        # Calculate acceptance rate
        total = len(self.prs)
        merged = self.merged_count
        self.pr_acceptance_rate = merged / total if total > 0 else 0.0

        # Calculate average time to first response
        response_times = [
            pr.time_to_first_response_hours
            for pr in self.prs.values()
            if pr.time_to_first_response_hours is not None
        ]
        if response_times:
            self.avg_time_to_first_response_hours = sum(response_times) / len(response_times)
        else:
            self.avg_time_to_first_response_hours = None

        # Calculate average engagement
        total_comments = sum(pr.total_comments for pr in self.prs.values())
        self.avg_engagement_level = total_comments / total if total > 0 else 0.0

        # Categorize behavior
        self.behavior_category = self._categorize_behavior()

    def _categorize_behavior(self) -> BehaviorCategory:
        """Categorize repository responsiveness based on metrics."""
        if self.total_prs < 2:
            return "insufficient_data"

        # Welcoming: fast response, high acceptance
        if (
            self.avg_time_to_first_response_hours is not None
            and self.avg_time_to_first_response_hours < 72
            and self.pr_acceptance_rate > 0.7
        ):
            return "welcoming"

        # Selective: slow response but some acceptance
        if self.pr_acceptance_rate > 0.3:
            return "selective"

        # Hostile: quick rejection without merge
        if (
            self.pr_acceptance_rate == 0
            and self.avg_time_to_first_response_hours is not None
            and self.avg_time_to_first_response_hours < 24
        ):
            return "hostile"

        # Unresponsive: very slow or no responses
        if (
            self.avg_time_to_first_response_hours is None
            or self.avg_time_to_first_response_hours > 168  # 1 week
        ):
            return "unresponsive"

        return "unresponsive"

    def validate(self) -> list[str]:
        """Validate model constraints. Returns list of error messages."""
        errors: list[str] = []

        if not 0.0 <= self.pr_acceptance_rate <= 1.0:
            errors.append(
                f"pr_acceptance_rate must be between 0.0 and 1.0, got {self.pr_acceptance_rate}"
            )

        valid_categories = (
            "welcoming",
            "selective",
            "unresponsive",
            "hostile",
            "insufficient_data",
        )
        if self.behavior_category not in valid_categories:
            errors.append(f"Invalid behavior_category: {self.behavior_category}")

        # Verify tool PR lists match prs dict
        for pr_num in self.codespell_prs + self.shellcheck_prs + self.other_prs:
            if pr_num not in self.prs:
                errors.append(f"PR number {pr_num} in tool list but not in prs dict")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "owner": self.owner,
            "name": self.name,
            "platform": self.platform,
            "full_name": self.full_name,
            "url": self.url,
            "accessible": self.accessible,
            "last_checked_at": (self.last_checked_at.isoformat() if self.last_checked_at else None),
            "repository_updated_at": (
                self.repository_updated_at.isoformat() if self.repository_updated_at else None
            ),
            "codespell_prs": self.codespell_prs,
            "shellcheck_prs": self.shellcheck_prs,
            "other_prs": self.other_prs,
            "avg_time_to_first_response_hours": self.avg_time_to_first_response_hours,
            "pr_acceptance_rate": self.pr_acceptance_rate,
            "avg_engagement_level": self.avg_engagement_level,
            "behavior_category": self.behavior_category,
            "prs": {str(num): pr.to_dict() for num, pr in self.prs.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Repository":
        """Create from dictionary (JSON deserialization)."""

        def parse_dt(val: str | None) -> datetime | None:
            if val is None:
                return None
            return datetime.fromisoformat(val.replace("Z", "+00:00"))

        # Parse PRs
        prs_dict: dict[int, PullRequest] = {}
        for num_str, pr_data in data.get("prs", {}).items():
            pr = PullRequest.from_dict(pr_data)
            prs_dict[int(num_str)] = pr

        return cls(
            owner=data["owner"],
            name=data["name"],
            platform=data["platform"],
            url=data["url"],
            prs=prs_dict,
            codespell_prs=data.get("codespell_prs", []),
            shellcheck_prs=data.get("shellcheck_prs", []),
            other_prs=data.get("other_prs", []),
            accessible=data.get("accessible", True),
            avg_time_to_first_response_hours=data.get("avg_time_to_first_response_hours"),
            pr_acceptance_rate=data.get("pr_acceptance_rate", 0.0),
            avg_engagement_level=data.get("avg_engagement_level", 0.0),
            behavior_category=data.get("behavior_category", "insufficient_data"),
            last_checked_at=parse_dt(data.get("last_checked_at")),
            repository_updated_at=parse_dt(data.get("repository_updated_at")),
        )
