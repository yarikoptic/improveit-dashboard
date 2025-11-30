"""Comment model for PR comment analysis."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

AuthorType = Literal["submitter", "maintainer", "bot"]


@dataclass
class Comment:
    """Represents a comment on a PR (used during analysis)."""

    id: int
    author: str
    author_type: AuthorType
    body: str
    created_at: datetime
    is_bot: bool

    def validate(self) -> list[str]:
        """Validate model constraints. Returns list of error messages."""
        errors: list[str] = []

        if self.author_type not in ("submitter", "maintainer", "bot"):
            errors.append(f"Invalid author_type: {self.author_type}")

        # If is_bot is True, author_type must be "bot"
        if self.is_bot and self.author_type != "bot":
            errors.append("is_bot=True but author_type is not 'bot'")

        return errors

    @classmethod
    def from_github_response(cls, data: dict[str, Any], pr_author: str) -> "Comment":
        """Create from GitHub API response.

        Args:
            data: GitHub API comment response
            pr_author: Username of the PR author (for classification)
        """
        user = data["user"]
        login = user["login"]
        user_type = user.get("type", "User")

        # Determine if bot
        is_bot = user_type == "Bot" or login.endswith("[bot]")

        # Determine author type
        if is_bot:
            author_type: AuthorType = "bot"
        elif login == pr_author:
            author_type = "submitter"
        else:
            author_type = "maintainer"

        # Parse created_at
        created_at_str = data["created_at"]
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))

        return cls(
            id=data["id"],
            author=login,
            author_type=author_type,
            body=data.get("body", ""),
            created_at=created_at,
            is_bot=is_bot,
        )
