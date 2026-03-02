"""Review state service for persisting review progress."""
import json
from pathlib import Path
from typing import Any, Optional


VALID_TYPES = {"weekly", "monthly", "quarterly"}


class ReviewStateService:
    """Manage review state files for weekly/monthly/quarterly reviews."""

    def __init__(self, data_dir: Path):
        self.reviews_dir = data_dir / "reviews"
        self.reviews_dir.mkdir(parents=True, exist_ok=True)

    def _validate_type(self, review_type: str) -> None:
        if review_type not in VALID_TYPES:
            raise ValueError(f"Invalid review type: {review_type}. Must be one of {VALID_TYPES}")

    def _state_path(self, review_type: str) -> Path:
        return self.reviews_dir / f"{review_type}-state.json"

    def get_state(self, review_type: str) -> Optional[dict[str, Any]]:
        """Load review state. Returns None if no active review."""
        self._validate_type(review_type)
        path = self._state_path(review_type)
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def save_state(self, review_type: str, state: dict[str, Any]) -> None:
        """Save review state."""
        self._validate_type(review_type)
        path = self._state_path(review_type)
        path.write_text(json.dumps(state, indent=2, default=str))

    def clear_state(self, review_type: str) -> None:
        """Clear review state (after review completion)."""
        self._validate_type(review_type)
        path = self._state_path(review_type)
        if path.exists():
            path.unlink()
