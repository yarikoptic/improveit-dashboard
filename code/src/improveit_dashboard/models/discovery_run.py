"""DiscoveryRun model for tracking execution metadata."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

RunMode = Literal["normal", "force"]


@dataclass
class DiscoveryRun:
    """Represents metadata about a single execution (for commit messages and logging)."""

    # Execution metadata
    started_at: datetime
    completed_at: datetime | None = None
    mode: RunMode = "normal"

    # Discovered changes
    new_repositories: int = 0
    new_prs: int = 0
    updated_prs: int = 0
    newly_merged_prs: int = 0
    newly_closed_prs: int = 0
    total_processed: int = 0

    # API usage
    api_calls_made: int = 0
    rate_limit_remaining: int = 5000

    # Errors
    errors: list[str] = field(default_factory=list)

    def to_commit_message(self) -> str:
        """Generate git commit message summarizing this run."""
        lines = [
            f"Update dashboard: {self.new_prs} new PRs, {self.newly_merged_prs} merged",
            "",
            f"- Discovered {self.new_repositories} new repositories",
            f"- Found {self.new_prs} new PRs across tracked repositories",
            f"- Updated {self.updated_prs} existing PRs with new data",
            f"- {self.newly_merged_prs} PRs newly merged since last run",
            f"- {self.newly_closed_prs} PRs closed without merge",
            f"- Processed {self.total_processed} PRs total",
            f"- API calls: {self.api_calls_made}, remaining quota: {self.rate_limit_remaining}",
            "",
            f"Mode: {self.mode}",
            f"Run: {self.started_at.isoformat()}",
        ]

        if self.errors:
            lines.append("")
            lines.append(f"Errors ({len(self.errors)}):")
            for error in self.errors[:5]:  # Limit to first 5 errors
                lines.append(f"  - {error}")
            if len(self.errors) > 5:
                lines.append(f"  ... and {len(self.errors) - 5} more")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "mode": self.mode,
            "new_repositories": self.new_repositories,
            "new_prs": self.new_prs,
            "updated_prs": self.updated_prs,
            "newly_merged_prs": self.newly_merged_prs,
            "newly_closed_prs": self.newly_closed_prs,
            "total_processed": self.total_processed,
            "api_calls_made": self.api_calls_made,
            "rate_limit_remaining": self.rate_limit_remaining,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiscoveryRun":
        """Create from dictionary (JSON deserialization)."""

        def parse_dt(val: str | None) -> datetime | None:
            if val is None:
                return None
            return datetime.fromisoformat(val.replace("Z", "+00:00"))

        return cls(
            started_at=parse_dt(data["started_at"]),  # type: ignore[arg-type]
            completed_at=parse_dt(data.get("completed_at")),
            mode=data.get("mode", "normal"),
            new_repositories=data.get("new_repositories", 0),
            new_prs=data.get("new_prs", 0),
            updated_prs=data.get("updated_prs", 0),
            newly_merged_prs=data.get("newly_merged_prs", 0),
            newly_closed_prs=data.get("newly_closed_prs", 0),
            total_processed=data.get("total_processed", 0),
            api_calls_made=data.get("api_calls_made", 0),
            rate_limit_remaining=data.get("rate_limit_remaining", 5000),
            errors=data.get("errors", []),
        )
