"""Atomic JSON persistence for model data."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from improveit_dashboard.models.discovery_run import DiscoveryRun
from improveit_dashboard.models.repository import Repository
from improveit_dashboard.utils.logging import get_logger

logger = get_logger(__name__)


# JSON file format version
MODEL_VERSION = "1.0"


def load_model(path: Path) -> tuple[dict[str, Repository], DiscoveryRun | None]:
    """Load model from JSON file.

    Args:
        path: Path to repositories.json

    Returns:
        Tuple of (repositories dict, last run info)
        - repositories: Dict mapping full_name to Repository
        - last_run: DiscoveryRun from last execution or None
    """
    if not path.exists():
        logger.info(f"No existing model at {path}, starting fresh")
        return {}, None

    logger.info(f"Loading model from {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Check version
    meta = data.get("meta", {})
    version = meta.get("version", "1.0")
    if version != MODEL_VERSION:
        logger.warning(f"Model version mismatch: {version} != {MODEL_VERSION}")

    # Parse repositories
    repositories: dict[str, Repository] = {}
    for full_name, repo_data in data.get("repositories", {}).items():
        try:
            repo = Repository.from_dict(repo_data)
            repositories[full_name] = repo
        except Exception as e:
            logger.error(f"Failed to parse repository {full_name}: {e}")

    # Parse last run
    last_run = None
    if "last_run" in meta:
        try:
            last_run = DiscoveryRun.from_dict(meta["last_run"])
        except Exception as e:
            logger.error(f"Failed to parse last_run: {e}")

    logger.info(f"Loaded {len(repositories)} repositories")
    return repositories, last_run


def save_model(
    path: Path,
    repositories: dict[str, Repository],
    last_run: DiscoveryRun | None = None,
) -> None:
    """Save model to JSON file atomically.

    Uses temp file + rename for crash safety.

    Args:
        path: Path to repositories.json
        repositories: Dict mapping full_name to Repository
        last_run: DiscoveryRun from current execution
    """
    logger.info(f"Saving model to {path}")

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Build model data
    data: dict[str, Any] = {
        "meta": {
            "version": MODEL_VERSION,
            "last_updated": datetime.utcnow().isoformat() + "Z",
        },
        "repositories": {},
    }

    if last_run:
        data["meta"]["last_run"] = last_run.to_dict()

    # Serialize repositories
    for full_name, repo in sorted(repositories.items()):
        data["repositories"][full_name] = repo.to_dict()

    # Write to temp file
    temp_path = path.with_suffix(".json.tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        # Atomic rename
        temp_path.rename(path)
        logger.info(f"Saved {len(repositories)} repositories to {path}")

    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise


def get_last_updated(path: Path) -> datetime | None:
    """Get the last_updated timestamp from model file.

    Useful for incremental updates without loading full model.

    Args:
        path: Path to repositories.json

    Returns:
        Last updated datetime or None if file doesn't exist
    """
    if not path.exists():
        return None

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("meta", {})
    last_updated_str = meta.get("last_updated")

    if last_updated_str:
        return datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))

    return None
