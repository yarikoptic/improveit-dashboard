"""Comment model for PR comment analysis."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

AuthorType = Literal["submitter", "maintainer", "bot"]

# Known bot usernames that may not have [bot] suffix
KNOWN_BOT_USERNAMES = frozenset(
    {
        "codecov",
        "coveralls",
        "dependabot",
        "renovate",
        "greenkeeper",
        "snyk-bot",
        "imgbot",
        "stale",
        "allcontributors",
        "semantic-release-bot",
        "github-actions",
        "CLAassistant",
        "cla-bot",
        "linux-foundation-easycla",
        "easycla",
    }
)

# Bot message patterns (case-insensitive prefixes/contains)
BOT_MESSAGE_PATTERNS = [
    "all committers have signed the cla",
    "cla check",
    "cla signature",
    "contributor license agreement",
    "coverage report",
    "codecov report",
    "this pull request has been automatically marked as stale",
    "codacy",
    "sonarcloud",
    "thank you for your contribution",  # Generic bot message
]


def _is_bot_message(body: str) -> bool:
    """Check if comment body matches known bot message patterns."""
    body_lower = body.lower().strip()
    for pattern in BOT_MESSAGE_PATTERNS:
        if pattern in body_lower:
            return True
    return False


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
        body = data.get("body", "")

        # Determine if bot (multiple detection methods)
        is_bot = (
            user_type == "Bot"
            or login.endswith("[bot]")
            or login.lower() in KNOWN_BOT_USERNAMES
            or _is_bot_message(body)
        )

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
            body=body,
            created_at=created_at,
            is_bot=is_bot,
        )
