"""Configuration model for discovery and processing."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, cast

import yaml

# Valid behavior categories
BehaviorCategory = Literal["welcoming", "selective", "unresponsive", "hostile", "insufficient_data"]
VALID_BEHAVIOR_CATEGORIES: frozenset[str] = frozenset(
    ["welcoming", "selective", "unresponsive", "hostile", "insufficient_data"]
)


@dataclass
class RepositoryOverride:
    """Manual override for repository behavior category."""

    category: BehaviorCategory
    note: str | None = None

    def validate(self) -> list[str]:
        """Validate override. Returns list of error messages."""
        errors: list[str] = []
        if self.category not in VALID_BEHAVIOR_CATEGORIES:
            errors.append(
                f"Invalid category '{self.category}'. "
                f"Must be one of: {', '.join(sorted(VALID_BEHAVIOR_CATEGORIES))}"
            )
        return errors


@dataclass
class Configuration:
    """Represents system configuration for discovery and processing."""

    # Discovery settings
    tracked_users: list[str] = field(default_factory=lambda: ["yarikoptic", "DimitriPapadopoulos"])
    tool_keywords: dict[str, list[str]] = field(
        default_factory=lambda: {
            "codespell": ["codespell", "codespellit"],
            "shellcheck": ["shellcheck", "shellcheckit"],
        }
    )
    platforms: list[str] = field(default_factory=lambda: ["github"])

    # API settings
    github_token: str = ""
    rate_limit_threshold: int = 100

    # Processing settings
    force_mode: bool = False
    batch_size: int = 10
    max_prs_per_run: int | None = None

    # Paths
    data_file: Path = field(default_factory=lambda: Path("data/repositories.json"))
    output_readme: Path = field(default_factory=lambda: Path("README.md"))
    output_readmes_dir: Path = field(default_factory=lambda: Path("READMEs"))
    output_summaries_dir: Path = field(default_factory=lambda: Path("Summaries"))

    # Manual overrides for repository behavior categories
    repository_overrides: dict[str, RepositoryOverride] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Post-initialization processing."""
        # Load token from environment if not set
        if not self.github_token:
            self.github_token = os.getenv("GITHUB_TOKEN", "")

        # Ensure paths are Path objects
        if isinstance(self.data_file, str):
            self.data_file = Path(self.data_file)
        if isinstance(self.output_readme, str):
            self.output_readme = Path(self.output_readme)
        if isinstance(self.output_readmes_dir, str):
            self.output_readmes_dir = Path(self.output_readmes_dir)
        if isinstance(self.output_summaries_dir, str):
            self.output_summaries_dir = Path(self.output_summaries_dir)

    @classmethod
    def from_file(cls, path: Path) -> "Configuration":
        """Load configuration from YAML file."""
        if not path.exists():
            return cls()

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls._from_dict(data)

    @classmethod
    def from_env(cls) -> "Configuration":
        """Load configuration from environment variables."""
        config = cls()

        # Override with environment variables
        if env_token := os.getenv("GITHUB_TOKEN"):
            config.github_token = env_token

        if env_force := os.getenv("IMPROVEIT_FORCE_MODE"):
            config.force_mode = env_force.lower() in ("true", "1", "yes")

        if env_max := os.getenv("IMPROVEIT_MAX_PRS"):
            config.max_prs_per_run = int(env_max)

        if env_batch := os.getenv("IMPROVEIT_BATCH_SIZE"):
            config.batch_size = int(env_batch)

        if env_threshold := os.getenv("IMPROVEIT_RATE_LIMIT_THRESHOLD"):
            config.rate_limit_threshold = int(env_threshold)

        if env_data_file := os.getenv("IMPROVEIT_DATA_FILE"):
            config.data_file = Path(env_data_file)

        return config

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Configuration":
        """Create configuration from dictionary."""
        kwargs: dict[str, Any] = {}

        if "tracked_users" in data:
            kwargs["tracked_users"] = data["tracked_users"]

        if "tool_keywords" in data:
            kwargs["tool_keywords"] = data["tool_keywords"]

        if "platforms" in data:
            kwargs["platforms"] = data["platforms"]

        if "github_token" in data:
            kwargs["github_token"] = data["github_token"]

        if "rate_limit_threshold" in data:
            kwargs["rate_limit_threshold"] = data["rate_limit_threshold"]

        if "force_mode" in data:
            kwargs["force_mode"] = data["force_mode"]

        if "batch_size" in data:
            kwargs["batch_size"] = data["batch_size"]

        if "max_prs_per_run" in data:
            kwargs["max_prs_per_run"] = data["max_prs_per_run"]

        if "data_file" in data:
            kwargs["data_file"] = Path(data["data_file"])

        if "output_readme" in data:
            kwargs["output_readme"] = Path(data["output_readme"])

        if "output_readmes_dir" in data:
            kwargs["output_readmes_dir"] = Path(data["output_readmes_dir"])

        if "output_summaries_dir" in data:
            kwargs["output_summaries_dir"] = Path(data["output_summaries_dir"])

        if "repository_overrides" in data:
            overrides: dict[str, RepositoryOverride] = {}
            for repo_name, override_data in data["repository_overrides"].items():
                if isinstance(override_data, dict):
                    # Cast is safe - validation will catch invalid categories
                    category = cast(
                        BehaviorCategory,
                        override_data.get("category", "insufficient_data"),
                    )
                    overrides[repo_name] = RepositoryOverride(
                        category=category,
                        note=override_data.get("note"),
                    )
                elif isinstance(override_data, str):
                    # Allow shorthand: repo_name: category
                    # Cast is safe - validation will catch invalid categories
                    overrides[repo_name] = RepositoryOverride(
                        category=cast(BehaviorCategory, override_data)
                    )
            kwargs["repository_overrides"] = overrides

        return cls(**kwargs)

    def validate(self) -> list[str]:
        """Validate configuration. Returns list of error messages."""
        errors: list[str] = []

        if not self.tracked_users:
            errors.append("tracked_users cannot be empty")

        if not self.platforms:
            errors.append("platforms cannot be empty")

        if self.rate_limit_threshold < 0:
            errors.append("rate_limit_threshold must be non-negative")

        if self.batch_size < 1:
            errors.append("batch_size must be at least 1")

        if self.max_prs_per_run is not None and self.max_prs_per_run < 1:
            errors.append("max_prs_per_run must be at least 1 if set")

        # Validate repository overrides
        for repo_name, override in self.repository_overrides.items():
            override_errors = override.validate()
            for err in override_errors:
                errors.append(f"repository_overrides[{repo_name}]: {err}")

        return errors

    def get_behavior_override(self, repo_full_name: str) -> RepositoryOverride | None:
        """Get manual override for a repository's behavior category.

        Args:
            repo_full_name: Repository full name (e.g., "owner/repo")

        Returns:
            RepositoryOverride if override exists, None otherwise
        """
        return self.repository_overrides.get(repo_full_name)

    def get_all_keywords(self) -> list[str]:
        """Get flat list of all tool keywords."""
        keywords: list[str] = []
        for kw_list in self.tool_keywords.values():
            keywords.extend(kw_list)
        return keywords

    def get_tool_for_title(self, title: str) -> str:
        """Determine tool type from PR title.

        Returns the first matching tool or 'other' if no match.
        """
        title_lower = title.lower()
        for tool, keywords in self.tool_keywords.items():
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    return tool
        return "other"
